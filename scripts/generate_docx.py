#!/usr/bin/env python3
"""Generate the AFNI Enterprise GenAI Framework proposal (detailed, diagram-rich, AFNI-internal).
Requires: python-docx. Diagrams built beforehand.
Output: proposal/Afni-LLMOps-Proposal.docx
"""
import os
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__))); DIA=os.path.join(ROOT,"diagrams")
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
    tcPr=cell._tc.get_or_add_tcPr(); shd=OxmlElement("w:shd"); shd.set(qn("w:val"),"clear"); shd.set(qn("w:fill"),hexfill); tcPr.append(shd)
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
        r=p.add_run(h); r.bold=True; r.font.color.rgb=WHITE; r.font.size=Pt(9.5); r.font.name=FONT
    for ri,row in enumerate(rows):
        cells=t.add_row().cells
        for ci,v in enumerate(row):
            if ri%2==1: _shade(cells[ci],"EEF1F7")
            p=cells[ci].paragraphs[0]; p.paragraph_format.space_after=Pt(2); p.paragraph_format.space_before=Pt(2)
            r=p.add_run(str(v)); r.font.size=Pt(9); r.font.name=FONT
            if ci==0: r.bold=True; r.font.color.rgb=NAVY
    if widths:
        for ci,w in enumerate(widths):
            for row in t.rows: row.cells[ci].width=w
    para("",sa=4); return t
def callout(title,text):
    t=doc.add_table(rows=1,cols=1); t.style="Table Grid"; c=t.rows[0].cells[0]; _shade(c,"EAF3F3")
    p=c.paragraphs[0]; r=p.add_run(title+"  "); r.bold=True; r.font.color.rgb=TEAL; r.font.name=FONT; r.font.size=Pt(10.5)
    r2=p.add_run(text); r2.font.name=FONT; r2.font.size=Pt(10.5); para("",sa=4)

print("Building detailed framework document...")
sec=doc.sections[0]; sec.top_margin=Inches(0.9); sec.bottom_margin=Inches(0.8); sec.left_margin=Inches(1.0); sec.right_margin=Inches(1.0)
def add_page_number(p):
    run=p.add_run(); f1=OxmlElement("w:fldChar"); f1.set(qn("w:fldCharType"),"begin")
    ins=OxmlElement("w:instrText"); ins.set(qn("xml:space"),"preserve"); ins.text="PAGE"
    f2=OxmlElement("w:fldChar"); f2.set(qn("w:fldCharType"),"end"); run._r.append(f1); run._r.append(ins); run._r.append(f2)
fp=sec.footer.paragraphs[0]; fp.alignment=WD_ALIGN_PARAGRAPH.CENTER
fr=fp.add_run("AFNI · Office of GenAI Architecture  ·  Enterprise GenAI Framework  ·  Confidential  ·  Page ")
fr.font.size=Pt(8); fr.font.color.rgb=GRAY; fr.font.name=FONT; add_page_number(fp)

# COVER
para("",sa=54)
para("ENTERPRISE PROPOSAL · 2026",12,bold=True,color=TEAL,align=WD_ALIGN_PARAGRAPH.CENTER,sa=10)
para("Enterprise GenAI Framework for AFNI",28,bold=True,color=NAVY,align=WD_ALIGN_PARAGRAPH.CENTER,sa=4)
para("Build the factory, not just the features",15,italic=True,color=GRAY,align=WD_ALIGN_PARAGRAPH.CENTER,sa=24)
para("One governed, reusable platform to onboard any GenAI use case — proven first by Voice Agent, the "
     "Performance Intelligence Index, and Hiring Intelligence. Grounded in Microsoft Foundry, the Microsoft "
     "Agent Framework, the Model Router, and the MCP/A2A agent protocol stack.",12.5,color=RGBColor(0x33,0x3B,0x49),align=WD_ALIGN_PARAGRAPH.CENTER,sa=28)
make_table(["Field","Detail"],
           [["Owner","AFNI, Inc. — internal & confidential"],["Prepared by","AFNI · Office of GenAI Architecture"],
            ["Document","Enterprise GenAI Framework Proposal"],["Version / Status","v3.0 / Draft for review"],
            ["Classification","Confidential — AFNI internal"],["Date","2026"]],widths=[Inches(1.8),Inches(4.6)])
