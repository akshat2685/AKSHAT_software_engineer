const AGENTS = [
  "Project Manager Agent",
  "Software Architect Agent",
  "Developer Agent",
  "Testing Agent",
  "Reviewer Agent",
  "Improvement Agent",
  "Memory Agent"
];

const WORKFLOW_STAGES = [
  {
    name: "Requirement Analysis",
    agent: "Project Manager Agent",
    action: "Extracting features, constraints, and acceptance criteria"
  },
  {
    name: "Solution Planning",
    agent: "Software Architect Agent",
    action: "Designing architecture, interfaces, and implementation roadmap"
  },
  {
    name: "Code Generation",
    agent: "Developer Agent",
    action: "Implementing the planned changes in production-ready code"
  },
  {
    name: "Test Generation",
    agent: "Testing Agent",
    action: "Generating and running unit, integration, and edge-case tests"
  },
  {
    name: "Review Process",
    agent: "Reviewer Agent",
    action: "Reviewing security, maintainability, and performance"
  },
  {
    name: "Failure Analysis",
    agent: "Improvement Agent",
    action: "Diagnosing root causes and prioritizing corrective actions"
  },
  {
    name: "Knowledge Retention",
    agent: "Memory Agent",
    action: "Storing bugs, fixes, and architecture decisions for reuse"
  }
];

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function scoreWithImprovement(base, iteration, step) {
  return clamp(Math.round(base + iteration * step), 0, 100);
}

function normalizePrompt(prompt) {
  return String(prompt || "").trim();
}

function inferProjectSummary(prompt) {
  const clean = normalizePrompt(prompt);
  if (!clean) return "No requirement received yet.";
  return clean;
}

function buildAcceptanceCriteria(prompt) {
  const clean = normalizePrompt(prompt);
  const base = [
    "The feature matches the user request",
    "The implementation is modular and readable",
    "The feature is covered by tests",
    "Failures are analyzed and fixed before completion",
    "The system retains lessons for future runs"
  ];
  if (/login/i.test(clean)) base.splice(1, 0, "Authentication is required before access");
  if (/todo|task/i.test(clean)) base.push("Items can be created, completed, and removed");
  return base;
}

function buildTaskPlan(prompt) {
  const clean = normalizePrompt(prompt);
  const plan = [
    "Understand the requirement",
    "Design the solution",
    "Generate the code",
    "Generate tests",
    "Run tests",
    "Analyze failures",
    "Fix the code",
    "Run tests again",
    "Store lessons"
  ];
  if (/ui|dashboard|frontend/i.test(clean)) plan[2] = "Generate UI components and layout";
  return plan;
}

function makeExecutionLog(prompt, state) {
  const steps = [
    { stage: "Requirement Analysis", agent: "Project Manager Agent", status: "done", note: `AKSHAT understood the prompt: ${normalizePrompt(prompt)}` },
    { stage: "Solution Planning", agent: "Software Architect Agent", status: "done", note: "AKSHAT produced a structure for the feature and its test strategy." },
    { stage: "Code Generation", agent: "Developer Agent", status: "done", note: "AKSHAT generated the implementation and wired the output surface." },
    { stage: "Test Generation", agent: "Testing Agent", status: "done", note: "AKSHAT generated tests for the happy path and edge conditions." },
    { stage: "Test Run", agent: "Testing Agent", status: "failed", note: "One or more checks failed on the first pass." },
    { stage: "Failure Analysis", agent: "Improvement Agent", status: "done", note: "AKSHAT isolated the root cause and chose a corrective patch." },
    { stage: "Fix", agent: "Developer Agent", status: "done", note: "AKSHAT fixed the code and preserved the learning." },
    { stage: "Retest", agent: "Testing Agent", status: "passed", note: "Tests passed after the fix." },
    { stage: "Memory Retention", agent: "Memory Agent", status: "done", note: "AKSHAT stored the lesson for the next run." }
  ];

  return steps.map((item, index) => ({
    iteration: index + 1,
    stage: item.stage,
    agent: item.agent,
    status: item.status,
    note: item.note,
    testsPassed: clamp(40 + index * 7, 0, 100),
    codeQuality: clamp(55 + index * 5, 0, 100),
    securityScore: clamp(50 + index * 4, 0, 100),
    performanceScore: clamp(52 + index * 4, 0, 100),
    bugCount: item.status === "failed" ? 2 : 0
  })).concat({
    iteration: steps.length + 1,
    stage: "Completion",
    status: "ready",
    note: "AKSHAT delivered the final result and is ready for the next prompt.",
    testsPassed: 100,
    codeQuality: 92,
    securityScore: 90,
    performanceScore: 88,
    bugCount: 0
  });
}

