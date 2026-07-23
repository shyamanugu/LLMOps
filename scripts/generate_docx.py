#!/usr/bin/env python3
"""Generate the AFNI Enterprise LLMOps written proposal (diagram-led, AFNI-internal).
Requires: python-docx. Diagrams (PNG) built beforehand by build_diagrams.py + rasterize.js.
Output: proposal/Afni-LLMOps-Proposal.docx
"""
import os
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIA=os.path.join(ROOT,"diagrams")
NAVY=RGBColor(0x12,0x1F,0x3D); INDIGO=RGBColor(0x1B,0x3A,0x6B); TEAL=RGBColor(0x00,0x7A,0x7A)
AMBER=RGBColor(0xB5,0x74,0x00); GRAY=RGBColor(0x50,0x5A,0x6A); WHITE=RGBColor(0xFF,0xFF,0xFF)
GREEN=RGBColor(0x2E,0x7D,0x45); RED=RGBColor(0xB0,0x30,0x25); FONT="Segoe UI"

doc=Document()
n=doc.styles["Normal"]; n.font.name=FONT; n.font.size=Pt(10.5); n.font.color.rgb=RGBColor(0x22,0x28,0x33)
n.paragraph_format.space_after=Pt(6); n.paragraph_format.line_spacing=1.12
for lvl,size,col in [(1,17,NAVY),(2,13.5,INDIGO),(3,11.5,TEAL)]:
    st=doc.styles[f"Heading {lvl}"]; st.font.name=FONT; st.font.size=Pt(size); st.font.color.rgb=col; st.font.bold=True
    st.paragraph_format.space_before=Pt(12 if lvl==1 else 8); st.paragraph_format.space_after=Pt(4)

def _shade(cell,hexfill):
    tcPr=cell._tc.get_or_add_tcPr(); shd=OxmlElement("w:shd")
    shd.set(qn("w:val"),"clear"); shd.set(qn("w:fill"),hexfill); tcPr.append(shd)

def para(text="",size=10.5,bold=False,italic=False,color=None,align=None,sa=6,sb=0):
    p=doc.add_paragraph(); p.paragraph_format.space_after=Pt(sa); p.paragraph_format.space_before=Pt(sb)
    if align: p.alignment=align
    if text:
        r=p.add_run(text); r.font.size=Pt(size); r.bold=bold; r.italic=italic; r.font.name=FONT
        if color: r.font.color.rgb=color
    return p

def bullet(text,lead=None):
    p=doc.add_paragraph(style="List Bullet"); p.paragraph_format.space_after=Pt(3)
    if lead:
        r=p.add_run(lead); r.bold=True; r.font.name=FONT; r.font.size=Pt(10.5)
    r2=p.add_run(text); r2.font.name=FONT; r2.font.size=Pt(10.5)

def h1(t): return doc.add_heading(t,level=1)
def h2(t): return doc.add_heading(t,level=2)

def image(png,width=6.5,caption=None):
    doc.add_paragraph().paragraph_format.space_after=Pt(2)
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(os.path.join(DIA,png),width=Inches(width))
    if caption:
        c=doc.add_paragraph(); c.alignment=WD_ALIGN_PARAGRAPH.CENTER; c.paragraph_format.space_before=Pt(3)
        r=c.add_run("Figure. "+caption); r.italic=True; r.font.size=Pt(9); r.font.color.rgb=GRAY; r.font.name=FONT

def make_table(headers,rows,widths=None,fill="1B3A6B"):
    t=doc.add_table(rows=1,cols=len(headers)); t.style="Table Grid"; t.alignment=WD_TABLE_ALIGNMENT.CENTER
    for i,h in enumerate(headers):
        c=t.rows[0].cells[i]; _shade(c,fill); p=c.paragraphs[0]; p.paragraph_format.space_after=Pt(2); p.paragraph_format.space_before=Pt(2)
        r=p.add_run(h); r.bold=True; r.font.color.rgb=WHITE; r.font.size=Pt(10); r.font.name=FONT
    for ri,row in enumerate(rows):
        cells=t.add_row().cells
        for ci,v in enumerate(row):
            if ri%2==1: _shade(cells[ci],"EEF1F7")
            p=cells[ci].paragraphs[0]; p.paragraph_format.space_after=Pt(2); p.paragraph_format.space_before=Pt(2)
            r=p.add_run(str(v)); r.font.size=Pt(9.5); r.font.name=FONT
            if ci==0: r.bold=True; r.font.color.rgb=NAVY
    if widths:
        for ci,w in enumerate(widths):
            for row in t.rows: row.cells[ci].width=w
    para("",sa=4); return t