doc.add_page_break()

# CONTENTS
h1("Contents")
toc=["1. Executive Summary","2. Business Context & Opportunity","3. The Enterprise GenAI Framework","4. Design Principles",
     "5. GenAI Pattern Catalog — Beyond Chatbots","6. Use-Case Onboarding — The Paved Road","7. Platform Architecture",
     "8. Enterprise Multi-Agent Orchestration","9. Model Strategy & the Model Router","10. Proof Point 1 — Voice Agent",
     "11. Proof Point 2 — Performance Intelligence Index","12. Proof Point 3 — Hiring Intelligence",
     "13. Security by Design — Zero Trust & OWASP LLM Top 10","14. Data Platform at Scale","15. Performance & Scalability",
     "16. GenAIOps — CI/CD & Validation","17. Evaluation Framework","18. Responsible AI & Governance","19. Observability & FinOps",
     "20. Operating Model & Team","21. Roadmap & Maturity Model","22. Reference Tech Stack (Bill of Materials)",
     "23. Business Case & ROI","24. Risks & Mitigations","25. Recommendation & Next Steps"]
for item in toc:
    p=doc.add_paragraph(); p.paragraph_format.space_after=Pt(3)
    r=p.add_run(item); r.font.size=Pt(11); r.font.name=FONT; r.font.color.rgb=INDIGO; r.bold=True
para("",sa=6)
para("Note on sources: technology capabilities (Microsoft Foundry, Agent Service, Model Router, Microsoft Agent "
     "Framework, GPT-5.x, MCP/A2A, OWASP Top 10 for LLM Applications 2025) reflect publicly documented 2026 state. "
     "All ROI and performance figures are illustrative placeholders to be replaced with AFNI actuals during discovery.",9.5,italic=True,color=GRAY)
doc.add_page_break()

# 1 EXEC SUMMARY
h1("1. Executive Summary")
para("This proposal asks AFNI to build not a set of AI features but the factory that produces them: an enterprise, "
     "reusable GenAI framework on Microsoft Foundry that lets AFNI onboard any GenAI use case quickly, safely and "
     "cost-effectively — and continuously adopt each new frontier model without rewrites. Only about 1% of enterprises "
     "describe their GenAI as mature; the differentiator is no longer a clever demo but the operating platform that turns "
     "demos into governed production systems.")
para("The framework is proven immediately on three high-value initiatives, which become its first onboarded use cases:")
bullet("real-time, multi-agent voice automation and agent-assist across the contact center.","Voice Agent — ")
bullet("an explainable composite performance score from 100% of interactions.","Performance Intelligence Index — ")
bullet("fair, high-volume recruitment where AI assists and humans decide.","Hiring Intelligence — ")
callout("The core idea:","Build one secure, governed, reusable platform — the paved road — so the 4th, 10th and 40th use "
        "case reuse it. Time-to-value drops from quarters to weeks; security, evaluation, observability and cost control "
        "are inherited by default.")
para("The framework treats GenAI as far more than chatbots (agentic workflows, document intelligence, batch analytics, "
     "multimodal, decision support, real-time voice), is model-agnostic and frontier-ready via the Foundry Model Router "
     "and an evaluation harness, and is engineered to the highest enterprise standards for security (Zero Trust; the 2025 "
     "OWASP Top 10 for LLM Applications), data-at-scale, performance, and GenAIOps CI/CD with blocking validation gates. "
     "Recommendation: approve Phase 0 to stand up the platform and onboard the three proof points.",bold=True,color=NAVY)

# 2 CONTEXT
h1("2. Business Context & Opportunity")
para("AFNI is a global BPO and customer-engagement provider (founded 1936, HQ Bloomington IL; ~3,400+ staff across the "
     "US, Mexico and the Philippines plus AFNI@Home). Service lines: Acquisition & Growth; Care & Retention; Collections; "
     "P&C Insurance including subrogation; under a Gainshare commercial model. Its economics turn on the cost and quality "
     "of high-volume voice and the cost and speed of high-volume hiring — both directly addressable by GenAI, and both "
     "reused many times across programs and geographies once a platform exists.")
