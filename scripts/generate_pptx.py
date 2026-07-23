#!/usr/bin/env python3
"""Generate the AFNI Enterprise LLMOps proposal deck (diagram-led, AFNI-internal).

Requires: python-pptx, Pillow
Diagrams (PNG) are produced by build_diagrams.py + rasterize.js beforehand.
Output: presentation/Afni-LLMOps-Proposal.pptx
"""
import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIA = os.path.join(ROOT, "diagrams")

NAVY=RGBColor(0x12,0x1F,0x3D); INDIGO=RGBColor(0x1B,0x3A,0x6B); TEAL=RGBColor(0x00,0xA6,0xA6)
CYAN=RGBColor(0x2E,0xC4,0xD3); AMBER=RGBColor(0xF5,0xA6,0x23); LIGHT=RGBColor(0xF4,0xF6,0xFA)
GRAY=RGBColor(0x5A,0x64,0x74); WHITE=RGBColor(0xFF,0xFF,0xFF); DARK=RGBColor(0x1C,0x24,0x33)
GREEN=RGBColor(0x2E,0x9E,0x5B); RED=RGBColor(0xC0,0x39,0x2B)
SW,SH=Inches(13.333),Inches(7.5); FONT="Segoe UI"

prs=Presentation(); prs.slide_width=SW; prs.slide_height=SH
BLANK=prs.slide_layouts[6]

def rect(s,x,y,w,h,color,line=None,shape=MSO_SHAPE.RECTANGLE):
    sp=s.shapes.add_shape(shape,x,y,w,h); sp.fill.solid(); sp.fill.fore_color.rgb=color
    if line is None: sp.line.fill.background()
    else: sp.line.color.rgb=line; sp.line.width=Pt(1)
    sp.shadow.inherit=False; return sp

def tb(s,x,y,w,h,runs,align=PP_ALIGN.LEFT,anchor=MSO_ANCHOR.TOP,sa=6,ls=1.05):
    t=s.shapes.add_textbox(x,y,w,h).text_frame; t.word_wrap=True; t.vertical_anchor=anchor
    t.margin_left=0;t.margin_right=0;t.margin_top=0;t.margin_bottom=0
    for i,para in enumerate(runs):
        p=t.paragraphs[0] if i==0 else t.add_paragraph()
        p.alignment=align; p.space_after=Pt(sa); p.space_before=Pt(0); p.line_spacing=ls
        for (txt,sz,b,col,*rest) in para:
            it=rest[0] if rest else False
            r=p.add_run(); r.text=txt; r.font.size=Pt(sz); r.font.bold=b; r.font.italic=it
            r.font.name=FONT; r.font.color.rgb=col
    return t

def bullets(s,x,y,w,h,items,size=15,color=DARK,gap=8,lh=1.08):
    t=s.shapes.add_textbox(x,y,w,h).text_frame; t.word_wrap=True; t.margin_left=0;t.margin_top=0
    for i,it in enumerate(items):
        text=it[0]; lvl=it[1] if len(it)>1 else 0; bold=it[2] if len(it)>2 else False
        col=it[3] if len(it)>3 else color
        p=t.paragraphs[0] if i==0 else t.add_paragraph()
        p.space_after=Pt(gap); p.space_before=Pt(0); p.line_spacing=lh; p.level=lvl
        r=p.add_run(); r.text=("▸  " if lvl==0 else "–  ")+text
        r.font.size=Pt(size-lvl); r.font.bold=bold; r.font.name=FONT; r.font.color.rgb=col
    return t

PAGE=[0]
def pg(): PAGE[0]+=1; return PAGE[0]

def footer(s):
    rect(s,0,SH-Inches(0.32),SW,Inches(0.32),NAVY)
    tb(s,Inches(0.5),SH-Inches(0.33),Inches(9),Inches(0.3),
       [[("AFNI · Office of GenAI Architecture  ·  Enterprise LLMOps  ·  Confidential",9,False,RGBColor(0xC7,0xD0,0xE0))]],anchor=MSO_ANCHOR.MIDDLE)
    tb(s,SW-Inches(1.3),SH-Inches(0.33),Inches(0.8),Inches(0.3),
       [[(str(pg()),9,True,WHITE)]],align=PP_ALIGN.RIGHT,anchor=MSO_ANCHOR.MIDDLE)

