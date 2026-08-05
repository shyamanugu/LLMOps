#!/usr/bin/env python3
"""v2 implementation deck: how we actually implement LLMOps (Azure + GitHub).
Follows the 3rdAug component flow, but each component shows the CONCRETE artifact
(repo tree, prompt YAML, models.yaml, eval gate, tool-selection harness, spans).
Fully editable (native shapes + real text, no images). Speaker notes. No timelines.
Requires: python-pptx.  Output: presentation/LLMOps-Implementation-v2.pptx
"""
import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR

NAVY=RGBColor(0x1F,0x3A,0x5F); BLUE=RGBColor(0x2F,0x5C,0x9E); TEAL=RGBColor(0x2A,0x9D,0x8F)
GRAYTX=RGBColor(0x3C,0x46,0x54); LIGHT=RGBColor(0xEE,0xF1,0xF5); MUTE=RGBColor(0x6B,0x74,0x80)
WHITE=RGBColor(0xFF,0xFF,0xFF); LINEC=RGBColor(0xC9,0xD2,0xDD); AMBER=RGBColor(0xC8,0x7B,0x1E)
SKY=RGBColor(0x3E,0x6F,0xB0); SLATE=RGBColor(0x51,0x6B,0x8A); DTEAL=RGBColor(0x2E,0x7D,0x7D)
PURP=RGBColor(0x6A,0x51,0x9E); GREEN=RGBColor(0x3E,0x8E,0x5A); ROSE=RGBColor(0xB0,0x4A,0x5A)
CODEBG=RGBColor(0x1E,0x28,0x36); CODEFG=RGBColor(0xDD,0xE4,0xEC); CODEKEY=RGBColor(0x7F,0xD0,0xC8)
FONT="Calibri"; MONO="Consolas"; SW,SH=Inches(13.333),Inches(7.5)
prs=Presentation(); prs.slide_width=SW; prs.slide_height=SH; BLANK=prs.slide_layouts[6]

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
def rrect(s,x,y,w,h,fill,line=LINEC,lw=1.0):
    sp=s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,x,y,w,h); sp.fill.solid(); sp.fill.fore_color.rgb=fill
    if line is None: sp.line.fill.background()
    else: sp.line.color.rgb=line; sp.line.width=Pt(lw)
    sp.shadow.inherit=False
    try: sp.adjustments[0]=0.06
    except Exception: pass
    return sp
def settext(sp,lines,anchor=MSO_ANCHOR.MIDDLE,align=PP_ALIGN.CENTER):
    tf=sp.text_frame; tf.word_wrap=True; tf.vertical_anchor=anchor
    tf.margin_left=Inches(0.08); tf.margin_right=Inches(0.08); tf.margin_top=Inches(0.03); tf.margin_bottom=Inches(0.03)
    for i,(t,sz,b,c) in enumerate(lines):
        p=tf.paragraphs[0] if i==0 else tf.add_paragraph()
        p.alignment=align; p.space_after=Pt(1); p.line_spacing=1.0
        r=p.add_run(); r.text=t; r.font.size=Pt(sz); r.font.bold=b; r.font.name=FONT; r.font.color.rgb=c
def box(s,x,y,w,h,head,sub=None,fill=LIGHT,headc=NAVY,hs=12.5,ss=10,subc=GRAYTX,align=PP_ALIGN.CENTER):
    sp=rrect(s,x,y,w,h,fill); lines=[(head,hs,True,headc)]
    if sub: lines.append((sub,ss,False,subc))
    settext(sp,lines,align=align); return sp
def arrow(s,x,y,w=Inches(0.34),h=Inches(0.3),color=TEAL,shape=MSO_SHAPE.RIGHT_ARROW):
    sp=s.shapes.add_shape(shape,x,y,w,h); sp.fill.solid(); sp.fill.fore_color.rgb=color; sp.line.fill.background(); sp.shadow.inherit=False; return sp
def connect(s,x1,y1,x2,y2,color=LINEC,w=1.4):
    ln=s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT,x1,y1,x2,y2); ln.line.color.rgb=color; ln.line.width=Pt(w); return ln
def title(s,text,num,kicker=None):
    if kicker: _txt(s,Inches(0.7),Inches(0.32),Inches(11.9),Inches(0.3),[[(kicker.upper(),11,True,TEAL)]])
    _txt(s,Inches(0.7),Inches(0.56),Inches(12.0),Inches(0.7),[[(text,23,True,NAVY)]])
    fillrect(s,Inches(0.72),Inches(1.16),Inches(1.5),Pt(3),TEAL)
    _txt(s,SW-Inches(1.1),SH-Inches(0.42),Inches(0.7),Inches(0.3),[[(str(num),10,False,MUTE)]],align=PP_ALIGN.RIGHT)
    _txt(s,Inches(0.7),SH-Inches(0.42),Inches(9),Inches(0.3),[[("LLMOps implementation (v2) — Azure + GitHub",9,False,MUTE)]])
def bullets(s,items,x=Inches(0.75),y=Inches(1.5),w=Inches(11.8),h=Inches(5.2),size=14.5,gap=8,color=GRAYTX):
    tf=s.shapes.add_textbox(x,y,w,h).text_frame; tf.word_wrap=True; tf.margin_left=0; tf.margin_top=0
    for i,it in enumerate(items):
        text=it[0]; lvl=it[1] if len(it)>1 else 0; bold=it[2] if len(it)>2 else False; col=it[3] if len(it)>3 else color
        p=tf.paragraphs[0] if i==0 else tf.add_paragraph()
        p.space_after=Pt(gap); p.space_before=Pt(0); p.line_spacing=1.05; p.level=lvl
        r=p.add_run(); r.text=("•  " if lvl==0 else "–  ")+text
        r.font.size=Pt(size-lvl); r.font.bold=bold; r.font.name=FONT; r.font.color.rgb=col
    return tf