make_table(["Strategic pressure","Implication","Framework response"],
           [["AI-native competitors reset price/quality","Margin pressure","Reusable platform lowers unit cost per use case"],
            ["Attrition & ramp never stop","Persistent hiring cost","Hiring Intelligence + PI Index coaching"],
            ["Frontier models ship constantly","Point solutions obsolete fast","Model Router + evals adopt new models"],
            ["Clients expect 24/7 compliant CX","Higher service bar","Voice Agent + guardrails + observability"]],
           widths=[Inches(2.4),Inches(2.0),Inches(2.2)])

# 3 FRAMEWORK
h1("3. The Enterprise GenAI Framework")
para("The framework is a platform-as-a-product: a set of reusable capability layers, a catalog of GenAI patterns, and a "
     "paved-road onboarding path, wrapped by cross-cutting security/governance and GenAIOps/observability. Use cases plug "
     "in on top and inherit the platform's controls by default.")
image("09-framework.png",width=6.7,caption="The enterprise GenAI framework — build the factory, not just the features.")
para("Cross-cutting concerns (Security & Governance on one side; GenAIOps, Observability & FinOps on the other) apply to "
     "every use case. The foundation is Microsoft Foundry on Azure: Agent Service, the Model Router, unified tracing and "
     "evaluation, and Content Safety.")

# 4 DESIGN PRINCIPLES
h1("4. Design Principles")
para("These are the non-negotiables that keep the framework coherent as it scales:")
for t,d in [("Platform as a product","Paved roads and self-service; the platform team ships golden paths, not tickets."),
            ("Reuse over rebuild","Composable building blocks — agents, tools, prompts, evals, IaC — assembled, not re-authored."),
            ("Model-agnostic & frontier-ready","Pin to capabilities and evaluations via the Model Router; never to a single model version."),
            ("Evaluation-driven everything","Nothing ships without passing offline, online and adversarial evaluations."),
            ("Deterministic guardrails","Wrap probabilistic agents in deterministic policy and controls."),
            ("Zero Trust","Treat all model input, output and retrieved content as untrusted; least privilege everywhere."),
            ("Human-in-the-loop","Graduated autonomy; human approval for consequential or irreversible actions."),
            ("Observability & cost first-class","Every trace and every token is measured, attributed and budgeted."),
            ("Privacy & security by default","Data minimization; secure/compliant-by-default templates."),
            ("Fail safe","Fallback models and graceful degradation; never a hard dependency on one model or region."),
            ("Everything-as-code","Declarative agents, versioned prompts, IaC — reproducible and reviewable."),
            ("Measure business outcomes","Optimize AHT, containment, time-to-fill and quality — not model vanity metrics.")]:
    bullet(d,t+" — ")

# 5 PATTERNS
h1("5. GenAI Pattern Catalog — Beyond Chatbots")
para("Each pattern is a reusable blueprint (reference architecture + evaluation suite + guardrail pack + IaC). A new use "
     "case selects a pattern rather than starting from scratch.")
image("11-patterns.png",width=6.7,caption="GenAI pattern catalog — conversational, agentic, analytical, multimodal, and more.")
make_table(["Pattern","Example AFNI application"],
           [["Agentic workflow","Subrogation triage & recovery; claims routing"],
            ["Document intelligence","Extract & validate insurance forms and correspondence"],
            ["Batch summarization & analytics","PI Index scoring of 100% of interactions"],
            ["Decision support & forecasting","Next-best-action in Collections; propensity to pay"],
            ["Real-time voice","Voice Agent — containment and agent-assist"],
            ["RAG","Grounded policy/plan answers across programs"]],
           widths=[Inches(2.4),Inches(4.0)])

# 6 ONBOARDING
h1("6. Use-Case Onboarding — The Paved Road")
para("Onboarding is a golden path: Intake → Value & Risk tiering → Blueprint selection → Assemble from reusable building "
     "blocks → Evaluate against gates → Deploy via canary → Operate with observability & FinOps → Improve via feedback. "
     "Security, compliance, evaluation and observability are inherited at every step, so teams focus on the use case, not "
     "the plumbing.")
