import {table_parser} from './helpers.js'
/** @typedef {import('./helpers.js').Parser} Parser */
/** @typedef {import('./helpers.js').HeadersFor} HeadersFor */

/** A very basic format for the reports, each field is just a string
 *
 * Fields marked with a `*` are probably going to be refactored into a more
 * accurate form, i.e. dates into 3-tuples, `to` field into a list of names,
 * etc...
 *
 * @typedef Basic_Report
 * @type {object}
 * @prop {string} this_report_is_being_sent_to *
 * @prop {string} coroner_name *
 * @prop {string} legal *
 * @prop {string} inquest
 * @prop {string} circumstances
 * @prop {string} concerns
 * @prop {string} action *
 * @prop {string} response *
 * @prop {string} date_of_report *
 */

/** @type {Basic_Report} */
export const default_report = {
    this_report_is_being_sent_to: '',
    coroner_name: '',
    legal: '',
    inquest: '',
    circumstances: '',
    concerns: '',
    action: '',
    response: '',
    date_of_report: ''
}

/** @type {HeadersFor<Basic_Report>} */
const report_headings = {
    'THIS REPORT IS BEING SENT TO:?|IS BEING SENT TO:?': 'this_report_is_being_sent_to',
    '1\\s*CORONER': 'coroner_name',
    "2\\s*CORONER[’']S LEGAL POWERS": 'legal',
    '3\\s*INVESTIGATION and INQUEST': 'inquest',
    '4\\s*CIRCUMSTANCES OF THE DEATH': 'circumstances',
    "5\\s*CORONER[’']S CONCERNS": 'concerns',
    '6\\s*ACTION SHOULD BE TAKEN': 'action',
    '7\\s*YOUR RESPONSE': 'response',
    '8\\s*COPIES and PUBLICATION': 'copies',
    // '9': 'date_of_report' // TODO: find out a good way to match this heading
}

const report_headings_pdf = {
    '(THIS REPORT IS BEING SENT TO:?|IS BEING SENT TO:?\n[\\s\\S]*?)1\\s*CORONER': 'this_report_is_being_sent_to',
    "(1\\s*CORONER\n[\\s\\S]*?)2\\s*CORONER[’']S LEGAL POWERS": 'coroner_name',
    "(2\\s*CORONER[’']S LEGAL POWERS\n[\\s\\S]*?)3\\s*INVESTIGATION and INQUEST": 'legal',
    '(3\\s*INVESTIGATION and INQUEST\n[\\s\\S]*?)4\\s*CIRCUMSTANCES OF THE DEATH': 'inquest',
    "(4\\s*CIRCUMSTANCES OF THE DEATH\n[\\s\\S]*?)5\\s*CORONER[’']S CONCERNS": 'circumstances',
    "(5\\s*CORONER[’']S CONCERNS\n[\\s\\S]*?)6\\s*ACTION SHOULD BE TAKEN": 'concerns',
    '(6\\s*ACTION SHOULD BE TAKEN\n[\\s\\S]*?)7\\s*YOUR RESPONSE': 'action',
    '(7\\s*YOUR RESPONSE\n[\\s\\S]*?)8\\s*COPIES and PUBLICATION': 'response',
    '(8\\s*COPIES and PUBLICATION\n[\\s\\S]*?)9': 'copies'
    // 9: 'date_of_report' // TODO: find out a good way to match this heading
}

/** Parses the rows of a table, using the headers
 * @template R
 * @param {string} text the text to parse
 * @param {Parser<R>} parse_report the custom report parser to use
 * @return {string[] | undefined} the table rows resulting
 */
export function parse_rows(text, parse_report) {
    let table = []
    for (const heading in report_headings_pdf) {
        let match = text.match(RegExp(heading, 'i'))
        if (match) {

            table.push(match[1])
        }
    }

    return parse_report(table)
}

/** Parses field into the basic format for a report
 * @type {Parser<Basic_Report>}
 */
export const parse_report_basic = table_parser(report_headings)
