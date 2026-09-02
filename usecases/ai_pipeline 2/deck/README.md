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

## The presentation to share — `AI_Pipeline_LLMOps.pptx`

**`AI_Pipeline_LLMOps.pptx`** is the editable PowerPoint to email / share on Teams. 10 slides,
each with **speaker notes** (plain comments in the Notes pane you can read while presenting).
Fully editable in PowerPoint / Google Slides.

Regenerate it any time after editing the content:
```bash
pip install python-pptx        # one-time
python deck/build_pptx.py      # -> deck/AI_Pipeline_LLMOps.pptx
```
Edit the wording in `deck/build_pptx.py` and re-run, or just edit the `.pptx` directly in
PowerPoint. There are **no screenshot placeholders** — add real screenshots in PowerPoint if
you want them.

## Click-through reference site (optional)

`index.html … usecases.html` is a browser-based reference version of the same story (top nav,
arrow-key navigation). Useful to hand over or explore at their own pace — not needed if you're
presenting from the PPT.

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
