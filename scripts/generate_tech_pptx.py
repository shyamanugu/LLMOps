#!/usr/bin/env python3
"""Generic, fully-editable technical deck on enterprise LLMOps (no images, native shapes only).
Requires: python-pptx.  Output: presentation/LLMOps-Framework-Technical.pptx
Design goals: simple, plain English, acronyms spelled out, editable in PowerPoint, speaker notes.
"""
import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

NAVY=RGBColor(0x1F,0x3A,0x5F); TEAL=RGBColor(0x2A,0x9D,0x8F); GRAYTX=RGBColor(0x3C,0x46,0x54)
LIGHT=RGBColor(0xEE,0xF1,0xF5); MUTE=RGBColor(0x6B,0x74,0x80); WHITE=RGBColor(0xFF,0xFF,0xFF)
LINEC=RGBColor(0xD5,0xDB,0xE3)
FONT="Calibri"
SW,SH=Inches(13.333),Inches(7.5)

prs=Presentation(); prs.slide_width=SW; prs.slide_height=SH
BLANK=prs.slide_layouts[6]

def add():
    s=prs.slides.add_slide(BLANK)
    r=s.shapes.add_shape(MSO_SHAPE.RECTANGLE,0,0,SW,SH); r.fill.solid(); r.fill.fore_color.rgb=WHITE; r.line.fill.background(); r.shadow.inherit=False
    return s

def _txt(s,x,y,w,h,runs,align=PP_ALIGN.LEFT,anchor=MSO_ANCHOR.TOP,sa=6,ls=1.05):
    tf=s.shapes.add_textbox(x,y,w,h).text_frame; tf.word_wrap=True; tf.vertical_anchor=anchor
    tf.margin_left=0; tf.margin_right=0; tf.margin_top=0; tf.margin_bottom=0
    for i,para in enumerate(runs):
        p=tf.paragraphs[0] if i==0 else tf.add_paragraph()
        p.alignment=align; p.space_after=Pt(sa); p.space_before=Pt(0); p.line_spacing=ls
        for (t,sz,b,c,*rest) in para:
            it=rest[0] if rest else False
            r=p.add_run(); r.text=t; r.font.size=Pt(sz); r.font.bold=b; r.font.italic=it; r.font.name=FONT; r.font.color.rgb=c
    return tf

def fillrect(s,x,y,w,h,color):
    sp=s.shapes.add_shape(MSO_SHAPE.RECTANGLE,x,y,w,h); sp.fill.solid(); sp.fill.fore_color.rgb=color
    sp.line.fill.background(); sp.shadow.inherit=False; return sp

def title(s,text,num):
    _txt(s,Inches(0.7),Inches(0.5),Inches(11.9),Inches(0.8),[[(text,28,True,NAVY)]])
    fillrect(s,Inches(0.72),Inches(1.28),Inches(1.5),Pt(3),TEAL)
    _txt(s,SW-Inches(1.1),SH-Inches(0.5),Inches(0.7),Inches(0.3),[[(str(num),10,False,MUTE)]],align=PP_ALIGN.RIGHT)
    _txt(s,Inches(0.7),SH-Inches(0.5),Inches(8),Inches(0.3),[[("Enterprise LLMOps — technical overview",9,False,MUTE)]])

def bullets(s,items,x=Inches(0.75),y=Inches(1.6),w=Inches(11.8),h=Inches(5.3),size=17,gap=11,color=GRAYTX):
    tf=s.shapes.add_textbox(x,y,w,h).text_frame; tf.word_wrap=True; tf.margin_left=0; tf.margin_top=0
    for i,it in enumerate(items):
        text=it[0]; lvl=it[1] if len(it)>1 else 0; bold=it[2] if len(it)>2 else False; col=it[3] if len(it)>3 else color
        p=tf.paragraphs[0] if i==0 else tf.add_paragraph()
        p.space_after=Pt(gap); p.space_before=Pt(0); p.line_spacing=1.08; p.level=lvl
        r=p.add_run(); r.text=("•  " if lvl==0 else "–  ")+text
        r.font.size=Pt(size-lvl); r.font.bold=bold; r.font.name=FONT; r.font.color.rgb=col
    return tf

