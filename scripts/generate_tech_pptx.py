#!/usr/bin/env python3
"""Editable, diagram-led technical deck: enterprise LLMOps framework implemented on Azure.
Native shapes only (no images) so it stays editable in PowerPoint. Speaker notes included.
Requires: python-pptx.  Output: presentation/LLMOps-Framework-Technical.pptx
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
SKY=RGBColor(0x3E,0x6F,0xB0); SLATE=RGBColor(0x51,0x6B,0x8A)
FONT="Calibri"; SW,SH=Inches(13.333),Inches(7.5)

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
    try: sp.adjustments[0]=0.08
    except Exception: pass
    return sp
def settext(sp,lines,anchor=MSO_ANCHOR.MIDDLE):
    tf=sp.text_frame; tf.word_wrap=True; tf.vertical_anchor=anchor
    tf.margin_left=Inches(0.1); tf.margin_right=Inches(0.1); tf.margin_top=Inches(0.04); tf.margin_bottom=Inches(0.04)
    for i,(t,sz,b,c) in enumerate(lines):
        p=tf.paragraphs[0] if i==0 else tf.add_paragraph()
        p.alignment=PP_ALIGN.CENTER; p.space_after=Pt(1); p.line_spacing=1.0
        r=p.add_run(); r.text=t; r.font.size=Pt(sz); r.font.bold=b; r.font.name=FONT; r.font.color.rgb=c
def box(s,x,y,w,h,head,sub=None,fill=LIGHT,headc=NAVY,hs=12.5,ss=10,subc=GRAYTX):
    sp=rrect(s,x,y,w,h,fill); lines=[(head,hs,True,headc)]
    if sub: lines.append((sub,ss,False,subc))
    settext(sp,lines); return sp
def arrow(s,x,y,w=Inches(0.34),h=Inches(0.3),color=TEAL,shape=MSO_SHAPE.RIGHT_ARROW):
    sp=s.shapes.add_shape(shape,x,y,w,h); sp.fill.solid(); sp.fill.fore_color.rgb=color; sp.line.fill.background(); sp.shadow.inherit=False; return sp
def title(s,text,num,kicker=None):
    if kicker: _txt(s,Inches(0.7),Inches(0.34),Inches(11.9),Inches(0.3),[[(kicker.upper(),11,True,TEAL)]])
    _txt(s,Inches(0.7),Inches(0.58),Inches(11.9),Inches(0.7),[[(text,26,True,NAVY)]])
    fillrect(s,Inches(0.72),Inches(1.24),Inches(1.5),Pt(3),TEAL)
    _txt(s,SW-Inches(1.1),SH-Inches(0.46),Inches(0.7),Inches(0.3),[[(str(num),10,False,MUTE)]],align=PP_ALIGN.RIGHT)
    _txt(s,Inches(0.7),SH-Inches(0.46),Inches(9),Inches(0.3),[[("Enterprise LLMOps on Azure — technical overview",9,False,MUTE)]])
def bullets(s,items,x=Inches(0.75),y=Inches(1.55),w=Inches(11.8),h=Inches(5.2),size=16,gap=10,color=GRAYTX):
    tf=s.shapes.add_textbox(x,y,w,h).text_frame; tf.word_wrap=True; tf.margin_left=0; tf.margin_top=0
    for i,it in enumerate(items):
        text=it[0]; lvl=it[1] if len(it)>1 else 0; bold=it[2] if len(it)>2 else False; col=it[3] if len(it)>3 else color
        p=tf.paragraphs[0] if i==0 else tf.add_paragraph()
        p.space_after=Pt(gap); p.space_before=Pt(0); p.line_spacing=1.06; p.level=lvl
        r=p.add_run(); r.text=("•  " if lvl==0 else "–  ")+text
        r.font.size=Pt(size-lvl); r.font.bold=bold; r.font.name=FONT; r.font.color.rgb=col
    return tf
def band(s,y,label,services,lblcolor,h=0.62):
    x=Inches(0.6); w=Inches(12.13); hh=Inches(h)
    rrect(s,x,y,w,hh,LIGHT)
    lab=rrect(s,x,y,Inches(3.0),hh,lblcolor,line=None); settext(lab,[(label,12.5,True,WHITE)])
    _txt(s,x+Inches(3.2),y,w-Inches(3.4),hh,[[(services,11,False,GRAYTX)]],anchor=MSO_ANCHOR.MIDDLE)
def table(s,x,y,w,headers,rows,cw,fs=11.5,hs=11.5,rh=Inches(0.5)):
    nr=len(rows)+1; t=s.shapes.add_table(nr,len(headers),x,y,w,rh*nr).table
    for i,cc in enumerate(cw): t.columns[i].width=cc
    for j,hh in enumerate(headers):
        c=t.cell(0,j); c.fill.solid(); c.fill.fore_color.rgb=NAVY; c.vertical_anchor=MSO_ANCHOR.MIDDLE
        c.margin_left=Inches(0.1); c.margin_top=Inches(0.02); c.margin_bottom=Inches(0.02)
        r=c.text_frame.paragraphs[0].add_run(); r.text=hh; r.font.size=Pt(hs); r.font.bold=True; r.font.color.rgb=WHITE; r.font.name=FONT
    for i,row in enumerate(rows):
        for j,v in enumerate(row):
            c=t.cell(i+1,j); c.fill.solid(); c.fill.fore_color.rgb=WHITE if i%2==0 else LIGHT; c.vertical_anchor=MSO_ANCHOR.MIDDLE
            c.margin_left=Inches(0.1); c.margin_top=Inches(0.02); c.margin_bottom=Inches(0.02)
            r=c.text_frame.paragraphs[0].add_run(); r.text=v; r.font.size=Pt(fs); r.font.name=FONT; r.font.color.rgb=GRAYTX
            if j==0: r.font.bold=True; r.font.color.rgb=NAVY
    return t
def notes(s,text): s.notes_slide.notes_text_frame.text=text

print("Building Azure LLMOps technical deck...")

# ---- 1 TITLE ----
s=add()
fillrect(s,0,0,Inches(0.28),SH,NAVY)
_txt(s,Inches(0.9),Inches(1.9),Inches(11.5),Inches(1.4),[[("Enterprise LLMOps Framework on Azure",32,True,NAVY)]])
fillrect(s,Inches(0.94),Inches(2.8),Inches(2.0),Pt(3),TEAL)
_txt(s,Inches(0.92),Inches(3.1),Inches(11.3),Inches(1.4),
     [[("A reusable foundation for building, testing, shipping, and running large language model (LLM) applications — built on Microsoft Azure.",17,False,GRAYTX)],
      [("LLMOps = Large Language Model Operations: the practices and tools that keep LLM apps reliable, safe, and affordable in production.",13,False,MUTE,True)]],sa=10)
_txt(s,Inches(0.92),Inches(6.35),Inches(11),Inches(0.5),[[("Technical overview  ·  presenter working copy",12,True,NAVY)]])
notes(s,"Set expectations: this is the technical view of the framework and, importantly, how we implement each part on Azure. I'll show the architecture, each component with its Azure service, how we build the base in about a month, and what it costs to run.")

# ---- 2 WHAT LLMOPS IS ----
s=add(); title(s,"What LLMOps means",2,"Basics")
bullets(s,[
    ("LLM (Large Language Model): the AI model that reads and writes text, like the model behind a chat assistant.",0),
    ("LLMOps (Large Language Model Operations): the way we build, test, release, and run LLM apps safely and the same way every time.",0),
    ("It is DevOps for LLM apps. DevOps (Development + Operations) is the normal way teams ship software; LLMOps adapts it for language models.",0),
    ("The difference: an LLM's answers are not fixed. So we must test answer quality, watch for wrong answers, and control the cost of every request.",0),
],y=Inches(1.55),gap=12)
# small visual: DevOps + models = LLMOps
by=Inches(4.7); bw=Inches(3.3); bh=Inches(1.4)
box(s,Inches(0.9),by,bw,bh,"DevOps","Test & ship software safely",fill=LIGHT)
box(s,Inches(4.9),by,bw,bh,"+ Language models","Answers vary; cost per use",fill=LIGHT)
arrow(s,Inches(4.28),by+bh/2-Inches(0.15),color=TEAL,shape=MSO_SHAPE.MATH_PLUS,w=Inches(0.3),h=Inches(0.3))
arrow(s,Inches(8.28),by+bh/2-Inches(0.15))
box(s,Inches(8.9),by,bw,bh,"= LLMOps","Reliable LLM apps in production",fill=RGBColor(0xE9,0xF3,0xF0),headc=TEAL)
notes(s,"Keep it plain. One line: LLMOps is DevOps for language-model apps, with extra care because answers vary and each call costs money.")

# ---- 3 FRAMEWORK ARCHITECTURE (hero, layered, native) ----
s=add(); title(s,"The framework, as layers",3,"Architecture")
y=1.5
band(s,Inches(y),"Apps & channels","Web app, chat, voice, and internal tools where people ask questions",SLATE,h=0.6); y+=0.68
band(s,Inches(y),"API gateway","Azure API Management — one secure entry point, usage limits, keys, logging",SKY,h=0.6); y+=0.68
band(s,Inches(y),"Orchestration & agents","Azure AI Foundry Agent Service · Semantic Kernel — coordinate steps, tools, and models",BLUE,h=0.6); y+=0.68
band(s,Inches(y),"Models","Azure OpenAI (GPT models) · Model Router · text embeddings",NAVY,h=0.6); y+=0.68
band(s,Inches(y),"Knowledge / RAG","Azure AI Search · Azure AI Document Intelligence — answer from our own documents",TEAL,h=0.6); y+=0.68
band(s,Inches(y),"Data","Microsoft Fabric / OneLake · Azure Cosmos DB · Blob Storage",RGBColor(0x2E,0x7D,0x7D),h=0.6); y+=0.72
# cross-cutting band
cc=rrect(s,Inches(0.6),Inches(y),Inches(12.13),Inches(0.62),RGBColor(0x22,0x2E,0x3E),line=None)
_txt(s,Inches(0.78),Inches(y),Inches(11.8),Inches(0.62),
     [[("Across everything:  ",11.5,True,RGBColor(0x8F,0xD3,0xCC)),
       ("Security & governance (Entra ID · Key Vault · Content Safety · Purview · Defender for Cloud)   ·   "
        "Observability (Azure Monitor · Application Insights)   ·   CI/CD (Azure DevOps / GitHub Actions)",11,False,WHITE)]],anchor=MSO_ANCHOR.MIDDLE)
notes(s,"This is the map for the whole talk. Read top to bottom: a request comes from an app, goes through the gateway, the orchestration layer decides what to do, calls the model and the knowledge search, which sit on our data. Security, monitoring and CI/CD apply across all of it. Every box names the Azure service that provides it.")

# ---- 4 COMPONENTS -> AZURE SERVICES ----
s=add(); title(s,"Each component and the Azure service that runs it",4,"Azure mapping")
table(s,Inches(0.6),Inches(1.5),Inches(12.13),
      ["Component","Azure service","What it does"],
      [["Model access & gateway","Azure API Management + Azure OpenAI","One secure door to the models, with limits and logging"],
       ["Orchestration / agents","Azure AI Foundry Agent Service, Semantic Kernel","Coordinates steps, tools, and models"],
       ["Knowledge / RAG","Azure AI Search + AI Document Intelligence","Finds and feeds in our own documents"],
       ["Guardrails / safety","Azure AI Content Safety","Blocks unsafe content, helps hide personal data"],
       ["Evaluation","Azure AI Foundry evaluations","Scores answer quality before release"],
       ["Observability","Azure Monitor + Application Insights","Logs, traces, dashboards, and alerts"],
       ["Security & access","Entra ID, Key Vault, Private Endpoints, Purview","Identity, secrets, private network, data governance"],
       ["CI/CD & environments","Azure DevOps / GitHub Actions","Tests and ships changes across dev, test, production"]],
      cw=[Inches(2.9),Inches(4.3),Inches(4.93)],fs=11,rh=Inches(0.6))
notes(s,"This is the 'how in Azure' slide people will screenshot. Left is the capability, middle is the exact Azure service, right is a plain-English one-liner. RAG = Retrieval-Augmented Generation: the model answers using our documents.")

# ---- 5 RAG ON AZURE ----
s=add(); title(s,"Knowledge / RAG on Azure",5,"Component deep-dive")
_txt(s,Inches(0.75),Inches(1.4),Inches(11.8),Inches(0.5),
     [[("RAG (Retrieval-Augmented Generation): before answering, we search our own documents and give the model the relevant pieces, so it answers from our data instead of guessing.",13,False,GRAYTX,True)]])
steps=[("Documents","policies, PDFs, records"),("Document Intelligence","read & split text"),
       ("Embeddings + AI Search","store as searchable index"),("Retrieve","find relevant pieces"),
       ("Model answers","grounded, with sources")]
x=Inches(0.7); y=Inches(2.6); bw=Inches(2.15); bh=Inches(1.4); gap=Inches(0.28)
cols=[SLATE,TEAL,BLUE,SKY,NAVY]
for i,((h,sub),c) in enumerate(zip(steps,cols)):
    sp=box(s,x,y,bw,bh,h,sub,fill=LIGHT);
    if i<len(steps)-1: arrow(s,x+bw-Inches(0.01),y+bh/2-Inches(0.15))
    x+=bw+gap
_txt(s,Inches(0.75),Inches(4.5),Inches(11.8),Inches(1.6),
     [[("Azure services: ",13,True,NAVY),("Azure AI Document Intelligence reads and splits files; Azure OpenAI creates embeddings "
       "(text turned into numbers); Azure AI Search stores them and finds matches by meaning; the model then answers using only those matches.",13,False,GRAYTX)],
      [("Why it matters: this is how we keep answers accurate and traceable to a source, instead of the model making things up.",13,False,GRAYTX,True)]],sa=10)
notes(s,"Walk the five boxes left to right. The key message: RAG is how we ground answers in our own data and show sources. Name the Azure services as you go. 'Embeddings' just means text stored as numbers so we can search by meaning.")

# ---- 6 ORCHESTRATION ON AZURE ----
s=add(); title(s,"Orchestration & agents on Azure",6,"Component deep-dive")
_txt(s,Inches(0.75),Inches(1.4),Inches(11.8),Inches(0.5),
     [[("The orchestrator is the logic that decides the steps: understand the request, fetch knowledge, call tools, and produce an answer. An 'agent' is an LLM that can take steps and use tools, not just chat.",13,False,GRAYTX,True)]])
# orchestrator center with children
ox=Inches(5.35); oy=Inches(2.5)
box(s,ox,oy,Inches(2.6),Inches(0.95),"Orchestrator","Azure AI Foundry Agent Service",fill=NAVY,headc=WHITE,ss=10,subc=RGBColor(0xAE,0xC6,0xDE))
children=[("Understand request","route the task",Inches(0.7)),("Knowledge / RAG","get documents",Inches(3.9)),
          ("Tools / systems","APIs, databases",Inches(7.1)),("Model","write the answer",Inches(10.3))]
cy=Inches(4.35)
for h,sub,cx in children:
    box(s,cx,cy,Inches(2.6),Inches(0.95),h,sub,fill=LIGHT)
    arrow(s,ox+Inches(1.2),oy+Inches(0.95),w=Inches(0.28),h=Inches(0.9),color=LINEC,shape=MSO_SHAPE.DOWN_ARROW) if False else None
    # connector line
    ln=s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, cx+Inches(1.3), cy, ox+Inches(1.3), oy+Inches(0.95))
    ln.line.color.rgb=LINEC; ln.line.width=Pt(1.5)
_txt(s,Inches(0.75),Inches(5.6),Inches(11.8),Inches(1.1),
     [[("On Azure: ",13,True,NAVY),("the Agent Service hosts the orchestrator and keeps its state; Semantic Kernel is the toolkit used to build it. "
       "Long jobs can pause and resume, and every step is logged for review.",13,False,GRAYTX)],
      [("Guardrails wrap each step, and a person can approve anything sensitive before it happens.",13,False,GRAYTX,True)]],sa=8)
notes(s,"Explain the orchestrator as the 'brain' that coordinates. It calls knowledge, tools, and the model. On Azure this is the Foundry Agent Service, built with Semantic Kernel. Mention that steps are logged and sensitive actions need human approval.")

# ---- 7 GUARDRAILS & SECURITY LAYERS ----
s=add(); title(s,"Keeping it safe — layers of defense",7,"Security")
layers=[("Identity & network","Entra ID sign-in, private network, no public exposure"),
        ("Gateway limits","Azure API Management — keys, rate limits, quotas"),
        ("Input checks","Azure AI Content Safety — block unsafe or malicious prompts"),
        ("Least access","tools and data limited to only what is needed; human approval for sensitive actions"),
        ("Output checks","filter unsafe content, hide personal data (PII) before it leaves"),
        ("Monitor & respond","Microsoft Defender for Cloud, alerts, and an audit trail")]
y=Inches(1.55); h=Inches(0.72)
for i,(h_,sub) in enumerate(layers):
    sp=rrect(s,Inches(2.2),y,Inches(9.0),h-Inches(0.08),LIGHT)
    _txt(s,Inches(2.45),y,Inches(2.9),h-Inches(0.08),[[(h_,13,True,NAVY)]],anchor=MSO_ANCHOR.MIDDLE)
    _txt(s,Inches(5.5),y,Inches(5.5),h-Inches(0.08),[[(sub,11.5,False,GRAYTX)]],anchor=MSO_ANCHOR.MIDDLE)
    fillrect(s,Inches(1.9),y,Inches(0.14),h-Inches(0.08),TEAL)
    y+=h
_txt(s,Inches(1.9),y+Inches(0.02),Inches(9.3),Inches(0.5),
     [[("Rule of thumb: treat everything going in and coming out of the model as untrusted, and check both.",12.5,True,NAVY,True)]])
notes(s,"Security folks care most here. Walk down the layers from outside in. The one line to land: we treat all model input and output as untrusted and check both. PII = Personally Identifiable Information, i.e. personal data.")

# ---- 8 EVALUATION & OBSERVABILITY ----
s=add(); title(s,"Making sure answers stay good, and watching them run",8,"Quality & monitoring")
box(s,Inches(0.7),Inches(1.6),Inches(5.9),Inches(4.6),"Evaluation (before release)",None,fill=LIGHT)
bullets(s,[
    ("Test answers with example questions and expected results.",0),
    ("Score for: correct, on-topic, and answered from our data.",0),
    ("Every release is checked against a saved test set, so quality does not slip.",0),
    ("Azure: Azure AI Foundry evaluations run these checks in the pipeline.",0,True,NAVY),
],x=Inches(0.95),y=Inches(2.15),w=Inches(5.45),h=Inches(4.0),size=13.5,gap=12)
box(s,Inches(6.9),Inches(1.6),Inches(5.83),Inches(4.6),"Observability (in production)",None,fill=LIGHT)
bullets(s,[
    ("Watch quality, speed, errors, and cost of every request.",0),
    ("Traces show each step the system took, for troubleshooting.",0),
    ("Alerts fire when something drifts or breaks.",0),
    ("Azure: Azure Monitor + Application Insights, using OpenTelemetry (an open standard for traces).",0,True,NAVY),
],x=Inches(7.15),y=Inches(2.15),w=Inches(5.4),h=Inches(4.0),size=13.5,gap=12)
notes(s,"Two halves: test before release, and watch in production. The message: we do not hope the model is right, we measure it, and we block a release if quality drops. Then in production we watch speed, errors and cost, not just quality.")

# ---- 9 CI/CD PIPELINE ON AZURE ----
s=add(); title(s,"How changes are tested and shipped (CI/CD)",9,"Delivery")
_txt(s,Inches(0.75),Inches(1.35),Inches(11.8),Inches(0.5),
     [[("CI/CD = Continuous Integration / Continuous Delivery: an automated pipeline that tests every change and releases it safely.",13,False,GRAYTX,True)]])
steps=[("Change","edit prompt/agent"),("Build","package"),("Test gates","quality · safety · cost"),
       ("Release","start small (canary)"),("Production","watch & improve")]
x=Inches(0.7); y=Inches(2.5); bw=Inches(2.15); bh=Inches(1.3); gap=Inches(0.28)
for i,(h,sub) in enumerate(steps):
    fill=RGBColor(0xF6,0xE9,0xE0) if i==2 else LIGHT
    hc=AMBER if i==2 else NAVY
    box(s,x,y,bw,bh,h,sub,fill=fill,headc=hc)
    if i<len(steps)-1: arrow(s,x+bw-Inches(0.01),y+bh/2-Inches(0.15))
    x+=bw+gap
# gates callout
_txt(s,Inches(0.7),Inches(4.15),Inches(11.9),Inches(0.4),[[("The test gates block a release if it fails any of:",13,True,AMBER)]])
g=[("Quality","answers still correct & on-topic"),("Groundedness","answers from our data, with sources"),
   ("Safety","no unsafe content; red-team checks"),("Cost & speed","within budget and time limits")]
gx=Inches(0.7)
for h,sub in g:
    box(s,gx,Inches(4.6),Inches(2.92),Inches(1.0),h,sub,fill=LIGHT); gx+=Inches(3.05)
_txt(s,Inches(0.75),Inches(5.85),Inches(11.8),Inches(0.6),
     [[("Azure: ",13,True,NAVY),("Azure DevOps or GitHub Actions runs the pipeline; releases go out gradually and roll back automatically if a problem shows up.",13,False,GRAYTX)]])
notes(s,"The heart of LLMOps. Nothing ships without passing the gates. Point at the amber 'test gates' box, then the four gates below. On Azure this runs in Azure DevOps or GitHub Actions, with gradual release and automatic rollback.")

# ---- 10 LIFECYCLE LOOP ----
s=add(); title(s,"The LLMOps lifecycle",10,"How it all flows")
steps=["Prepare\ndata & prompts","Build","Test\n(evaluate)","Release\n(CI/CD)","Run & monitor","Improve"]
x=Inches(0.75); y=Inches(2.4); bw=Inches(1.85); bh=Inches(1.35); gap=Inches(0.14)
for i,st in enumerate(steps):
    head=st.split("\n")[0]; sub=st.split("\n")[1] if "\n" in st else ""
    box(s,x,y,bw,bh,head,sub,fill=LIGHT)
    if i<len(steps)-1: arrow(s,x+bw-Inches(0.02),y+bh/2-Inches(0.15),w=Inches(0.24))
    x+=bw+gap
# loop-back arrow
lb=arrow(s,Inches(0.9),Inches(4.15),w=Inches(10.8),h=Inches(0.22),color=RGBColor(0xBF,0xD6,0xD2),shape=MSO_SHAPE.LEFT_ARROW)
_txt(s,Inches(0.9),Inches(4.5),Inches(11.6),Inches(1.4),
     [[("The loop matters most: ",14,True,NAVY),("real use produces feedback — wrong answers, new questions, cost data — which flows back to improve prompts, data, and tests.",14,False,GRAYTX)],
      [("This is what turns a one-time build into an operation that keeps getting better.",14,False,GRAYTX,True)]],sa=10)
notes(s,"Simple left-to-right, then it loops back. Emphasize the loop: feedback from real use improves the system. That loop is why it's 'Ops' and not just 'build once'.")

# ---- 11 BUILD PLAN (1 MONTH, AZURE) ----
s=add(); title(s,"Building the base framework on Azure — about one month",11,"Plan")
table(s,Inches(0.6),Inches(1.5),Inches(12.13),
      ["Week","Focus","What we set up on Azure"],
      [["Week 1","Set up & secure","Azure subscription & resource groups, Entra ID access, Key Vault, private network, API Management gateway, Azure OpenAI, basic logging."],
       ["Week 2","Core services","Azure AI Search (RAG), Foundry Agent Service orchestration, Content Safety guardrails."],
       ["Week 3","Quality & pipeline","Azure AI Foundry evaluations, Azure DevOps/GitHub CI/CD pipeline, separate dev / test / production."],
       ["Week 4","Monitor & harden","Azure Monitor + App Insights dashboards, cost tracking, security review, docs, and a small sample app to prove it works."]],
      cw=[Inches(1.2),Inches(2.5),Inches(8.43)],fs=12,rh=Inches(0.98))
_txt(s,Inches(0.6),Inches(5.95),Inches(12.13),Inches(0.9),
     [[("Honest scope: ",13,True,NAVY),("one month gives a working, reusable base on Azure — not a finished product. "
       "It is enough to onboard the first real project safely, and we harden it further over time.",13,False,GRAYTX)]])
notes(s,"Concrete Azure build plan. Each week names the Azure services stood up. Be honest: one month is a solid base, not everything. By week 4 a sample app runs end to end, proving the base works. Adjust if the team is small.")

# ---- 12 ONBOARDING A USE CASE ----
s=add(); title(s,"Using the framework for a new project",12,"Onboarding")
steps=[("Define need","and success measures"),("Pick pattern","reuse building blocks"),
       ("Connect data","specific to the project"),("Test quality","fix prompts until it passes"),
       ("Release small","watch closely"),("Improve","from real feedback")]
x=Inches(0.7); y=Inches(2.3); bw=Inches(1.85); bh=Inches(1.35); gap=Inches(0.14)
for i,(h,sub) in enumerate(steps):
    box(s,x,y,bw,bh,h,sub,fill=LIGHT)
    if i<len(steps)-1: arrow(s,x+bw-Inches(0.02),y+bh/2-Inches(0.15),w=Inches(0.24))
    x+=bw+gap
_txt(s,Inches(0.7),Inches(4.35),Inches(11.9),Inches(1.5),
     [[("Because the base already exists, most of this is configuration and testing — not new engineering.",15,True,NAVY)],
      [("That is why the first project takes the longest, and every one after it is faster and cheaper.",14,False,GRAYTX,True)]],sa=10)
notes(s,"This is what the framework is for. Notice most steps are configuration, not building. The framework did the shared, hard work once. Keep it generic; no specific project named.")

# ---- 13 RUNNING COSTS ----
s=add(); title(s,"What it costs to keep running on Azure",13,"Running cost")
_txt(s,Inches(0.6),Inches(1.42),Inches(12.13),Inches(0.4),
     [[("These are ongoing costs, not a one-time build. Most go up as the system is used more.",12.5,False,GRAYTX,True)]])
table(s,Inches(0.6),Inches(1.9),Inches(12.13),
      ["Cost area","Azure service","What drives it","Size"],
      [["Model usage","Azure OpenAI","Paid per token (a few characters); more traffic = more cost","Largest, variable"],
       ["Compute / hosting","Container Apps / App Service","Always-on services","Medium, steady"],
       ["Search index","Azure AI Search","Storage + number of lookups","Medium"],
       ["Data storage","Blob / Fabric / Cosmos DB","Volume of data kept","Low–Medium"],
       ["Monitoring","Azure Monitor / App Insights","Volume of logs and traces","Low–Medium"],
       ["People","—","Small team to maintain & support","Biggest overall"]],
      cw=[Inches(2.4),Inches(3.0),Inches(4.73),Inches(2.0)],fs=10.5,rh=Inches(0.56))
_txt(s,Inches(0.6),Inches(6.25),Inches(12.13),Inches(0.7),
     [[("Two big levers: ",12.5,True,NAVY),("use the Model Router to pick a smaller, cheaper model when a task allows it, and cache repeated answers so we do not pay twice.",12.5,False,GRAYTX)]])
notes(s,"They asked specifically about running costs, so slow down. Two messages: costs are ongoing, and the two biggest are model usage (variable, grows with traffic) and people (fixed). I can give a real monthly figure once we know expected volume. Mention the two cost levers.")

# ---- 14 TEAM & RISKS ----
s=add(); title(s,"Who runs it, and what to watch",14,"People & risk")
box(s,Inches(0.7),Inches(1.6),Inches(5.9),Inches(4.6),"Team & roles",None,fill=LIGHT)
bullets(s,[
    ("Platform lead / architect — owns design & standards.",0),
    ("Engineers — build the framework & pipeline.",0),
    ("Data engineer — prepares and connects data.",0),
    ("Security & governance — access, privacy, compliance.",0),
    ("Support / operations — keeps it running.",0),
],x=Inches(0.95),y=Inches(2.15),w=Inches(5.45),h=Inches(4.0),size=13,gap=11)
box(s,Inches(6.9),Inches(1.6),Inches(5.83),Inches(4.6),"Risks to watch",None,fill=LIGHT)
bullets(s,[
    ("Wrong or made-up answers → grounding + testing.",0),
    ("Cost surprises → usage limits, budgets, alerts.",0),
    ("Too much automation → keep humans in the loop.",0),
    ("Locked to one model → the gateway lets us switch.",0),
    ("Security gaps → treat all input/output as untrusted.",0),
],x=Inches(7.15),y=Inches(2.15),w=Inches(5.4),h=Inches(4.0),size=13,gap=11)
notes(s,"Two short columns. Left: a small focused team can build the base in a month and support many projects. Right: the main risks and the one-line fix for each. The gateway point matters to leadership — we are not locked to one model provider.")

# ---- 15 SUMMARY ----
s=add(); title(s,"Summary and next steps",15,"Wrap-up")
bullets(s,[
    ("LLMOps is how we run LLM apps reliably, not just build a demo.",0),
    ("Build the reusable framework on Azure first — about one month for a solid base.",0,True,NAVY),
    ("Each component maps to a specific Azure service, so the build is concrete.",0),
    ("Then onboard projects quickly on top of it — mostly configuration, not new engineering.",0),
    ("Plan for ongoing running costs — mainly model usage and people.",0),
    ("Next step: agree the scope for the one-month base build and set up the Azure environment.",0,True,NAVY),
],y=Inches(1.7),gap=13)
notes(s,"Recap and make one clear ask: agreement on scope for the one-month Azure base build, and access to set up the environment. Keep it to a single decision.")

# ---- 16 GLOSSARY ----
s=add(); title(s,"Terms in plain English (quick reference)",16,"Appendix")
gloss=[("LLM","Large Language Model — AI that reads and writes text."),
       ("LLMOps","Large Language Model Operations — building, testing, shipping, running LLM apps."),
       ("RAG","Retrieval-Augmented Generation — the model answers using our own documents."),
       ("CI/CD","Continuous Integration / Continuous Delivery — automated testing and release."),
       ("Embeddings","Text turned into numbers so we can search by meaning."),
       ("Token","The small unit of text a model reads/writes; billing is per token."),
       ("Guardrails","Automatic safety checks on what goes in and comes out."),
       ("PII","Personally Identifiable Information — personal data like names, phone numbers."),
       ("Agent","An LLM that can use tools and take steps, not just chat."),
       ("Canary release","Releasing to a small slice first to catch problems early."),
       ("OpenTelemetry","An open standard for collecting traces and metrics."),
       ("Content Safety","Azure service that detects unsafe content and personal data.")]
colw=Inches(5.95); x0=Inches(0.7); y0=Inches(1.55); rowh=Inches(0.8)
for i,(term,defn) in enumerate(gloss):
    r=i//2; c=i%2; x=x0+c*(colw+Inches(0.25)); y=y0+r*rowh
    _txt(s,x,y,colw,rowh,[[(term+"  ",12.5,True,TEAL),(defn,12,False,GRAYTX)]],ls=1.0)
notes(s,"Appendix. Leave it up during questions for the acronyms. Skip in the main flow if short on time.")

out=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"presentation","LLMOps-Framework-Technical.pptx")
prs.save(out)
print(f"Saved: {out}  ({len(prs.slides._sldIdLst)} slides)")
