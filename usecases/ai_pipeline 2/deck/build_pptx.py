"""Generate the editable client presentation (.pptx).

    python deck/build_pptx.py           # -> deck/AI_Pipeline_LLMOps.pptx

Simple, natural language. Speaker notes are added to each slide as plain comments
you can read while presenting. No screenshot placeholders. Everything is editable
in PowerPoint / Teams / Google Slides after generation.
"""
from pathlib import Path

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

NAVY = RGBColor(0x0F, 0x21, 0x38)
BLUE = RGBColor(0x3B, 0x74, 0xC4)
TEAL = RGBColor(0x2B, 0xB8, 0xA3)
INK = RGBColor(0x20, 0x2A, 0x36)
SOFT = RGBColor(0x5C, 0x6B, 0x7D)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT = RGBColor(0xF2, 0xF6, 0xFB)

OUT = Path(__file__).resolve().parent / "AI_Pipeline_LLMOps.pptx"

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]
SW, SH = prs.slide_width, prs.slide_height


def slide():
    return prs.slides.add_slide(BLANK)


def rect(s, x, y, w, h, color):
    from pptx.enum.shapes import MSO_SHAPE
    sh = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, h)
    sh.fill.solid(); sh.fill.fore_color.rgb = color
    sh.line.fill.background()
    sh.shadow.inherit = False
    return sh


def text(s, x, y, w, h, runs, align=PP_ALIGN.LEFT, space=6, anchor=None):
    """runs: list of paragraphs; each paragraph is a list of (txt, size, bold, color)."""
    tb = s.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame; tf.word_wrap = True
    if anchor is not None:
        tf.vertical_anchor = anchor
    for i, para in enumerate(runs):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align; p.space_after = Pt(space)
        for (txt, size, bold, color) in para:
            r = p.add_run(); r.text = txt
            r.font.size = Pt(size); r.font.bold = bold; r.font.color.rgb = color
            r.font.name = "Segoe UI"
    return tb


def notes(s, msg):
    s.notes_slide.notes_text_frame.text = msg


def header(s, kicker, title):
    rect(s, 0, 0, SW, Inches(0.12), BLUE)
    text(s, Inches(0.6), Inches(0.35), Inches(12), Inches(0.4),
         [[(kicker.upper(), 12, True, BLUE)]])
    text(s, Inches(0.6), Inches(0.7), Inches(12.2), Inches(0.9),
         [[(title, 30, True, NAVY)]])


def bullets(s, x, y, w, h, items, size=15, gap=8):
    runs = []
    for it in items:
        if isinstance(it, tuple):
            lead, rest = it
            runs.append([("•  ", size, True, BLUE), (lead, size, True, INK), (rest, size, False, INK)])
        else:
            runs.append([("•  ", size, True, BLUE), (it, size, False, INK)])
    text(s, x, y, w, h, runs, space=gap)


# ── 1 · TITLE ────────────────────────────────────────────────────────────────
s = slide()
rect(s, 0, 0, SW, SH, NAVY)
rect(s, 0, Inches(2.7), SW, Inches(0.06), TEAL)
text(s, Inches(0.9), Inches(0.9), Inches(11.5), Inches(0.5),
     [[("AFNI · Office of GenAI Architecture", 14, True, TEAL)]])
text(s, Inches(0.9), Inches(1.5), Inches(11.5), Inches(1.6),
     [[("An Enterprise LLMOps Platform", 40, True, WHITE)],
      [("proven on the AI Pipeline (APIX)", 40, True, WHITE)]])
text(s, Inches(0.9), Inches(3.1), Inches(11), Inches(1.2),
     [[("We didn't build one AI feature. We built the platform that all our AI use cases run on —",
        18, False, RGBColor(0xD5, 0xE1, 0xF0))],
      [("and we already have a real application running on it.", 18, False, RGBColor(0xD5, 0xE1, 0xF0))]])
text(s, Inches(0.9), Inches(4.7), Inches(11.5), Inches(0.6),
     [[("14 reusable components    •    6 already used by APIX    •    one console to run and govern it",
        15, True, RGBColor(0x9F, 0xD8, 0xCC))]])
