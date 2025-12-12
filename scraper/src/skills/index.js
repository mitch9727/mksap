/**
 * Skills Index
 *
 * Exports all Claude Skills for easy importing.
 *
 * @module skills
 */

const authenticationAssistant = require('./authenticationAssistant');
const errorDiagnostician = require('./errorDiagnostician');

module.exports = {
  // Authentication Assistant Skill
  analyzeAuthenticationState: authenticationAssistant.analyzeAuthenticationState,
  checkSessionHealth: authenticationAssistant.checkSessionHealth,

  // Error Diagnostician Skill
  diagnoseError: errorDiagnostician.diagnoseError,
  smartRetry: errorDiagnostician.smartRetry
};