def codepanel(s,x,y,w,h,lines,titlebar=None):
    if titlebar:
        tb=rrect(s,x,y,w,Inches(0.34),RGBColor(0x2C,0x3A,0x4C),line=None)
        _txt(s,x+Inches(0.15),y,w-Inches(0.3),Inches(0.34),[[(titlebar,10.5,True,CODEKEY)]],anchor=MSO_ANCHOR.MIDDLE)
        y=y+Inches(0.34); h=h-Inches(0.34)
    rrect(s,x,y,w,h,CODEBG,line=None)
    tf=s.shapes.add_textbox(x+Inches(0.15),y+Inches(0.1),w-Inches(0.3),h-Inches(0.2)).text_frame
    tf.word_wrap=True; tf.margin_left=0; tf.margin_top=0
    for i,ln in enumerate(lines):
        p=tf.paragraphs[0] if i==0 else tf.add_paragraph(); p.space_after=Pt(0); p.line_spacing=1.05
        r=p.add_run(); r.text=ln if ln else " "; r.font.name=MONO; r.font.size=Pt(9.5); r.font.color.rgb=CODEFG
def delta(s,y,today,ours,change,x=Inches(0.6),w=Inches(12.13),h=Inches(1.15)):
    cw=(w.inches-0.2*2)/3
    cols=[("TODAY",today,RGBColor(0xB0,0x4A,0x5A),RGBColor(0xFB,0xEE,0xEF)),
          ("OUR SETUP",ours,TEAL,RGBColor(0xEA,0xF5,0xF2)),
          ("WHAT CHANGES",change,NAVY,RGBColor(0xEC,0xF0,0xF7))]
    xx=x
    for lbl,txt,hc,bg in cols:
        rrect(s,xx,y,Inches(cw),h,bg,line=None)
        _txt(s,xx+Inches(0.15),y+Inches(0.1),Inches(cw-0.3),Inches(0.3),[[(lbl,10.5,True,hc)]])
        _txt(s,xx+Inches(0.15),y+Inches(0.42),Inches(cw-0.3),h-Inches(0.5),[[(txt,11,False,GRAYTX)]])
        xx=xx+Inches(cw+0.2)
def table(s,x,y,w,headers,rows,cw,fs=11,hs=11,rh=Inches(0.5)):
    nr=len(rows)+1; t=s.shapes.add_table(nr,len(headers),x,y,w,rh*nr).table
    for i,cc in enumerate(cw): t.columns[i].width=cc
    for j,hh in enumerate(headers):
        c=t.cell(0,j); c.fill.solid(); c.fill.fore_color.rgb=NAVY; c.vertical_anchor=MSO_ANCHOR.MIDDLE
        c.margin_left=Inches(0.08); c.margin_top=Inches(0.02); c.margin_bottom=Inches(0.02)
        r=c.text_frame.paragraphs[0].add_run(); r.text=hh; r.font.size=Pt(hs); r.font.bold=True; r.font.color.rgb=WHITE; r.font.name=FONT
    for i,row in enumerate(rows):
        for j,v in enumerate(row):
            c=t.cell(i+1,j); c.fill.solid(); c.fill.fore_color.rgb=WHITE if i%2==0 else LIGHT; c.vertical_anchor=MSO_ANCHOR.MIDDLE
            c.margin_left=Inches(0.08); c.margin_top=Inches(0.02); c.margin_bottom=Inches(0.02)
            r=c.text_frame.paragraphs[0].add_run(); r.text=v; r.font.size=Pt(fs); r.font.name=FONT; r.font.color.rgb=GRAYTX
            if j==0: r.font.bold=True; r.font.color.rgb=NAVY
    return t
def notes(s,t): s.notes_slide.notes_text_frame.text=t

print("Building v2 implementation deck...")

# 1 TITLE
s=add(); fillrect(s,0,0,Inches(0.28),SH,NAVY)
_txt(s,Inches(0.9),Inches(1.95),Inches(11.5),Inches(1.2),[[("LLMOps: how we implement it",30,True,NAVY)]])
fillrect(s,Inches(0.94),Inches(2.78),Inches(2.0),Pt(3),TEAL)
_txt(s,Inches(0.92),Inches(3.08),Inches(11.3),Inches(1.6),
     [[("Component by component — the actual setup on Azure + GitHub, and what changes from how we work today.",17,False,GRAYTX)],
      [("Version 2. Grounded in APIX and Hiring Intelligence; reusable for any use case. No timelines.",13,False,MUTE,True)]],sa=10)
_txt(s,Inches(0.92),Inches(6.35),Inches(11),Inches(0.5),[[("Working draft for review",12,True,NAVY)]])
notes(s,"This version answers the real question from last time: not 'what are the options' but 'how exactly do we implement each component, and how is it different from what we already do'. Every component slide has a Today / Our setup / What changes strip.")

# 2 HOW TO READ / ORDER
s=add(); title(s,"How to read this, and the order we build it",2,"Approach")
_txt(s,Inches(0.7),Inches(1.35),Inches(12),Inches(0.4),[[("Every component below is shown three ways:",13,True,NAVY)]])
delta(s,Inches(1.8),"how the team works now (assumption, to confirm)","the concrete setup we put in place","the specific difference — nothing generic",h=Inches(1.0))
_txt(s,Inches(0.7),Inches(3.1),Inches(12),Inches(0.4),[[("We onboard components one at a time. Source control + CI/CD comes first — it is the backbone the rest plug into.",13,True,NAVY,True)]])
order=[("1 Source control + CI/CD","the backbone"),("2 Prompt management","versioned + gated"),("3 Model management","config + gate"),
       ("4 Evaluation","the gate itself"),("5 Observability","trace everything"),("6 Guardrails","safety + PII"),
       ("7 Data / RAG","feed from our data"),("8 Serving / deploy","host + release"),("9 Feedback","improve")]