def box(s,x,y,w,h,head,sub,fill=LIGHT,headc=NAVY):
    sp=s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,x,y,w,h)
    sp.fill.solid(); sp.fill.fore_color.rgb=fill; sp.line.color.rgb=LINEC; sp.line.width=Pt(1); sp.shadow.inherit=False
    tf=sp.text_frame; tf.word_wrap=True; tf.vertical_anchor=MSO_ANCHOR.MIDDLE
    tf.margin_left=Inches(0.12); tf.margin_right=Inches(0.12); tf.margin_top=Inches(0.06); tf.margin_bottom=Inches(0.06)
    p=tf.paragraphs[0]; p.alignment=PP_ALIGN.CENTER; p.space_after=Pt(2)
    r=p.add_run(); r.text=head; r.font.size=Pt(13); r.font.bold=True; r.font.name=FONT; r.font.color.rgb=headc
    if sub:
        p2=tf.add_paragraph(); p2.alignment=PP_ALIGN.CENTER; p2.line_spacing=1.0
        r2=p2.add_run(); r2.text=sub; r2.font.size=Pt(10.5); r2.font.name=FONT; r2.font.color.rgb=GRAYTX
    return sp

def arrow(s,x,y,w=Inches(0.32),h=Inches(0.32)):
    sp=s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW,x,y,w,h)
    sp.fill.solid(); sp.fill.fore_color.rgb=TEAL; sp.line.fill.background(); sp.shadow.inherit=False
    return sp

def table(s,x,y,w,headers,rows,cw,fs=12,hs=12,rh=Inches(0.5)):
    nr=len(rows)+1; t=s.shapes.add_table(nr,len(headers),x,y,w,rh*nr).table
    for i,cc in enumerate(cw): t.columns[i].width=cc
    for j,hh in enumerate(headers):
        c=t.cell(0,j); c.fill.solid(); c.fill.fore_color.rgb=NAVY; c.vertical_anchor=MSO_ANCHOR.MIDDLE
        c.margin_left=Inches(0.1); c.margin_top=Inches(0.03); c.margin_bottom=Inches(0.03)
        r=c.text_frame.paragraphs[0].add_run(); r.text=hh; r.font.size=Pt(hs); r.font.bold=True; r.font.color.rgb=WHITE; r.font.name=FONT
    for i,row in enumerate(rows):
        for j,v in enumerate(row):
            c=t.cell(i+1,j); c.fill.solid(); c.fill.fore_color.rgb=WHITE if i%2==0 else LIGHT; c.vertical_anchor=MSO_ANCHOR.MIDDLE
            c.margin_left=Inches(0.1); c.margin_top=Inches(0.03); c.margin_bottom=Inches(0.03)
            r=c.text_frame.paragraphs[0].add_run(); r.text=v; r.font.size=Pt(fs); r.font.name=FONT; r.font.color.rgb=GRAYTX
            if j==0: r.font.bold=True; r.font.color.rgb=NAVY
    return t

def notes(s,text):
    s.notes_slide.notes_text_frame.text=text

print("Building editable technical deck...")

# ---- 1 TITLE ----
s=add()
fillrect(s,0,0,Inches(0.28),SH,NAVY)
_txt(s,Inches(0.9),Inches(2.1),Inches(11.5),Inches(1.6),
     [[("Building an Enterprise LLMOps Framework",34,True,NAVY)]])
fillrect(s,Inches(0.94),Inches(3.05),Inches(2.0),Pt(3),TEAL)
_txt(s,Inches(0.92),Inches(3.35),Inches(11.2),Inches(1.2),
     [[("A reusable foundation for running large language model (LLM) applications in production.",17,False,GRAYTX)],
      [("LLMOps = Large Language Model Operations: the practices and tools to build, test, ship, and run LLM apps reliably.",13,False,MUTE,True)]],sa=10)
