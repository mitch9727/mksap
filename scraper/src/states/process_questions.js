// scraper/src/states/process_questions.js
const BaseState = require('./base');
const selectors = require('../selectors');
const { extractFigures } = require('../extractors/figures');
const { extractTables } = require('../extractors/tables');
const { extractSyllabus } = require('../extractors/syllabus');
const { extractText } = require('../utils/htmlParser');
const { writeQuestionJson } = require('../utils/questionWriter');
const { smartRetry, diagnoseError } = require('../skills/errorDiagnostician');
const ProgressCheckpointAgent = require('../agents/progressCheckpointAgent');

class ProcessQuestionsState extends BaseState {
    async execute() {
        const systemFolder = this.machine.systemConfig.folder;
        const systemCode = this.machine.systemCode;
        const outputDir = this.machine.getSystemOutputDir();
        this.logger.info(`Processing questions for ${this.machine.systemConfig.name}...`);
        this.logger.info(`Saving to: ${outputDir}`);

        // Initialize checkpoint agent
        const checkpointAgent = new ProgressCheckpointAgent(outputDir, this.logger);

        // Check for existing checkpoint
        const checkpoint = checkpointAgent.loadCheckpoint(systemFolder);
        const processedQuestionIds = new Set(checkpoint?.processedQuestions || []);

        if (checkpoint) {
            this.logger.info(`✓ Checkpoint found! Resuming from: ${checkpoint.lastQuestionId}`);
            this.logger.info(`  Already processed: ${checkpoint.questionCount} questions`);
            this.logger.info(`  Last page: ${checkpoint.currentPage}`);
        }

        // Loop controls
        let hasNextPage = true;
        let questionCount = checkpoint?.questionCount || 0;
        let currentPage = 1;

        while (hasNextPage) {
            // 1. Get all question items
            const questions = await this.page.locator(selectors.list.questionItem).all();
            this.logger.info(`Found ${questions.length} questions on this page.`);

            for (let i = 0; i < questions.length; i++) {
                const qItem = questions[i];

                try {
                    // Use smart retry with AI-powered error diagnosis
                    await smartRetry(
                        async () => {
                            // Open Modal
                            this.logger.info(`Opening question ${i + 1}/${questions.length}...`);
                            await qItem.click();

                            // Wait for Modal Content
                            const modal = this.page.locator(selectors.question.container);
                            await modal.waitFor({ state: 'visible', timeout: 5000 });

                            // --- EXTRACTION START ---
                            const data = await this.scrapeStrictSchema(modal, systemFolder, outputDir);
                            // --- EXTRACTION END ---

                            // Skip if already processed (from checkpoint)
                            if (processedQuestionIds.has(data.ID)) {
                                this.logger.info(`⏭️  Skipping ${data.ID} (already processed)`);

                                // Close Modal
                                await this.page.click(selectors.question.closeBtn);
                                await modal.waitFor({ state: 'hidden' });
                                return; // Skip saving
                            }

                            // Save as individual JSON file
                            const jsonPath = await writeQuestionJson(data, systemFolder, outputDir);
                            questionCount++;
                            processedQuestionIds.add(data.ID);
                            this.logger.info(`✓ Saved ${data.ID} to ${jsonPath}`);

                            // Save checkpoint every 10 questions
                            if (checkpointAgent.shouldSaveCheckpoint(questionCount)) {
                                checkpointAgent.saveCheckpoint({
                                    systemFolder,
                                    systemCode,
                                    currentPage,
                                    questionCount,
                                    lastQuestionId: data.ID,
                                    processedQuestions: Array.from(processedQuestionIds)
                                });
                                this.logger.info(`💾 Checkpoint saved (${questionCount} questions)`);
                            }

                            // Close Modal
                            await this.page.click(selectors.question.closeBtn);
                            await modal.waitFor({ state: 'hidden' });
                        },
                        {
                            page: this.page,
                            state: 'PROCESS_QUESTIONS',
                            context: {
                                questionIndex: i + 1,
                                systemFolder,
                                operation: 'extract_question'
                            },
                            maxRetries: 3
                        }
                    );
                } catch (error) {
                    // Check if error is USAGE_LIMIT_REACHED
                    if (error.message === 'USAGE_LIMIT_REACHED') {
                        // Save checkpoint before throwing
                        checkpointAgent.saveCheckpoint({
                            systemFolder,
                            systemCode,
                            currentPage,
                            questionCount,
                            lastQuestionId: processedQuestionIds.size > 0 ? Array.from(processedQuestionIds).pop() : 'UNKNOWN',
                            processedQuestions: Array.from(processedQuestionIds)
                        });

                        this.logger.error('');
                        this.logger.error(`💾 Emergency checkpoint saved: ${questionCount} questions processed`);
                        this.logger.error('');

                        throw error; // Propagate to WorkerPool
                    }

                    // For other errors, try to get AI diagnosis
                    try {
                        const screenshot = await this.page.screenshot({ encoding: 'base64' });
                        const diagnosis = await diagnoseError({
                            error,
                            state: 'PROCESS_QUESTIONS',
                            screenshot,
                            context: { questionIndex: i + 1, systemFolder }
                        });

                        this.logger.error(`AI Diagnosis: ${diagnosis.diagnosis}`);
                        this.logger.error(`Suggested fix: ${diagnosis.suggestedFix}`);
                    } catch (diagError) {
                        // AI diagnosis failed - just log the original error
                        this.logger.error(`Failed to process question ${i + 1}: ${error.message}`);
                    }

                    // Continue to next question
                }
            }

            currentPage++;

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

        // Delete checkpoint on successful completion
        checkpointAgent.deleteCheckpoint(systemFolder);
        this.logger.info('💾 Checkpoint deleted (successful completion)');

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