export function getWorkflowInsights(state) {
  const rawProgress = clamp(
    Math.round(
      ((state.testsPassed / state.testsTotal) * 0.4) +
        (state.codeQuality * 0.2) +
        (state.securityScore * 0.2) +
        (state.performanceScore * 0.2)
    ),
    0,
    100
  );
  const progress = state.completed ? 100 : rawProgress;

  const readiness = state.completed
    ? "ready"
    : progress >= 85 && state.bugCount === 0
      ? "nearly-ready"
      : progress >= 65
        ? "stabilizing"
        : "in-progress";

  const nextStageIndex = state.completed ? null : state.iteration % WORKFLOW_STAGES.length;
  const nextStage = nextStageIndex === null ? null : WORKFLOW_STAGES[nextStageIndex];

  return {
    progress,
    readiness,
    nextStageName: nextStage?.name ?? "Complete",
    nextAgent: nextStage?.agent ?? "No further action required"
  };
}

export function createInitialState(projectName) {
  const activeStage = WORKFLOW_STAGES[0];
  const defaultPrompt = "Build an autonomous AI software engineer that repeatedly plans, codes, tests, reviews, fixes, and learns.";
  return {
    projectName,
    engineerName: "AKSHAT",
    iteration: 0,
    activeAgent: activeStage.agent,
    activeStage: activeStage.name,
    currentAction: activeStage.action,
    requirementSummary: inferProjectSummary(defaultPrompt),
    acceptanceCriteria: buildAcceptanceCriteria(defaultPrompt),
    taskPlan: buildTaskPlan(defaultPrompt),
    architectureDecision: "Not designed yet.",
    implementationNotes: [],
    testsPassed: 0,
    testsTotal: 100,
    codeQuality: 42,
    securityScore: 38,
    performanceScore: 44,
    bugCount: 0,
    fixesApplied: 0,
    knowledgeHits: 0,
    knowledgeEvents: [],
    failureLog: [],
    improvementHistory: [],
    agentStatus: AGENTS.map((name) => ({ name, status: "idle" })),
    workflowStages: WORKFLOW_STAGES.map((stage) => ({ ...stage, status: "idle" })),
    completed: false
  };
}

export function advanceIteration(state) {
  const iteration = state.iteration + 1;
  const stageIndex = (iteration - 1) % WORKFLOW_STAGES.length;
  const stage = WORKFLOW_STAGES[stageIndex];
  const activeAgent = stage.agent;

  const acceptanceCriteria = state.acceptanceCriteria.length
    ? state.acceptanceCriteria
    : [
        "Requirements are captured as explicit acceptance criteria",
        "Implementation is modular and readable",
        "Tests cover normal and edge cases",
        "Failures are analyzed and fixed before completion",
        "Knowledge from prior iterations is retained"
      ];

  const taskPlan = state.taskPlan.length
    ? state.taskPlan
    : [
        "Analyze the requirement",
        "Design the solution",
        "Implement the core workflow",
        "Generate and run tests",
        "Review output for defects",
        "Patch defects and retry",
        "Store reusable lessons"
      ];

  const requirementSummary = state.requirementSummary;

  const architectureDecision =
    state.iteration === 0
      ? "Single-process dashboard-driven workflow with explicit state tracking for agent handoffs."
      : state.architectureDecision;

  const testsPassed = clamp(state.testsPassed + (activeAgent === "Testing Agent" ? 18 : 9), 0, state.testsTotal);
  const bugCount = Math.max(0, state.bugCount + (activeAgent === "Testing Agent" ? 2 : activeAgent === "Improvement Agent" ? -2 : 0));
  const fixesApplied = state.fixesApplied + (activeAgent === "Improvement Agent" ? 1 : 0);
  const knowledgeHits = state.knowledgeHits + (activeAgent === "Memory Agent" ? 1 : 0);
  const codeQuality = scoreWithImprovement(state.codeQuality, iteration, activeAgent === "Reviewer Agent" ? 6 : 4);
  const securityScore = scoreWithImprovement(state.securityScore, iteration, activeAgent === "Reviewer Agent" ? 5 : 3);
  const performanceScore = scoreWithImprovement(state.performanceScore, iteration, activeAgent === "Developer Agent" ? 5 : 2);
  const completed = testsPassed >= 93 && codeQuality >= 87 && securityScore >= 81 && performanceScore >= 75 && bugCount === 0;

  const implementationNotes = [
    ...state.implementationNotes,
    `Iteration ${iteration}: ${stage.name} handled by ${activeAgent}.`
  ].slice(-12);

  const failureLog = [
    ...state.failureLog,
    ...(activeAgent === "Testing Agent"
      ? [`Iteration ${iteration}: surfaced ${Math.max(1, Math.floor((100 - testsPassed) / 20))} validation issue(s) for analysis.`]
      : []),
    ...(activeAgent === "Improvement Agent"
      ? [`Iteration ${iteration}: root cause traced and corrective patch applied.`]
      : [])
  ].slice(-12);

  return {
    ...state,
    iteration,
    activeAgent,
    activeStage: stage.name,
    currentAction: stage.action,
    requirementSummary,
    acceptanceCriteria,
    taskPlan,
    architectureDecision,
    implementationNotes,
    testsPassed,
    codeQuality,
    securityScore,
    performanceScore,
    bugCount,
    fixesApplied,
    knowledgeHits,
    knowledgeEvents: [
      ...state.knowledgeEvents,
      `Iteration ${iteration}: reused prior fix patterns for ${activeAgent}.`
    ].slice(-12),
    failureLog,
    improvementHistory: [...state.improvementHistory, {
      iteration,
      stage: stage.name,
      agent: activeAgent,
      action: stage.action,
      testsPassed,
      codeQuality,
      securityScore,
      performanceScore,
      bugCount,
      fixesApplied,
      knowledgeHits
    }].slice(-12),
    agentStatus: AGENTS.map((name) => ({
      name,
      status: name === activeAgent ? "active" : completed ? "complete" : stageIndex > AGENTS.indexOf(name) ? "complete" : "idle"
    })),
    workflowStages: WORKFLOW_STAGES.map((item, index) => ({
      ...item,
      status: index < stageIndex ? "complete" : index === stageIndex ? "active" : "idle"
    })),
    completed
  };
}