image("10-onboarding.png",width=6.7,caption="The paved road — from idea to production in weeks.")

# 7 ARCHITECTURE
h1("7. Platform Architecture")
para("A layered reference architecture on Microsoft Foundry. Each layer has a clear responsibility and named services; "
     "the Foundry Agent Service hosts durable agents, the Model Router selects models, and an Azure API Management AI "
     "gateway enforces token metering, quotas and caching. Environments (dev/test/prod) follow a Cloud Adoption Framework "
     "landing zone with private networking and Entra ID identity.")
image("01-platform-architecture.png",width=6.7,caption="Layered reference architecture on Microsoft Foundry.")

# 8 ORCHESTRATION
h1("8. Enterprise Multi-Agent Orchestration")
para("Orchestration uses the Microsoft Agent Framework (the production convergence of AutoGen and Semantic Kernel; GA 2026, "
     ".NET & Python). A supervisor routes to specialist agents using sequential, concurrent, group-chat, handoff or Magentic "
     "patterns. Enterprise properties make it production-grade: durable execution (checkpointing, pause/resume, retries, "
     "idempotency, compensation/saga, human-in-the-loop approvals); memory tiers (session, user, procedural); an agent "
     "registry; tools via MCP and cross-runtime agents via A2A; and deterministic guardrails around every probabilistic hop.")
image("12-agent-runtime.png",width=6.7,caption="Enterprise agent runtime — durable, governed, interoperable.")
make_table(["Specialist agent","Voice Agent","PI Index","Hiring Intelligence"],
           [["Intent / Router","route the call","classify interaction","funnel stage routing"],
            ["Knowledge / RAG","policy answers","context for scoring","role & process FAQs"],
            ["Action / Tooling (MCP)","update CRM, take payment","read interaction stores","read/write ATS"],
            ["Compliance / Guardrail","TCPA/PCI","score explainability","EEOC / NYC LL144"],
            ["Summarize / QA & Scoring","disposition","dimension scoring","interview notes (assist)"]],
           widths=[Inches(1.9),Inches(1.5),Inches(1.5),Inches(1.5)])

# 9 MODEL STRATEGY
h1("9. Model Strategy & the Model Router")
para("AFNI pins to capabilities and evaluations, not to a model version. The Foundry Model Router sends each request to the "
     "cheapest model that meets a measured quality bar, with prompt caching. The catalog spans frontier reasoning models "
     "(GPT-5.5, GPT-5.4/5.2 with 272k context), low-latency chat (GPT-5.5 Instant), speech-to-speech (gpt-realtime-1.5), "
     "open-weight models (Llama, Phi) for cost/edge tiers, and fine-tuned/distilled task models.")
image("16-model-strategy.png",width=6.7,caption="Model strategy — ride the frontier without rewrites.")
para("A frontier-adoption loop absorbs new models automatically: a new model is evaluated against golden sets, shadow-tested "
     "in production, and promoted by the router only if it beats the incumbent on quality, cost or latency — with no "
     "application rewrite.")

# 10-12 PROOF POINTS
h1("10. Proof Point 1 — Voice Agent")
para("Real-time voice automation and agent-assist, delivered in three modes (agent-assist copilot; autonomous voice for "
     "containable calls at sub-second latency using gpt-realtime-1.5; post-call analytics that feed the PI Index). Content "
     "Safety, PII redaction and TCPA/PCI guardrails run on every turn.")
image("04-voice-flow.png",width=6.7,caption="Voice Agent — end-to-end real-time call flow.")
make_table(["KPI","Target *"],[["Containment / deflection","20–40% of eligible calls"],["Average Handle Time","15–25% reduction"],
            ["QA coverage","100% (via PI Index)"],["Compliance adherence","monitored on every call"]],widths=[Inches(3.2),Inches(3.2)])
para("* Illustrative — replaced with AFNI actuals in discovery.",9,italic=True,color=GRAY)