cw=Inches(3.9); ch=Inches(0.82); x0=Inches(0.7); y0=Inches(3.7)
for i,(h,sub) in enumerate(order):
    r=i//3; c=i%3; x=x0+c*(cw+Inches(0.16)); y=y0+r*(ch+Inches(0.16))
    box(s,x,y,cw,ch,h,sub,fill=LIGHT,hs=12,ss=9.5)
notes(s,"Explain the three-column strip once here; it repeats on every component slide. And the build order: CI/CD first, then onboard the rest one by one.")

# 3 REPO + CICD BACKBONE
s=add(); title(s,"Source control & CI/CD — the backbone (built first)",3,"Component 1")
codepanel(s,Inches(0.6),Inches(1.5),Inches(6.1),Inches(4.7),
    ["llmops-platform/","├─ prompts/apix/*.prompt.yaml   # one YAML per prompt","├─ agents/apix/pipeline.agent.yaml",
     "├─ evals/apix/golden.*.jsonl    # golden datasets","│  └─ tool_selection.py         # custom evaluator",
     "├─ src/","│  ├─ pipelines/apix/run.py","│  └─ common/  prompt_loader.py","│               model_router.py","│               tracing.py",
     "├─ models.yaml                  # task alias -> model","├─ .github/","│  ├─ CODEOWNERS  (/prompts, /agents)",
     "│  └─ workflows/","│     ├─ pr-checks.yml   # eval GATE on PR","│     ├─ eval-full.yml   # full golden run",
     "│     └─ deploy.yml      # OIDC, canary, rollback","├─ infra/   (Bicep)","└─ dashboards/"],titlebar="the monorepo")
_txt(s,Inches(6.9),Inches(1.5),Inches(5.8),Inches(0.5),[[("What makes it LLMOps (not just DevOps):",13,True,NAVY)]])
bullets(s,[("prompts, agents and golden datasets are versioned like code, reviewed by pull request.",0),
    ("every change runs an evaluation GATE before it can merge or deploy.",0),
    ("login to Azure uses GitHub OIDC (federated) — no stored cloud keys.",0),
    ("deploys are gated per environment, released gradually (canary), and auto-roll back.",0)],
    x=Inches(6.9),y=Inches(2.0),w=Inches(5.8),h=Inches(3.0),size=12.5,gap=9)
delta(s,Inches(5.15),"prompts/agents live inside code files; no eval before ship","monorepo + reviewed changes + an automated evaluation gate","a quality gate + structure, not just a repo",x=Inches(6.9),w=Inches(5.83),h=Inches(1.05))
notes(s,"CODEOWNERS = required reviewers on prompts/agents. OIDC = the pipeline signs in to Azure with a short-lived token, no stored secret. The point vs plain DevOps is the evaluation gate.")

# 4 CI/CD GATE FLOW
s=add(); title(s,"Every change flows through the evaluation gate",4,"Component 1")
steps=[("Pull request","edit prompt/agent"),("pr-checks.yml","unit + eval subset"),("Eval GATE","pass thresholds?"),
       ("Registry","versioned"),("Canary","small % of traffic"),("Prod / rollback","promote or revert")]
x=Inches(0.6); y=Inches(1.9); bw=Inches(1.95); bh=Inches(1.2); gap=Inches(0.15)
for i,(h,sub) in enumerate(steps):
    fill=RGBColor(0xF6,0xE9,0xE0) if i==2 else LIGHT; hc=AMBER if i==2 else NAVY
    box(s,x,y,bw,bh,h,sub,fill=fill,headc=hc,hs=12)
    if i<len(steps)-1: arrow(s,x+bw-Inches(0.02),y+bh/2-Inches(0.13),w=Inches(0.22))
    x=x+bw+gap
codepanel(s,Inches(0.6),Inches(3.5),Inches(12.13),Inches(2.5),
    ["# .github/workflows/pr-checks.yml  (abbreviated)",
     "on: { pull_request: { paths: [\"prompts/**\",\"agents/**\",\"src/**\",\"evals/**\"] } }",
     "permissions: { id-token: write }          # OIDC -> Azure, no stored keys",
     "steps:",
     "  - uses: azure/login@v2                    # federated login",
     "  - run: pytest tests/                      # unit / contract",
     "  - run: python evals/run.py --subset changed --fail-under baseline",
     "        #  runs Ragas + DeepEval + tool_selection; exits non-zero (blocks merge) if a metric drops"],
     titlebar="the gate, in the pipeline")
notes(s,"The amber box is the gate. This is the mechanism behind 'a prompt change must pass the golden dataset before it ships'. Show the real workflow: it fails the PR if a metric drops below baseline.")

# 5 PROMPT MGMT — THE DIFFERENTIATOR
s=add(); title(s,"Prompt management — what's actually different",5,"Component 2")
rrect(s,Inches(0.6),Inches(1.45),Inches(12.13),Inches(0.72),RGBColor(0xFB,0xEE,0xEF),line=None)
_txt(s,Inches(0.8),Inches(1.53),Inches(11.7),Inches(0.6),
     [[("The prompts are already in Git, inside the code files. So \"store prompts in Git\" is NOT the change. ",12.5,True,RGBColor(0xB0,0x4A,0x5A)),
       ("Three things are:",12.5,True,NAVY)]],anchor=MSO_ANCHOR.MIDDLE)
bullets(s,[("One YAML file PER prompt — id, version, template, variables, eval_refs, changelog. (We have no YAML-per-prompt today.)",0,True,NAVY),
    ("Every prompt change runs the pipeline and must PASS the golden-dataset thresholds (eval_refs) before it deploys.",0,True,NAVY),
    ("A registry that holds prompts so we can roll back / swap / compare versions on their evaluation scores.",0,True,NAVY)],
    x=Inches(0.75),y=Inches(2.4),w=Inches(6.0),h=Inches(2.6),size=12.5,gap=11)
