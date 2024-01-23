import { createReadStream, createWriteStream, promises as fs } from 'fs';
import { parse } from 'csv-parse';
import { stringify } from 'csv-stringify';

const beforeChangesFile = "src/data/reports.csv";
const afterChangesFile = "src/data/reports_all.csv";
const outputDiffFile = "src/data/reports_diff.csv";

const readCSV = async (filePath) => {
    const records = [];
    return new Promise((resolve, reject) => {
        createReadStream(filePath)
            .pipe(parse({
                columns: true,
                skip_empty_lines: true
            }))
            .on('data', (record) => records.push(record))
            .on('end', () => resolve(records))
            .on('error', reject);
    });
};

const compareRecords = (oldRecords, newRecords) => {
    const changes = [];
    const updateDate = new Date().toISOString();

    newRecords.forEach(newRecord => {
        const oldRecord = oldRecords.find(r => r.report_url === newRecord.report_url);
        if (oldRecord) {
            const changedFields = {};

            Object.keys(newRecord).forEach(key => {
                if (newRecord[key] !== oldRecord[key]) {
                    changedFields[key] = {old: oldRecord[key], new: newRecord[key]};
                }
            });

            if (Object.keys(changedFields).length > 0) {
                changes.push({
                    report_url: newRecord.report_url,
                    changes: changedFields,
                    updated_at: updateDate
                });
            }
        }
    });

    return changes;
};

const writeCSV = (changes, outputFilePath) => {
    const stringifier = stringify({ header: true });
    const writableStream = createWriteStream(outputFilePath);
    stringifier.pipe(writableStream);

    for (const change of changes) {
        stringifier.write(change);
    }

    stringifier.end();
};

export async function compareCSVFiles() {
    const oldRecords = await readCSV(beforeChangesFile);
    const newRecords = await readCSV(afterChangesFile);

    const changes = compareRecords(oldRecords, newRecords);
    writeCSV(changes, outputDiffFile);
    fs.unlink(beforeChangesFile);
    fs.rename(afterChangesFile, beforeChangesFile);
}

async function extractFirstColumn(filePath) {
    const fileContent = await fs.readFile(filePath);
    const records = [];

    await new Promise((resolve, reject) => {
        parse(fileContent, {
            columns: true,
            skip_empty_lines: true,
        })
            .on('data', (row) => {
                records.push(row.report_url);
            })
            .on('end', resolve)
            .on('error', reject);
    });

    return records;
}

export async function write_diff_log(log_path) {
    const date = new Date();
    const reportUrls = await extractFirstColumn(outputDiffFile);
    await fs.writeFile(
        log_path,
        `Latest full fetch on ${date.toLocaleDateString()} at ${date.toLocaleTimeString()}, for which:\n` +
        ` - ${reportUrls.length} reports changed in the last month.\n`
    );
}
