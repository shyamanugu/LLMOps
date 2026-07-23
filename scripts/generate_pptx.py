#!/usr/bin/env python3
"""Generate the AFNI Enterprise GenAI Framework deck (tight, diagram-led, framework-first).
Requires: python-pptx, Pillow. Diagrams built beforehand by build_diagrams.py + rasterize.js.
Output: presentation/Afni-LLMOps-Proposal.pptx
"""
import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from PIL import Image

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); DIA=os.path.join(ROOT,"diagrams")
NAVY=RGBColor(0x12,0x1F,0x3D); INDIGO=RGBColor(0x1B,0x3A,0x6B); TEAL=RGBColor(0x00,0xA6,0xA6)
CYAN=RGBColor(0x2E,0xC4,0xD3); AMBER=RGBColor(0xF5,0xA6,0x23); LIGHT=RGBColor(0xF4,0xF6,0xFA)
GRAY=RGBColor(0x5A,0x64,0x74); WHITE=RGBColor(0xFF,0xFF,0xFF); DARK=RGBColor(0x1C,0x24,0x33)
GREEN=RGBColor(0x2E,0x9E,0x5B); RED=RGBColor(0xC0,0x39,0x2B)
SW,SH=Inches(13.333),Inches(7.5); FONT="Segoe UI"
prs=Presentation(); prs.slide_width=SW; prs.slide_height=SH; BLANK=prs.slide_layouts[6]

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
            r=p.add_run(); r.text=txt; r.font.size=Pt(sz); r.font.bold=b; r.font.italic=it; r.font.name=FONT; r.font.color.rgb=col
    return t
def bullets(s,x,y,w,h,items,size=15,color=DARK,gap=8,lh=1.08):
    t=s.shapes.add_textbox(x,y,w,h).text_frame; t.word_wrap=True; t.margin_left=0;t.margin_top=0
    for i,it in enumerate(items):
        text=it[0]; lvl=it[1] if len(it)>1 else 0; bold=it[2] if len(it)>2 else False; col=it[3] if len(it)>3 else color
        p=t.paragraphs[0] if i==0 else t.add_paragraph()
        p.space_after=Pt(gap); p.space_before=Pt(0); p.line_spacing=lh; p.level=lvl
        r=p.add_run(); r.text=("▸  " if lvl==0 else "–  ")+text
        r.font.size=Pt(size-lvl); r.font.bold=bold; r.font.name=FONT; r.font.color.rgb=col
    return t
PAGE=[0]
def pg(): PAGE[0]+=1; return PAGE[0]
def footer(s):
    rect(s,0,SH-Inches(0.32),SW,Inches(0.32),NAVY)
    tb(s,Inches(0.5),SH-Inches(0.33),Inches(9),Inches(0.3),[[("AFNI · Office of GenAI Architecture  ·  Enterprise GenAI Framework  ·  Confidential",9,False,RGBColor(0xC7,0xD0,0xE0))]],anchor=MSO_ANCHOR.MIDDLE)
    tb(s,SW-Inches(1.3),SH-Inches(0.33),Inches(0.8),Inches(0.3),[[(str(pg()),9,True,WHITE)]],align=PP_ALIGN.RIGHT,anchor=MSO_ANCHOR.MIDDLE)
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
    nr=len(rows)+1; t=s.shapes.add_table(nr,len(headers),x,y,w,rh*nr).table
    if cw:
        for i,c in enumerate(cw): t.columns[i].width=c
    for j,h in enumerate(headers):
        c=t.cell(0,j); c.fill.solid(); c.fill.fore_color.rgb=INDIGO; c.vertical_anchor=MSO_ANCHOR.MIDDLE
        c.margin_left=Inches(0.08);c.margin_top=Inches(0.02);c.margin_bottom=Inches(0.02)
        r=c.text_frame.paragraphs[0].add_run(); r.text=h; r.font.size=Pt(hs); r.font.bold=True; r.font.color.rgb=WHITE; r.font.name=FONT
    for i,row in enumerate(rows):
        for j,v in enumerate(row):
            c=t.cell(i+1,j); c.fill.solid(); c.fill.fore_color.rgb=WHITE if i%2==0 else LIGHT; c.vertical_anchor=MSO_ANCHOR.MIDDLE
            c.margin_left=Inches(0.08);c.margin_top=Inches(0.02);c.margin_bottom=Inches(0.02)
            r=c.text_frame.paragraphs[0].add_run(); r.text=str(v); r.font.size=Pt(fs); r.font.name=FONT; r.font.color.rgb=DARK
            if j==0: r.font.bold=True; r.font.color.rgb=NAVY
    return t
