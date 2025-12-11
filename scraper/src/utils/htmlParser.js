// scraper/src/utils/htmlParser.js
const cheerio = require('cheerio');

function cleanHtml(rawHtml) {
    if (!rawHtml) return '';
    const $ = cheerio.load(rawHtml);
    
    // Remove scripts, styles, buttons
    $('script, style, button, .hidden').remove();
    
    return $.html();
}

function extractText(html) {
    if (!html) return '';
    const $ = cheerio.load(html);
    return $.text().trim();
}

// Convert specific MKSAP HTML quirks to Markdown-friendly HTML
function normalizeContent(html) {
    const $ = cheerio.load(html);
    // e.g., convert span.bold to <b>
    $('.bold').each((i, el) => $(el).replaceWith(`<b>${$(el).html()}</b>`));
    return $('body').html() || '';
}

module.exports = { cleanHtml, extractText, normalizeContent };