_txt(s,Inches(0.92),Inches(6.4),Inches(11),Inches(0.6),
     [[("Technical overview  ·  presenter working copy",12,True,NAVY)]])
notes(s,"Short intro. Today I'll cover four things: what LLMOps means, why we should build a reusable framework before any single project, how we'd build the base in about a month, and what it costs to keep running. I'll keep the jargon light and define terms as we go.")

# ---- 2 WHAT IS LLMOPS ----
s=add(); title(s,"What LLMOps means",2)
bullets(s,[
    ("LLM (Large Language Model): the AI model that reads and writes text — the kind of model behind chat assistants.",0),
    ("LLMOps (Large Language Model Operations): the way we build, test, release, and run apps that use these models — safely and the same way every time.",0),
    ("Think of it as DevOps for LLM apps. DevOps (Development + Operations) is the normal way software teams ship code. MLOps (Machine Learning Operations) does the same for data models. LLMOps adapts this for language models.",0),
    ("Why it needs its own approach: an LLM's answers are not fixed. Ask the same question twice and the wording can differ. So we have to test answer quality, watch for wrong answers, and keep an eye on cost for every request.",0),
],gap=13)
notes(s,"Keep this plain. One line: LLMOps is DevOps for apps built on language models. The twist is that outputs vary, so testing and monitoring look different from normal software. Don't go deep here; we'll expand later.")

# ---- 3 WHY FRAMEWORK FIRST ----
s=add(); title(s,"Why build a reusable framework first",3)
bullets(s,[
    ("Most teams jump straight to one project. Each time, they rebuild the same plumbing: connecting to the model, adding search over documents, logging, and safety checks.",0),
    ("That is slow, expensive, and hard to control. Many pilots never reach real production because the basics were built in a hurry.",0),
    ("Better approach: build the shared foundation once. Then each new project plugs into it instead of starting from zero.",0,True,NAVY),
    ("Payoff: new work starts in days instead of months, and security, testing, and monitoring are already there.",0),
],gap=14)
# simple contrast boxes
box(s,Inches(0.9),Inches(4.9),Inches(5.4),Inches(1.7),"Without a framework",
    "Every project rebuilds plumbing. Slow, costly, inconsistent, hard to govern.",fill=RGBColor(0xF7,0xEC,0xEC),headc=RGBColor(0xA3,0x3A,0x2F))
box(s,Inches(6.9),Inches(4.9),Inches(5.4),Inches(1.7),"With a framework",
    "Build once. Projects reuse it. Fast, consistent, safe, easier to control cost.",fill=RGBColor(0xE9,0xF3,0xF0),headc=TEAL)
notes(s,"This is the main argument of the whole deck. Analogy: build the road once, then any car can drive on it. We are not proposing a product yet — we are proposing the foundation that every future project uses.")

# ---- 4 WHAT'S IN THE FRAMEWORK ----
s=add(); title(s,"What the framework provides",4)
blocks=[("Model access","One secure gateway to the LLMs, with usage limits."),
        ("Orchestration","The logic that coordinates steps and tools (agents)."),
        ("Knowledge / RAG","RAG = Retrieval-Augmented Generation: answer from our own documents."),
        ("Guardrails","Automatic checks on inputs and outputs; hide personal data."),
        ("Evaluation","Automated tests that score answer quality before release."),
        ("Observability","Logs, traces, and dashboards to see what happened."),
        ("Security & access","Identity, permissions (RBAC), and secret management."),
        ("CI/CD & environments","A pipeline that tests and ships changes safely.")]
cols=4; bw=Inches(2.92); bh=Inches(1.7); gx=Inches(0.14); gy=Inches(0.2); x0=Inches(0.75); y0=Inches(1.65)
for i,(h,sub) in enumerate(blocks):
    r=i//cols; c=i%cols
    box(s,x0+c*(bw+gx),y0+r*(bh+gy),bw,bh,h,sub)