codepanel(s,Inches(6.95),Inches(2.35),Inches(5.75),Inches(3.9),
    ["# prompts/apix/coaching-report.prompt.yaml","id: apix.coaching_report","version: 3","labels: [prod]",
     "model_alias: reason        # via models.yaml","temperature: 0.2","inputs: [agent_name, program, scores, evidence]",
     "template: |","  Using ONLY the evidence below, write a","  coaching note. Cite evidence. Do not invent.","eval_refs: [evals/apix/golden.telesales.jsonl]",
     "changelog:","  - v3: require evidence citation"],titlebar="one YAML per prompt")
notes(s,"This is THE slide from the feedback. Say it plainly: they already keep prompts in Git, so that is not new. The new things are the YAML-per-prompt artifact, the evaluation gate on every change, and the registry for rollback/compare. Kiran himself said 'we don't have a YAML file now — that's a good one.'")

# 6 PROMPT REGISTRY OPTIONS
s=add(); title(s,"Where prompts are held: the registry (start simple)",6,"Component 2")
table(s,Inches(0.6),Inches(1.5),Inches(12.13),
      ["Option","What it is","Recommendation"],
      [["Git + in-app cache","prompts stay in our repo; app caches them; no extra service","Start here — simplest"],
       ["Langfuse prompt management","open-source product (Lang family); we self-host it in our own network; also gives token/cost dashboards","Add as we scale"],
       ["Foundry prompt assets","native to the Azure AI platform; managed, more secure; cost to confirm","Option as we scale"]],
      cw=[Inches(2.6),Inches(6.6),Inches(2.93)],fs=11,rh=Inches(0.72))
codepanel(s,Inches(0.6),Inches(4.35),Inches(7.4),Inches(1.9),
    ["# src/common/prompt_loader.py","def load_prompt(prompt_id, label='prod'):","    p = registry.get(prompt_id, label=label)",
     "    return p.template, p.config['model_alias'], p.version","# the app asks for 'this prompt, prod label' — never hard-codes text"],
     titlebar="how the app loads a prompt")
_txt(s,Inches(8.2),Inches(4.4),Inches(4.5),Inches(1.9),
     [[("A registry just holds the prompts so we can fall back to a previous version if a new one fails the gate.",12,False,GRAYTX)],
      [("Cost: minor, to be confirmed for the Foundry / Langfuse options.",11.5,False,MUTE,True)]],sa=8)
notes(s,"Explain what a registry IS (Kiran asked). Recommendation is decisive: start with Git + in-app cache, add Langfuse or Foundry later. Langfuse is an open-source product we self-host in our own network; Foundry is Azure-native. I'll bring the cost numbers.")

# 7 MODEL MGMT
s=add(); title(s,"Model management — config-driven, gated",7,"Component 3")
_txt(s,Inches(0.6),Inches(1.4),Inches(12.13),Inches(0.4),
     [[("We likely already pick a bigger model for complex agents and a cheaper one for simple ones. What we add is structure:",12.5,False,GRAYTX,True)]])
codepanel(s,Inches(0.6),Inches(1.95),Inches(6.1),Inches(2.9),
    ["# models.yaml — the ONLY place a task maps to a model","environments:","  prod:","    aliases:","      reason: gpt-5.2","      bulk:   gpt-5-mini","      voice:  gpt-realtime-1.5","      embed:  text-embedding-3-large","",
     "# app code says resolve('reason') — never 'gpt-5.2'"],titlebar="models.yaml")
bullets(s,[("app code asks for a task alias (reason / bulk / voice); the deployment is resolved from config.",0),
    ("swapping a model = a config change, reviewed like code, that must pass the evaluation gate.",0),
    ("one shared config reused by every agent and use case under one hub (Azure AI Foundry).",0)],
    x=Inches(6.95),y=Inches(2.0),w=Inches(5.8),h=Inches(2.8),size=12.5,gap=10)
delta(s,Inches(5.05),"model names chosen in code, per agent","task-aliases in one config; swap via reviewed change","a shared, gated, config-driven choice",h=Inches(1.15))
notes(s,"Be honest: smaller delta here. They already choose models by complexity. What we add is the config-alias pattern, the eval gate on a swap, and reuse across use cases under one Foundry hub.")

# 8 EVALUATION — GOLDEN DATASET
s=add(); title(s,"Evaluation: the golden dataset is the gate",8,"Component 4")
bullets(s,[("A golden dataset is the ground-truth set of test cases for a use case — the first thing we build.",0),
    ("Same idea as normal ground truth, but in LLMOps it runs as a GATE at every change / pipeline run.",0,True,NAVY),
    ("Sources (three-step): SME-authored first -> real traffic over time -> reviewed again by SMEs & business.",0),
    ("Per use case AND per program (APIX: Telesales and WCC score differently). Start ~50-200 cases.",0)],
    x=Inches(0.7),y=Inches(1.5),w=Inches(6.0),h=Inches(3.2),size=13,gap=11)
codepanel(s,Inches(6.95),Inches(1.5),Inches(5.75),Inches(2.9),
    ["// evals/apix/golden.telesales.jsonl  (one line)","{","  \"id\": \"apix-telesales-014\",","  \"input\": {\"transcript_id\":\"c-88421\",",
     "            \"program\":\"telesales\"},","  \"grading\": {\"must_cite_evidence\": true,","    \"expected_score_band\": [70,85],","    \"must_flag\": [\"missed_upsell\"]},",
     "  \"meta\": {\"source\": \"sme_authored\"}","}"],titlebar="golden dataset record")
delta(s,Inches(4.85),"quality checked manually / by spot-checking a few calls","a versioned golden dataset run automatically on every change","evaluation becomes a release gate, not a manual look",h=Inches(1.15))
notes(s,"Kiran asked 'how is golden data different from normal ground truth?' — answer: it IS normal ground truth, but we run it as an automatic gate on every change. And it grows from real traffic, not just SME answers.")