def callout(title,text):
    t=doc.add_table(rows=1,cols=1); t.style="Table Grid"; c=t.rows[0].cells[0]; _shade(c,"EAF3F3")
    p=c.paragraphs[0]; r=p.add_run(title+"  "); r.bold=True; r.font.color.rgb=TEAL; r.font.name=FONT; r.font.size=Pt(10.5)
    r2=p.add_run(text); r2.font.name=FONT; r2.font.size=Pt(10.5); para("",sa=4)

print("Building diagram-led document...")
sec=doc.sections[0]; sec.top_margin=Inches(0.9); sec.bottom_margin=Inches(0.8); sec.left_margin=Inches(1.0); sec.right_margin=Inches(1.0)
def add_page_number(p):
    run=p.add_run(); f1=OxmlElement("w:fldChar"); f1.set(qn("w:fldCharType"),"begin")
    ins=OxmlElement("w:instrText"); ins.set(qn("xml:space"),"preserve"); ins.text="PAGE"
    f2=OxmlElement("w:fldChar"); f2.set(qn("w:fldCharType"),"end"); run._r.append(f1); run._r.append(ins); run._r.append(f2)
fp=sec.footer.paragraphs[0]; fp.alignment=WD_ALIGN_PARAGRAPH.CENTER
fr=fp.add_run("AFNI · Office of GenAI Architecture  ·  Enterprise LLMOps  ·  Confidential  ·  Page ")
fr.font.size=Pt(8); fr.font.color.rgb=GRAY; fr.font.name=FONT; add_page_number(fp)

# COVER
para("",sa=60)
para("ENTERPRISE PROPOSAL · 2026",12,bold=True,color=TEAL,align=WD_ALIGN_PARAGRAPH.CENTER,sa=10)
para("Enterprise LLMOps for AFNI",30,bold=True,color=NAVY,align=WD_ALIGN_PARAGRAPH.CENTER,sa=4)
para("Multi-agent GenAI, industrialized",16,italic=True,color=GRAY,align=WD_ALIGN_PARAGRAPH.CENTER,sa=26)
para("One governed platform powering three flagship initiatives — Voice Agent, the "
     "Performance Intelligence Index, and Hiring Intelligence.",13,color=RGBColor(0x33,0x3B,0x49),align=WD_ALIGN_PARAGRAPH.CENTER,sa=34)
make_table(["Field","Detail"],
           [["Owner","AFNI, Inc. — internal & confidential"],["Prepared by","AFNI · Office of GenAI Architecture"],
            ["Document","Enterprise LLMOps Proposal"],["Version / Status","v2.0 / Draft for review"],
            ["Classification","Confidential — AFNI internal"],["Date","2026"]],widths=[Inches(1.8),Inches(4.6)])
doc.add_page_break()

# CONTENTS
h1("Contents")
for item in ["1. Executive Summary","2. Business Context & Opportunity","3. The Three Flagship Initiatives",
             "4. Platform Architecture","5. Multi-Agent Systems","6. Voice Agent","7. Performance Intelligence Index",
             "8. Hiring Intelligence","9. LLMOps Lifecycle & Toolchain","10. Responsible AI & Governance",
             "11. Security, Privacy & Compliance","12. Observability & FinOps","13. Operating Model & Team",
             "14. Implementation Roadmap","15. Business Case & ROI","16. Risks & Mitigations","17. Recommendation & Next Steps"]:
    p=doc.add_paragraph(); p.paragraph_format.space_after=Pt(4)
    r=p.add_run(item); r.font.size=Pt(11); r.font.name=FONT; r.font.color.rgb=INDIGO; r.bold=True