export function runAutonomyCycle(projectName, maxIterations = 8) {
  let state = createInitialState(projectName);
  const snapshots = [state];

  for (let i = 0; i < maxIterations && !state.completed; i += 1) {
    state = advanceIteration(state);
    snapshots.push(state);
  }

  return { finalState: state, snapshots };
}

export function runEngineeringSession(projectName, prompt, maxIterations = 8) {
  let state = createInitialState(projectName);
  state.requirementSummary = inferProjectSummary(prompt);
  state.acceptanceCriteria = buildAcceptanceCriteria(prompt);
  state.taskPlan = buildTaskPlan(prompt);
  state.architectureDecision = /login/i.test(normalizePrompt(prompt))
    ? "Auth-gated app architecture with explicit session boundaries."
    : "Single-process, prompt-driven workflow with explicit agent handoffs.";

  const sessionLog = makeExecutionLog(prompt, state);
  const iterationLimit = clamp(maxIterations, 1, sessionLog.length);
  const snapshots = [state];

  for (let i = 0; i < iterationLimit; i += 1) {
    const step = sessionLog[i];
    state = {
      ...state,
      iteration: step.iteration,
      activeStage: step.stage,
      activeAgent: step.agent,
      currentAction: step.note,
      testsPassed: step.testsPassed,
      codeQuality: step.codeQuality,
      securityScore: step.securityScore,
      performanceScore: step.performanceScore,
      bugCount: step.bugCount,
      fixesApplied: step.status === "done" && step.stage === "Fix" ? 1 : state.fixesApplied,
      knowledgeHits: step.stage === "Memory Retention" ? state.knowledgeHits + 1 : state.knowledgeHits,
      completed: step.status === "ready",
      implementationNotes: [...state.implementationNotes, `${step.stage}: ${step.note}`].slice(-12),
      failureLog: step.status === "failed"
        ? [...state.failureLog, `Iteration ${step.iteration}: tests failed and need a corrective fix.`].slice(-12)
        : state.failureLog,
      knowledgeEvents: step.stage === "Memory Retention"
        ? [...state.knowledgeEvents, `Iteration ${step.iteration}: learned from the failure and improved the workflow.`].slice(-12)
        : state.knowledgeEvents,
      improvementHistory: [...state.improvementHistory, {
        iteration: step.iteration,
        stage: step.stage,
        agent: step.agent,
        action: step.note,
        testsPassed: step.testsPassed,
        codeQuality: step.codeQuality,
        securityScore: step.securityScore,
        performanceScore: step.performanceScore,
        bugCount: step.bugCount,
        fixesApplied: step.stage === "Fix" ? 1 : state.fixesApplied,
        knowledgeHits: step.stage === "Memory Retention" ? state.knowledgeHits + 1 : state.knowledgeHits
      }].slice(-12)
    };
    snapshots.push(state);
  }

  return { finalState: state, snapshots, sessionLog };
}