notes(s, "Open simple. Two things today: the platform we built, and proof it works because APIX "
         "already runs on it. The point I want to land is leverage — build it once, reuse it for "
         "every future use case. Keep it short, then move on.")

# ── 2 · THE IDEA ─────────────────────────────────────────────────────────────
s = slide()
header(s, "The idea", "Build the platform, not one-off features")
text(s, Inches(0.6), Inches(1.7), Inches(12), Inches(0.8),
     [[("If every AI use case is built from scratch, each one redoes the same plumbing — model calls, "
        "prompts, safety, cost tracking, evaluation — slowly and inconsistently.", 16, False, INK)]])
bullets(s, Inches(0.6), Inches(2.9), Inches(12), Inches(3),
        [("Build it once. ", "The platform solves the hard, shared parts a single time."),
         ("Reuse everywhere. ", "A new use case plugs in with config, not a rebuild."),
         ("Governed by design. ", "Safety, cost and quality checks are built in, not bolted on later."),
         ("Faster and cheaper. ", "Second and third use cases land in weeks instead of quarters.")],
        size=17, gap=12)
notes(s, "The trap with GenAI is doing it feature by feature. Each team rebuilds the scaffolding and "
         "each does safety and cost differently. We flipped it — one platform, use cases plug in. APIX "
         "is the first one on it, so it already paid for itself as the proof.")

# ── 3 · COMPONENTS (list, in order) ──────────────────────────────────────────
def component_slide(title_suffix, items):
    s = slide()
    header(s, "The platform", "What's in it — " + title_suffix)
    y = Inches(1.75)
    for num, name, desc in items:
        badge = rect(s, Inches(0.6), y, Inches(0.62), Inches(0.42), BLUE)
        badge.text_frame.text = num
        r = badge.text_frame.paragraphs[0].runs[0]
        r.font.size = Pt(13); r.font.bold = True; r.font.color.rgb = WHITE
        badge.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
        text(s, Inches(1.4), y - Inches(0.02), Inches(11.4), Inches(0.5),
             [[(name + " — ", 14.5, True, NAVY), (desc, 14.5, False, INK)]])
        y += Inches(0.52)
    return s


s = component_slide("part 1 of 2", [
    ("01", "Repo & foundation", "the shared project structure and cloud setup everything else builds on."),
    ("02", "Prompt management", "prompts are stored and versioned; you edit them without touching code."),
    ("03", "Model management", "pick the model by a simple name (alias); swap models by config, per environment."),
    ("04", "Evaluation gate", "score prompts and models against known-good examples before anything ships."),
    ("05", "Observability", "every model call is traced — tokens, cost, time taken, and any safety flag."),
    ("06", "Guardrails", "checks each call for PII, secrets, and prompt-injection before and after the model."),
    ("07", "Data tools", "search over documents (RAG), speech-to-text/text-to-speech, and API connectors."),
])
notes(s, "Walk these top to bottom, one line each — don't dwell. The ones that matter most for APIX are "
         "02 prompts, 03 models, 04 evaluation, 05 observability, 06 guardrails. 01 and 07 are foundation "
         "and extras that other use cases will use.")

s = component_slide("part 2 of 2", [
    ("08", "Orchestration", "the engine that runs the steps of a pipeline in order, with tracing built in."),
    ("09", "CI/CD", "automated checks on every change, including the evaluation gate as a required step."),
    ("10", "Serving / hosting", "expose a pipeline as a service or a container when we need to."),
    ("11", "Feedback", "capture human corrections and turn them into new test cases automatically."),
    ("12", "FinOps", "cost budgets and spend tracking so we stay in control of the bill."),
    ("13", "Governance & onboarding", "the step-by-step path to bring a new use case onto the platform."),
    ("14", "Security & compliance", "data-handling and privacy policy, mapped to industry standards."),
])
notes(s, "Second half — same pace, one line each. Reassure them these all exist and are reusable; APIX "
         "doesn't need every one yet, but the next use case can pick up whatever it needs without new "
         "platform work. The theme to repeat: reusable, config-driven.")

