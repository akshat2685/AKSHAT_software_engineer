(() => {
  const socket = new WebSocket((location.protocol === 'https:' ? 'wss://' : 'ws://') + location.host + '/ws');
  const avatarOrb = document.querySelector('#avatar-orb');
  const avatarRoot = document.querySelector('.avatar');
  const avatarStateEl = document.querySelector('#avatar-state');
  const bubbleText = document.querySelector('.bubble > div:last-child');
  const pupils = Array.from(document.querySelectorAll('.pupil'));
  const mouth = document.querySelector('.mouth');
  const rings = Array.from(document.querySelectorAll('.ring'));
  const particles = Array.from(document.querySelectorAll('.particle'));
  let lastMove = Date.now();
  let speechLockedUntil = 0;
  const greetKey = 'akshat_avatar_greeted_once';
  const clamp = (value, min, max) => Math.max(min, Math.min(max, value));
  const escapeHtml = (text) => String(text ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');

  const setMessage = (text) => {
    if (bubbleText) bubbleText.textContent = text;
  };

  const setState = (state, msg) => {
    const normalized = String(state || 'idle').toLowerCase().replace(/\s+/g, '-');
    if (avatarRoot) {
      avatarRoot.className = avatarRoot.className
        .split(' ')
        .filter((c) => !c.startsWith('state-'))
        .concat(['state-' + normalized])
        .join(' ');
    }
    if (avatarStateEl) avatarStateEl.textContent = state || 'Idle';
    if (msg) setMessage(msg);
    if (normalized === 'success') speechLockedUntil = Date.now() + 2000;
    if (normalized === 'error') speechLockedUntil = Date.now() + 3000;
  };

  const renderList = (selector, items) => {
    const el = document.querySelector(selector);
    if (!el) return;
    el.innerHTML = (items && items.length ? items : ['Waiting for task'])
      .map((item) => `<li>${escapeHtml(item)}</li>`)
      .join('');
  };

  const renderText = (selector, text) => {
    const el = document.querySelector(selector);
    if (el) el.textContent = text || 'No result yet.';
  };

  const renderAgents = (workflow) => {
    const outputs = workflow && workflow.agent_outputs ? workflow.agent_outputs : {};
    document.querySelectorAll('[data-agent-name]').forEach((card) => {
      const name = card.getAttribute('data-agent-name');
      const output = card.querySelector('[data-agent-output]');
      if (output) output.textContent = outputs[name] || 'Waiting for assigned work.';
    });
  };

  const updateFromStatus = (data) => {
    if (!data) return;
    setState(data.avatar_state || data.status || 'Idle', data.current_action || 'Waiting');
    renderList('[data-todo-list]', data.todo_list || []);
    renderList('[data-plan-list]', data.plan || []);
    renderText('[data-final-result]', data.final_deliverable || (data.workflow && data.workflow.final_deliverable));
    renderText('[data-current-agent]', data.current_agent || 'Idle');
    renderText('[data-current-state]', data.avatar_state || data.status || 'Idle');
    renderText('[data-current-action]', (data.avatar_state || data.status || 'Idle') + ' / ' + (data.current_action || 'Waiting'));
    renderText('[data-tool-count]', String((data.active_tools || data.tools || []).length));
    renderAgents(data.workflow || {});
  };

  const speakOnce = (text) => {
    try {
      if (!sessionStorage.getItem(greetKey) && 'speechSynthesis' in window) {
        sessionStorage.setItem(greetKey, '1');
        const u = new SpeechSynthesisUtterance(text);
        u.rate = 1;
        u.pitch = 1;
        u.volume = 1;
        window.speechSynthesis.cancel();
        window.speechSynthesis.speak(u);
      }
    } catch {}
  };

  const moveEyes = (x, y) => {
    if (!avatarOrb || !pupils.length) return;
    const rect = avatarOrb.getBoundingClientRect();
    const dx = ((x - rect.left) / rect.width - 0.5) * 2;
    const dy = ((y - rect.top) / rect.height - 0.5) * 2;
    const px = clamp(dx * 9, -9, 9);
    const py = clamp(dy * 7, -7, 7);
    pupils.forEach((p) => {
      p.style.setProperty('--px', px + 'px');
      p.style.setProperty('--py', py + 'px');
    });
    avatarOrb.style.transform = 'perspective(1000px) translate(' + (px * 0.55) + 'px,' + (py * 0.35) + 'px) rotateX(' + (-py * 0.25) + 'deg) rotateY(' + (px * 0.32) + 'deg) scale(1.018)';
    lastMove = Date.now();
  };

  const animateIdle = () => {
    if (!avatarOrb || Date.now() - lastMove < 250) return;
    const t = Date.now() / 1000;
    const sway = Math.sin(t / 1.4) * 2.2;
    const lift = Math.sin(t / 1.9) * 6;
    const tilt = Math.sin(t / 2.6) * 0.9;
    avatarOrb.style.transform = 'perspective(1000px) translateY(' + (-4 + lift) + 'px) rotateZ(' + tilt + 'deg) rotateY(' + sway + 'deg) scale(1.01)';
    if (mouth) mouth.classList.toggle('smile', Math.sin(t / 3.5) > 0.85);
  };

  const animateThinking = () => {
    rings.forEach((r, i) => {
      r.style.opacity = String(0.7 + Math.sin(Date.now() / 500 + i) * 0.08);
    });
    particles.forEach((p, i) => {
      p.style.opacity = Date.now() > speechLockedUntil ? String(0.18 + (i % 4) * 0.08) : '0';
    });
  };

  socket.addEventListener('message', (e) => {
    try {
      const evt = JSON.parse(e.data);
      const feed = document.querySelector('#live-feed');
      if (feed) {
        const item = document.createElement('div');
        item.className = 'feed-item';
        item.innerHTML = `<div class="label">${escapeHtml(evt.ts)} / ${escapeHtml(evt.kind)}</div><div>${escapeHtml(evt.message)}</div>`;
        feed.prepend(item);
      }
      if (evt.data && evt.data.data) updateFromStatus(evt.data.data);
      if (evt.data && evt.data.avatar_state) setState(evt.data.avatar_state, evt.data.current_action || evt.message);
      if (evt.kind === 'chat') appendChat('assistant', evt.message);
      const consoleEl = document.querySelector('#console');
      if (consoleEl && evt.data && evt.data.current_action) consoleEl.textContent = evt.data.current_action + '\nStatus: ' + (evt.data.status || '');
      if (['planning', 'researching', 'coding', 'testing', 'error', 'success'].includes(evt.kind)) {
        setState(evt.kind, evt.message);
      }
    } catch {}
  });

  async function pollStatus(remaining) {
    if (remaining <= 0) return;
    try {
      const response = await fetch('/api/status');
      const data = await response.json();
      updateFromStatus(data);
      if (!['success', 'error'].includes(String(data.status || '').toLowerCase())) {
        setTimeout(() => pollStatus(remaining - 1), 1000);
      }
    } catch {
      setTimeout(() => pollStatus(remaining - 1), 1000);
    }
  }

  async function submitTask() {
    const input = document.querySelector('#task-input');
    const prompt = input ? input.value.trim() : '';
    const consoleEl = document.querySelector('#console');
    if (!prompt) return;
    appendChat('user', prompt);
    input.value = '';
    const started = 'AKSHAT is thinking.';
    setState('Thinking', started);
    if (consoleEl) consoleEl.textContent = started + '\nTask: ' + prompt;
    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({message: prompt})
    });
    const data = await response.json();
    if (data.error) {
      alert(data.error);
      return;
    }
    appendChat('assistant', data.reply || '');
    updateFromStatus(data.state || data);
    pollStatus(data.mode === 'workflow' ? 18 : 1);
  }

  function appendChat(role, text) {
    const chat = document.querySelector('#chat-thread');
    if (!chat || !text) return;
    const item = document.createElement('div');
    item.className = 'chat-line ' + role;
    item.textContent = text;
    chat.appendChild(item);
    chat.scrollTop = chat.scrollHeight;
  }

  async function runTool() {
    const nameEl = document.querySelector('#tool-name');
    const argsEl = document.querySelector('#tool-args');
    const output = document.querySelector('#tool-output');
    const tool = nameEl ? nameEl.value : '';
    let args = {};
    try {
      args = argsEl && argsEl.value.trim() ? JSON.parse(argsEl.value) : {};
    } catch (err) {
      if (output) output.textContent = 'Invalid JSON args: ' + err.message;
      return;
    }
    if (output) output.textContent = 'Running ' + tool + '...';
    const response = await fetch('/api/tool', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({tool, args})
    });
    const data = await response.json();
    if (output) output.textContent = JSON.stringify(data, null, 2);
    pollStatus(1);
  }

  window.submitTask = submitTask;
  window.runTool = runTool;
  window.refreshAkshat = () => pollStatus(1);
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' && event.target && event.target.id === 'task-input') {
      event.preventDefault();
      submitTask();
    }
  });
  window.addEventListener('mousemove', (e) => {
    moveEyes(e.clientX, e.clientY);
  });
  setInterval(() => { animateIdle(); animateThinking(); }, 50);
  setState(avatarStateEl ? avatarStateEl.textContent : 'Idle', bubbleText ? bubbleText.textContent : "Hello, I'm AKSHAT.");
  speakOnce("Hello, I'm AKSHAT. I'll help you build, test, and improve this app.");
  pollStatus(1);
})();
