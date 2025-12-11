// scraper/src/states/process_questions.js
const BaseState = require('./base');
const selectors = require('../selectors');
const { extractFigures } = require('../extractors/figures');
const { extractTables } = require('../extractors/tables');
const { extractSyllabus } = require('../extractors/syllabus');
const { extractText } = require('../utils/htmlParser');
const { writeQuestionJson } = require('../utils/questionWriter');

class ProcessQuestionsState extends BaseState {
    async execute() {
        const systemFolder = this.machine.systemConfig.folder;
        const outputDir = this.machine.getSystemOutputDir();
        this.logger.info(`Processing questions for ${this.machine.systemConfig.name}...`);
        this.logger.info(`Saving to: ${outputDir}`);

        // Loop controls
        let hasNextPage = true;
        let questionCount = 0;

        while (hasNextPage) {
            // 1. Get all question items
            const questions = await this.page.locator(selectors.list.questionItem).all();
            this.logger.info(`Found ${questions.length} questions on this page.`);

            for (let i = 0; i < questions.length; i++) {
                const qItem = questions[i];

                try {
                    // Open Modal
                    this.logger.info(`Opening question ${i + 1}/${questions.length}...`);
                    await qItem.click();

                    // Wait for Modal Content
                    const modal = this.page.locator(selectors.question.container);
                    await modal.waitFor({ state: 'visible', timeout: 5000 });

                    // --- EXTRACTION START ---
                    const data = await this.scrapeStrictSchema(modal, systemFolder, outputDir);
                    // --- EXTRACTION END ---

                    // Save as individual JSON file
                    const jsonPath = await writeQuestionJson(data, systemFolder, outputDir);
                    questionCount++;
                    this.logger.info(`✓ Saved ${data.ID} to ${jsonPath}`);

                    // Close Modal
                    await this.page.click(selectors.question.closeBtn);
                    await modal.waitFor({ state: 'hidden' });
                } catch (error) {
                    this.logger.error(`Failed to process question ${i + 1}: ${error.message}`);
                    // Continue to next question
                }
            }

            // Pagination Check
            const nextBtn = this.page.locator(selectors.list.nextPageBtn);
            if (await nextBtn.isVisible() && await nextBtn.isEnabled()) {
                this.logger.info('Navigating to Next Page...');
                await nextBtn.click();
                await this.page.waitForLoadState('networkidle');
                await this.page.waitForTimeout(2000); // Breathe
            } else {
                this.logger.info('No more pages. Exiting loop.');
                hasNextPage = false;
            }
        }

        this.logger.info(`✓ Completed: Processed ${questionCount} questions for ${this.machine.systemConfig.name}`);
        return 'EXIT';
    }

    async scrapeStrictSchema(modal, systemFolder, outputDir) {
        // ID Extraction - use the specific selector
        let ID = '';
        try {
            ID = await modal.locator(selectors.question.questionId).innerText();
            ID = ID.trim().toUpperCase();
            if (!ID) {
                ID = 'UNKNOWN_' + Date.now();
            }
        } catch (e) {
            ID = 'UNKNOWN_' + Date.now();
        }

        // Educational Objective
        let educationalObjective = '';
        try {
            educationalObjective = await modal.locator(selectors.question.educationalObjective).innerText();
            educationalObjective = educationalObjective.trim();
        } catch (e) {
            // Optional field
        }

        // Care Type - may be multiple tags, extract all and join
        let careType = '';
        try {
            const careTypeElements = await modal.locator(selectors.question.careType).all();
            const careTypes = await Promise.all(
                careTypeElements.map(el => el.innerText())
            );
            careType = careTypes.join(', ').trim();
        } catch (e) {
            // Optional field
        }

        // "Answer and Critique" - full explanation body
        let answerAndCritique = '';
        try {
            const critiqueHtml = await modal.locator(selectors.question.critique).innerHTML();
            answerAndCritique = extractText(critiqueHtml);
        } catch (e) {
            // Optional field
        }

        // Key Points - may be multiple items, extract all
        let keyPoint = '';
        try {
            const keyPointElements = await modal.locator(selectors.question.keyPoint).all();
            const keyPoints = await Promise.all(
                keyPointElements.map(el => el.innerText())
            );
            keyPoint = keyPoints.join('\n').trim();
        } catch (e) {
            // Optional field
        }

        // Reference
        let reference = '';
        try {
            reference = await modal.locator(selectors.question.references).innerText();
            reference = reference.trim();
        } catch (e) {
            // Optional field
        }

        // Last Updated - extract from page, fallback to current date
        let lastUpdated = new Date().toLocaleDateString();
        try {
            const dateElement = await modal.locator(selectors.question.lastUpdated).innerText();
            if (dateElement) {
                lastUpdated = dateElement.trim();
            }
        } catch (e) {
            // Keep fallback date
        }

        // Assets - pass system folder and output directory
        const Figures = await extractFigures(this.page, ID, systemFolder, outputDir).catch(e => {
            this.logger.warn('Figure extraction failed: ' + e.message);
            return [];
        });

        const Tables = await extractTables(this.page, ID, systemFolder, outputDir).catch(e => {
            this.logger.warn('Table extraction failed: ' + e.message);
            return [];
        });

        const Videos = []; // Placeholder for future expansion

        // Related Text (Syllabus) - optional
        let RelatedText = {};
        try {
            const syllabusData = await extractSyllabus(this.page, ID, systemFolder, outputDir);
            if (syllabusData && syllabusData.bodyHtml) {
                RelatedText = syllabusData;
            }
        } catch (e) {
            this.logger.debug('Syllabus extraction skipped or failed: ' + e.message);
        }

        return {
            "ID": ID,
            "Reference": reference,
            "Last Updated": lastUpdated,
            "Educational Objective": educationalObjective,
            "Care type": careType,
            "Answer and Critique": answerAndCritique,
            "Key Point": keyPoint,
            "Figures": Figures,
            "Tables": Tables,
            "Videos": Videos,
            "Related Text": RelatedText
        };
    }
}

module.exports = ProcessQuestionsState;