doc.add_page_break()

# 1 EXEC SUMMARY
h1("1. Executive Summary")
para("AFNI operates in a business where Generative AI is no longer optional. As a global business "
     "process outsourcing and customer-engagement provider, AFNI's economics are driven by the cost "
     "and quality of high-volume voice interactions and the cost and speed of hiring the people who "
     "handle them. AI-native competitors are resetting client expectations on price, availability and "
     "consistency. The opportunity is to move first — as an AI-enabled partner.")
para("This proposal recommends that AFNI stand up an enterprise-grade LLMOps platform on Microsoft "
     "Azure AI Foundry and use it to deliver three flagship, multi-agent initiatives:")
bullet("real-time voice automation and agent-assist across the contact center.","Voice Agent — ")
bullet("an AI-generated, explainable composite score computed from 100% of interactions.","Performance Intelligence Index — ")
bullet("fair, high-volume recruitment for AFNI's own hiring, where AI assists and humans decide.","Hiring Intelligence — ")
para("The strategy is platform-first: build the foundations — orchestration, retrieval, evaluation, "
     "guardrails, observability, security and governance — once, so every initiative reuses them and "
     "future use cases (subrogation automation, a knowledge assistant) ship in weeks. All three run on "
     "the same multi-agent pattern: an orchestrator routing to specialist agents.")
callout("The core idea:","Give AFNI one secure, governed platform to build, evaluate, deploy, govern and "
        "continuously improve fleets of cooperating AI agents — with the same operational rigor AFNI "
        "already applies to running contact centers.")
para("Delivery follows a Crawl → Walk → Run roadmap over roughly nine to twelve months, beginning with "
     "a four-week Phase 0. Responsible AI, human-in-the-loop control, and compliance (PCI-DSS, HIPAA, "
     "TCPA, SOC 2, GDPR, and hiring-fairness law such as EEOC and NYC Local Law 144) are designed in from "
     "day one. All financial figures in this document are illustrative placeholders, to be replaced with "
     "AFNI's actuals during discovery.")
para("Recommendation: approve Phase 0 to lock the foundations and launch the Voice Agent copilot, the PI "
     "Index MVP, and the Hiring Intelligence screening pilot.",bold=True,color=NAVY)

# 2 CONTEXT
h1("2. Business Context & Opportunity")
para("AFNI, Inc. is a global BPO and customer-engagement provider founded in 1936, headquartered in "
     "Bloomington, Illinois, with roughly 3,400+ professionals across the United States, Mexico and the "
     "Philippines, plus the AFNI@Home remote program. (Public-source figures; to be confirmed.)")
make_table(["Service line","What it involves","GenAI relevance"],
           [["Acquisition & Growth","Sales and acquisition","Outbound assist, lead qualification"],
            ["Care & Retention","Service and loyalty","Voice Agent, agent-assist, self-service"],
            ["Collections","Receivables and recovery","Compliant reminders, negotiation assist"],
            ["P&C Insurance","Support incl. subrogation","Document AI, claims & subrogation automation"],
            ["Gainshare model","Outcome-based partnerships","Efficiency directly improves shared margin"]],
           widths=[Inches(1.7),Inches(2.5),Inches(2.4)])
para("Strategic pressures on BPOs: margin and labor-cost pressure as AI-native providers reset price "
     "expectations; persistent agent attrition and ramp cost; rising client expectations for 24/7, "
     "consistent, compliant interactions; and a first-mover advantage for AI-enabled partners.")

# 3 THREE INITIATIVES
h1("3. The Three Flagship Initiatives")
para("AFNI builds one shared multi-agent LLMOps platform and delivers three flagship initiatives on top "
     "of it. Voice Agent generates real-time automation and interaction data; the Performance Intelligence "
     "Index turns 100% of that data into performance intelligence; Hiring Intelligence reuses the same "
     "agents and voice stack to hire the workforce. Build once, reuse everywhere.")
image("03-three-initiatives.png",width=6.6,caption="Three flagship initiatives on one shared platform.")

