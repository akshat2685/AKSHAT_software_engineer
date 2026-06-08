const { createElement: h, useEffect, useState } = React;

function Stat({ label, value }) {
  return h("div", { className: "stat" }, [
    h("div", { className: "label", key: "label" }, label),
    h("div", { className: "value", key: "value" }, String(value ?? "")),
  ]);
}

function AgentWorkflow({ workflow }) {
  const events = workflow?.events || [];
  return h("section", { className: "panel span-12" }, [
    h("div", { className: "label", key: "label" }, "Agent Workflow"),
    h("div", { className: "workflow-strip", key: "stats" }, [
      h(Stat, { label: "Current Agent", value: workflow?.current_agent || "Idle", key: "agent" }),
      h(Stat, { label: "Task Type", value: workflow?.task_type || "general", key: "task" }),
      h(Stat, { label: "Iterations", value: workflow?.iteration_count || 0, key: "iteration" }),
      h(Stat, { label: "Quality", value: workflow?.quality_score || 0, key: "quality" }),
      h(Stat, { label: "Security", value: workflow?.security_score || 0, key: "security" }),
    ]),
    h("div", { className: "agent-grid", key: "deployment" }, [
      h("div", { className: "agent-card", key: "deployment-card" }, [
        h("strong", { key: "title" }, "Deployment"),
        h("div", { key: "url" }, workflow?.deployment_url || "No deployment yet."),
        h("small", { key: "status" }, workflow?.deployment_status || "pending"),
      ]),
      h("div", { className: "agent-card", key: "order-card" }, [
        h("strong", { key: "title" }, "Execution Order"),
        h("div", { key: "order" }, (workflow?.execution_order || []).join(" -> ") || "Waiting for task."),
      ]),
    ]),
    h("div", { className: "agent-grid", key: "events" }, events.length ? events.map((event, index) =>
      h("div", { className: "agent-card", key: index }, [
        h("strong", { key: "agent" }, event.agent),
        h("div", { key: "task" }, event.task),
        h("small", { key: "output" }, event.output),
      ])
    ) : h("div", { className: "muted" }, "No workflow run yet.")),
  ]);
}

function Dashboard() {
  const [state, setState] = useState(null);
  const [prompt, setPrompt] = useState("");

  async function refresh() {
    const response = await fetch("/api/status");
    setState(await response.json());
  }

  async function submitTask() {
    await fetch("/api/task", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt }),
    });
    await refresh();
  }

  useEffect(() => {
    refresh();
    const socket = new WebSocket((location.protocol === "https:" ? "wss://" : "ws://") + location.host + "/ws");
    socket.addEventListener("message", refresh);
    return () => socket.close();
  }, []);

  if (!state) return h("main", { className: "main" }, "Loading AKSHAT...");

  return h("main", { className: "content" }, [
    h("section", { className: "panel span-12", key: "task" }, [
      h("div", { className: "label", key: "label" }, "Task Input"),
      h("input", { value: prompt, onChange: (event) => setPrompt(event.target.value), placeholder: "Describe a software task", key: "input" }),
      h("button", { onClick: submitTask, key: "button" }, "Run Workflow"),
    ]),
    h(AgentWorkflow, { workflow: state.workflow, key: "workflow" }),
    h("section", { className: "panel span-6", key: "todo" }, [
      h("div", { className: "label", key: "label" }, "Todo List"),
      h("ul", { className: "list", key: "list" }, (state.todo_list || ["Waiting for task"]).map((item, index) => h("li", { key: index }, item))),
    ]),
    h("section", { className: "panel span-6", key: "deliverable" }, [
      h("div", { className: "label", key: "label" }, "Final Deliverable"),
      h("div", { className: "console", key: "body" }, state.final_deliverable || "No deliverable yet."),
    ]),
  ]);
}

ReactDOM.createRoot(document.getElementById("react-root")).render(h(Dashboard));