def diagram_slide(kicker,title,png,area_top=1.32,area_h=5.72,maxw=12.5):
    s=slide(); header(s,kicker,title); footer(s)
    im=Image.open(os.path.join(DIA,png)); iw,ih=im.size; ar=iw/ih
    w=maxw; h=w/ar
    if h>area_h: h=area_h; w=h*ar
    left=(13.333-w)/2; top=area_top+(area_h-h)/2
    s.shapes.add_picture(os.path.join(DIA,png),Inches(left),Inches(top),width=Inches(w)); return s

print("Building framework deck...")

# 1 TITLE
s=slide(); rect(s,0,0,SW,SH,NAVY); rect(s,0,0,Inches(0.22),SH,TEAL)
rect(s,Inches(0.9),Inches(2.05),Inches(1.7),Inches(0.11),AMBER)
tb(s,Inches(0.9),Inches(1.2),Inches(11),Inches(0.5),[[("ENTERPRISE PROPOSAL  ·  2026",14,True,CYAN)]])
tb(s,Inches(0.9),Inches(2.3),Inches(11.9),Inches(2.2),[[("Enterprise GenAI Framework for AFNI",40,True,WHITE)],[("Build the factory, not just the features",28,True,RGBColor(0x9F,0xB0,0xCC))]],ls=1.0,sa=4)
tb(s,Inches(0.92),Inches(4.5),Inches(11.5),Inches(0.7),[[("One governed, reusable platform to onboard any GenAI use case — proven first by Voice Agent, "
   "the Performance Intelligence Index, and Hiring Intelligence.",16,False,RGBColor(0xC7,0xD0,0xE0),True)]])
rect(s,Inches(0.9),Inches(5.7),Inches(11.5),Pt(1.2),INDIGO)
tb(s,Inches(0.9),Inches(5.9),Inches(11),Inches(1.0),[[("AFNI · Office of GenAI Architecture",13,True,WHITE)],[("Draft v3.0 · Internal & Confidential",11,False,RGBColor(0x9F,0xB0,0xCC))]],sa=3)

# 2 WHY NOW
s=slide(); header(s,"Why now","From AI features to an AI factory"); footer(s)
bullets(s,Inches(0.6),Inches(1.45),Inches(6.4),Inches(4.6),[
    ("Only ~1% of enterprises describe their GenAI as mature — most are stuck in pilot purgatory.",0,True,NAVY),
    ("AFNI's economics turn on high-volume voice and constant, high-volume hiring — both AI-addressable.",0),
    ("Frontier models now ship every few months (GPT-5.5 and beyond); point solutions are obsolete on arrival.",0),
    ("The winners build a reusable platform once and onboard use case after use case on top of it.",0,True,NAVY),
    ("GenAI is far more than chatbots — agents, document intelligence, analytics, real-time voice.",0),
],size=14,gap=13)
rect(s,Inches(7.4),Inches(1.45),Inches(5.3),Inches(4.6),LIGHT); rect(s,Inches(7.4),Inches(1.45),Inches(5.3),Inches(0.5),INDIGO)
tb(s,Inches(7.6),Inches(1.5),Inches(5),Inches(0.4),[[("THE SHIFT",12,True,WHITE)]],anchor=MSO_ANCHOR.MIDDLE)
for t_,d_,y in [("Feature → Platform","reusable paved road, not one-offs",2.15),
                ("Chatbot → Agent fleet","durable, tool-using, governed",3.05),
                ("Model pin → Frontier-ready","router + evals adopt new models",3.95),
                ("Pilot → Production","GenAIOps, security, evaluation gates",4.85)]:
    tb(s,Inches(7.6),Inches(y),Inches(4.9),Inches(0.35),[[(t_,13,True,TEAL)]])
    tb(s,Inches(7.6),Inches(y+0.3),Inches(4.9),Inches(0.4),[[(d_,11.5,False,GRAY)]])

