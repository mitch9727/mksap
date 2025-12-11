// scraper/src/utils/jsonWriter.js
const fs = require('fs');
const path = require('path');
const { OUTPUT_BASE } = require('./fileSystem');

const jsonlPath = path.join(OUTPUT_BASE, 'data.jsonl');

async function appendToJsonl(data) {
    // Ensure we don't write circular structures or huge binary buffers
    // The data object from process_questions is already clean.
    const line = JSON.stringify(data) + '\n';
    await fs.promises.appendFile(jsonlPath, line, 'utf8');
}

module.exports = { appendToJsonl };
