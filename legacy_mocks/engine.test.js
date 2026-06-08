import test from "node:test";
import assert from "node:assert/strict";
import { createInitialState, advanceIteration, getWorkflowInsights, runAutonomyCycle, runEngineeringSession } from "../src/engine.js";

test("creates a clean initial state", () => {
  const state = createInitialState("Demo");
  assert.equal(state.projectName, "Demo");
  assert.equal(state.engineerName, "AKSHAT");
  assert.equal(state.iteration, 0);
  assert.equal(state.testsPassed, 0);
  assert.equal(state.completed, false);
  assert.equal(state.activeStage, "Requirement Analysis");
  assert.ok(state.acceptanceCriteria.length > 0);
  assert.ok(state.taskPlan.length > 0);
  assert.ok(state.agentStatus.some((agent) => agent.name === "Developer Agent"));
});

test("advances the autonomy loop and improves scores", () => {
  const first = advanceIteration(createInitialState("Demo"));
  const second = advanceIteration(first);

  assert.equal(second.iteration, 2);
  assert.notEqual(second.activeStage, first.activeStage);
  assert.ok(second.testsPassed >= first.testsPassed);
  assert.ok(second.codeQuality >= first.codeQuality);
  assert.ok(second.securityScore >= first.securityScore);
  assert.ok(Array.isArray(second.workflowStages));
});

test("runs multiple iterations and records history", () => {
  const { finalState, snapshots } = runAutonomyCycle("Demo", 5);

  assert.equal(snapshots.length, 6);
  assert.ok(finalState.improvementHistory.length > 0);
  assert.ok(finalState.knowledgeEvents.length > 0);
  assert.ok(finalState.failureLog.length > 0);
  assert.ok(typeof finalState.completed === "boolean");
});

test("derives workflow insights from the current state", () => {
  const { finalState } = runAutonomyCycle("Demo", 20);
  const insights = getWorkflowInsights(finalState);

  assert.equal(finalState.completed, true);
  assert.equal(insights.readiness, "ready");
  assert.equal(insights.nextStageName, "Complete");
  assert.equal(insights.nextAgent, "No further action required");
  assert.ok(insights.progress >= 0 && insights.progress <= 100);
});

test("preserves the real agent names in the engineering session", () => {
  const session = runEngineeringSession("Demo", "Build a Todo App with login", 4);

  assert.equal(session.sessionLog[0].agent, "Project Manager Agent");
  assert.equal(session.sessionLog[2].agent, "Developer Agent");
  assert.equal(session.finalState.activeAgent, "Testing Agent");
  assert.equal(session.finalState.activeStage, "Test Generation");
});