# 3 FRAMEWORK HERO
diagram_slide("The framework","One reusable platform — onboard any GenAI use case","09-framework.png")
# 4 PATTERN CATALOG
diagram_slide("Beyond chatbots","GenAI pattern catalog","11-patterns.png")
# 5 ONBOARDING
diagram_slide("Paved road","Use-case onboarding in weeks, not quarters","10-onboarding.png")
# 6 PLATFORM ARCH
diagram_slide("Platform architecture","Layered reference architecture on Microsoft Foundry","01-platform-architecture.png")
# 7 AGENT RUNTIME
diagram_slide("Enterprise agent runtime","Durable, governed, interoperable orchestration","12-agent-runtime.png")
# 8 MODEL STRATEGY
diagram_slide("Model strategy","Ride the frontier without rewrites","16-model-strategy.png")

# 9 PROOF POINTS intro (three initiatives)
diagram_slide("Proof points","Three initiatives, onboarded via the framework","03-three-initiatives.png")
# 10-12 three use cases
diagram_slide("Proof point 1 · Voice Agent","Real-time voice automation & agent-assist","04-voice-flow.png",area_top=1.3,area_h=5.4)
diagram_slide("Proof point 2 · PI Index","100% of interactions → one explainable score","05-pi-index.png")
diagram_slide("Proof point 3 · Hiring Intelligence","An agent at every stage — humans decide","06-hiring-intelligence.png",area_top=1.3,area_h=5.2)

# 13 SECURITY
diagram_slide("Security by design","Zero Trust + OWASP LLM Top 10 defense-in-depth","13-security.png")
# 14 DATA
diagram_slide("Data at scale","Enterprise data platform feeding grounded AI","14-data-platform.png")
# 15 PERFORMANCE
diagram_slide("Performance & scale","Engineered for sub-second voice and bulk analytics","17-performance.png")
# 16 CI/CD
diagram_slide("GenAIOps CI/CD","Nothing ships without passing evaluation gates","15-genaiops-cicd.png")
# 17 EVALUATION
diagram_slide("Evaluation","Measured quality — offline, online, adversarial","18-evaluation.png")

# 18 DESIGN PRINCIPLES
s=slide(); header(s,"Design principles","The non-negotiables"); footer(s)
prin=[("Platform as a product","paved roads & self-service"),("Reuse over rebuild","composable building blocks"),
      ("Model-agnostic, frontier-ready","router + evals, no version lock-in"),("Evaluation-driven","nothing ships without passing evals"),
      ("Deterministic guardrails","wrap probabilistic agents"),("Zero Trust","treat all model I/O as untrusted"),
      ("Human-in-the-loop","graduated autonomy for risky actions"),("Observability & cost first-class","every trace, every token"),
      ("Privacy & security by default","secure/compliant templates"),("Fail safe","fallbacks & graceful degradation"),
      ("Everything-as-code","reproducible, versioned"),("Measure business outcomes","not model vanity metrics")]
for i,(t_,d_) in enumerate(prin):
    r=i//3; cc=i%3; x=0.6+cc*4.06; y=1.5+r*1.28
    rect(s,Inches(x),Inches(y),Inches(3.9),Inches(1.12),LIGHT); rect(s,Inches(x),Inches(y),Inches(0.1),Inches(1.12),TEAL if i%2==0 else AMBER)
    tb(s,Inches(x+0.22),Inches(y+0.12),Inches(3.6),Inches(0.4),[[(f"{i+1}. "+t_,13,True,NAVY)]])
    tb(s,Inches(x+0.22),Inches(y+0.52),Inches(3.6),Inches(0.5),[[(d_,11.5,False,GRAY)]])