# 4 ARCHITECTURE
h1("4. Platform Architecture")
para("The platform is a layered reference architecture on Azure AI Foundry. Each layer has a clear "
     "responsibility and named Azure services, so initiatives compose from shared building blocks. "
     "Environments are separated (dev/test/prod) on a Cloud Adoption Framework landing zone, with private "
     "networking, Entra ID identity, Key Vault secrets, and an Azure API Management AI gateway for token "
     "metering, quotas and caching.")
image("01-platform-architecture.png",width=6.6,caption="Layered reference architecture on Azure AI Foundry.")

# 5 MULTI-AGENT
h1("5. Multi-Agent Systems")
para("Every initiative uses one pattern: a supervisor/orchestrator interprets a request and routes work "
     "to specialist agents, each with a narrow, testable responsibility. Deterministic guardrails wrap the "
     "probabilistic agents so policy — disclosures, PII handling, do-not-say/must-say — is enforced, not "
     "hoped for. The same seven specialists answer callers (Voice Agent), score interactions (PI Index), "
     "and move candidates through the funnel (Hiring Intelligence).")
image("02-multi-agent.png",width=6.6,caption="One orchestrator, seven specialist agents, reused everywhere.")

# 6 VOICE
h1("6. Voice Agent")
para("Voice is AFNI's highest-volume, highest-cost channel. Voice Agent is delivered in three modes, "
     "sequenced from lowest to highest risk: an agent-assist copilot for live reps; an autonomous voice "
     "agent for containable call types using sub-second speech-to-speech; and post-call analytics that "
     "feed the Performance Intelligence Index. Content Safety, PII redaction and TCPA/PCI guardrails run "
     "on every turn.")
image("04-voice-flow.png",width=6.6,caption="End-to-end real-time call flow.")
make_table(["KPI","Baseline (today)","Target with Voice Agent *"],
           [["Containment / deflection","Manual IVR","20–40% of eligible call types"],
            ["Average Handle Time","Program baseline","15–25% reduction"],
            ["QA coverage","2–10% sampled","100% (via PI Index)"],
            ["Compliance adherence","Sampled review","Monitored on every call"]],
           widths=[Inches(2.4),Inches(1.9),Inches(2.1)])
para("* Illustrative — replaced with AFNI actuals in discovery.",9,italic=True,color=GRAY)

# 7 PI INDEX
h1("7. Performance Intelligence Index")
para("The Performance Intelligence Index (PI Index) is an AI-generated, explainable composite score "
     "computed from 100% of interactions — not sampled QA. A team of analysis agents scores each "
     "interaction across seven dimensions (compliance adherence, communication & empathy, resolution/FCR, "
     "script & process, sentiment trajectory, efficiency, and business outcome); a calibrated, explainable "
     "scoring engine rolls these into one index per agent, team, program and client.")
image("05-pi-index.png",width=6.6,caption="From 100% of interactions to one explainable composite score.")
para("Outputs feed coaching recommendations, QA calibration, Gainshare/performance reporting, and anomaly "
     "and risk alerts. Governance covers score explainability, fairness across agents and sites, and human "
     "calibration with an appeals path.")

# 8 HIRING
h1("8. Hiring Intelligence")
para("Hiring Intelligence applies the platform to AFNI's own high-volume recruiting across three "
     "countries, with an agent at every funnel stage: JD generation, sourcing & résumé ranking, "
     "conversational screening (chat plus an optional voice pre-screen that reuses the Voice Agent "
     "platform), scheduling, structured interview-scoring assist, and a continuous fairness monitor.")
image("06-hiring-intelligence.png",width=6.6,caption="An agent at every stage — humans make the decisions.")
callout("Non-negotiable principle:","AI assists, humans decide. There is no autonomous rejection of "
        "candidates. Every automated employment decision tool is bias-audited and explainable, complying "
        "with EEOC, NYC Local Law 144, the Illinois AI Video Interview Act, the EU AI Act's high-risk "
        "employment provisions, and GDPR.")
make_table(["KPI","Target *"],
           [["Recruiter screening effort","30–50% reduction"],["Time-to-fill","materially shorter"],
            ["Cost-per-hire","reduced"],["Candidate experience (NPS)","improved"],
            ["Offer-accept rate","improved"],["90-day attrition","reduced via better matching"]],
           widths=[Inches(3.2),Inches(3.2)])
