# Prompt Iteration 03 — Load Test Hang via VS Code Debugger

## Goal
Get to the bottom of why running the load test via the VS Code "Run and
Debug" panel never finished, when running the exact same command directly
in a terminal always completed on time. This wasn't a request to generate
new code — it was a live debugging session.

## Context provided
- Symptom reported as-is, from actually using the project the way its own
  `.vscode/launch.json` told me to: "yine işlem askıda kaldı test
  tamamlanmıyor" (it hung again, the test isn't finishing) — after the AI
  had already shipped a fix for a *different* hang earlier in the same
  session (a missing `timeout=` on the HTTP requests).
- The AI's own verification of that earlier fix had only ever run
  `locustfile.py` from a plain terminal (`.venv/bin/locust ...`), where it
  finished in the expected ~60-70s every time.

## Investigation
1. First hang (network-related): `ps` showed the process alive with very
   low CPU time and an open TCP connection to n11.com's Cloudflare IP that
   never closed. `requests` has no default timeout, so a single stalled
   connection blocks the whole run past `--run-time`. Fixed by adding
   `timeout=REQUEST_TIMEOUT_S` to every `self.client.get()` call.
2. Reported again after the fix — same symptom, but this time `lsof` on the
   hung process showed *no* outbound TCP connection at all, only the local
   debugpy control socket. That ruled out the network theory entirely and
   pointed somewhere else: the debugger itself.
3. Locust depends on `gevent` for its concurrency model (monkey-patches
   sockets/threads to cooperatively schedule "users" as greenlets).
   `debugpy`'s tracing is a known source of conflicts with gevent's
   scheduler — greenlet switches can stop resuming once a debugger attaches
   tracing hooks. This matched the symptom (alive, ~0% CPU, no network,
   debugpy connected) better than any application-level bug.

## Output evaluation
**Accepted:**
- Moving the Locust task out of `launch.json` (debugpy) entirely and into
  `.vscode/tasks.json` as a plain shell task — there's no real value in
  single-stepping through gevent greenlets anyway, so the debugger wasn't
  buying anything for this specific task.

**Rejected:**
- Trying to make Locust debugger-compatible (e.g. disabling gevent
  monkey-patching) — more fragile than just not debugging a load-generation
  tool with a Python stepper, and outside the scope of what this assignment
  needs.

## Iteration notes
The key turn here wasn't a prompt re-write — it was that the AI's first fix
was correct for the bug it could see (no timeout), but the *test of the
fix* used a different execution path (terminal) than the one that actually
exposed the second bug (VS Code debugger). Re-running through the same
real workflow that surfaced the original report was what caught it, not a
better prompt.
