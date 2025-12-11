/**
 * MKSAP CSS Selectors - Master Configuration File
 *
 * All selectors have been manually discovered by inspecting the actual MKSAP
 * website HTML structure and are verified to work with Playwright.
 *
 * These selectors are used throughout the scraper to locate and extract data
 * from MKSAP pages.
 *
 * IMPORTANT: If MKSAP website structure changes, these selectors must be updated.
 * See SELECTORS_REFERENCE.md for complete documentation of each selector.
 * See SELECTOR_DISCOVERY_GUIDE.md for how to discover/update selectors.
 *
 * @module selectors
 * @exports {Object} Selector groups organized by page section
 */

module.exports = {
    login: {
        // Confirmed: span with data-testid showing logged-in user
        loggedInIndicator: 'span[data-testid="greeting"]'
    },

    nav: {
        // Navigation links to reach the question bank
        questionBankLink: 'a[href="/app/question-bank"]',

        // Factory functions for system-specific selectors
        // Usage: systemLink('cv') → 'a[href="/app/question-bank/content-areas/cv"]'
        systemLink: (systemCode) =>
            `a[href="/app/question-bank/content-areas/${systemCode}"]`,

        // Usage: answeredQuestionsLink('cv') → 'a[href="/app/question-bank/content-areas/cv/answered-questions"]'
        answeredQuestionsLink: (systemCode) =>
            `a[href="/app/question-bank/content-areas/${systemCode}/answered-questions"]`,

        // Legacy selectors (for backward compatibility during migration)
        cardiovascularLink: 'a[href="/app/question-bank/content-areas/cv"]'
    },

    list: {
        // Question list container
        container: '.list-group',
        // Individual question item button
        questionItem: 'button.list-group-item.list-group-item-action',
        // Pagination next button
        nextPageBtn: 'button:has-text("Next"), a:has-text("Next")'
    },

    question: {
        // Main question section
        container: 'section',
        // Close button for question view
        closeBtn: 'button.btn-close[aria-label="Close"]',

        // Question metadata
        questionId: '.text-uppercase.text-nowrap',  // e.g., "cvmcq24004"
        educationalObjective: 'p.h5 span',  // After "Educational Objective:" text
        careType: 'span.tag.tag-primary',  // Multiple tags, contains care type
        lastUpdated: '.last-updated span.date',  // e.g., "June 2025"

        // Content sections
        critique: 'div.critique',  // Answer explanation
        keyPoint: 'ul.keypoints-list li',  // Key points list items
        references: 'h5:has-text("Reference") + p.small',  // Reference section

        // Assets
        figures: 'img[src*="d2chybfyz5ban.cloudfront.net"]',  // Diagnostic images
        figureLinks: 'a.callout[href*="/figures/"]',  // Links to figures
        tableLinks: 'a.callout[href*="/tables/"]',  // Links to open table modals
        tables: 'table',  // Data tables (in modal after clicking link)

        // Related text/syllabus
        syllabusLink: 'a[href*="/syllabus/"]'
    },

    syllabus: {
        // Syllabus/related text content area
        contentBody: 'main, article, section',
        // Breadcrumbs navigation - page location items
        breadcrumbs: 'ol.page-location li span'
    }
};