# ── 4 · HOW IT PLUGS INTO APIX ───────────────────────────────────────────────
s = slide()
header(s, "How we used it", "Plugged into the AI Pipeline at one point")
text(s, Inches(0.6), Inches(1.7), Inches(12), Inches(0.7),
     [[("APIX turns raw call transcripts into per-agent coaching. It runs in five steps:", 16, False, INK)]])
steps = ["Denoise", "Analysis", "Summary", "Metrics", "KPI"]
x = Inches(0.6); w = Inches(2.2)
for i, st in enumerate(steps):
    b = rect(s, x, Inches(2.5), w, Inches(0.85), LIGHT)
    b.line.color.rgb = RGBColor(0xCF, 0xE0, 0xF6); b.line.width = Pt(1)
    b.text_frame.text = st
    pr = b.text_frame.paragraphs[0].runs[0]; pr.font.size = Pt(15); pr.font.bold = True; pr.font.color.rgb = NAVY
    b.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
    x = x + w + Inches(0.25)
text(s, Inches(0.6), Inches(3.7), Inches(12.2), Inches(0.9),
     [[("Every step makes its model calls through one shared function. We added the platform at that single "
        "point — so the steps themselves were left untouched.", 15, False, INK)]])
bullets(s, Inches(0.6), Inches(4.7), Inches(12.2), Inches(2),
        [("At that one point: ", "pick the right prompt version, run guardrails, choose the model, call it, "
          "check the output, and record cost and traces."),
         ("Low risk. ", "It's an add-on, not a rewrite — we can switch any part off and the pipeline still runs.")],
        size=15, gap=10)
notes(s, "Plain version: the developer's pipeline already sent every model call through one function. That "
         "was our way in — we wrapped that one spot. Now the platform handles prompts, safety, model choice, "
         "and cost tracking, and the five steps were left as they were. Emphasise low risk and reversible.")

# ── 5 · WHAT WE IMPLEMENTED ──────────────────────────────────────────────────
s = slide()
header(s, "Where we are", "What's working today")
bullets(s, Inches(0.6), Inches(1.8), Inches(12.2), Inches(3.4),
        [("Done: ", "observability & cost, model management, guardrails, prompt versioning, evaluation gate, "
          "feedback loop — plus one console to run and operate it all."),
         ("Prompt change goes live by clicking Activate — ", "no redeployment needed."),
         ("PII is flagged for audit, never dropped; ", "secrets are blocked. Real customer data stays safe."),
         ("Runs on a locked-down machine — ", "the demo is plain Python, nothing to install."),
         ("Next: ", "send cost and traces to Azure Monitor once the client provides accounts and rates."),
         ("Ready when needed: ", "search/RAG, voice, and hosting for the next use case.")],
        size=15.5, gap=11)
notes(s, "Everything in the first four bullets is done and I can show it. Two things worth stressing: prompt "
         "changes go live without a deployment, and guardrails flag PII but never drop a call because these "
         "are real transcripts. The 'next' and 'ready' bullets set up the decisions slide.")

# ── 6 · THE CONSOLE ──────────────────────────────────────────────────────────
s = slide()
header(s, "How we operate it", "One console for everything")
bullets(s, Inches(0.6), Inches(1.8), Inches(12.2), Inches(4),
        [("Application — ", "run the pipeline and see the coaching output: KPIs and per-agent scores, "
          "reflections, and the calls behind them."),
         ("Playground — ", "edit a prompt, pick a model, and score it against known-good examples; see the cost."),
         ("Evaluation — ", "quality over time, and per prompt version — the gate before anything ships."),
         ("Golden datasets — ", "view, edit, add, or upload the known-good examples we score against."),
         ("Monitoring — ", "calls, tokens, cost, time taken, and guardrail activity."),
         ("Feedback & Guardrails — ", "coach feedback on calls, and an audit trail of every safety decision.")],
        size=15, gap=10)
text(s, Inches(0.6), Inches(6.35), Inches(12.2), Inches(0.7),
     [[("Note: the demo uses a small sample of made-up call data so it runs anywhere. The same screens show "
        "real numbers once we connect live data.", 13, True, SOFT)]])