def header(s,kicker,title):
    rect(s,0,0,SW,Inches(1.12),NAVY); rect(s,0,Inches(1.12),SW,Inches(0.055),TEAL)
    rect(s,Inches(0.5),Inches(0.26),Inches(0.12),Inches(0.6),AMBER)
    tb(s,Inches(0.8),Inches(0.2),Inches(11.8),Inches(0.32),[[(kicker.upper(),12,True,CYAN)]])
    tb(s,Inches(0.8),Inches(0.5),Inches(12),Inches(0.55),[[(title,25,True,WHITE)]])

def slide():
    s=prs.slides.add_slide(BLANK); rect(s,0,0,SW,SH,WHITE); return s

def card(s,x,y,w,h,title,items,accent=TEAL,ts=14,bs=12):
    rect(s,x,y,w,h,LIGHT); rect(s,x,y,w,Inches(0.09),accent)
    tb(s,x+Inches(0.18),y+Inches(0.15),w-Inches(0.36),Inches(0.5),[[(title,ts,True,NAVY)]])
    bullets(s,x+Inches(0.18),y+Inches(0.6),w-Inches(0.36),h-Inches(0.7),items,size=bs,gap=5)

def table(s,x,y,w,headers,rows,cw=None,fs=11,hs=11,rh=Inches(0.4)):
    nr=len(rows)+1; nc=len(headers)
    t=s.shapes.add_table(nr,nc,x,y,w,rh*nr).table
    if cw:
        for i,c in enumerate(cw): t.columns[i].width=c
    for j,h in enumerate(headers):
        c=t.cell(0,j); c.fill.solid(); c.fill.fore_color.rgb=INDIGO
        c.vertical_anchor=MSO_ANCHOR.MIDDLE; c.margin_left=Inches(0.08);c.margin_top=Inches(0.02);c.margin_bottom=Inches(0.02)
        r=c.text_frame.paragraphs[0].add_run(); r.text=h; r.font.size=Pt(hs); r.font.bold=True; r.font.color.rgb=WHITE; r.font.name=FONT
    for i,row in enumerate(rows):
        for j,v in enumerate(row):
            c=t.cell(i+1,j); c.fill.solid(); c.fill.fore_color.rgb=WHITE if i%2==0 else LIGHT
            c.vertical_anchor=MSO_ANCHOR.MIDDLE; c.margin_left=Inches(0.08);c.margin_top=Inches(0.02);c.margin_bottom=Inches(0.02)
            r=c.text_frame.paragraphs[0].add_run(); r.text=str(v); r.font.size=Pt(fs); r.font.name=FONT; r.font.color.rgb=DARK
            if j==0: r.font.bold=True; r.font.color.rgb=NAVY
    return t

def diagram_slide(kicker,title,png,area_top=1.32,area_h=5.72,maxw=12.5):
    s=slide(); header(s,kicker,title); footer(s)
    im=Image.open(os.path.join(DIA,png)); iw,ih=im.size; ar=iw/ih
    w=maxw; h=w/ar
    if h>area_h: h=area_h; w=h*ar
    left=(13.333-w)/2; top=area_top+(area_h-h)/2
    s.shapes.add_picture(os.path.join(DIA,png),Inches(left),Inches(top),width=Inches(w))
    return s