# 9 EVALUATION — HOW / METRIC GROUPS
s=add(); title(s,"Evaluation: how we actually score it",9,"Component 4")
table(s,Inches(0.6),Inches(1.45),Inches(12.13),
      ["Metric group","Judges","How we score it (the mechanism)"],
      [["RAG / retrieval","backed by our data?","Ragas (groundedness, context relevance)"],
       ["Writing quality","how it reads","DeepEval / LLM-as-judge with a rubric"],
       ["Execution / task path","did it do the right thing","custom Python checks on the pipeline path"],
       ["Agent behavior","correct tool usage","custom Python (Ragas/DeepEval don't cover this)"],
       ["Safety / fairness","safe and unbiased?","Content Safety + custom checks"]],
      cw=[Inches(2.5),Inches(3.0),Inches(6.63)],fs=11,rh=Inches(0.56))
_txt(s,Inches(0.6),Inches(4.9),Inches(12.13),Inches(1.3),
     [[("Options, in one line: ",12.5,True,NAVY),
       ("Ragas and DeepEval (code frameworks) cover RAG and writing quality; agent behavior / tool usage needs custom "
        "Python; LangSmith does evaluation + observability too but is licensed (not open source). We use a mix, and the "
        "thresholds live in evaluators.yaml, enforced by the CI gate.",12.5,False,GRAYTX)]])
notes(s,"This answers 'it doesn't say HOW we evaluate'. Each metric group maps to a concrete mechanism. Say plainly: Ragas/DeepEval for RAG+writing; custom Python for tool selection and task path; LangSmith is an option but licensed.")

# 10 EVALUATION — TOOL SELECTION HARNESS
s=add(); title(s,"Evaluation: checking the agent picked the right tool",10,"Component 4")
_txt(s,Inches(0.6),Inches(1.4),Inches(12.13),Inches(0.4),
     [[("When an MCP tool server exposes several tools, a wrong tool that still answers is unreliable. We test it in code:",12.5,False,GRAYTX,True)]])
codepanel(s,Inches(0.6),Inches(1.95),Inches(7.6),Inches(3.5),
    ["# evals/tool_selection.py","def evaluate_tool_selection(cases, run_agent):","  for c in cases:            # input + expected_tool (+ args)",
     "    trace  = run_agent(c['input'])","    chosen = trace.tool_calls[0].name if trace.tool_calls else None",
     "    args_ok = compare_args(trace.tool_calls[0].args, c['expected_args'])","    record(correct = chosen == c['expected_tool'], args_ok = args_ok)",
     "  return dict(accuracy=..., wrong_tool_rate=...,","              missing_tool_rate=..., arg_correctness=...)"],titlebar="custom Python (not Ragas/DeepEval)")
bullets(s,[("we know the right tool for each test case",0),("run the agent; read the tool it chose from the trace",0),
    ("score: accuracy, per-tool precision/recall, wrong-tool, missing-tool, argument correctness",0),
    ("this is why observability records the tool call (see next section)",0,True,NAVY)],
    x=Inches(8.4),y=Inches(2.05),w=Inches(4.3),h=Inches(3.3),size=12,gap=10)
notes(s,"Kiran's MCP point. The harness reads the chosen tool from the trace and compares to the expected tool. Ragas/DeepEval don't do this — it's a small custom check. Note the link to observability: we can only score this because the tool call is traced.")

# 11 OBSERVABILITY — TRACE TREE (answers the 3 questions)
s=add(); title(s,"Observability: what gets tracked on every request",11,"Component 5")
spinex=Inches(1.0)
box(s,Inches(0.7),Inches(1.5),Inches(6.5),Inches(0.6),"Request (trace)","one call analysed / one candidate screened",fill=NAVY,headc=WHITE,hs=12,ss=9,subc=RGBColor(0xAE,0xC6,0xDE))
connect(s,spinex,Inches(2.1),spinex,Inches(4.95),color=LINEC,w=1.6)
connect(s,spinex,Inches(2.65),Inches(1.3),Inches(2.65),color=LINEC,w=1.6)
box(s,Inches(1.3),Inches(2.38),Inches(5.9),Inches(0.55),"Agent step (span)","dimension analysis / résumé rank",fill=BLUE,headc=WHITE,hs=11.5,ss=9,subc=RGBColor(0xCF,0xDC,0xF0))
connect(s,Inches(2.85),Inches(2.93),Inches(2.85),Inches(3.16),color=LINEC,w=1.4)
connect(s,Inches(5.55),Inches(2.93),Inches(5.55),Inches(3.16),color=LINEC,w=1.4)
box(s,Inches(1.55),Inches(3.16),Inches(2.6),Inches(0.5),"Model call (span)",None,fill=TEAL,headc=WHITE,hs=10.5)
box(s,Inches(4.3),Inches(3.16),Inches(2.6),Inches(0.5),"Tool call (span)",None,fill=DTEAL,headc=WHITE,hs=10.5)
connect(s,spinex,Inches(3.95),Inches(1.3),Inches(3.95),color=LINEC,w=1.6)
box(s,Inches(1.3),Inches(3.68),Inches(5.9),Inches(0.55),"Agent session","links multi-turn / the whole pipeline run",fill=SLATE,headc=WHITE,hs=11.5,ss=9,subc=RGBColor(0xD5,0xDD,0xE8))
connect(s,spinex,Inches(4.85),Inches(1.3),Inches(4.85),color=LINEC,w=1.6)
box(s,Inches(1.3),Inches(4.58),Inches(5.9),Inches(0.5),"Feedback event","thumbs / edit / override — same trace id",fill=LIGHT,hs=11.5,ss=9)
rrect(s,Inches(7.55),Inches(2.38),Inches(5.15),Inches(2.7),RGBColor(0xEA,0xF5,0xF2),line=RGBColor(0xBF,0xD6,0xD2))
_txt(s,Inches(7.75),Inches(2.5),Inches(4.8),Inches(0.35),[[("Answers the three questions directly:",12.5,True,TEAL)]])
bullets(s,[("model calls → tracked (model+version, prompt+version, tokens, cost, latency)",0),
    ("tool calls → tracked (tool, args, result, and was-it-the-correct-tool)",0),
    ("agent sessions → tracked (one trace id links every step and turn)",0)],
    x=Inches(7.75),y=Inches(3.0),w=Inches(4.75),h=Inches(2.0),size=11.5,gap=9)