_txt(s,Inches(0.75),Inches(5.7),Inches(11.8),Inches(1.0),
     [[("Terms: RBAC = Role-Based Access Control (people get only the access their role needs). "
        "CI/CD = Continuous Integration / Continuous Delivery (an automated way to test and release changes). "
        "Personal data is often called PII = Personally Identifiable Information.",12,False,MUTE,True)]])
notes(s,"Walk across the eight boxes quickly. The point is these are shared services every project reuses. Don't read every word — highlight model gateway, RAG, guardrails, evaluation, and CI/CD. Mention the terms line at the bottom so people are not lost on acronyms.")

# ---- 5 LIFECYCLE ----
s=add(); title(s,"How an LLM app moves through the framework",5)
steps=["Prepare\ndata & prompts","Build\nprompts & agents","Test\n(evaluate)","Release\n(CI/CD)","Run & monitor"]
bw=Inches(2.15); bh=Inches(1.5); y=Inches(2.4); x=Inches(0.75); gap=Inches(0.28)
for i,st in enumerate(steps):
    head=st.split("\n")[0]; sub=st.split("\n")[1] if "\n" in st else ""
    box(s,x,y,bw,bh,head,sub)
    if i<len(steps)-1: arrow(s,x+bw+Inches(-0.02),y+bh/2-Inches(0.16))
    x+=bw+gap
_txt(s,Inches(0.75),Inches(4.4),Inches(11.8),Inches(1.6),
     [[("A change never ships straight to production. It is tested first, released through the pipeline, "
        "then watched in real use.",15,False,GRAYTX)],
      [("Feedback from real use flows back to the start — we improve prompts, data, and tests over time. "
        "This loop is the heart of LLMOps.",15,False,GRAYTX)]],sa=12)
notes(s,"Five simple steps, left to right, then it loops back. Emphasize two things: nothing ships without being tested, and real-world feedback comes back to improve the system. That loop is what makes it 'operations' and not just 'build'.")

# ---- 6 BUILD PLAN (1 MONTH) ----
s=add(); title(s,"Building the base framework — about one month",6)
table(s,Inches(0.75),Inches(1.65),Inches(11.85),
      ["Week","Focus","What we deliver"],
      [["Week 1","Set up & secure","Cloud project, access controls, the model gateway, secret storage, and basic logging."],
       ["Week 2","Core services","Document search (RAG), orchestration, and guardrails (safety and personal-data checks)."],
       ["Week 3","Quality & pipeline","Evaluation tests, the CI/CD pipeline, and separate dev, test, and production environments."],
       ["Week 4","Monitor & harden","Dashboards, cost tracking, a security review, documentation, and a small sample app to prove it works."]],
      cw=[Inches(1.3),Inches(2.6),Inches(7.95)],fs=13,rh=Inches(0.95))
_txt(s,Inches(0.75),Inches(5.9),Inches(11.85),Inches(1.0),
     [[("Honest scope: ",13,True,NAVY),("one month gives a solid, working base — not a finished product. "
       "It is enough to onboard the first real project safely, and we harden it further as we go.",13,False,GRAYTX)]])
notes(s,"Be honest about scope. One month gets a working foundation, not everything. Each week builds on the last. By the end we have a sample app running through the whole thing, which proves the base is real. Adjust weeks if the team is smaller.")

# ---- 7 ONBOARDING A USE CASE ----
s=add(); title(s,"Using the framework for a new project",7)
bullets(s,[
    ("Describe the need and agree what a good result looks like — the measures we will judge it by.",0),
    ("Pick the closest pattern and reuse the existing building blocks. Do not rebuild what we already have.",0),
    ("Connect the specific data and systems for this project.",0),
    ("Test the answers against real examples and adjust the prompts until quality passes.",0),
    ("Release through the same pipeline, start small, and watch it closely.",0),
    ("Improve using real feedback.",0),
],gap=12)
_txt(s,Inches(0.75),Inches(5.9),Inches(11.85),Inches(0.9),
     [[("Because the foundation already exists, most of this is configuration and testing — not new engineering. "
        "That is why later projects are much faster than the first.",14,False,GRAYTX,True)]])