def divider(num,title,sub):
    s=slide(); rect(s,0,0,SW,SH,NAVY); rect(s,0,Inches(3.0),SW,Inches(1.5),INDIGO)
    rect(s,Inches(0.9),Inches(3.0),Inches(0.14),Inches(1.5),AMBER)
    tb(s,Inches(1.3),Inches(2.15),Inches(10),Inches(0.7),[[(num,60,True,RGBColor(0x2A,0x40,0x6E))]])
    tb(s,Inches(1.3),Inches(3.2),Inches(11),Inches(0.8),[[(title,34,True,WHITE)]],anchor=MSO_ANCHOR.MIDDLE)
    tb(s,Inches(1.32),Inches(4.6),Inches(10.5),Inches(0.6),[[(sub,15,False,CYAN,True)]])
    return s

print("Building diagram-led deck...")

# 1 TITLE
s=slide(); rect(s,0,0,SW,SH,NAVY); rect(s,0,0,Inches(0.22),SH,TEAL)
rect(s,Inches(0.9),Inches(2.05),Inches(1.7),Inches(0.11),AMBER)
tb(s,Inches(0.9),Inches(1.2),Inches(11),Inches(0.5),[[("ENTERPRISE PROPOSAL  ·  2026",14,True,CYAN)]])
tb(s,Inches(0.9),Inches(2.3),Inches(11.8),Inches(2.2),
   [[("Enterprise LLMOps for AFNI",44,True,WHITE)],[("Multi-agent GenAI, industrialized",30,True,RGBColor(0x9F,0xB0,0xCC))]],ls=1.0,sa=4)
tb(s,Inches(0.92),Inches(4.5),Inches(11.4),Inches(0.7),
   [[("One governed platform powering three flagship initiatives — Voice Agent, "
      "the Performance Intelligence Index, and Hiring Intelligence.",16,False,RGBColor(0xC7,0xD0,0xE0),True)]])
rect(s,Inches(0.9),Inches(5.7),Inches(11.5),Pt(1.2),INDIGO)
tb(s,Inches(0.9),Inches(5.9),Inches(11),Inches(1.0),
   [[("AFNI · Office of GenAI Architecture",13,True,WHITE)],
    [("Draft v2.0 · Internal & Confidential",11,False,RGBColor(0x9F,0xB0,0xCC))]],sa=3)

# 2 AGENDA
s=slide(); header(s,"Orientation","What this proposal covers"); footer(s)
card(s,Inches(0.6),Inches(1.45),Inches(6.0),Inches(5.4),"Strategy & platform",
     [("Why now — the BPO inflection point",0,True),("The three flagship initiatives",0,True),
      ("Platform reference architecture",0,True),("Multi-agent systems — one pattern",0,True),
      ("Voice Agent",0,True),("Performance Intelligence Index",0,True),("Hiring Intelligence",0,True)],accent=TEAL,bs=14)
card(s,Inches(6.75),Inches(1.45),Inches(6.0),Inches(5.4),"Operate & govern",
     [("LLMOps lifecycle & toolchain",0,True),("Responsible AI & governance",0,True),
      ("Security & compliance",0,True),("Observability & FinOps",0,True),
      ("Operating model & CoE",0,True),("Roadmap: Crawl → Walk → Run",0,True),
      ("Business case, risks & next steps",0,True)],accent=AMBER,bs=14)

# 3 CONTEXT
s=slide(); header(s,"Context","Why GenAI, why now — for AFNI"); footer(s)
bullets(s,Inches(0.6),Inches(1.45),Inches(6.5),Inches(4.5),[
    ("AFNI: global BPO & customer engagement, founded 1936; ~3,400+ staff across US, Mexico, the Philippines + AFNI@Home.",0),
    ("Service lines: Acquisition & Growth, Care & Retention, Collections, P&C Insurance (subrogation), Gainshare model.",0),
    ("Voice is the highest-volume, highest-cost channel; hiring at scale is constant.",0,True,NAVY),
    ("AI-native competitors are resetting client price and quality expectations.",0),
    ("Move first as an AI-enabled partner — or be repriced.",0,True,NAVY),
],size=14,gap=12)
rect(s,Inches(7.4),Inches(1.45),Inches(5.3),Inches(4.6),LIGHT); rect(s,Inches(7.4),Inches(1.45),Inches(5.3),Inches(0.5),INDIGO)
tb(s,Inches(7.6),Inches(1.5),Inches(5),Inches(0.4),[[("STRATEGIC PRESSURE ON BPOs",12,True,WHITE)]],anchor=MSO_ANCHOR.MIDDLE)
yy=2.15
for t_,d_ in [("Margin & labor cost","AI-native providers reset economics"),
              ("Attrition & ramp","Hiring & training never stop"),
              ("CX expectations","24/7, instant, consistent, compliant"),
              ("First-mover advantage","Become the AI partner of choice")]:
    tb(s,Inches(7.6),Inches(yy),Inches(4.9),Inches(0.35),[[(t_,13,True,TEAL)]])
    tb(s,Inches(7.6),Inches(yy+0.3),Inches(4.9),Inches(0.4),[[(d_,11.5,False,GRAY)]])
    yy+=0.95