para("* Illustrative — validated in discovery.",9,italic=True,color=GRAY)

# 9 LLMOPS
h1("9. LLMOps Lifecycle & Toolchain")
para("LLMOps is the operational backbone that turns pilots into dependable production systems: curate "
     "data and knowledge → engineer versioned prompts and agents → evaluate → ship via CI/CD → serve → "
     "observe → feed learnings back. Governance and Responsible AI wrap the entire loop.")
image("07-llmops-lifecycle.png",width=5.4,caption="A continuous, governed improvement loop.")
para("Evaluation is the quality gate: golden datasets scored by LLM-as-judge plus human review; "
     "groundedness/faithfulness for retrieval; red-teaming and safety evals; regression gates that block "
     "promotion; and online A/B and shadow testing. Releases use canary or blue-green deployment with "
     "instant rollback, behind the API Management gateway.")

# 10 RESPONSIBLE AI
h1("10. Responsible AI & Governance")
para("Governance follows Microsoft's Responsible AI pillars — fairness, reliability & safety, privacy & "
     "security, inclusiveness, transparency, accountability — operationalized through an AI use-case intake "
     "with risk-tiering, mandatory human-in-the-loop for consequential decisions, model/system cards, "
     "Content Safety, audit trails, AI incident response, red-teaming, and an AI governance board.")
make_table(["Tier","Examples","Controls"],
           [["High","Hiring decisions, collections, PI Index scoring","Full HITL, bias audits, legal sign-off, appeals"],
            ["Medium","Customer voice answers","Guardrails + sampled human QA + monitoring"],
            ["Low","Internal drafting, summaries","Standard guardrails + spot checks"]],
           widths=[Inches(1.0),Inches(2.8),Inches(2.6)])

# 11 SECURITY
h1("11. Security, Privacy & Compliance")
bullet("Microsoft Entra ID with least-privilege RBAC and managed identities.","Identity — ")
bullet("Azure Key Vault; no secrets in code.","Secrets — ")
bullet("VNet with private endpoints; no public egress for sensitive data.","Network — ")
bullet("honored across US, Mexico and the Philippines.","Data residency — ")
bullet("Defender for Cloud posture; Purview lineage and DLP; prompt-injection defenses.","Posture — ")
make_table(["Framework","Where it applies","Primary controls"],
           [["PCI-DSS","Payment capture","Pause/mask, tokenization, scope isolation"],
            ["HIPAA","Healthcare programs","PHI handling, BAAs, access controls"],
            ["TCPA","Outbound voice","Consent, do-not-call, disclosures"],
            ["SOC 2","Platform","Control framework, audit evidence"],
            ["GDPR","PII","Data-subject rights, minimization"],
            ["EEOC / NYC LL144","Hiring","Bias audits, notice, human decision"]],
           widths=[Inches(1.5),Inches(2.0),Inches(2.9)])

# 12 OBSERVABILITY
h1("12. Observability & FinOps")
para("The platform instruments quality, groundedness, latency (p50/p95), errors, drift, safety events and "
     "token usage, traced end-to-end with OpenTelemetry GenAI conventions into Application Insights and "
     "Azure Monitor. FinOps controls cost through token metering and quotas at the gateway, cost showback "
     "per initiative, model right-sizing, semantic caching, and budget guardrails.")
make_table(["Example SLO","Target"],
           [["Voice turn latency (p95)","< 1 second"],["Groundedness score","≥ threshold, gated"],
            ["Availability","99.9%"],["Safety-event rate","below alert threshold"]],
           widths=[Inches(3.2),Inches(3.2)])

# 13 OPERATING MODEL
h1("13. Operating Model & Team")
para("An AFNI GenAI Center of Excellence (CoE) operates a federated hub-and-spoke model: the CoE owns the "
     "platform, guardrails and standards, while Operations and HR 'spokes' own their initiatives and "
     "outcomes. All roles are AFNI-internal.")