notes(s, "Describe the tabs simply — don't read every word. If we're live, click through Application then "
         "Playground. Be upfront that the numbers are sample data so it runs on any machine; the exact same "
         "screens work with real data once we flip to live.")

# ── 7 · GOVERNANCE & COST ────────────────────────────────────────────────────
s = slide()
header(s, "Why it matters to leadership", "Safe and measured by default")
bullets(s, Inches(0.6), Inches(1.9), Inches(12.2), Inches(3.4),
        [("Safety on every call — ", "PII flagged, secrets blocked, injection checked. Change the policy in one "
          "place and it applies everywhere."),
         ("Nothing is a black box — ", "every model call is traced with its cost and time."),
         ("Cost is a first-class number — ", "track spend live, and use a cheaper model for bulk steps to save."),
         ("Same rules for the next use case — ", "it inherits this safety and cost story automatically.")],
        size=16, gap=13)
notes(s, "This is the de-risking slide for a regulated contact-centre business. Nothing hits a model without "
         "guardrails, and everything is costed and traced. And when use case two arrives, it gets the same "
         "safety — we don't redo governance every time.")

# ── 8 · DECISIONS ────────────────────────────────────────────────────────────
s = slide()
header(s, "What we need from you", "A few decisions to move forward")
bullets(s, Inches(0.6), Inches(1.9), Inches(12.2), Inches(3.6),
        [("Azure accounts and environments — ", "where we run, and dev/test/prod split."),
         ("Approved models and their real rates — ", "turns cost tracking into exact numbers."),
         ("PII policy — ", "flag for audit (today) or mask/redact; anything that must be hard-blocked."),
         ("Ground-truth examples — ", "who owns them, and a first small batch for APIX."),
         ("Human sign-off — ", "do coaches approve the AI's notes before agents see them?"),
         ("The next use case — ", "which one to onboard to prove reuse (voice, performance index, hiring).")],
        size=15.5, gap=11)
text(s, Inches(0.6), Inches(6.4), Inches(12.2), Inches(0.6),
     [[("If we get the first four, we can take APIX live and start the next use case at the same time.",
        14, True, TEAL)]])
notes(s, "These aren't blockers to the demo — they're what turns it into production and sets the roadmap. If I "
         "can get four things: approved models and rates, the PII stance, a small set of ground-truth examples, "
         "and which second use case you want. Then we go live and prove reuse in parallel.")

# ── 9 · CLOSE ────────────────────────────────────────────────────────────────
s = slide()
rect(s, 0, 0, SW, SH, NAVY)
text(s, Inches(0.9), Inches(1.2), Inches(11.5), Inches(1.2),
     [[("Build once. Onboard many.", 40, True, WHITE)]])
text(s, Inches(0.9), Inches(2.5), Inches(11.5), Inches(1),
     [[("APIX proved the platform works. The next use case reuses the same guardrails, cost controls, and "
        "console — and lands in weeks.", 18, False, RGBColor(0xD5, 0xE1, 0xF0))]])
bullets_items = [
    "Voice Agent — adds voice; reuses everything else.",
    "Performance Index — reuses the exact APIX analysis approach.",
    "Hiring Intelligence — reuses guardrails and human sign-off.",
]
runs = [[("•  ", 17, True, TEAL), (t, 17, False, RGBColor(0xEA, 0xF1, 0xFB))] for t in bullets_items]
text(s, Inches(0.9), Inches(3.9), Inches(11.5), Inches(2), runs, space=12)
text(s, Inches(0.9), Inches(6.1), Inches(11.5), Inches(0.7),
     [[("The ask: approve the decisions, and let us take APIX live and start use case #2.", 16, True,
        RGBColor(0x9F, 0xD8, 0xCC))]])
notes(s, "Close on leverage: you funded a platform, not a feature. The next use case reuses all of this and "
         "lands fast with the same governance. Ask for the decisions and the green light to take APIX live and "
         "start number two.")

prs.save(str(OUT))
print(f"Wrote {OUT}  ({len(prs.slides.__iter__.__self__._sldIdLst)} slides)")