# 4 VISION callout
s=slide(); header(s,"The vision","One platform, fleets of cooperating agents"); footer(s)
rect(s,Inches(0.6),Inches(1.5),Inches(12.1),Inches(1.5),INDIGO)
tb(s,Inches(1.0),Inches(1.65),Inches(11.4),Inches(1.2),
   [[("“Give AFNI one secure, governed platform to build, evaluate, deploy, govern and "
      "continuously improve fleets of cooperating AI agents — with the same operational rigor "
      "AFNI already applies to running contact centers.”",17,True,WHITE,True)]],anchor=MSO_ANCHOR.MIDDLE)
for (t_,d_,c),x in zip([("Platform-first","Build foundations once; every initiative reuses them",TEAL),
                        ("Multi-agent","Orchestrator + specialists — one pattern everywhere",CYAN),
                        ("Governed by design","Responsible AI, compliance & human-in-the-loop built in",AMBER),
                        ("Measurable","Quality, cost & business KPIs instrumented end to end",GREEN)],
                       [0.6,3.66,6.72,9.78]):
    card(s,Inches(x),Inches(3.3),Inches(2.92),Inches(3.4),t_,[(d_,0)],accent=c,bs=13)

# 5 SECTION strategy
divider("01","The Three Initiatives","Voice Agent · Performance Intelligence Index · Hiring Intelligence")
# 6 three initiatives diagram
diagram_slide("Strategy","Three flagship initiatives, one shared platform","03-three-initiatives.png")

# 7 SECTION platform
divider("02","The Platform","Enterprise LLMOps on Azure AI Foundry")
diagram_slide("Reference architecture","A layered platform every initiative is built on","01-platform-architecture.png")
diagram_slide("Multi-agent systems","One orchestrator, seven specialist agents","02-multi-agent.png")

# 8 SECTION voice
divider("03","Voice Agent","Real-time voice automation & agent-assist")
diagram_slide("Voice Agent","End-to-end real-time call flow","04-voice-flow.png",area_top=1.3,area_h=4.4)
# add KPI strip under voice flow on same style — new slide with KPIs
s=slide(); header(s,"Voice Agent","Modes & measurable outcomes"); footer(s)
for (t_,sub,items,c),x in zip([
    ("Agent-assist copilot","lowest risk, fastest value",["Live transcription & next-best-action","Compliance nudges","Auto summary & disposition"],TEAL),
    ("Autonomous voice agent","scoped, containable calls",["FAQs, verification, appointments","Payment reminders","Warm handoff when needed"],INDIGO),
    ("Post-call analytics","feeds the PI Index",["100% coverage, not sampled","Compliance & QA scoring","Coaching insight"],AMBER)],
    [0.6,4.98,9.36]):
    card(s,Inches(x),Inches(1.45),Inches(3.75),Inches(3.4),t_,[(sub,0,True,c)]+[(i,0) for i in items],accent=c,bs=12.5)