h1("11. Proof Point 2 — Performance Intelligence Index")
para("An AI-generated, explainable composite score from 100% of interactions (not sampled QA). Analysis agents score each "
     "interaction across seven dimensions; a calibrated engine rolls them into one PI Index per agent, team, program and "
     "client, feeding coaching, QA calibration and Gainshare reporting.")
image("05-pi-index.png",width=6.7,caption="PI Index — from every interaction to one explainable score.")

h1("12. Proof Point 3 — Hiring Intelligence")
para("The platform applied to AFNI's own high-volume hiring, with an agent at every funnel stage and fairness throughout.")
image("06-hiring-intelligence.png",width=6.7,caption="Hiring Intelligence — an agent at every stage; humans decide.")
callout("Non-negotiable:","AI assists, humans decide. No autonomous rejection; every automated employment decision tool is "
        "bias-audited and explainable — EEOC, NYC Local Law 144, IL AI Video Interview Act, EU AI Act, GDPR.")

# 13 SECURITY
h1("13. Security by Design — Zero Trust & OWASP LLM Top 10")
para("Security is Zero Trust and defense-in-depth, mapped explicitly to the 2025 OWASP Top 10 for LLM Applications. All "
     "model input, output and retrieved content is treated as untrusted; tools are least-privilege; consequential actions "
     "require human approval; and everything is traced for audit.")
image("13-security.png",width=6.7,caption="Zero Trust defense-in-depth mapped to the OWASP LLM Top 10 (2025).")
make_table(["OWASP LLM (2025)","AFNI control"],
           [["LLM01 Prompt injection","Prompt shields; isolate untrusted content"],
            ["LLM02 Sensitive info disclosure","PII redaction; output filtering; DLP"],
            ["LLM06 Excessive agency","Least-privilege tools; human-in-the-loop approvals"],
            ["LLM09 Misinformation","Grounding, citations, evaluation gates"],
            ["LLM10 Unbounded consumption","Rate & cost limits; quotas; budgets"]],
           widths=[Inches(2.6),Inches(3.8)])

# 14 DATA
h1("14. Data Platform at Scale")
para("A Microsoft Fabric / OneLake lakehouse ingests batch and streaming data, with scalable chunking and integrated "
     "vectorization, vector indexes partitioned per domain and tenant, incremental/CDC refresh, and Microsoft Purview for "
     "lineage, DLP and retention. This is what lets the PI Index consume 100% of interactions economically.")
image("14-data-platform.png",width=6.7,caption="Enterprise data platform feeding grounded AI.")

# 15 PERFORMANCE
h1("15. Performance & Scalability")
para("Performance is engineered against explicit latency budgets (a sub-second voice turn is decomposed across speech-to-"
     "text, retrieval, inference, guardrails and text-to-speech), with layered caching, the Model Router for cost-latency-"
     "quality, provisioned throughput for critical paths, autoscaling, async/streaming responses, batching for bulk workloads "
     "like the PI Index, and graceful degradation with fallback models.")
image("17-performance.png",width=6.7,caption="Engineered for sub-second voice and bulk analytics.")

# 16 CI/CD
h1("16. GenAIOps — CI/CD & Validation")
para("GenAIOps is the operational backbone. Everything is code (declarative YAML agents, versioned prompts, IaC). A pull "
     "request triggers evaluation-in-CI, where a series of blocking gates — unit/contract, prompt regression versus a golden-"
     "set baseline, groundedness, safety/red-team, and cost/latency budgets — must pass before promotion. Releases use canary "
     "or blue-green deployment behind the API Management gateway, with post-deploy online A/B and shadow testing, guardrail "
     "monitors, auto-rollback, and a feedback loop that turns production signals into the next golden dataset.")
image("15-genaiops-cicd.png",width=6.7,caption="GenAIOps CI/CD — nothing ships without passing evaluation gates.")

