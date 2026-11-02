Build a frontend for "ForgeOps" (an AI engineering investigation copilot) and
integrate it into the existing backend so the whole thing runs on localhost via
Docker — no mock data, talk to the real API.

BEFORE WRITING ANYTHING
- Inspect the existing repo structure, the current Dockerfile, and how the
  backend currently runs (framework — likely FastAPI given the Pydantic
  models, port it listens on, entrypoint command). Don't assume a layout —
  read what's actually there first and adapt to it.
- Find or infer the real request/response contract: the backend exposes an
  endpoint that accepts a query (and presumably a thread_id for
  continuation) and returns a QueryResponse shaped like:

  {
    "thread_id": string,
    "status": string,              // e.g. "ok" | "error" | other — check actual values used
    "guardrail": {
      "decision": "allow" | "reject",
      "category": string,
      "reason": string
    },
    "investigation_plan": string,
    "selected_agents": string[],
    "final_response": string,      // markdown-ish text: ## Summary / ## Root Cause /
                                    // ## Evidence / ## Recommended Action / ## Limitations
    "errors": string[]
  }

  Treat this as the source of truth over anything I described earlier — if the
  actual Pydantic model differs, follow the real code.

THEME
- Matrix aesthetic: black background, green monospace text, subtle glow/
  scanline accents, optional low-opacity falling-character rain in the
  background. Readability over flash.

RESPONSE-HANDLING LOGIC (three distinct states, not just success/fail)
1. guardrail.decision === "reject"
   → Show a distinct "ACCESS DENIED"-style panel (different accent, e.g.
     amber/red instead of green) with guardrail.category and
     guardrail.reason. Do not show findings/answer UI at all — the
     investigation never ran.
2. status indicates an error (investigation ran but failed/partial)
   → Show the green-terminal ErrorPanel listing `errors`. If
     `final_response` is non-empty anyway, still show it — partial results
     are useful, just flag that errors occurred alongside it.
3. Happy path
   → Parse and render `final_response` as structured content: pull out the
     Summary / Root Cause / Evidence / Recommended Action / Limitations
     sections and render each in its own styled block rather than dumping
     raw markdown. If a section reads like a hedge ("likely", "cannot be
     established", "insufficient evidence"), visually mark it uncertain
     (dim/amber tag) instead of presenting it with full confidence.
   → Under the main answer, show a small "Checked:" tag strip built from
     `selected_agents` (e.g. "GitHub · CI/CD") — just the fact that these
     ran, not their internals.
   → If `errors` is non-empty even on a nominally-ok status, show a small
     non-blocking "partial issues" note.

GENERAL UI REQUIREMENTS
- Input box for the query + submit, terminal-style loading state
  ("investigating...").
- Never crash: wrap all parsing/rendering in defensive checks for
  missing/null/malformed fields, fetch failures, timeouts, non-JSON
  responses. Any unhandled case → fall back to a generic in-theme error
  panel with the raw error, never a blank screen or console-only crash.
- Abstract backend/schema vocabulary from the UI copy — no field names like
  "guardrail_category" or "Finding" shown to the user; translate to plain
  labels.
- Support continuing in the same thread (reuse `thread_id` from the first
  response on follow-up queries) if the backend supports it — check the
  actual endpoint behavior first.

INTEGRATION + DOCKER
- Wire the frontend to call the backend's real endpoint. Use a relative
  path or an env-configurable base URL (e.g. `VITE_API_URL` /
  `window.__API_URL__`) rather than hardcoding — set it to work against
  localhost by default.
- Update the existing Dockerfile (or docker-compose.yml if one exists) so
  that a single `docker compose up` / `docker build && run` serves both the
  API and the frontend reachable from the host at localhost:
  - If the backend is FastAPI, the simplest integration is building the
    frontend and serving it as static files from the same FastAPI app
    (mount the built `dist/` at `/`), so one container, one port, no CORS
    headaches. Prefer this unless the existing setup clearly expects
    separate services.
  - If separate containers make more sense given the existing compose
    setup, add a frontend service + set up CORS on the backend for the
    frontend's origin, and wire both into docker-compose with the frontend
    on a clearly stated localhost port (e.g. localhost:3000) proxying API
    calls to the backend service.
  - Whichever approach: make sure it's a single command to bring the whole
    thing up on localhost, and tell me exactly what that command and URL
    are when you're done.
- Do not break the backend's existing run path (tests, existing endpoints)
  — this is additive.

DELIVERABLE
- Updated Dockerfile/compose, the frontend source, and the wiring between
  them — all integrated into the existing repo structure, not a standalone
  demo. End with the exact command to run and the localhost URL to open.
