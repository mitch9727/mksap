/**
 * Progress Checkpoint Agent
 *
 * Saves scraping progress periodically to enable resume from failure.
 * Never lose more than N questions of progress.
 *
 * @module progressCheckpointAgent
 */

const fs = require('fs');
const path = require('path');
const aiConfig = require('../../config/ai_config');

class ProgressCheckpointAgent {
  /**
   * Create a new checkpoint agent
   *
   * @param {Object} config - Agent configuration
   * @param {number} config.checkpointFrequency - Save every N questions
   * @param {string} config.checkpointDir - Directory for checkpoints
   * @param {boolean} config.autoResume - Automatically resume from checkpoint
   */
  constructor(config = {}) {
    this.config = {
      ...aiConfig.agents.progressCheckpointAgent,
      ...config
    };

    this.checkpointFrequency = this.config.checkpointFrequency || 10;
    this.checkpointDir = this.config.checkpointDir || './output';
    this.autoResume = this.config.autoResume !== false;

    // Current checkpoint state
    this.currentCheckpoint = null;
  }

  /**
   * Get checkpoint file path for a system
   *
   * @param {string} systemFolder - System folder name (e.g., 'Cardiovascular')
   * @returns {string} Checkpoint file path
   */
  getCheckpointPath(systemFolder) {
    return path.join(this.checkpointDir, systemFolder, '.checkpoint.json');
  }

  /**
   * Load existing checkpoint for a system
   *
   * @param {string} systemFolder - System folder name
   * @returns {Object|null} Checkpoint data or null if none exists
   */
  loadCheckpoint(systemFolder) {
    const checkpointPath = this.getCheckpointPath(systemFolder);

    if (!fs.existsSync(checkpointPath)) {
      return null;
    }

    try {
      const data = fs.readFileSync(checkpointPath, 'utf8');
      const checkpoint = JSON.parse(data);

      console.log(
        `[ProgressCheckpointAgent] Loaded checkpoint for ${systemFolder}: ` +
        `${checkpoint.questionCount} questions, page ${checkpoint.currentPage}`
      );

      this.currentCheckpoint = checkpoint;
      return checkpoint;
    } catch (error) {
      console.error(
        `[ProgressCheckpointAgent] Failed to load checkpoint: ${error.message}`
      );
      return null;
    }
  }

