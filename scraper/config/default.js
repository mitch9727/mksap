// scraper/config/default.js
const path = require('path');

module.exports = {
    baseUrl: 'https://mksap.acponline.org',
    // Headless mode is largely controlled by the InitState auth check now, 
    // but this sets the preference for authenticated runs.
    headless: true, 
    authFile: path.join(__dirname, 'auth.json'),
    outputDir: path.join(__dirname, '../output'),
    maxRetries: 3,
    selectors: require('../src/selectors')
};