# 17 EVALUATION
h1("17. Evaluation Framework")
para("Quality is measured, not assumed, across three surfaces: offline (golden datasets, LLM-as-judge, Foundry auto-generated "
     "rubric evaluators, groundedness), online (A/B, shadow, guardrail monitors, user & QA feedback), and human & red-team "
     "(SME calibration, adversarial red-teaming, safety, bias & fairness audits). A regression-blocking release gate governs "
     "every promotion, and failures feed back into the golden datasets.")
image("18-evaluation.png",width=6.7,caption="Measured quality — offline, online, and adversarial.")

# 18 RESPONSIBLE AI
h1("18. Responsible AI & Governance")
para("Governance follows Microsoft's Responsible AI pillars, operationalized through an AI use-case intake with risk-tiering, "
     "mandatory human-in-the-loop for consequential decisions, model/system cards, Content Safety, audit trails, red-teaming, "
     "AI incident response, and an AI governance board.")
make_table(["Tier","Examples","Controls"],
           [["High","Hiring decisions, collections, PI Index scoring","Full HITL, bias audits, legal sign-off, appeals"],
            ["Medium","Customer voice answers","Guardrails + sampled human QA + monitoring"],
            ["Low","Internal drafting, summaries","Standard guardrails + spot checks"]],widths=[Inches(1.0),Inches(2.8),Inches(2.6)])

# 19 OBSERVABILITY
h1("19. Observability & FinOps")
para("A single OpenTelemetry pipeline traces every model call, tool invocation, sub-agent hop and handoff, with evaluations "
     "linked back to the exact trace. FinOps controls cost via token metering and quotas at the gateway, cost showback per "
     "use case, model right-sizing through the router, semantic caching, and budget guardrails. Cost-per-resolved-call and "
     "cost-per-screen are tracked as first-class KPIs.")
make_table(["Example SLO","Target"],[["Voice turn latency (p95)","< 1 second"],["Groundedness","≥ threshold, gated"],
            ["Availability","99.9%"],["Safety-event rate","below alert threshold"]],widths=[Inches(3.2),Inches(3.2)])

# 20 OPERATING MODEL
h1("20. Operating Model & Team")
para("A GenAI Center of Excellence operates a federated hub-and-spoke model: the platform team owns the paved road, "
     "guardrails and standards; Operations and HR spokes own their use cases and outcomes. All roles are AFNI-internal.")
make_table(["Role","Focus"],
           [["Executive sponsor","Funding, priorities, unblock"],["AI product owner (platform)","Paved road, backlog, adoption"],
            ["GenAI architect (lead)","Architecture, standards, review"],["Prompt / agent engineers","Agent design & evaluation"],
            ["GenAIOps engineers","CI/CD, serving, observability"],["Data engineers","Lakehouse, RAG, vectorization"],
            ["RAI / governance officer","Risk tiering, audits, policy"],["Security engineer + FinOps","Zero Trust, cost control"]],
           widths=[Inches(2.4),Inches(4.0)])

# 21 ROADMAP
h1("21. Roadmap & Maturity Model")
para("Delivery follows Crawl → Walk → Run → Fly, advancing maturity from ad-hoc to a governed, then self-service platform.")
image("08-roadmap.png",width=6.7,caption="Crawl → Walk → Run over ~9–12 months, then Fly (self-service at scale).")
make_table(["Phase","Timing","What lands"],
           [["Phase 0","Weeks 0–4","Landing zone, security baseline, paved-road v0, intake"],
            ["Phase 1 · Crawl","Months 1–3","Platform MVP; Voice Agent copilot; PI Index MVP; Hiring screening; eval harness"],
            ["Phase 2 · Walk","Months 4–7","Autonomous voice; PI Index live; Hiring voice pre-screen; GenAIOps CI/CD; CoE; onboard 2 new use cases"],
            ["Phase 3 · Run","Months 8–12","Scale programs/geos; subrogation & knowledge assistant; full governance/DR"],
            ["Fly","12 months +","Self-service onboarding at scale; agent marketplace; A2A ecosystem"]],
           widths=[Inches(1.4),Inches(1.2),Inches(3.8)])