table(s,Inches(0.6),Inches(5.15),Inches(12.1),["KPI","Target *"],
      [["Containment / deflection","20–40% of eligible call types"],["Average Handle Time","15–25% reduction"],
       ["QA coverage","~5% sampled → 100%"],["Compliance adherence","monitored on every call"]],
      cw=[Inches(4.6),Inches(7.5)],fs=12,rh=Inches(0.36))
tb(s,Inches(0.6),Inches(6.85),Inches(12),Inches(0.3),[[("* Illustrative — replaced with AFNI actuals in discovery.",10,False,GRAY,True)]])

# 9 SECTION PI Index
divider("04","Performance Intelligence Index","100% of interactions → one explainable score")
diagram_slide("PI Index","From every interaction to a composite performance score","05-pi-index.png")

# 10 SECTION hiring
divider("05","Hiring Intelligence","Fair, high-volume recruitment — humans decide")
diagram_slide("Hiring Intelligence","An agent at every stage, fairness throughout","06-hiring-intelligence.png",area_top=1.3,area_h=5.0)

# 11 SECTION operate
divider("06","Operate & Govern","LLMOps, trust, security, cost & delivery")
diagram_slide("LLMOps lifecycle","How agents are built, evaluated, shipped & watched","07-llmops-lifecycle.png")

# 12 Responsible AI
s=slide(); header(s,"Responsible AI & governance","Trust engineered in, not bolted on"); footer(s)
for t_,c,x in [("Fairness",TEAL,0.6),("Reliability & safety",CYAN,2.54),("Privacy & security",INDIGO,4.48),
               ("Inclusiveness",GREEN,6.42),("Transparency",AMBER,8.36),("Accountability",RGBColor(0x8E,0x44,0xAD),10.3)]:
    rect(s,Inches(x),Inches(1.45),Inches(1.86),Inches(0.85),c)
    tb(s,Inches(x),Inches(1.45),Inches(1.86),Inches(0.85),[[(t_,12,True,WHITE)]],align=PP_ALIGN.CENTER,anchor=MSO_ANCHOR.MIDDLE)
card(s,Inches(0.6),Inches(2.55),Inches(6.0),Inches(4.05),"Governance mechanisms",
     [("AI use-case intake with risk-tiering (low / med / high)",0),("Human-in-the-loop for consequential decisions",0),
      ("Model & system cards per deployed agent",0),("Content Safety: prompt shields, groundedness, PII",0),
      ("Audit trails, AI incident response, red-teaming",0),("AI governance board with regular cadence",0)],accent=NAVY,bs=12.5)
card(s,Inches(6.75),Inches(2.55),Inches(6.0),Inches(4.05),"Risk tiering drives controls",
     [("High (hiring, collections): full HITL, bias audits, legal sign-off",0,True,RED),
      ("Medium (customer voice): guardrails + sampled QA + monitoring",0,True,AMBER),
      ("Low (internal drafting): standard guardrails + spot checks",0,True,GREEN),
      ("Controls scale with consequence — not one-size-fits-all.",0,False,GRAY)],accent=AMBER,bs=12.5)

# 13 Security & compliance
s=slide(); header(s,"Security & compliance","Enterprise-grade by construction"); footer(s)
bullets(s,Inches(0.6),Inches(1.5),Inches(5.7),Inches(4.8),[
    ("Entra ID · least-privilege RBAC · managed identities",0),("Key Vault secrets; none in code",0),
    ("VNet + private endpoints; no public data egress",0),("Encryption at rest & in transit",0),
    ("Data residency across US / Mexico / Philippines",0),("Defender for Cloud · Purview lineage & DLP",0),
    ("Prompt-injection & data-exfiltration defenses",0)],size=13.5,gap=11)
table(s,Inches(6.5),Inches(1.5),Inches(6.2),["Framework","Where it applies"],
      [["PCI-DSS","Payment capture — pause/mask"],["HIPAA","Healthcare client programs"],["TCPA","Outbound voice & consent"],
       ["SOC 2","Platform controls"],["GDPR","PII & data-subject rights"],["EEOC / NYC LL144","Hiring fairness & bias audit"]],
      cw=[Inches(2.3),Inches(3.9)],fs=12,rh=Inches(0.52))

