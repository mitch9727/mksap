/**
 * Agents Index
 *
 * Exports all Claude Agents for easy importing.
 *
 * @module agents
 */

const progressCheckpoint = require('./progressCheckpointAgent');

module.exports = {
  // Progress Checkpoint Agent
  ProgressCheckpointAgent: progressCheckpoint.ProgressCheckpointAgent,
  getCheckpointAgent: progressCheckpoint.getCheckpointAgent
};