# 19 GOVERNANCE (concise)
s=slide(); header(s,"Responsible AI & governance","Trust engineered in"); footer(s)
for t_,c,x in [("Fairness",TEAL,0.6),("Reliability & safety",CYAN,2.54),("Privacy & security",INDIGO,4.48),
               ("Inclusiveness",GREEN,6.42),("Transparency",AMBER,8.36),("Accountability",RGBColor(0x8E,0x44,0xAD),10.3)]:
    rect(s,Inches(x),Inches(1.45),Inches(1.86),Inches(0.85),c)
    tb(s,Inches(x),Inches(1.45),Inches(1.86),Inches(0.85),[[(t_,12,True,WHITE)]],align=PP_ALIGN.CENTER,anchor=MSO_ANCHOR.MIDDLE)
card(s,Inches(0.6),Inches(2.55),Inches(6.0),Inches(4.05),"Governance mechanisms",
     [("AI use-case intake with risk-tiering",0),("Human-in-the-loop for consequential decisions",0),
      ("Model & system cards per agent",0),("Content Safety + groundedness + PII redaction",0),
      ("Audit trails, red-teaming, AI incident response",0),("AI governance board with regular cadence",0)],accent=NAVY,bs=12.5)
card(s,Inches(6.75),Inches(2.55),Inches(6.0),Inches(4.05),"Risk tiering drives controls",
     [("High (hiring, collections, PI scoring): full HITL, bias audits, legal sign-off",0,True,RED),
      ("Medium (customer voice): guardrails + sampled QA + monitoring",0,True,AMBER),
      ("Low (internal drafting): standard guardrails + spot checks",0,True,GREEN),
      ("Aligned to EU AI Act, EEOC/NYC LL144, GDPR, HIPAA, PCI, TCPA, SOC 2",0,False,GRAY)],accent=AMBER,bs=12.5)

# 20 OPERATING MODEL + ROADMAP diagram
s=slide(); header(s,"Operating model","A GenAI Center of Excellence (all AFNI-internal)"); footer(s)
rect(s,Inches(4.55),Inches(1.42),Inches(4.2),Inches(0.8),NAVY)
tb(s,Inches(4.55),Inches(1.42),Inches(4.2),Inches(0.8),[[("GenAI Center of Excellence",13.5,True,WHITE)],[("platform · paved roads · standards · governance",9.5,False,CYAN)]],align=PP_ALIGN.CENTER,anchor=MSO_ANCHOR.MIDDLE,sa=2)
roles=[("Exec sponsor",TEAL),("AI product owner",CYAN),("GenAI architect (lead)",INDIGO),("Prompt / agent engineers",GREEN),
       ("GenAIOps engineers",RGBColor(0x3E,0x5C,0x99)),("Data engineers",GRAY),("RAI / governance",AMBER),("Security + FinOps",RGBColor(0x8E,0x44,0xAD))]
for i,(t_,c) in enumerate(roles):
    r=i//4; cc=i%4; x=0.6+cc*3.07; y=2.6+r*0.9
    rect(s,Inches(x),Inches(y),Inches(2.95),Inches(0.75),LIGHT); rect(s,Inches(x),Inches(y),Inches(0.1),Inches(0.75),c)
    tb(s,Inches(x+0.25),Inches(y),Inches(2.7),Inches(0.75),[[(t_,12,True,NAVY)]],anchor=MSO_ANCHOR.MIDDLE)
rect(s,Inches(0.6),Inches(4.55),Inches(12.15),Inches(1.9),INDIGO)
tb(s,Inches(0.85),Inches(4.72),Inches(11.7),Inches(1.6),[[("Federated hub-and-spoke: ",13.5,True,WHITE),
   ("the CoE (platform team) owns the paved road, guardrails and standards; Operations and HR 'spokes' own their use cases and "
   "outcomes. New use cases self-serve onto the platform and inherit security, evaluation and observability by default. "
   "A RACI governs every lifecycle activity.",13.5,False,RGBColor(0xD5,0xDE,0xEE))]],anchor=MSO_ANCHOR.MIDDLE)

