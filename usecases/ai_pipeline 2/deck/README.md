# Client presentation deck (HTML)

A self-contained set of linked HTML pages for presenting the AFNI LLMOps platform and the
AI Pipeline (APIX) implementation to the client. **No internet, no build, no install** —
just open the file in any browser (works over `file://`, so it's safe on a locked-down VDI).

## Present it

Open **`index.html`** in a browser (double-click, or drag into Chrome/Edge).

Navigate by:
- the **top menu**,
- the **Next → / ← Prev** buttons (bottom bar), or
- the **← →  arrow keys** (deck feels like slides).

Tip: press **F11** for full-screen presentation mode.

## Pages (in order)

1. **index.html** — Overview: the thesis and how the walkthrough is structured.
2. **platform.html** — The LLMOps platform: 14 components by category + what's reusable.
3. **implementation.html** — How the platform plugs into AI Pipeline (APIX): planned vs. implemented.
4. **decisions.html** — 10 concrete roadmap decisions we need from the client.
5. **future.html** — How the same platform powers future use cases (reuse story).
6. **usecases.html** — Candidate AFNI use cases, **hidden behind a Show/Hide button** (exploratory,
   revealed only on click so they don't distract from the committed roadmap).

Shared files: `deck.css` (styles), `deck.js` (nav + pager + arrow keys + the show/hide toggle).

## Editing

Plain HTML/CSS/JS — edit any page and refresh. To add a page, copy an existing one and add it to
the `PAGES` array in `deck.js` so the nav/pager pick it up.