# 14 Observability & FinOps
s=slide(); header(s,"Observability & FinOps","You can't scale what you can't see or cost"); footer(s)
card(s,Inches(0.6),Inches(1.5),Inches(6.0),Inches(5.15),"Observe every interaction",
     [("Quality & groundedness in production",0),("Latency p50/p95 vs sub-second voice SLOs",0),
      ("Errors, drift & safety events with alerting",0),("Token usage per request, agent & tool",0),
      ("OpenTelemetry GenAI tracing → App Insights",0),("Dashboards for ops, eng & governance",0)],accent=TEAL,bs=13)
card(s,Inches(6.75),Inches(1.5),Inches(6.0),Inches(5.15),"Control the spend (FinOps)",
     [("Token metering & quotas at the APIM gateway",0),("Cost showback per initiative & business unit",0),
      ("Model right-sizing: GPT-4o vs mini vs open-weight",0),("Semantic caching & prompt compression",0),
      ("Budget guardrails & anomaly alerts",0),("Cost-per-resolved-call / per-screen as KPIs",0)],accent=AMBER,bs=13)

# 15 Operating model
s=slide(); header(s,"Operating model","An AFNI GenAI Center of Excellence"); footer(s)
rect(s,Inches(4.55),Inches(1.45),Inches(4.2),Inches(0.85),NAVY)
tb(s,Inches(4.55),Inches(1.45),Inches(4.2),Inches(0.85),
   [[("GenAI Center of Excellence",14,True,WHITE)],[("platform · standards · governance",10,False,CYAN)]],
   align=PP_ALIGN.CENTER,anchor=MSO_ANCHOR.MIDDLE,sa=2)
roles=[("Exec sponsor",TEAL),("AI product owner",CYAN),("GenAI architect (lead)",INDIGO),("Prompt / agent engineers",GREEN),
       ("LLMOps engineers",RGBColor(0x3E,0x5C,0x99)),("Data engineers",GRAY),("RAI / governance officer",AMBER),("Security engineer",RGBColor(0x8E,0x44,0xAD))]
for i,(t_,c) in enumerate(roles):
    r=i//4; cc=i%4; x=0.6+cc*3.07; y=2.75+r*0.95
    rect(s,Inches(x),Inches(y),Inches(2.95),Inches(0.8),LIGHT); rect(s,Inches(x),Inches(y),Inches(0.1),Inches(0.8),c)
    tb(s,Inches(x+0.25),Inches(y),Inches(2.7),Inches(0.8),[[(t_,12.5,True,NAVY)]],anchor=MSO_ANCHOR.MIDDLE)
rect(s,Inches(0.6),Inches(4.9),Inches(12.15),Inches(1.55),INDIGO)
tb(s,Inches(0.85),Inches(5.05),Inches(11.7),Inches(1.3),
   [[("Federated hub-and-spoke: ",14,True,WHITE),
     ("the CoE owns the platform, guardrails and standards; Operations and HR 'spokes' own their "
      "initiatives and outcomes. SMEs from Ops, HR, Compliance and Security embed into delivery pods; "
      "a RACI governs every lifecycle activity. All roles are AFNI-internal.",14,False,RGBColor(0xD5,0xDE,0xEE))]],anchor=MSO_ANCHOR.MIDDLE)

# 16 Roadmap
diagram_slide("Roadmap","Crawl → Walk → Run over ~9–12 months","08-roadmap.png")