# 22 BOM
h1("22. Reference Tech Stack (Bill of Materials)")
make_table(["Capability","Product / component"],
           [["Agent platform","Microsoft Foundry + Foundry Agent Service"],
            ["Orchestration","Microsoft Agent Framework (AutoGen + Semantic Kernel)"],
            ["Model access & routing","Model Router; Azure OpenAI GPT-5.x; gpt-realtime-1.5"],
            ["Tools & interop","MCP (tools) + A2A (agent-to-agent)"],
            ["Knowledge / RAG","Azure AI Search; AI Document Intelligence"],
            ["Data platform","Microsoft Fabric / OneLake; Event Hubs; Cosmos DB"],
            ["Gateway & compute","Azure API Management; Container Apps / AKS; Functions"],
            ["Security & governance","Entra ID; Key Vault; Purview; Defender for Cloud + AI; Content Safety"],
            ["Observability & CI/CD","Azure Monitor + App Insights + OpenTelemetry; GitHub Actions / Azure DevOps"]],
           widths=[Inches(2.2),Inches(4.2)])
para("Alternatives considered: AWS Bedrock AgentCore and Google Vertex AI Agent Builder are credible; Microsoft Foundry is "
     "recommended as primary given AFNI's Microsoft footprint and Foundry's integrated agent, safety and governance tooling "
     "for regulated workloads. MCP and A2A keep the platform interoperable and portable.")

# 23 BUSINESS CASE
h1("23. Business Case & ROI")
para("All figures are illustrative placeholders, to be replaced with AFNI actuals during Phase 0.",italic=True)
make_table(["Value lever","Initiative / driver","Illustrative impact"],
           [["Platform amortization","every new use case","each onboarding cheaper & faster"],
            ["100% QA coverage & coaching","PI Index","from ~5% sampled to 100%"],
            ["Containment & AHT","Voice Agent","20–40% contained; 15–25% lower AHT"],
            ["Recruiter effort & time-to-fill","Hiring Intelligence","30–50% less screening effort"],
            ["Model cost efficiency","Model Router + caching","cheapest model meeting quality bar"]],
           widths=[Inches(2.4),Inches(1.9),Inches(2.6)])
para("Illustrative payback: 9–15 months, improving with every use case onboarded. Under Gainshare, efficiency improves "
     "shared margin directly.",bold=True,color=NAVY)

# 24 RISKS
h1("24. Risks & Mitigations")
make_table(["Risk","Mitigation"],
           [["Prompt injection / data exfiltration","Prompt shields, untrusted-content isolation, DLP, private networking"],
            ["Hallucination / wrong answers","RAG grounding, groundedness gates, HITL"],
            ["Excessive agency","Least-privilege MCP tools, human approval for irreversible actions"],
            ["Compliance breach (TCPA/PCI/EEOC)","Compliance agent, risk-tiering, bias audits, legal sign-off"],
            ["Unfair scoring (PI Index / hiring)","Fairness monitors, explainability, human calibration & appeals"],
            ["Runaway token cost","APIM metering, Model Router, caching, budget alerts"],
            ["Quality regression on change","Golden-set regression gates, canary + auto-rollback"],
            ["Model / vendor lock-in","Model Router, MCP/A2A interop, portable agents-as-code"]],
           widths=[Inches(2.6),Inches(3.8)])

# 25 RECOMMENDATION
h1("25. Recommendation & Next Steps")
para("Approve a four-week Phase 0 to stand up the platform and onboard the three proof points.",bold=True,color=NAVY)
bullet("Establish the Azure/Foundry landing zone, security baseline and guardrail policy.","1.  ")
bullet("Stand up the paved road: agents-as-code, evaluation gates, observability and FinOps.","2.  ")
bullet("Onboard the three proof points: Voice Agent copilot, PI Index MVP, Hiring screening.","3.  ")
bullet("Publish the use-case intake so the 4th, 5th and 6th use cases self-serve onto the platform.","4.  ")
para("")
para("AFNI · Office of GenAI Architecture — internal & confidential. Build the factory — then let it run.",9,italic=True,color=GRAY,align=WD_ALIGN_PARAGRAPH.CENTER)

out=os.path.join(ROOT,"proposal","Afni-LLMOps-Proposal.docx"); doc.save(out); print(f"Saved: {out}")