make_table(["Role","Focus"],
           [["Executive sponsor","Funding, priorities, unblock"],["AI product owner","Backlog, outcomes, adoption"],
            ["GenAI architect (lead)","Architecture, standards, review"],["Prompt / agent engineers","Agent design & evaluation"],
            ["LLMOps engineers","CI/CD, serving, observability"],["Data engineers","Knowledge pipelines, RAG data"],
            ["RAI / governance officer","Risk tiering, audits, policy"],["Security engineer","Identity, network, compliance"]],
           widths=[Inches(2.4),Inches(4.0)])

# 14 ROADMAP
h1("14. Implementation Roadmap")
image("08-roadmap.png",width=6.6,caption="Crawl → Walk → Run over ~9–12 months.")
make_table(["Phase","Timing","Exit criteria"],
           [["Phase 0","Weeks 0–4","Foundations live; initiatives scoped"],
            ["Phase 1 · Crawl","Months 1–3","Pilots show measurable value"],
            ["Phase 2 · Walk","Months 4–7","Production use at scale in ≥1 program"],
            ["Phase 3 · Run","Months 8–12","Enterprise scale; improvement flywheel running"]],
           widths=[Inches(1.5),Inches(1.3),Inches(3.7)])

# 15 BUSINESS CASE
h1("15. Business Case & ROI")
para("All figures are illustrative placeholders, to be replaced with AFNI's actual volumes, rates and "
     "cost structure during Phase 0 discovery.",italic=True)
make_table(["Value lever","Initiative","Illustrative impact"],
           [["100% QA coverage & faster coaching","PI Index","from ~5% sampled to 100%"],
            ["Call containment / deflection","Voice Agent","20–40% of eligible calls"],
            ["AHT reduction (agent-assist)","Voice Agent","15–25% shorter handle time"],
            ["Recruiter screening effort","Hiring Intelligence","30–50% fewer manual hours"],
            ["Time-to-fill & cost-per-hire","Hiring Intelligence","both materially reduced"],
            ["Attrition (matching + coaching)","Hiring + PI Index","lower 90-day attrition"]],
           widths=[Inches(2.4),Inches(1.9),Inches(2.6)])
para("Illustrative payback: 9–15 months. Under AFNI's Gainshare model, efficiency gains improve shared "
     "margin directly.",bold=True,color=NAVY)

# 16 RISKS
h1("16. Risks & Mitigations")
make_table(["Risk","Category","Mitigation"],
           [["Hallucination / wrong answers","Model/quality","RAG grounding, groundedness gates, HITL, guardrails"],
            ["Compliance breach (TCPA/PCI/EEOC)","Legal","Compliance agent, risk-tiering, bias audits, legal sign-off"],
            ["Unfair scoring (PI Index / hiring)","Fairness","Fairness monitors, explainability, human calibration & appeals"],
            ["Runaway token cost","Cost","APIM metering, right-sizing, caching, budget alerts"],
            ["Quality regression on change","Delivery","Golden-set regression gates, canary + rollback"],
            ["Low adoption / change fatigue","Adoption","Copilot-first, agent involvement, enablement, clear ROI"],
            ["Data leakage / prompt injection","Security","Private networking, Content Safety, prompt shields, DLP"]],
           widths=[Inches(2.2),Inches(1.1),Inches(3.1)])

# 17 RECOMMENDATION
h1("17. Recommendation & Next Steps")
para("Approve a four-week Phase 0 to lock the foundations and launch the initial pilots.",bold=True,color=NAVY)
bullet("Confirm the three flagship initiatives and success metrics with Operations and HR leaders.","1.  ")
bullet("Stand up the Azure landing zone, security baseline and guardrail policy.","2.  ")
bullet("Run use-case intake and risk-tiering; secure data access.","3.  ")
bullet("Launch the Voice Agent copilot, the PI Index MVP, and the Hiring Intelligence screening pilot.","4.  ")
para("")
para("AFNI · Office of GenAI Architecture — internal & confidential.",9,italic=True,color=GRAY,align=WD_ALIGN_PARAGRAPH.CENTER)

out=os.path.join(ROOT,"proposal","Afni-LLMOps-Proposal.docx")
doc.save(out); print(f"Saved: {out}")
