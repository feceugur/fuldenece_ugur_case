# AI Usage Documentation

## 1. Context, Prompt, Skill, Agent — in relation to AI coding assistants

**Context** is the information you supply to the AI before or alongside your request — existing code, file structure, constraints, or examples that shape what the AI produces. Without context, the AI works from generic knowledge; with context, it can generate code that fits your specific codebase.

**Prompt** is the natural-language instruction you send to the AI — the actual question or command that drives the response. A well-structured prompt is specific about the goal, the constraints, and the expected format of the output.

**Skill** refers to a reusable, pre-defined capability that an AI assistant can invoke — such as "write a Playwright test" or "generate a load test" — often packaged as a template or tool within the assistant's system. Skills encode best practices so you don't have to re-explain them every time.

**Agent** is an AI system that can autonomously plan and execute multi-step tasks, calling tools (file read/write, web search, code execution) and making decisions along the way, rather than just responding to a single prompt.

## 2. How I validated the AI output — what I rejected and why

I validated by running the generated tests against the actual site and checking that selectors matched real DOM elements. I rejected the initial version's use of `page.locator("form")` with a hard-coded index because it broke when the page structure changed between navigations. I also rejected `time.sleep()` calls — they make tests flaky; Playwright's `wait_for_load_state` is both more reliable and semantically correct.

## 3. One point where AI was weak — and how I solved it manually

The AI consistently assumed stable, semantic CSS class names like `.job-title` or `.department`, which don't exist on insiderone.com (the site uses opaque, hashed class names). I solved this manually by inspecting the live DOM in DevTools, identifying the actual element hierarchy, and rewriting the locators to use text content and ARIA roles instead of class-based selectors.

## 4. When I would prefer to write code manually instead of using AI

I prefer writing manually when the logic is deeply stateful or depends on subtle timing — for example, multi-step UI flows where each step's result determines the next selector. AI tends to generate each step in isolation and misses cross-step dependencies. Manual coding is also faster for very short, one-off assertions where explaining the context to the AI takes longer than just writing the line.