notes(s,"Kiran's exact three questions: model calls, tool calls, agent sessions. Every box is a span with its own recorded fields, tied by one trace id. The 'was it the correct tool' field is what powers the tool-selection evaluation.")

# 12 OBSERVABILITY — CAPTURE + STACK
s=add(); title(s,"Observability: the fields, and the stack",12,"Component 5")
codepanel(s,Inches(0.6),Inches(1.5),Inches(6.5),Inches(3.4),
    ["# src/common/tracing.py  (model call span)","with tracer.start_as_current_span('gen_ai.chat') as sp:","  sp.set_attribute('gen_ai.request.model', deployment)",
     "  sp.set_attribute('app.prompt_id', prompt_id)","  sp.set_attribute('app.prompt_version', version)","  sp.set_attribute('gen_ai.usage.input_tokens', u.prompt_tokens)",
     "  sp.set_attribute('gen_ai.usage.output_tokens', u.completion_tokens)","  sp.set_attribute('app.cost_usd', cost(deployment, u))",
     "# tool span also sets: tool.name, tool.args,","#   eval.expected_tool, eval.was_correct_tool"],titlebar="OpenTelemetry spans")
_txt(s,Inches(7.35),Inches(1.5),Inches(5.4),Inches(0.4),[[("The stack:",13,True,NAVY)]])
bullets(s,[("OpenTelemetry (open standard) to instrument every call.",0),
    ("Azure Application Insights + Log Analytics = system of record (data stays in our tenant).",0),
    ("self-hosted Langfuse = the LLM-specific view: token/cost per model, prompt versions, per-trace scores.",0),
    ("traces link to cost (FinOps) and to evaluation scores.",0),
    ("personal data (PII) is hashed / redacted before it is stored.",0)],
    x=Inches(7.35),y=Inches(2.0),w=Inches(5.4),h=Inches(3.2),size=12,gap=9)
delta(s,Inches(5.15),"application logs only; no per-step model/tool detail","full trace tree via OpenTelemetry -> App Insights + Langfuse","step-level visibility + cost + quality per request",h=Inches(1.1))
notes(s,"Show the actual span code and the exact attributes. Two-layer stack: Azure-native for the record of truth, Langfuse for the LLM view. Note PII redaction in traces.")

# 13 GUARDRAILS
s=add(); title(s,"Guardrails & safety — where they sit",13,"Component 6")
flow=[("Input check","Content Safety on the prompt / transcript"),("Model call","the pipeline step"),("PII redaction","hide personal data"),("Output check","Content Safety on the answer"),("Return / store","or hand to a human")]
x=Inches(0.6); y=Inches(1.9); bw=Inches(2.3); bh=Inches(1.3); gap=Inches(0.13)
cols=[TEAL,NAVY,AMBER,TEAL,GREEN]
for i,((h,sub),c) in enumerate(zip(flow,cols)):
    box(s,x,y,bw,bh,h,sub,fill=LIGHT,hs=11.5,ss=9); fillrect(s,x,y,bw,Inches(0.08),c)
    if i<len(flow)-1: arrow(s,x+bw-Inches(0.01),y+bh/2-Inches(0.13),w=Inches(0.18))
    x=x+bw+gap
codepanel(s,Inches(0.6),Inches(3.5),Inches(8.2),Inches(1.7),
    ["safe_in  = content_safety.analyze_text(input_text)   # block/flag categories","answer   = call_model(...)","answer   = pii_redact(answer)                        # hide personal data",
     "safe_out = content_safety.analyze_text(answer)       # before returning/storing"],titlebar="guardrails in the pipeline")
_txt(s,Inches(9.0),Inches(3.55),Inches(3.7),Inches(1.7),
     [[("Human-in-the-loop for consequential outputs (APIX coaching, hiring decisions): the AI assists, a person decides.",12,False,GRAYTX,True)]])
delta(s,Inches(5.4),"minimal / ad-hoc checks","Content Safety + PII redaction on input and output","safety built into every step, not optional",h=Inches(0.95))
notes(s,"Guardrails wrap each step: check input, redact personal data, check output. Content Safety is the Azure service. For anything consequential, a human still decides.")

# 14 DATA / RAG
s=add(); title(s,"Data & RAG pipeline",14,"Component 7")
steps=[("Sources","transcripts, JDs, records"),("Ingest + clean","+ remove personal data"),("Chunk + embed","text-embedding-3-large"),("AI Search index","search by meaning"),("Retrieve","at answer time")]
x=Inches(0.6); y=Inches(2.0); bw=Inches(2.3); bh=Inches(1.35); gap=Inches(0.15)
for i,(h,sub) in enumerate(steps):
    box(s,x,y,bw,bh,h,sub,fill=LIGHT,hs=12,ss=9.5)
    if i<len(steps)-1: arrow(s,x+bw-Inches(0.01),y+bh/2-Inches(0.13),w=Inches(0.2))
    x=x+bw+gap
_txt(s,Inches(0.6),Inches(3.7),Inches(12),Inches(0.4),
     [[("Refresh: on a schedule or when a source changes (change-data-capture). Index aliases allow blue-green re-index.",12.5,False,GRAYTX,True)]])
delta(s,Inches(4.5),"ad-hoc / one-off ingestion","managed ingest -> chunk -> embed -> Azure AI Search, with refresh","a repeatable, refreshed pipeline",h=Inches(1.1))
notes(s,"RAG = Retrieval-Augmented Generation. The pipeline is standard but made repeatable and refreshed. Index aliases let us rebuild without downtime.")