  /**
   * Save checkpoint for current progress
   *
   * @param {Object} state - Current scraping state
   * @param {string} state.systemFolder - System folder name
   * @param {string} state.systemCode - System code (e.g., 'cv')
   * @param {number} state.currentPage - Current pagination page
   * @param {number} state.questionCount - Total questions processed
   * @param {string} state.lastQuestionId - Last question ID processed
   * @param {Array} state.processedQuestions - Array of processed question IDs
   * @returns {boolean} True if checkpoint saved successfully
   */
  saveCheckpoint(state) {
    const {
      systemFolder,
      systemCode,
      currentPage,
      questionCount,
      lastQuestionId,
      processedQuestions = []
    } = state;

    try {
      // Create checkpoint data
      const checkpoint = {
        systemFolder,
        systemCode,
        currentPage,
        questionCount,
        lastQuestionId,
        processedQuestions,
        timestamp: new Date().toISOString(),
        version: '1.0'
      };

      // Ensure checkpoint directory exists
      const checkpointPath = this.getCheckpointPath(systemFolder);
      const dir = path.dirname(checkpointPath);

      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }

      // Write checkpoint file
      fs.writeFileSync(checkpointPath, JSON.stringify(checkpoint, null, 2), 'utf8');

      console.log(
        `[ProgressCheckpointAgent] Checkpoint saved: ${questionCount} questions, ` +
        `page ${currentPage}, last ID: ${lastQuestionId}`
      );

      this.currentCheckpoint = checkpoint;
      return true;
    } catch (error) {
      console.error(
        `[ProgressCheckpointAgent] Failed to save checkpoint: ${error.message}`
      );
      return false;
    }
  }

  /**
   * Check if checkpoint should be saved
   *
   * @param {number} questionCount - Current question count
   * @returns {boolean} True if checkpoint should be saved
   */
  shouldSaveCheckpoint(questionCount) {
    return questionCount > 0 && questionCount % this.checkpointFrequency === 0;
  }

  /**
   * Delete checkpoint file (after successful completion)
   *
   * @param {string} systemFolder - System folder name
   * @returns {boolean} True if deleted successfully
   */
  deleteCheckpoint(systemFolder) {
    const checkpointPath = this.getCheckpointPath(systemFolder);

    if (!fs.existsSync(checkpointPath)) {
      return true;
    }

    try {
      fs.unlinkSync(checkpointPath);
      console.log(`[ProgressCheckpointAgent] Checkpoint deleted for ${systemFolder}`);
      this.currentCheckpoint = null;
      return true;
    } catch (error) {
      console.error(
        `[ProgressCheckpointAgent] Failed to delete checkpoint: ${error.message}`
      );
      return false;
    }
  }

  /**
   * Check if a question has already been processed
   *
   * @param {string} questionId - Question ID to check
   * @returns {boolean} True if already processed
   */
  isQuestionProcessed(questionId) {
    if (!this.currentCheckpoint) {
      return false;
    }

    return this.currentCheckpoint.processedQuestions?.includes(questionId) || false;
  }

  /**
   * Get resume state for continuing scrape
   *
   * @param {string} systemFolder - System folder name
   * @returns {Object|null} Resume state or null if no checkpoint
   */
  getResumeState(systemFolder) {
    const checkpoint = this.loadCheckpoint(systemFolder);

    if (!checkpoint) {
      return null;
    }

    return {
      startPage: checkpoint.currentPage,
      skipQuestions: checkpoint.processedQuestions,
      resumeFromQuestionId: checkpoint.lastQuestionId,
      previousQuestionCount: checkpoint.questionCount
    };
  }

  /**
   * List all active checkpoints
   *
   * @returns {Array} Array of checkpoint info objects
   */
  listAllCheckpoints() {
    const checkpoints = [];

    if (!fs.existsSync(this.checkpointDir)) {
      return checkpoints;
    }

    // Scan all system folders
    const systemFolders = fs.readdirSync(this.checkpointDir, { withFileTypes: true })
      .filter(dirent => dirent.isDirectory())
      .map(dirent => dirent.name);

    for (const systemFolder of systemFolders) {
      const checkpointPath = this.getCheckpointPath(systemFolder);

      if (fs.existsSync(checkpointPath)) {
        try {
          const data = fs.readFileSync(checkpointPath, 'utf8');
          const checkpoint = JSON.parse(data);

          checkpoints.push({
            systemFolder,
            questionCount: checkpoint.questionCount,
            currentPage: checkpoint.currentPage,
            lastQuestionId: checkpoint.lastQuestionId,
            timestamp: checkpoint.timestamp
          });
        } catch (error) {
          console.error(
            `[ProgressCheckpointAgent] Failed to read checkpoint for ${systemFolder}: ${error.message}`
          );
        }
      }
    }

    return checkpoints;
  }

  /**
   * Display checkpoint status message
   *
   * @param {string} systemFolder - System folder name
   */
  displayCheckpointStatus(systemFolder) {
    const checkpoint = this.loadCheckpoint(systemFolder);

    if (!checkpoint) {
      console.log(
        `[ProgressCheckpointAgent] No checkpoint found for ${systemFolder}. ` +
        `Starting fresh scrape.`
      );
      return;
    }

    console.log(`\n${'='.repeat(60)}`);
    console.log(`[ProgressCheckpointAgent] CHECKPOINT FOUND`);
    console.log(`${'='.repeat(60)}`);
    console.log(`System: ${systemFolder}`);
    console.log(`Questions processed: ${checkpoint.questionCount}`);
    console.log(`Current page: ${checkpoint.currentPage}`);
    console.log(`Last question ID: ${checkpoint.lastQuestionId}`);
    console.log(`Timestamp: ${checkpoint.timestamp}`);

    if (this.autoResume) {
      console.log(`\nResuming from checkpoint...`);
    } else {
      console.log(`\nAuto-resume disabled. Delete checkpoint to start fresh.`);
    }

    console.log(`${'='.repeat(60)}\n`);
  }

  /**
   * Get current checkpoint data
   *
   * @returns {Object|null} Current checkpoint or null
   */
  getCurrentCheckpoint() {
    return this.currentCheckpoint;
  }
}

// Singleton instance
let agentInstance = null;

/**
 * Get singleton checkpoint agent instance
 *
 * @param {Object} config - Optional config override
 * @returns {ProgressCheckpointAgent}
 */
function getCheckpointAgent(config = {}) {
  if (!agentInstance) {
    agentInstance = new ProgressCheckpointAgent(config);
  }
  return agentInstance;
}

module.exports = {
  ProgressCheckpointAgent,
  getCheckpointAgent
};
