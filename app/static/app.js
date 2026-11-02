(function () {
  "use strict";

  // ---------------------------------------------------------------------------
  // Config
  // ---------------------------------------------------------------------------
  const API_BASE = (window.__API_URL__ && window.__API_URL__.replace(/\/+$/, "")) ||
    (typeof VITE_API_URL !== "undefined" ? VITE_API_URL.replace(/\/+$/, "") : "") ||
    window.location.origin;

  // ---------------------------------------------------------------------------
  // State
  // ---------------------------------------------------------------------------
  let threadId = null;

  // ---------------------------------------------------------------------------
  // DOM refs
  // ---------------------------------------------------------------------------
  const queryInput = document.getElementById("queryInput");
  const threadInput = document.getElementById("threadInput");
  const submitBtn = document.getElementById("submitBtn");
  const newThreadBtn = document.getElementById("newThread");
  const loadingEl = document.getElementById("loading");
  const outputEl = document.getElementById("output");
  const threadIdEl = document.getElementById("threadId");

  // ---------------------------------------------------------------------------
  // Helpers
  // ---------------------------------------------------------------------------
  function setLoading(loading) {
    loadingEl.classList.toggle("hidden", !loading);
    submitBtn.disabled = loading;
    if (!loading) outputEl.classList.remove("hidden");
  }

  function showOutput(html) {
    if (!html || String(html).trim() === "") {
      html = `<div class="section"><div class="section-content">no content returned from the server.</div></div>`;
    }
    outputEl.innerHTML = html;
    outputEl.classList.remove("hidden");
  }

  function escapeHtml(str) {
    if (typeof str !== "string") return "";
    return str
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function renderSection(title, content, options = {}) {
    const uncertain = options.uncertain
      ? '<span class="tag-uncertain">uncertain</span>'
      : "";
    const items = Array.isArray(content)
      ? content.map((i) => `<li>${escapeHtml(i)}</li>`).join("")
      : "";
    const listHtml = items ? `<ul>${items}</ul>` : "";
    const textHtml = !items ? escapeHtml(String(content)) : "";
    return `
      <div class="section">
        <div class="section-title">${escapeHtml(title)} ${uncertain}</div>
        <div class="section-content">
          ${listHtml}
          ${textHtml}
        </div>
      </div>
    `;
  }

  function isHedged(text) {
    if (typeof text !== "string") return false;
    const hedges = [
      "likely",
      "probable",
      "possibly",
      "may",
      "might",
      "could",
      "appears",
      "seems",
      "suggests",
      "indicated",
      "insufficient evidence",
      "cannot be determined",
      "not established",
      "unclear",
      "inconclusive",
    ];
    const lower = text.toLowerCase();
    return hedges.some((h) => lower.includes(h));
  }

  function renderFinalResponseFromObject(fr) {
    if (!fr || typeof fr !== "object") return "";

    const summary = fr.summary || "";
    const rootCause = fr.root_cause || "";
    const evidence = Array.isArray(fr.evidence) ? fr.evidence : [];
    const recommendedAction = Array.isArray(fr.recommended_action) ? fr.recommended_action : [];
    const limitations = Array.isArray(fr.limitations) ? fr.limitations : [];

    let html = "";

    if (summary) {
      html += renderSection("Summary", summary, {
        uncertain: isHedged(summary),
      });
    }

    if (rootCause) {
      html += renderSection("Root Cause", rootCause, {
        uncertain: isHedged(rootCause),
      });
    }

    if (evidence.length) {
      html += renderSection("Evidence", evidence, {
        uncertain: evidence.some((e) => isHedged(e)),
      });
    }

    if (recommendedAction.length) {
      html += renderSection("Recommended Action", recommendedAction, {
        uncertain: recommendedAction.some((a) => isHedged(a)),
      });
    }

    if (limitations.length) {
      html += renderSection("Limitations", limitations);
    }

    if (!html) {
      html = `<div class="section"><div class="section-content">${escapeHtml(JSON.stringify(fr))}</div></div>`;
    }

    return html;
  }

  function renderFinalResponse(finalResponse) {
    if (!finalResponse || typeof finalResponse !== "string") return "";

    const lines = finalResponse.split(/\n+/);
    let currentKey = null;
    const buf = {};

    for (const line of lines) {
      const headerMatch = line.match(/^##\s+(.+)/i);
      if (headerMatch) {
        currentKey = headerMatch[1].trim();
        buf[currentKey] = buf[currentKey] || [];
        continue;
      }
      if (currentKey && line.trim()) {
        buf[currentKey] = buf[currentKey] || [];
        buf[currentKey].push(line.trim());
      }
    }

    const firstHeaderIdx = lines.findIndex((l) => /^##\s+/i.test(l));
    if (firstHeaderIdx > 0) {
      const preamble = lines.slice(0, firstHeaderIdx).join(" ").trim();
      if (preamble) buf["Summary"] = [preamble];
    }

    const merge = (key, arr) => {
      if (!arr || arr.length === 0) return "";
      return arr.join(" ");
    };

    const summary = merge("Summary", buf.Summary);
    const rootCause = merge("Root Cause", buf["Root Cause"]);
    const evidence = buf.Evidence || [];
    const recommendedAction = buf["Recommended Action"] || [];
    const limitations = buf.Limitations || [];

    let html = "";

    if (summary) {
      html += renderSection("Summary", summary, {
        uncertain: isHedged(summary),
      });
    }

    if (rootCause) {
      html += renderSection("Root Cause", rootCause, {
        uncertain: isHedged(rootCause),
      });
    }

    if (evidence.length) {
      html += renderSection("Evidence", evidence, {
        uncertain: evidence.some((e) => isHedged(e)),
      });
    }

    if (recommendedAction.length) {
      html += renderSection("Recommended Action", recommendedAction, {
        uncertain: recommendedAction.some((a) => isHedged(a)),
      });
    }

    if (limitations.length) {
      html += renderSection("Limitations", limitations);
    }

    if (!html) {
      html = `<div class="section"><div class="section-content">${escapeHtml(finalResponse)}</div></div>`;
    }

    return html;
  }

  function renderCheckedStrip(selectedAgents) {
    if (!Array.isArray(selectedAgents) || selectedAgents.length === 0) return "";
    const tags = selectedAgents
      .map((a) => `<span class="tag">${escapeHtml(a)}</span>`)
      .join("");
    return `<div class="checked-strip"><span class="label">checked:</span><div class="tags">${tags}</div></div>`;
  }

  function renderGuardrailDecision(guardrail) {
    const decision = (guardrail && guardrail.decision) || "unknown";
    const category = (guardrail && guardrail.category) || "—";
    const reason = (guardrail && guardrail.reason) || "—";

    if (decision === "reject") {
      return `
        <div class="panel-denied">
          <div class="section-title">access denied</div>
          <div class="section-content">
            <p><strong>decision:</strong> ${escapeHtml(decision)}</p>
            <p><strong>category:</strong> ${escapeHtml(category)}</p>
            <p><strong>reason:</strong> ${escapeHtml(reason)}</p>
            <p style="margin-top:8px;font-size:11px;color:#ff8888;">investigation not performed.</p>
          </div>
        </div>
      `;
    }

    if (decision === "clarify") {
      return `
        <div class="panel-error">
          <div class="section-title">clarification needed</div>
          <div class="section-content">
            <p><strong>category:</strong> ${escapeHtml(category)}</p>
            <p><strong>reason:</strong> ${escapeHtml(reason)}</p>
          </div>
        </div>
      `;
    }

    return `
      <div class="section">
        <div class="section-title">guardrail</div>
        <div class="section-content">
          <p><strong>decision:</strong> ${escapeHtml(decision)}</p>
          <p><strong>category:</strong> ${escapeHtml(category)}</p>
          <p><strong>reason:</strong> ${escapeHtml(reason)}</p>
        </div>
      </div>
    `;
  }

  function renderErrorPanel(errors) {
    if (!Array.isArray(errors) || errors.length === 0) return "";
    const items = errors.map((e) => `<li>${escapeHtml(e)}</li>`).join("");
    return `
      <div class="panel-error">
        <div class="section-title">investigation errors</div>
        <div class="section-content"><ul>${items}</ul></div>
      </div>
    `;
  }

  function renderPartialNote(errors) {
    if (!Array.isArray(errors) || errors.length === 0) return "";
    return `<div class="note-partial">partial issues: some sources returned errors</div>`;
  }

  function renderResponse(data) {
    console.log("ForgeOps response:", data); // debug

    let html = "";

    // Always show thread info
    html += `
      <div class="section">
        <div class="section-title">thread</div>
        <div class="section-content">${escapeHtml(String(data.thread_id || "—"))}</div>
      </div>
    `;

    // Guardrail decision
    if (data.guardrail) {
      html += renderGuardrailDecision(data.guardrail);

      // If rejected, stop here — no investigation ran
      if (data.guardrail.decision === "reject") {
        showOutput(html);
        return;
      }
    }

    // Investigation plan
    if (data.investigation_plan && String(data.investigation_plan).trim()) {
      html += renderSection("investigation plan", data.investigation_plan);
    }

    // Status
    if (data.status && String(data.status).trim()) {
      html += renderSection("status", data.status);
    }

    // Errors (non-blocking)
    if (data.errors && data.errors.length) {
      html += renderErrorPanel(data.errors);
    }

    // Final response (happy path or partial)
    if (data.final_response) {
      if (typeof data.final_response === "object") {
        html += renderFinalResponseFromObject(data.final_response);
      } else if (typeof data.final_response === "string" && data.final_response.trim()) {
        html += renderFinalResponse(data.final_response);
      }
    }

    // If still nothing meaningful, show raw fallback
    if (!html || html.trim() === "") {
      html = `<div class="section"><div class="section-content">no investigation results returned.</div></div>`;
    }

    // Checked strip
    if (data.selected_agents) {
      html += renderCheckedStrip(data.selected_agents);
    }

    // Partial note if errors exist alongside final response
    if (data.errors && data.errors.length && data.final_response) {
      html += renderPartialNote(data.errors);
    }

    showOutput(html);
  }

  // ---------------------------------------------------------------------------
  // API call
  // ---------------------------------------------------------------------------
  async function runInvestigation(query, threadIdValue) {
    const body = { user_query: query };
    if (threadIdValue) body.thread_id = threadIdValue;

    const resp = await fetch(`${API_BASE}/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    if (!resp.ok) {
      let detail = `HTTP ${resp.status}`;
      try {
        const err = await resp.json();
        detail = err.detail || detail;
      } catch (_) {}
      throw new Error(detail);
    }

    return await resp.json();
  }

  // ---------------------------------------------------------------------------
  // Event handlers
  // ---------------------------------------------------------------------------
  async function onSubmit() {
    const query = queryInput.value.trim();
    if (!query) return;

    // Use manually entered thread_id, otherwise fall back to stored threadId
    const enteredThreadId = threadInput.value.trim();
    const effectiveThreadId = enteredThreadId || threadId;

    setLoading(true);
    try {
      const data = await runInvestigation(query, effectiveThreadId);
      threadId = data.thread_id || effectiveThreadId;
      threadIdEl.textContent = threadId;
      // Echo back the thread id to the input if it was auto-generated
      if (!enteredThreadId && threadId) {
        threadInput.value = threadId;
      }
      renderResponse(data);
    } catch (err) {
      showOutput(`
        <div class="panel-error">
          <div class="section-title">request failed</div>
          <div class="section-content">${escapeHtml(err.message)}</div>
        </div>
      `);
    } finally {
      setLoading(false);
    }
  }

  submitBtn.addEventListener("click", onSubmit);

  queryInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      onSubmit();
    }
  });

  newThreadBtn.addEventListener("click", () => {
    threadId = null;
    threadIdEl.textContent = "—";
    threadInput.value = "";
    queryInput.value = "";
    outputEl.classList.add("hidden");
  });

  // ---------------------------------------------------------------------------
  // Rain effect (canvas)
  // ---------------------------------------------------------------------------
  (function initRain() {
    const canvas = document.getElementById("rain");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    let w, h, cols, drops;

    function resize() {
      w = canvas.width = window.innerWidth;
      h = canvas.height = window.innerHeight;
      cols = Math.floor(w / 20);
      drops = new Array(cols).fill(1);
    }

    function draw() {
      ctx.fillStyle = "rgba(0, 0, 0, 0.05)";
      ctx.fillRect(0, 0, w, h);

      ctx.fillStyle = "#00ff41";
      ctx.font = "15px monospace";

      for (let i = 0; i < drops.length; i++) {
        const text = String.fromCharCode(0x30a0 + Math.random() * 30);
        const x = i * 20 + 10;
        ctx.fillText(text, x, drops[i] * 20);

        if (drops[i] * 20 > h && Math.random() > 0.975) {
          drops[i] = 0;
        }
        drops[i]++;
      }
    }

    resize();
    window.addEventListener("resize", resize);
    setInterval(draw, 50);
  })();

  // ---------------------------------------------------------------------------
  // Init
  // ---------------------------------------------------------------------------
  queryInput.focus();
})();