# 15 SERVING / HOSTING
s=add(); title(s,"Serving, gateway & hosting on Azure",15,"Component 8")
box(s,Inches(0.7),Inches(1.8),Inches(2.7),Inches(1.1),"API Management","one entry point, quotas, metering",fill=LIGHT,hs=12,ss=9.5)
arrow(s,Inches(3.5),Inches(2.25))
box(s,Inches(4.0),Inches(1.8),Inches(3.0),Inches(1.1),"Container Apps","each pipeline step as a service; scale to zero",fill=RGBColor(0xEA,0xF5,0xF2),headc=TEAL,hs=12,ss=9.5)
box(s,Inches(7.3),Inches(1.8),Inches(2.6),Inches(1.1),"Functions","event triggers (new transcript)",fill=LIGHT,hs=12,ss=9.5)
box(s,Inches(10.1),Inches(1.8),Inches(2.6),Inches(1.1),"Foundry Agent Svc","hosted agents (later)",fill=LIGHT,hs=12,ss=9.5)
table(s,Inches(0.7),Inches(3.35),Inches(12.0),
      ["Environment","What runs","Gate to promote"],
      [["dev","latest merged build","auto"],
       ["test","release candidate","reviewer + eval-full passes"],
       ["prod","canary 10% -> 100%","reviewer + healthy + auto-rollback on alarm"]],
      cw=[Inches(2.0),Inches(5.5),Inches(4.5)],fs=11,rh=Inches(0.5))
delta(s,Inches(5.35),"deployed manually","Container Apps behind APIM; gated dev/test/prod; canary","automated, gated, reversible releases",h=Inches(1.0))
notes(s,"Recommend Container Apps for the pipeline steps, Functions for triggers, APIM as the gateway. Environments are gated; prod uses canary + auto-rollback.")

# 16 FEEDBACK LOOP
s=add(); title(s,"Feedback & improvement loop",16,"Component 9")
steps=["Capture\nfeedback","Land in\nApp Insights / Langfuse","Triage\nnegatives","Add to\ngolden dataset","Fix &\nre-evaluate","Ship"]
x=Inches(0.6); y=Inches(2.0); bw=Inches(1.9); bh=Inches(1.35); gap=Inches(0.14)
for i,st in enumerate(steps):
    head=st.split("\n")[0]; sub=st.split("\n")[1] if "\n" in st else ""
    box(s,x,y,bw,bh,head,sub,fill=LIGHT,hs=11.5,ss=9)
    if i<len(steps)-1: arrow(s,x+bw-Inches(0.01),y+bh/2-Inches(0.13),w=Inches(0.18))
    x=x+bw+gap
arrow(s,Inches(0.8),Inches(3.6),w=Inches(10.9),h=Inches(0.2),color=RGBColor(0xBF,0xD6,0xD2),shape=MSO_SHAPE.LEFT_ARROW)
bullets(s,[("captured: thumbs + reason, coach edits to a report, recruiter overrides — all tied to the trace id.",0),
    ("weak results become new golden-dataset cases, so the gate gets stricter where it matters.",0),
    ("fine-tuning only later, once prompts + retrieval plateau — on human-approved, PII-scrubbed examples.",0)],
    x=Inches(0.7),y=Inches(4.15),w=Inches(12),h=Inches(1.8),size=12.5,gap=10)
notes(s,"The loop that makes it an operation. Real feedback becomes golden-dataset cases, which raises the bar. Fine-tuning is a later step, not the starting point.")

# 17 AZURE HOSTING PLAN
s=add(); title(s,"The Azure hosting plan (services)",17,"Hosting")
table(s,Inches(0.6),Inches(1.45),Inches(12.13),
      ["Layer","Azure service","Purpose"],
      [["Models / AI","Azure OpenAI, Content Safety","the models; safety checks"],
       ["Knowledge / RAG","Azure AI Search","retrieval index"],
       ["Data / state","Cosmos DB / Azure SQL, Blob Storage","agent state, APIX scores, transcripts, datasets"],
       ["Gateway / compute","API Management, Container Apps, Functions","entry point; run the pipeline steps"],
       ["Observability","Azure Monitor, App Insights, self-hosted Langfuse","tracing, dashboards, LLM view"],
       ["Web app (APIX)","App Service / Static Web Apps","the dashboard front end"],
       ["Security / identity","Entra ID, Key Vault, Private Endpoints, Purview, Defender","identity, secrets, network, governance"],
       ["CI/CD","GitHub + GitHub Actions (OIDC)","test & release automatically"]],
      cw=[Inches(1.9),Inches(4.4),Inches(5.83)],fs=10.5,rh=Inches(0.5))
_txt(s,Inches(0.6),Inches(6.3),Inches(12.13),Inches(0.4),
     [[("Shared once vs per use case: ",12,True,NAVY),("everything above is shared; per use case we add only prompts, agents, tools, and golden datasets.",12,False,GRAYTX)]])
notes(s,"The hosting plan Kiran asked for. Everything here is the shared platform; a new use case only adds its own prompts, agents, tools and golden data. No timelines.")

