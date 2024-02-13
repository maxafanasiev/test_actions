import fs from 'fs/promises'
import Papa from 'papaparse'
import {fetch_html, map_series} from '../fetch/helpers.js'
import {priority_match} from './approx_match.js'
import {first_last_name, get_initials, remove_email_block, shorten_whitespace, split_caps} from './simplify_name.js'
import {load_correction_data, merge_failed} from './helpers.js'

/**
 * Fetches the list of page urls from the coroner society website
 *
 * @param {string} url the coroner society url
 * @returns {Promise<string[]>} the list of page urls
 */
async function fetch_page_urls(url) {
    const $ = await fetch_html(url)

    // determine how many pages we need to search and the urls for those pages
    const last_path = 'ul.paging > li.last > a'
    const last_url = $(last_path).attr('href')
    const last_num = Number(last_url.match(/\/coroners\/_\/(\d+)\//)[1])

    return Array.from({length: last_num}, (_, i) => `${url}_/${i + 1}/`)
}

/**
 * Fetches the list of coroners from a coroner page
 *
 * @param {string} page_url the url of the coroner page to fetch names from
 * @returns {Promise<{name: string, title: string, role: string, email: string}[]>} the list of coroners on the page
 */
async function fetch_page(page_url) {
    const $ = await fetch_html(page_url)
    const people = $('ul.people > li')

    return people.get().map(person => {
        // fetches the name, title, role, and email of a coroner
        // role is a bit dodgy here, it can be an area, "Retired", "Honorary", etc
        // email may not always be present, but the rest seem consistent
        const elem = $(person)
        const name = elem.find('a').text()
        const [title, role] = elem
            .find('span')
            .get()
            .map(span => $(span).text())

        return {name, title, role}
    })
}

/**
 * Fetches the list of coroners from the coroner society website
 *
 * @param {string} url the coroner society url
 * @returns {Promise<{name: string, title: string, role: string, email: string}[]>} the list of coroners
 */
async function fetch_name_list(url) {
    const page_urls = await fetch_page_urls(url)
    const pages = await map_series(
        page_urls,
        fetch_page,
        'Fetching coroners |:bar| :current/:total pages'
    )
    return pages.flat()
}

async function removeDuplicatesFromCsv(filePath) {
    try {
        const fileContent = await fs.readFile(filePath, 'utf8');

        const parsedContent = Papa.parse(fileContent, {header: true});
        const rows = parsedContent.data;

        let counter = 0
        const uniqueRows = new Map();
        rows.forEach(row => {
            const uniqueKey = row['name'];
            if (!uniqueRows.has(uniqueKey)) {
                uniqueRows.set(uniqueKey, row);
                counter += 1;
            }
        });

        const uniqueRowsArray = Array.from(uniqueRows.values());
        const updatedCsv = Papa.unparse(uniqueRowsArray);

        await fs.writeFile(filePath, updatedCsv);
        console.log(`${counter} duplicates deleted`);
    } catch (error) {
        console.error('Error while deleting duplicates in CSV:', error);
    }
}

async function appendNewRowsToCsv(filePath, newData) {
    try {
        const existingContent = await fs.readFile(filePath, 'utf8');

        const parsedExistingContent = Papa.parse(existingContent, {header: true});
        const existingRows = parsedExistingContent.data;

        const existingNames = new Set(existingRows.map(row => row[Object.keys(row)[0]]));
        const newRows = newData.filter(row => !existingNames.has(row[Object.keys(row)[0]]));

        if (newRows.length > 0) {
            const newRowsCsv = Papa.unparse(newRows, {header: false});

            await fs.appendFile(filePath, "\n" + newRowsCsv);
        }
        console.log(`Appended ${newRows.length} new rows to ${filePath}`);
    } catch (error) {
        console.error('Error appending new rows to CSV:', error);
    }
}

/**
 * Calculates a list of possible replacements for a name map, with different
 * levels of simplification and priorities
 * @param {{[key: string]: string}} full_name_map a map from a simple to match name to the full name
 * @returns {{[key: string]: string}[]} a list of maps from a name to the full name, with different levels of simplification
 */
function replacements_from(full_name_map) {
    const full_names = Object.entries(full_name_map)
    const short_names = full_names.map(([full_name, name]) => [
        first_last_name(full_name),
        name
    ])
    const initials = short_names.flatMap(([short_name, name]) =>
        get_initials(short_name).map(initial => [initial, name])
    )

    // replacements have priority as so:
    // 1. match on full name
    // 2. match on shortened name (first and last name only)
    // 3. match on initials
    return [
        full_name_map,
        Object.fromEntries(short_names),
        Object.fromEntries(initials)
    ]
}

/**
 * Creates a function that corrects the coroner name to the closest match in the
 * coroner society list and saves the failed matches on close
 * @param {boolean} keep_failed whether to keep existing failed parses
 * @returns {Promise<import('.').CorrectFn<string>>}
 */
export default async function Corrector(keep_failed = true) {
    const fetched = await fetch_name_list(
        'https://www.coronersociety.org.uk/coroners/'
    )

    // const fetched1 = await fetch_name_list(
    //     'https://www.coronersociety.org.uk/coroners/'
    // )
    // const fetched2 = await fetch_name_list(
    //     'https://www.coronersociety.org.uk/coroners/'
    // )
    // const fetched3 = await fetch_name_list(
    //     'https://www.coronersociety.org.uk/coroners/'
    // )
    //
    // let fetched = [...fetched1, ...fetched2, ...fetched3];
    console.log(fetched.length)
    let fetched_simple = fetched.map(({name, ...rest}) => ({
        name: shorten_whitespace(remove_email_block(name)),
        ...rest
    }))

    console.log(fetched_simple.length)


    // await fs.writeFile(
    //     './src/data/coroners-society.csv',
    //     Papa.unparse(fetched_simple)
    // )
    const fetched_replace = Object.fromEntries(
        fetched_simple.map(({name}) => [name, name])
    )
    console.log(Object.keys(fetched_replace).length)

    await fs.writeFile(
        './src/correct/data/fetched_names.json',
        JSON.stringify(fetched_replace, null, 2)
    )

    let {failed, incorrect, corrections} = await load_correction_data('names')
    if (!keep_failed) failed = []

    const replacements = [
        ...replacements_from(fetched_replace),
        ...corrections.flatMap(replacements_from)
    ]

    function correct_name(text) {
        if (text === undefined || text.length === 0) return undefined
        if (incorrect.has(text)) return undefined

        const name = split_caps(text)
        const match = priority_match(name, replacements, 2, 0.2, true)
        if (match === undefined) {
            failed.push(text)
            return text
        }
        return match
    }

    fetched_simple = fetched_simple.map(item => ({
        ...item,
        name: correct_name(item.name) || item.name
    }));
    await appendNewRowsToCsv('./src/data/coroners-society.csv', fetched_simple)
    await removeDuplicatesFromCsv('./src/data/coroners-society.csv')


    correct_name.close = () =>
        fs.writeFile(
            './src/correct/failed_parses/names.json',
            JSON.stringify(merge_failed(failed, get_initials), null, 2)
        )
    return correct_name
}