# 17 Business case
s=slide(); header(s,"Business case","Where the value comes from (illustrative)"); footer(s)
table(s,Inches(0.6),Inches(1.5),Inches(12.1),["Value lever","Initiative","Illustrative impact *"],
      [["100% QA coverage & faster coaching","PI Index","from ~5% sampled to 100%"],
       ["Call containment / deflection","Voice Agent","20–40% of eligible calls"],
       ["AHT reduction (agent-assist)","Voice Agent","15–25% shorter handle time"],
       ["Recruiter screening effort","Hiring Intelligence","30–50% fewer manual hours"],
       ["Time-to-fill & cost-per-hire","Hiring Intelligence","both materially reduced"],
       ["Attrition (better matching / coaching)","Hiring + PI Index","lower 90-day attrition"]],
      cw=[Inches(4.6),Inches(2.9),Inches(4.6)],fs=12,rh=Inches(0.5))
rect(s,Inches(0.6),Inches(5.55),Inches(12.1),Inches(0.95),INDIGO)
tb(s,Inches(0.85),Inches(5.6),Inches(11.6),Inches(0.85),
   [[("Illustrative payback: 9–15 months. ",14,True,WHITE),
     ("All figures are placeholders to be replaced with AFNI's actual volumes, rates and cost structure "
      "during Phase 0 discovery. Under Gainshare, efficiency improves shared margin directly.",13,False,RGBColor(0xD5,0xDE,0xEE),True)]],anchor=MSO_ANCHOR.MIDDLE)

# 18 Risks
s=slide(); header(s,"Risks & mitigations","Named early, managed deliberately"); footer(s)
table(s,Inches(0.6),Inches(1.5),Inches(12.1),["Risk","Mitigation"],
      [["Hallucination / wrong answers","RAG grounding, groundedness eval gates, HITL, guardrails"],
       ["Compliance breach (TCPA/PCI/EEOC)","Compliance agent, risk-tiering, bias audits, legal sign-off"],
       ["Unfair scoring (PI Index / hiring)","Fairness monitors, explainability, human calibration & appeals"],
       ["Runaway token cost","APIM metering, model right-sizing, caching, budget alerts"],
       ["Quality regression on change","Golden-set regression gates, canary + rollback"],
       ["Low adoption / change fatigue","Copilot-first, agent involvement, enablement, clear ROI"]],
      cw=[Inches(4.6),Inches(7.5)],fs=11.5,rh=Inches(0.62))

# 19 Close
s=slide(); rect(s,0,0,SW,SH,NAVY); rect(s,0,0,Inches(0.22),SH,TEAL)
tb(s,Inches(0.9),Inches(0.8),Inches(11),Inches(0.5),[[("RECOMMENDATION & NEXT STEPS",14,True,CYAN)]])
tb(s,Inches(0.9),Inches(1.35),Inches(11.5),Inches(0.9),[[("Approve a 4-week Phase 0 to lock foundations",30,True,WHITE)]])
for n,t_ in [("1","Confirm the three initiatives & success metrics with Ops and HR leaders"),
             ("2","Stand up the Azure landing zone, security baseline & guardrail policy"),
             ("3","Run use-case intake & risk-tiering; secure data access"),
             ("4","Launch Voice Agent copilot, PI Index MVP & Hiring screening pilots")]:
    y=2.6+(int(n)-1)*0.82
    rect(s,Inches(0.9),Inches(y),Inches(0.6),Inches(0.6),AMBER)
    tb(s,Inches(0.9),Inches(y),Inches(0.6),Inches(0.6),[[(n,20,True,NAVY)]],align=PP_ALIGN.CENTER,anchor=MSO_ANCHOR.MIDDLE)
    tb(s,Inches(1.7),Inches(y),Inches(10.8),Inches(0.6),[[(t_,15,False,WHITE)]],anchor=MSO_ANCHOR.MIDDLE)
rect(s,Inches(0.9),Inches(6.15),Inches(11.5),Pt(1.2),INDIGO)
tb(s,Inches(0.9),Inches(6.35),Inches(11.5),Inches(0.8),
   [[("AFNI · Office of GenAI Architecture   |   Thank you — questions & discussion welcome",14,True,WHITE)]])

out=os.path.join(ROOT,"presentation","Afni-LLMOps-Proposal.pptx")
prs.save(out)
print(f"Saved: {out}  ({len(prs.slides._sldIdLst)} slides)")