# 18 END TO END
s=add(); title(s,"End to end: one picture",18,"Architecture")
box(s,Inches(0.5),Inches(1.7),Inches(2.6),Inches(2.2),"GitHub","prompts, agents,\nevals, infra as code\n+ Actions gate",fill=LIGHT,hs=13,ss=10)
_txt(s,Inches(0.5),Inches(4.0),Inches(2.6),Inches(0.4),[[("CI/CD gate",11,True,TEAL)]],align=PP_ALIGN.CENTER)
arrow(s,Inches(3.15),Inches(2.7))
box(s,Inches(3.6),Inches(1.7),Inches(3.1),Inches(2.2),"Azure runtime","APIM -> Container Apps:\norchestrator, agents,\nOpenAI, AI Search,\nContent Safety, Cosmos",fill=RGBColor(0xEA,0xF5,0xF2),headc=TEAL,hs=13,ss=9.5)
arrow(s,Inches(6.75),Inches(2.7))
box(s,Inches(7.2),Inches(1.7),Inches(2.5),Inches(2.2),"Telemetry","App Insights +\nLangfuse:\ntraces, cost,\neval scores",fill=LIGHT,hs=13,ss=9.5)
arrow(s,Inches(9.75),Inches(2.7))
box(s,Inches(10.2),Inches(1.7),Inches(2.5),Inches(2.2),"Fabric lakehouse","dashboards +\ntraining data",fill=LIGHT,hs=13,ss=9.5)
connect(s,Inches(11.45),Inches(3.9),Inches(11.45),Inches(4.35),color=RGBColor(0xBF,0xD6,0xD2),w=2)
connect(s,Inches(11.45),Inches(4.35),Inches(1.8),Inches(4.35),color=RGBColor(0xBF,0xD6,0xD2),w=2)
connect(s,Inches(1.8),Inches(4.35),Inches(1.8),Inches(3.9),color=RGBColor(0xBF,0xD6,0xD2),w=2)
_txt(s,Inches(2.0),Inches(4.15),Inches(9.4),Inches(0.3),[[("feedback + failures become new golden-dataset cases — the loop closes",11.5,True,TEAL,True)]],align=PP_ALIGN.CENTER)
_txt(s,Inches(0.6),Inches(4.8),Inches(12.1),Inches(1.4),
     [[("A change is gated by evaluation before it ships; a live request runs through the gateway and pipeline; every step "
        "is traced with cost and quality; feedback flows back into the golden datasets. That closed loop is the LLMOps setup.",13,False,GRAYTX)]])
notes(s,"The single-picture summary. Four flows: gated change, live request, telemetry, feedback loop. This is 'how we set up LLMOps here', end to end.")

# 19 CONSOLIDATED TODAY -> OURS
s=add(); title(s,"What changes, in one table",19,"Summary")
table(s,Inches(0.6),Inches(1.45),Inches(12.13),
      ["Component","Today (to confirm)","What we add"],
      [["Source control / CI-CD","repo, manual releases","evaluation gate on every change; gated, reversible deploys"],
       ["Prompt management","prompts inside code files","YAML per prompt + eval gate + registry for rollback/compare"],
       ["Model management","model names in code","task-aliases in config; swap must pass the gate"],
       ["Evaluation","manual spot-checks","golden datasets + Ragas/DeepEval/custom Python, run as a gate"],
       ["Observability","app logs","full trace tree: model calls, tool calls, agent sessions"],
       ["Guardrails","minimal","Content Safety + PII redaction on input and output"],
       ["Data / RAG","ad-hoc","managed, refreshed ingestion into Azure AI Search"],
       ["Serving / deploy","manual","Container Apps + APIM; canary + rollback"]],
      cw=[Inches(2.4),Inches(3.6),Inches(6.13)],fs=10.5,rh=Inches(0.52))
notes(s,"The one table Kiran wanted: for each component, what exists today and exactly what we add. This is the 'what do we have and what needs to change' answer.")

# 20 SUMMARY / NEXT
s=add(); title(s,"Summary and next step",20,"Wrap-up")
bullets(s,[("This is the implementation, component by component — the actual files, config, and gates on Azure + GitHub.",0,True,NAVY),
    ("For each component we showed what exists today and exactly what changes — prompt management is the clearest example.",0),
    ("CI/CD + the evaluation gate is the backbone; we onboard the other components one by one.",0),
    ("Observability tracks every request, model call, tool call, and agent session; evaluation runs as the gate.",0),
    ("Hosting is a shared Azure platform; a new use case only adds its prompts, agents, tools, and golden data.",0),
    ("Next: confirm the current state with the team, then set up the backbone and onboard the first component.",0,True,NAVY)],
    y=Inches(1.6),gap=12)
notes(s,"Recap. The ask is to align on this approach and start with the backbone. No dates — we agreed to leave timelines out for now.")

# 21 GLOSSARY
s=add(); title(s,"Terms in plain English",21,"Appendix")
gloss=[("LLMOps","running LLM apps reliably — versioned, tested, released, monitored"),
       ("Golden dataset","saved test cases with expected answers/rules; the evaluation gate"),
       ("Evaluation gate","an automatic check that blocks a change if quality drops"),
       ("Registry","where prompts are held so we can roll back / swap versions"),
       ("Ragas / DeepEval","open-source frameworks that score RAG & writing quality"),
       ("LangSmith","a licensed platform for evaluation + observability"),
       ("Langfuse","open-source, self-hosted prompt mgmt + observability"),
       ("OIDC","federated login to Azure with no stored keys"),
       ("Trace / span","a trace is one request; a span is one step inside it"),
       ("MCP","Model Context Protocol — the standard way to give agents tools"),
       ("RAG","Retrieval-Augmented Generation — answer from our own data"),
       ("Canary","release to a small % of traffic first, then all"),
       ("PII","Personally Identifiable Information — personal data to protect"),
       ("Container Apps / Functions","Azure ways to run our services / triggers"),
       ("Foundry","the Azure AI platform (model catalog, agents, prompt assets)"),
       ("APIX / WCC / Telesales","the use case and the two AFNI programs")]
colw=Inches(5.95); x0=Inches(0.6); y0=Inches(1.45); rowh=Inches(0.63)
for i,(term,defn) in enumerate(gloss):
    r=i//2; c=i%2; x=x0+c*(colw+Inches(0.25)); y=y0+r*rowh
    _txt(s,x,y,colw,rowh,[[(term+"  ",12,True,TEAL),(defn,10.5,False,GRAYTX)]],ls=1.0)
notes(s,"Appendix — leave up for questions.")

out=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"presentation","LLMOps-Implementation-v2.pptx")
prs.save(out)
print(f"Saved: {out}  ({len(prs.slides._sldIdLst)} slides)")
