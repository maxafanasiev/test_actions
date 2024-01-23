import {createWriteStream,readFileSync, promises as fs} from 'fs';
import {parse} from 'csv-parse/sync';
import {stringify} from 'csv-stringify';

const beforeChangesFile = "src/data/reports.csv";
const afterChangesFile = "src/data/reports_all.csv";
const outputDiffFile = "src/data/reports_diff.csv";

const readCSV = (filePath) => {
    const fileContent = readFileSync(filePath);
    return parse(fileContent, {
        columns: true,
        skip_empty_lines: true
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

export function compareCSVFiles() {
    const oldRecords = readCSV(beforeChangesFile);
    const newRecords = readCSV(afterChangesFile);

    const changes = compareRecords(oldRecords, newRecords);
    writeCSV(changes, outputDiffFile);
    fs.unlink(beforeChangesFile);
    fs.rename(afterChangesFile, beforeChangesFile);
}


function extractFirstColumn(filePath) {
    const fileContent = fs.readFileSync(filePath);
    const records = parse(fileContent, {
        columns: true,
        skip_empty_lines: true,
    });

    return records.map(row => row.report_url);
}

export function write_diff_log(log_path) {
    const date = new Date();
    const reportUrls = extractFirstColumn(outputDiffFile);
    fs.writeFile(
        log_path,
        `Latest full fetch on ${date.toLocaleDateString()} at ${date.toLocaleTimeString()}, for which:\n` +
        ` - ${reportUrls.length} reports changed in the last month.\n`
    );
}