# 21 ROADMAP
diagram_slide("Roadmap","Crawl → Walk → Run → Fly","08-roadmap.png")

# 22 BUSINESS CASE
s=slide(); header(s,"Business case","Value compounds across use cases (illustrative)"); footer(s)
table(s,Inches(0.6),Inches(1.5),Inches(12.1),["Value lever","Initiative / driver","Illustrative impact *"],
      [["Platform amortization","every new use case","each onboarding cheaper & faster"],
       ["100% QA coverage & coaching","PI Index","from ~5% sampled to 100%"],
       ["Call containment / AHT","Voice Agent","20–40% contained · 15–25% lower AHT"],
       ["Recruiter effort & time-to-fill","Hiring Intelligence","30–50% less screening effort"],
       ["Model cost efficiency","Model Router + caching","cheapest model meeting quality bar"],
       ["Attrition (matching + coaching)","Hiring + PI Index","lower 90-day attrition"]],
      cw=[Inches(4.0),Inches(3.3),Inches(4.8)],fs=12,rh=Inches(0.5))
rect(s,Inches(0.6),Inches(5.55),Inches(12.1),Inches(0.95),INDIGO)
tb(s,Inches(0.85),Inches(5.6),Inches(11.6),Inches(0.85),[[("Illustrative payback: 9–15 months, improving with every use case. ",14,True,WHITE),
   ("All figures are placeholders for AFNI actuals in Phase 0. Under Gainshare, efficiency improves shared margin directly.",13,False,RGBColor(0xD5,0xDE,0xEE),True)]],anchor=MSO_ANCHOR.MIDDLE)

# 23 CLOSE
s=slide(); rect(s,0,0,SW,SH,NAVY); rect(s,0,0,Inches(0.22),SH,TEAL)
tb(s,Inches(0.9),Inches(0.8),Inches(11),Inches(0.5),[[("RECOMMENDATION & NEXT STEPS",14,True,CYAN)]])
tb(s,Inches(0.9),Inches(1.35),Inches(11.5),Inches(0.9),[[("Approve Phase 0 — stand up the platform, prove it on three use cases",26,True,WHITE)]])
for n,t_ in [("1","Establish the Azure/Foundry landing zone, security baseline & guardrail policy"),
             ("2","Stand up the paved road: agents-as-code, evaluation gates, observability, FinOps"),
             ("3","Onboard the three proof points: Voice Agent copilot, PI Index MVP, Hiring screening"),
             ("4","Publish the use-case intake so the 4th, 5th and 6th use cases self-serve onto the platform")]:
    y=2.6+(int(n)-1)*0.82
    rect(s,Inches(0.9),Inches(y),Inches(0.6),Inches(0.6),AMBER)
    tb(s,Inches(0.9),Inches(y),Inches(0.6),Inches(0.6),[[(n,20,True,NAVY)]],align=PP_ALIGN.CENTER,anchor=MSO_ANCHOR.MIDDLE)
    tb(s,Inches(1.7),Inches(y),Inches(10.9),Inches(0.6),[[(t_,15,False,WHITE)]],anchor=MSO_ANCHOR.MIDDLE)
rect(s,Inches(0.9),Inches(6.15),Inches(11.5),Pt(1.2),INDIGO)
tb(s,Inches(0.9),Inches(6.35),Inches(11.5),Inches(0.8),[[("AFNI · Office of GenAI Architecture   |   Build the factory — then let it run.",14,True,WHITE)]])

out=os.path.join(ROOT,"presentation","Afni-LLMOps-Proposal.pptx"); prs.save(out)
print(f"Saved: {out}  ({len(prs.slides._sldIdLst)} slides)")