notes(s,"This is the 'later part' the framework is built for. Notice most steps are configuration, not building. The framework did the hard, shared work once. Keep this generic — no specific project named.")

# ---- 8 SAFE & COMPLIANT ----
s=add(); title(s,"Keeping it safe and compliant",8)
bullets(s,[
    ("Treat everything going into and coming out of the model as untrusted, and check both.",0),
    ("Guardrails block unsafe content, hide personal data (PII), and keep the model on task.",0),
    ("Access control (RBAC) so people and systems only see what they should.",0),
    ("Keep data private: isolated networks, encryption, and clear rules on how long data is kept.",0),
    ("Human review for sensitive decisions — the AI assists, people decide.",0,True,NAVY),
    ("Keep an audit trail: a record of what the system did and why.",0),
],gap=12)
notes(s,"Security people will care about this slide. The one line to land: we treat all model input and output as untrusted and check both. And for anything sensitive, a human makes the final call.")

# ---- 9 QUALITY ----
s=add(); title(s,"Making sure the answers stay good",9)
bullets(s,[
    ("LLM answers vary, so we test them like any other software — with example questions and expected results.",0),
    ("We score for three things: is it correct, does it stay on topic, and does it answer from our data rather than making things up.",0),
    ("Every release is checked against a saved set of test questions, so quality does not slip over time.",0),
    ("In production we watch quality, speed, errors, and cost, and get alerts when something drifts.",0),
    ("Real problems get added back into the tests, so the system keeps getting better.",0),
],gap=13)
notes(s,"The key idea: we do not just hope the model is right — we measure it, and we block a release if quality drops. 'Answering from our data, not making things up' is the phrase to use for grounding.")

# ---- 10 RUNNING COSTS ----
s=add(); title(s,"What it costs to keep running",10)
_txt(s,Inches(0.75),Inches(1.5),Inches(11.85),Inches(0.4),
     [[("These are ongoing costs, not a one-time build. Most of them go up as the system is used more.",13,False,GRAYTX,True)]])
table(s,Inches(0.75),Inches(2.0),Inches(11.85),
      ["Cost area","What drives it","Rough size"],
      [["Model usage","Paid per token (a token is a few characters of text). More traffic means more cost.","Largest and variable"],
       ["Hosting / compute","Always-on servers running the services.","Medium, steady"],
       ["Search / vector database","Storage plus number of lookups (stores text as numbers to search by meaning).","Medium"],
       ["Monitoring & logs","How much log and trace data we keep.","Low to medium"],
       ["Evaluation","Running the test suites; grading sometimes uses the model itself.","Low to medium"],
       ["People","A small team to maintain and support it.","Usually the biggest overall"]],
      cw=[Inches(2.5),Inches(6.85),Inches(2.5)],fs=11.5,rh=Inches(0.6))
_txt(s,Inches(0.75),Inches(6.35),Inches(11.85),Inches(0.7),
     [[("Two big levers to control cost: ",13,True,NAVY),("use a smaller, cheaper model where a task allows it, "
       "and cache repeated answers so we do not pay twice. Both cut model-usage cost sharply.",13,False,GRAYTX)]])
notes(s,"They asked specifically about running costs, so slow down here. Two messages: costs are ongoing (not one-time), and the two biggest are model usage (variable, grows with traffic) and people (fixed). I will not give a dollar figure until we know expected volume, but I can once we do. Mention the two cost levers at the bottom.")

# ---- 11 TEAM ----
s=add(); title(s,"Who builds and runs it",11)
bullets(s,[
    ("Platform lead / architect — owns the design and the standards everyone follows.",0),
    ("Engineers — build the framework and the pipeline.",0),
    ("Data engineer — prepares and connects the data.",0),
    ("Security & governance — handles access, privacy, and compliance.",0),
    ("Support / operations — keeps it running and handles issues.",0),
],gap=13)
_txt(s,Inches(0.75),Inches(5.3),Inches(11.85),Inches(0.8),
     [[("A small, focused team can build the base in about a month, then support many projects on top of it.",14,False,GRAYTX,True)]])
notes(s,"Keep it short. The message: it does not take a large team. A small group builds the base, then supports many projects. Roles can be shared in a smaller org.")

# ---- 12 RISKS ----
s=add(); title(s,"Risks to watch",12)
bullets(s,[
    ("Wrong or made-up answers. Fix by grounding answers in our data and testing every release.",0),
    ("Cost surprises. Fix by setting usage limits, budgets, and alerts from day one.",0),
    ("Too much automation. Keep people in the loop for sensitive actions.",0),
    ("Getting locked to one vendor or model. Use the gateway so we can switch models later.",0),
    ("Security gaps. Treat all input and output as untrusted and give least access by default.",0),
],gap=13)
notes(s,"Show we have thought about what can go wrong and how we handle each one. The vendor lock-in point matters to leadership: the gateway means we are not stuck with one model provider.")

# ---- 13 HELPS CLIENTS ----
s=add(); title(s,"How this helps our clients",13)
bullets(s,[
    ("Once the framework exists, we can stand up new AI capabilities for clients quickly and safely.",0),
    ("Clients get faster delivery, consistent quality, and clear control over cost — without every project starting from scratch.",0),
    ("We can offer it as a managed capability: build it, run it, and improve it on their behalf.",0),
    ("The same foundation supports many clients and many needs, so our investment pays back across engagements.",0,True,NAVY),
],gap=14)
notes(s,"This is the business angle for leadership. We build the foundation once, then help client after client with it. That is faster, safer, and cheaper than building one-off solutions each time, and it becomes a service we can offer.")

# ---- 14 SUMMARY ----
s=add(); title(s,"Summary and next steps",14)
bullets(s,[
    ("LLMOps is how we run language-model apps reliably, not just build a demo.",0),
    ("Build the reusable framework first — about one month for a solid base.",0,True,NAVY),
    ("Then onboard projects quickly on top of it.",0),
    ("Plan for ongoing running costs — mainly model usage and people.",0),
    ("Next step: agree the scope for the one-month base build and set up the cloud environment.",0,True,NAVY),
],gap=14)
notes(s,"Recap the four points, then ask for the one decision I need: agreement on scope for the one-month base build, and access to set up the cloud environment. Keep it to a single clear ask.")

# ---- 15 GLOSSARY (appendix) ----
s=add(); title(s,"Terms in plain English (quick reference)",15)
gloss=[("LLM","Large Language Model — AI that reads and writes text."),
       ("LLMOps","Large Language Model Operations — building, testing, shipping, and running LLM apps."),
       ("RAG","Retrieval-Augmented Generation — the model answers using our own documents."),
       ("CI/CD","Continuous Integration / Continuous Delivery — automated testing and release."),
       ("RBAC","Role-Based Access Control — people get only the access their role needs."),
       ("PII","Personally Identifiable Information — personal data like names and phone numbers."),
       ("Token","The small unit of text a model reads and writes; billing is per token."),
       ("Prompt","The instruction we give the model."),
       ("Guardrails","Automatic safety checks on what goes in and comes out."),
       ("Vector database","Stores text as numbers so we can search by meaning."),
       ("Agent","An LLM that can use tools and take steps, not just chat."),
       ("DevOps / MLOps","The standard ways to ship software / machine-learning models.")]
colw=Inches(5.9); x0=Inches(0.75); y0=Inches(1.65); rowh=Inches(0.82)
for i,(term,defn) in enumerate(gloss):
    r=i//2; c=i%2; x=x0+c*(colw+Inches(0.2)); y=y0+r*rowh
    _txt(s,x,y,colw,rowh,[[(term+"  ",12.5,True,TEAL),(defn,12,False,GRAYTX)]],ls=1.0)
notes(s,"Appendix. Leave this up during questions if people want the acronyms. Skip it in the main flow if time is short.")

out=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"presentation","LLMOps-Framework-Technical.pptx")
prs.save(out)
print(f"Saved: {out}  ({len(prs.slides._sldIdLst)} slides)")
