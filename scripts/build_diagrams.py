#!/usr/bin/env python3
"""Generate professional SVG architecture diagrams for the AFNI LLMOps proposal.

Writes .svg files to ../diagrams/. A companion Node script (rasterize.js) converts
them to high-resolution PNGs (via sharp) for embedding in the PPTX and DOCX.
Design is diagram-led: minimal text, strong graphics, one consistent palette.
"""
import os

DIA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "diagrams")
os.makedirs(DIA, exist_ok=True)

# ---- palette ---------------------------------------------------------------
NAVY="#121F3D"; INDIGO="#1B3A6B"; TEAL="#00A6A6"; CYAN="#2EC4D3"
AMBER="#F5A623"; GREEN="#2E9E5B"; PURPLE="#7A4FB5"; ROSE="#D65A7A"
LIGHT="#F4F6FA"; GRAY="#5A6474"; INK="#1C2433"; LINE="#E1E6F0"; WHITE="#FFFFFF"
FONT="Segoe UI, Arial, sans-serif"

def esc(s): return (s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;"))

class SVG:
    def __init__(self, w, h, bg=WHITE):
        self.w=w; self.h=h; self.els=[]; self.bg=bg
    def raw(self, s): self.els.append(s)
    def rect(self, x, y, w, h, fill, rx=0, stroke=None, sw=1.5, opacity=None):
        s=f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}"'
        if stroke: s+=f' stroke="{stroke}" stroke-width="{sw}"'
        if opacity is not None: s+=f' opacity="{opacity}"'
        s+="/>"; self.els.append(s)
    def card(self, x, y, w, h, fill=WHITE, rx=14, stroke=LINE, sw=1.5, shadow=True):
        if shadow:
            self.els.append(f'<rect x="{x}" y="{y+4}" width="{w}" height="{h}" rx="{rx}" fill="#0B1430" opacity="0.10"/>')
        self.rect(x,y,w,h,fill,rx,stroke,sw)
    def toptab(self, x, y, w, h, color, rx=14, tab=6):
        # card with a colored top accent bar
        self.card(x,y,w,h)
        self.els.append(f'<path d="M{x+rx},{y} h{w-2*rx} a{rx},{rx} 0 0 1 {rx},{rx} v{tab} h{-w} v{-tab} a{rx},{rx} 0 0 1 {rx},{-rx} z" fill="{color}"/>')
    def text(self, x, y, s, size=15, color=INK, anchor="start", weight="normal", spacing=None, italic=False):
        st=f'font-family="{FONT}" font-size="{size}" fill="{color}" text-anchor="{anchor}" font-weight="{weight}"'
        if spacing: st+=f' letter-spacing="{spacing}"'
        if italic: st+=' font-style="italic"'
        self.els.append(f'<text x="{x}" y="{y}" {st}>{esc(s)}</text>')
    def tspan_center(self, cx, cy, lines, size=14, color=INK, weight="normal", lh=1.25):
        # multi-line centered block, vertically centered on cy
        n=len(lines); total=(n-1)*size*lh
        y0=cy - total/2 + size*0.34
        for i,ln in enumerate(lines):
            self.text(cx, y0+i*size*lh, ln, size, color, "middle", weight)
    def chip(self, x, y, label, size=12.5, fill="#EAF3F3", color="#0A5C5C", pad=10, h=25):
        w=len(label)*size*0.60 + pad*2
        self.rect(x,y,w,h,fill,rx=h/2)
        self.text(x+w/2, y+h*0.66, label, size, color, "middle", "600")
        return w
    def chiprow(self, x, y, labels, size=12.5, fill="#EAF3F3", color="#0A5C5C", gap=8, h=25):
        cx=x
        for lb in labels:
            w=self.chip(cx,y,lb,size,fill,color,h=h); cx+=w+gap
        return cx
    def arrow(self, x1, y1, x2, y2, color=GRAY, w=2.4, dash=None, head=True):
        d=f' stroke-dasharray="{dash}"' if dash else ""
        m=' marker-end="url(#ah)"' if head else ""
        self.els.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{w}"{d}{m}/>')
    def arrowc(self, x1, y1, x2, y2, color=GRAY, w=2.4):  # colored head
        mid=(x1+x2)/2
        self.els.append(f'<path d="M{x1},{y1} C{mid},{y1} {mid},{y2} {x2},{y2}" fill="none" stroke="{color}" stroke-width="{w}" marker-end="url(#ah)"/>')
    def icon(self, cx, cy, kind, color=WHITE, r=13):
        # simple line icons drawn in a circle badge (badge drawn by caller)
        s=r
        if kind=="mic":
            self.els.append(f'<rect x="{cx-s*0.28}" y="{cy-s*0.6}" width="{s*0.56}" height="{s*0.85}" rx="{s*0.28}" fill="{color}"/>')
            self.els.append(f'<path d="M{cx-s*0.5},{cy} a{s*0.5},{s*0.5} 0 0 0 {s},0" fill="none" stroke="{color}" stroke-width="2"/>')
            self.els.append(f'<line x1="{cx}" y1="{cy+s*0.5}" x2="{cx}" y2="{cy+s*0.8}" stroke="{color}" stroke-width="2"/>')
        elif kind=="gauge":
            self.els.append(f'<path d="M{cx-s*0.7},{cy+s*0.35} a{s*0.7},{s*0.7} 0 1 1 {s*1.4},0" fill="none" stroke="{color}" stroke-width="2.2"/>')
            self.els.append(f'<line x1="{cx}" y1="{cy+s*0.35}" x2="{cx+s*0.45}" y2="{cy-s*0.3}" stroke="{color}" stroke-width="2.2"/>')
        elif kind=="people":
            for dx in (-s*0.32, s*0.32):
                self.els.append(f'<circle cx="{cx+dx}" cy="{cy-s*0.25}" r="{s*0.24}" fill="{color}"/>')
                self.els.append(f'<path d="M{cx+dx-s*0.34},{cy+s*0.55} a{s*0.34},{s*0.34} 0 0 1 {s*0.68},0 z" fill="{color}"/>')
        elif kind=="brain":
            self.els.append(f'<circle cx="{cx}" cy="{cy}" r="{s*0.55}" fill="none" stroke="{color}" stroke-width="2.2"/>')
            self.els.append(f'<line x1="{cx}" y1="{cy-s*0.55}" x2="{cx}" y2="{cy+s*0.55}" stroke="{color}" stroke-width="2"/>')
            self.els.append(f'<circle cx="{cx-s*0.22}" cy="{cy-s*0.08}" r="1.8" fill="{color}"/><circle cx="{cx+s*0.22}" cy="{cy+s*0.12}" r="1.8" fill="{color}"/>')
        elif kind=="shield":
            self.els.append(f'<path d="M{cx},{cy-s*0.7} L{cx+s*0.6},{cy-s*0.4} V{cy+s*0.1} Q{cx+s*0.6},{cy+s*0.6} {cx},{cy+s*0.75} Q{cx-s*0.6},{cy+s*0.6} {cx-s*0.6},{cy+s*0.1} V{cy-s*0.4} Z" fill="none" stroke="{color}" stroke-width="2.2"/>')
        elif kind=="gear":
            self.els.append(f'<circle cx="{cx}" cy="{cy}" r="{s*0.34}" fill="none" stroke="{color}" stroke-width="2.2"/>')
            for a in range(0,360,45):
                import math; rad=math.radians(a)
                x0=cx+math.cos(rad)*s*0.45; y0=cy+math.sin(rad)*s*0.45
                x1=cx+math.cos(rad)*s*0.62; y1=cy+math.sin(rad)*s*0.62
                self.els.append(f'<line x1="{x0}" y1="{y0}" x2="{x1}" y2="{y1}" stroke="{color}" stroke-width="2.2"/>')
        elif kind=="db":
            self.els.append(f'<ellipse cx="{cx}" cy="{cy-s*0.4}" rx="{s*0.55}" ry="{s*0.22}" fill="none" stroke="{color}" stroke-width="2"/>')
            self.els.append(f'<path d="M{cx-s*0.55},{cy-s*0.4} V{cy+s*0.4} a{s*0.55},{s*0.22} 0 0 0 {s*1.1},0 V{cy-s*0.4}" fill="none" stroke="{color}" stroke-width="2"/>')
        elif kind=="flow":
            self.els.append(f'<circle cx="{cx-s*0.5}" cy="{cy}" r="{s*0.2}" fill="{color}"/><circle cx="{cx+s*0.5}" cy="{cy-s*0.4}" r="{s*0.2}" fill="{color}"/><circle cx="{cx+s*0.5}" cy="{cy+s*0.4}" r="{s*0.2}" fill="{color}"/>')
            self.els.append(f'<line x1="{cx-s*0.32}" y1="{cy-s*0.05}" x2="{cx+s*0.32}" y2="{cy-s*0.35}" stroke="{color}" stroke-width="2"/><line x1="{cx-s*0.32}" y1="{cy+s*0.05}" x2="{cx+s*0.32}" y2="{cy+s*0.35}" stroke="{color}" stroke-width="2"/>')
        elif kind=="doc":
            self.els.append(f'<path d="M{cx-s*0.42},{cy-s*0.6} h{s*0.62} l{s*0.24},{s*0.24} v{s*0.96} h{-s*0.86} z" fill="none" stroke="{color}" stroke-width="2"/>')
            for dy in (-0.15,0.1,0.35):
                self.els.append(f'<line x1="{cx-s*0.24}" y1="{cy+s*dy}" x2="{cx+s*0.24}" y2="{cy+s*dy}" stroke="{color}" stroke-width="1.8"/>')
        elif kind=="lock":
            self.els.append(f'<rect x="{cx-s*0.42}" y="{cy-s*0.1}" width="{s*0.84}" height="{s*0.7}" rx="{s*0.12}" fill="none" stroke="{color}" stroke-width="2"/>')
            self.els.append(f'<path d="M{cx-s*0.26},{cy-s*0.1} v{-s*0.22} a{s*0.26},{s*0.26} 0 0 1 {s*0.52},0 v{s*0.22}" fill="none" stroke="{color}" stroke-width="2"/>')
            self.els.append(f'<circle cx="{cx}" cy="{cy+s*0.22}" r="{s*0.09}" fill="{color}"/>')
        elif kind=="check":
            self.els.append(f'<path d="M{cx-s*0.4},{cy} l{s*0.28},{s*0.3} l{s*0.55},{-s*0.6}" fill="none" stroke="{color}" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/>')
        elif kind=="cloud":
            self.els.append(f'<path d="M{cx-s*0.5},{cy+s*0.25} a{s*0.3},{s*0.3} 0 0 1 {s*0.15},{-s*0.55} a{s*0.35},{s*0.35} 0 0 1 {s*0.7},{-s*0.05} a{s*0.28},{s*0.28} 0 0 1 {s*0.1},{s*0.62} z" fill="none" stroke="{color}" stroke-width="2"/>')
        elif kind=="bolt":
            self.els.append(f'<path d="M{cx+s*0.1},{cy-s*0.6} l{-s*0.4},{s*0.7} h{s*0.28} l{-s*0.12},{s*0.5} l{s*0.5},{-s*0.75} h{-s*0.3} z" fill="{color}"/>')
        elif kind=="route":
            self.els.append(f'<circle cx="{cx-s*0.5}" cy="{cy}" r="{s*0.16}" fill="{color}"/>')
            for dy in (-0.42,0,0.42):
                self.els.append(f'<circle cx="{cx+s*0.5}" cy="{cy+s*dy}" r="{s*0.14}" fill="{color}"/>')
                self.els.append(f'<path d="M{cx-s*0.34},{cy} Q{cx},{cy} {cx+s*0.36},{cy+s*dy}" fill="none" stroke="{color}" stroke-width="1.8"/>')
        elif kind=="grid":
            for gx in (-0.35,0.05):
                for gy in (-0.35,0.05):
                    self.els.append(f'<rect x="{cx+s*gx}" y="{cy+s*gy}" width="{s*0.3}" height="{s*0.3}" rx="2" fill="none" stroke="{color}" stroke-width="1.8"/>')
    def badge(self, cx, cy, kind, bg, r=17, icon_color=WHITE):
        self.els.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{bg}"/>')
        self.icon(cx, cy, kind, icon_color, r=r*0.8)
    def save(self, name):
        defs=(f'<defs><marker id="ah" markerWidth="10" markerHeight="10" refX="7" refY="3.2" orient="auto" markerUnits="userSpaceOnUse">'
              f'<path d="M0,0 L8,3.2 L0,6.4 z" fill="{GRAY}"/></marker></defs>')
        head=f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" viewBox="0 0 {self.w} {self.h}">'
        body=f'<rect width="{self.w}" height="{self.h}" fill="{self.bg}"/>'
        out=head+defs+body+"".join(self.els)+"</svg>"
        p=os.path.join(DIA, name+".svg")
        with open(p,"w",encoding="utf-8") as f: f.write(out)
        print("wrote", name+".svg")

def title(d, kicker, ttl, x=60, y=58):
    d.text(x, y-22, kicker.upper(), 15, TEAL, weight="700", spacing="2")
    d.text(x, y+12, ttl, 30, NAVY, weight="800")
    d.rect(x, y+26, 66, 5, AMBER, rx=2.5)

# ============================================================================
# DIAGRAM 1 — Platform reference architecture (layered)
# ============================================================================
def d1_platform():
    d=SVG(1640, 1020, WHITE)
    title(d, "Enterprise GenAI Platform", "Layered reference architecture on Microsoft Foundry")
    layers=[
        ("Experience & channels", ["Voice Live / CCaaS · ACS","Web & chat","Agent-assist desktop","Teams / M365 Copilot","Batch & API"], CYAN, "mic"),
        ("Orchestration & agents", ["Microsoft Agent Framework","Foundry Agent Service","MCP tools · A2A interop","Durable workflows · memory"], TEAL, "flow"),
        ("Models & AI services", ["Model Router (cost/quality)","GPT-5.5 · gpt-realtime-1.5","Model catalog + open-weight","Content Safety"], INDIGO, "route"),
        ("Knowledge & RAG", ["Azure AI Search (hybrid+semantic)","Integrated vectorization","AI Document Intelligence","Grounding & citations"], "#3E5C99", "db"),
        ("Data platform (at scale)", ["Microsoft Fabric / OneLake","Event Hubs (streaming) + batch","Cosmos DB · vector stores","Purview lineage & DLP"], "#4A6AA8", "grid"),
        ("GenAIOps & DevOps", ["Agents-as-code (YAML)","Evaluation-in-CI · gates","GitHub Actions / Azure DevOps","Container Apps / AKS · APIM"], GRAY, "gear"),
        ("Security & governance", ["Entra ID · Key Vault","Defender for Cloud + AI","Microsoft Purview","Private endpoints / VNet"], NAVY, "shield"),
        ("Observability & FinOps", ["Unified OpenTelemetry tracing","Quality · latency · drift · safety","Token metering","Cost showback"], "#2E7D7D", "gauge"),
    ]
    x=60; w=1520; y=104; lh=108; gap=8
    for name, chips, color, ic in layers:
        d.card(x, y, w, lh-gap)
        d.rect(x, y, 300, lh-gap, color, rx=14)
        d.rect(x+286, y, 14, lh-gap, color)  # square off right edge of label
        d.badge(x+40, y+(lh-gap)/2, ic, "rgba(255,255,255,0.18)", r=19, icon_color=WHITE)
        d.tspan_center(x+185, y+(lh-gap)/2, name.split(" & "), 17, WHITE, "700") if " & " in name else d.text(x+70,y+(lh-gap)/2+6,name,17,WHITE,weight="700")
        # chips
        cx=x+330; cy=y+(lh-gap)/2-13
        row=cx
        for i,c in enumerate(chips):
            cw=d.chip(row, cy, c, 13, LIGHT, INDIGO, h=27)
            row+=cw+9
            if row> x+w-180 and i < len(chips)-1:
                row=cx; cy+=33
        y+=lh
    d.save("01-platform-architecture")

# ============================================================================
# DIAGRAM 2 — Multi-agent orchestration pattern
# ============================================================================
def d2_agents():
    d=SVG(1640, 1000, WHITE)
    title(d, "Multi-Agent Systems", "One orchestrator, seven specialist agents — reused everywhere")
    # channel chips
    d.text(820, 118, "Requests from channels", 15, GRAY, "middle", "600")
    d.chiprow(560, 132, ["Voice / CCaaS","Chat","Agent desktop","ATS / HR"], 13, LIGHT, INDIGO, gap=10, h=27)
    # memory (left) and tools (right)
    d.toptab(60, 190, 250, 104, PURPLE)
    d.badge(100, 250, "db", PURPLE, r=18); d.text(130, 238, "Memory", 15.5, NAVY, weight="700")
    d.tspan_center(210, 258, ["Cosmos DB","short + long term"], 12.5, GRAY)
    d.toptab(1330, 190, 250, 104, "#4A6AA8")
    d.badge(1370, 250, "gear", "#4A6AA8", r=18); d.text(1400, 238, "Tools", 15.5, NAVY, weight="700")
    d.tspan_center(1480, 258, ["CRM · HRIS","billing · systems"], 12.5, GRAY)
    # orchestrator
    ox,oy,ow,oh=620,196,400,96
    d.card(ox,oy,ow,oh,NAVY,rx=16,stroke=NAVY)
    d.badge(ox+52, oy+oh/2, "flow", "rgba(255,255,255,0.16)", r=22)
    d.text(ox+92, oy+42, "ORCHESTRATOR", 20, WHITE, weight="800")
    d.text(ox+92, oy+68, "supervisor · routing · policy · hand-off", 13.5, CYAN)
    d.arrow(310, 242, 618, 242, PURPLE, 2.2, dash="5,5")
    d.arrow(1330, 242, 1022, 242, "#4A6AA8", 2.2, dash="5,5")
    d.arrow(820, 160, 820, 194, GRAY, 2.2)
    # specialist agents
    agents=[("Intent / Router","classify & route",TEAL,"flow"),
            ("Knowledge / RAG","grounded, cited answers",INDIGO,"db"),
            ("Action / Tooling","act on systems of record","#4A6AA8","gear"),
            ("Compliance","disclosures · PII · TCPA",AMBER,"shield"),
            ("Sentiment","emotion & escalation cues",GREEN,"brain"),
            ("Escalation / Handoff","warm transfer to human",PURPLE,"people"),
            ("Summarize / QA & Score","disposition · scoring","#2E7D7D","gauge")]
    cw,ch,gap=340,120,30
    row1=agents[:4]; row2=agents[4:]
    def draw_row(items, y):
        tot=len(items)*cw+(len(items)-1)*gap; sx=(1640-tot)/2
        for i,(t,sub,c,ic) in enumerate(items):
            x=sx+i*(cw+gap)
            d.toptab(x,y,cw,ch,c)
            d.badge(x+40,y+ch/2+4,ic,c,r=20)
            d.text(x+76,y+ch/2-6,t,17,NAVY,weight="700")
            d.text(x+76,y+ch/2+20,sub,13,GRAY)
            d.arrow(820, 292, x+cw/2, y-2, GRAY, 1.8)
        return sx
    draw_row(row1, 380)
    draw_row(row2, 540)
    # guardrail band
    by=720
    d.rect(60,by,1520,150,LIGHT,rx=16,stroke=LINE)
    d.rect(60,by,1520,46,NAVY,rx=16)
    d.rect(60,by+30,1520,16,NAVY)
    d.text(820,by+30,"DETERMINISTIC GUARDRAILS WRAP EVERY (PROBABILISTIC) AGENT",14,WHITE,"middle","700",spacing="1")
    d.chiprow(150, by+78, ["Azure AI Content Safety","Prompt shields","PII detection & redaction","Groundedness checks","Do-not-say / must-say policy","Human-in-the-loop checkpoints"], 13.5, WHITE, INDIGO, gap=14, h=34)
    d.text(820, by+134, "Patterns: supervisor · sequential · concurrent · hand-off · group-chat · reflection / critic", 13.5, GRAY, "middle", italic=True)
    d.save("02-multi-agent")

# ============================================================================
# DIAGRAM 3 — Three initiatives on one platform
# ============================================================================
def d3_three():
    d=SVG(1640, 940, WHITE)
    title(d, "The Strategy", "Three flagship initiatives · one shared platform")
    pillars=[("Voice Agent","Real-time voice automation & assist",TEAL,"mic",
              ["Agent-assist copilot for live reps","Autonomous voice for containable calls","Sub-second speech-to-speech","TCPA / PCI guardrails on every turn"]),
             ("Performance Intelligence Index","100% interaction performance scoring",INDIGO,"gauge",
              ["Scores every interaction, not samples","Seven explainable analysis dimensions","Composite, comparable PI Index","Drives coaching & QA calibration"]),
             ("Hiring Intelligence","Fair, high-volume recruitment",AMBER,"people",
              ["Screening & résumé ranking","Conversational + voice pre-screen","Interview scoring (assist only)","Fairness first — humans decide"])]
    pw,ph,gap=460,470,70; y=140
    xs=[60,60+pw+gap,60+2*(pw+gap)]
    for (t,sub,c,ic,bl),x in zip(pillars,xs):
        d.toptab(x,y,pw,ph,c,tab=10)
        d.badge(x+pw/2, y+78, ic, c, r=34, icon_color=WHITE)
        d.tspan_center(x+pw/2, y+150, [t] if len(t)<22 else t.split(" ",1), 21, NAVY, "800")
        d.text(x+pw/2, y+ (150 if len(t)<22 else 176), "", 1, NAVY, "middle")
        d.text(x+pw/2, y+205, sub, 14, c, "middle", "600")
        yy=y+250
        for b in bl:
            d.els.append(f'<circle cx="{x+40}" cy="{yy-5}" r="4" fill="{c}"/>')
            d.text(x+58, yy, b, 14.5, INK)
            yy+=42
    # synergy arrow: Voice Agent -> PI Index (adjacent gap only, no text overlap)
    d.arrow(xs[0]+pw+4, y+150, xs[1]-4, y+150, GRAY, 2.4)
    d.text((xs[0]+pw+xs[1])/2, y+126, "100%", 12.5, GRAY, "middle", "700")
    d.text((xs[0]+pw+xs[1])/2, y+180, "interaction", 12, GRAY, "middle", italic=True)
    d.text((xs[0]+pw+xs[1])/2, y+196, "data", 12, GRAY, "middle", italic=True)
    # synergy: PI/agents reused by Hiring (adjacent gap)
    d.arrow(xs[1]+pw+4, y+150, xs[2]-4, y+150, GRAY, 2.4)
    d.text((xs[1]+pw+xs[2])/2, y+126, "shared", 12.5, GRAY, "middle", "700")
    d.text((xs[1]+pw+xs[2])/2, y+180, "agents &", 12, GRAY, "middle", italic=True)
    d.text((xs[1]+pw+xs[2])/2, y+196, "voice stack", 12, GRAY, "middle", italic=True)
    # platform base
    by=650
    d.card(60,by,1520,120,INDIGO,rx=18,stroke=INDIGO)
    d.text(90,by+50,"Shared multi-agent LLMOps platform",22,WHITE,weight="800")
    d.text(90,by+80,"Azure AI Foundry · Agent Service · Content Safety · Evaluation · Observability · Governance",14,CYAN)
    for x in xs:
        d.arrow(x+pw/2, by, x+pw/2, y+ph+2, "#B9C4DA", 2, head=False)
    d.text(1550, by+95, "build once · reuse everywhere", 13, "#B9C4DA", "end", italic=True)
    d.save("03-three-initiatives")

# ============================================================================
# DIAGRAM 4 — Voice Agent real-time call flow
# ============================================================================
def d4_voice():
    d=SVG(1640, 760, WHITE)
    title(d, "Voice Agent", "End-to-end real-time call flow")
    stages=[("Caller","inbound / outbound",GRAY,"people"),
            ("Telephony / CCaaS","Genesys · NICE · ACS",INDIGO,"flow"),
            ("Realtime STT","gpt-realtime speech",TEAL,"mic"),
            ("Orchestrator","route + policy",NAVY,"flow"),
            ("Agents + RAG + Tools","answer & act",CYAN,"brain"),
            ("Systems of record","CRM · billing","#4A6AA8","db"),
            ("Reply (TTS) / Handoff","voice or warm transfer",GREEN,"mic")]
    bw,bh,gap=180,170,42; y=180; sx=64
    for i,(t,sub,c,ic) in enumerate(stages):
        x=sx+i*(bw+gap)
        d.toptab(x,y,bw,bh,c,tab=8)
        d.badge(x+bw/2, y+58, ic, c, r=24)
        d.tspan_center(x+bw/2, y+108, t.split(" / ") if " / " in t and len(t)>16 else [t] if len(t)<15 else t.split(" ",1), 14.5, NAVY, "700")
        d.text(x+bw/2, y+148, sub, 12, GRAY, "middle")
        if i<len(stages)-1:
            d.arrow(x+bw+6, y+bh/2, x+bw+gap-6, y+bh/2, AMBER, 2.6)
    # guardrail band
    by=420
    d.rect(64,by,1512,92,LIGHT,rx=14,stroke=LINE)
    d.badge(110,by+46,"shield",NAVY,r=20)
    d.text(150,by+40,"Every turn",15,NAVY,weight="700")
    d.chiprow(150, by+55, ["Content Safety","PII redaction","TCPA consent","PCI pause / mask","Full tracing"], 13, WHITE, INDIGO, gap=12, h=30)
    d.text(1540, by+52, "sub-second latency budget", 13.5, TEAL, "end", "700")
    # feeds PI index
    fy=560
    d.arrow(1100, 350, 1100, fy-4, GRAY, 2, dash="5,5")
    d.rect(900,fy,400,70,"#EEF3FF",rx=12,stroke="#C9D6F0")
    d.badge(940,fy+35,"gauge",INDIGO,r=18)
    d.text(970,fy+30,"Transcripts & signals feed",13.5,NAVY,weight="600")
    d.text(970,fy+52,"the Performance Intelligence Index",13.5,INDIGO,weight="700")
    d.save("04-voice-flow")

# ============================================================================
# DIAGRAM 5 — Performance Intelligence Index architecture
# ============================================================================
def d5_piindex():
    d=SVG(1640, 980, WHITE)
    title(d, "Performance Intelligence Index", "From 100% of interactions to one explainable score")
    # Col A - interactions
    ax,ay,aw=60,150,250
    d.toptab(ax,ay,aw,470,INDIGO)
    d.badge(ax+aw/2,ay+66,"flow",INDIGO,r=30)
    d.tspan_center(ax+aw/2,ay+140,["100% of","interactions"],20,NAVY,"800")
    for i,lb in enumerate(["Voice transcripts","Chat & messaging","Dispositions","CRM outcomes","QA metadata"]):
        yy=ay+205+i*48
        d.rect(ax+24,yy,aw-48,36,LIGHT,rx=8)
        d.text(ax+aw/2,yy+23,lb,13.5,INDIGO,"middle","600")
    # Col B - analysis agents
    bx,bw=360,330
    d.toptab(bx,ay,bw,470,TEAL)
    d.text(bx+bw/2,ay+42,"Multi-agent analysis",17,NAVY,"middle","800")
    dims=["Compliance adherence","Communication & empathy","Resolution / FCR","Script & process","Sentiment trajectory","Efficiency (AHT)","Business outcome"]
    for i,dm in enumerate(dims):
        yy=ay+64+i*56
        d.rect(bx+22,yy,bw-44,44,WHITE,rx=9,stroke=LINE)
        d.els.append(f'<circle cx="{bx+44}" cy="{yy+22}" r="6" fill="{TEAL}"/>')
        d.text(bx+62,yy+27,dm,13.8,INK,weight="600")
    # Col C - scoring
    cx,cw=730,230
    d.toptab(cx,ay+120,cw,230,AMBER)
    d.badge(cx+cw/2,ay+180,"gear",AMBER,r=26)
    d.tspan_center(cx+cw/2,ay+255,["Weighted","scoring engine"],17,NAVY,"800")
    d.text(cx+cw/2,ay+300,"calibrated · explainable",12.5,GRAY,"middle")
    # Col D - scorecard
    dx,dw=1010,570
    d.toptab(dx,ay,dw,470,NAVY,tab=10)
    d.text(dx+40,ay+56,"PI Index — composite score",17,NAVY,weight="800")
    # big number
    d.els.append(f'<circle cx="{dx+130}" cy="{ay+200}" r="86" fill="none" stroke="{LINE}" stroke-width="16"/>')
    d.els.append(f'<circle cx="{dx+130}" cy="{ay+200}" r="86" fill="none" stroke="{GREEN}" stroke-width="16" stroke-linecap="round" stroke-dasharray="470 540" transform="rotate(-90 {dx+130} {ay+200})"/>')
    d.text(dx+130,ay+210,"87",52,NAVY,"middle","800")
    d.text(dx+130,ay+250,"of 100",13,GRAY,"middle")
    # dimension bars
    bars=[("Compliance",92,GREEN),("Empathy",85,TEAL),("Resolution",88,TEAL),("Efficiency",79,AMBER),("Outcome",90,GREEN)]
    for i,(lb,val,c) in enumerate(bars):
        yy=ay+120+i*58
        bxx=dx+260
        d.text(bxx,yy+4,lb,13.5,INK,weight="600")
        d.rect(bxx,yy+14,250,14,LIGHT,rx=7)
        d.rect(bxx,yy+14,250*val/100,14,c,rx=7)
        d.text(bxx+270,yy+16,str(val),13.5,NAVY,weight="700")
    # arrows
    d.arrow(ax+aw+6, 385, bx-6, 385, GRAY, 2.4)
    d.arrow(bx+bw+6, 385, cx-6, 385, GRAY, 2.4)
    d.arrow(cx+cw+6, 385, dx-6, 385, GRAY, 2.4)
    # outputs band
    oy=690
    d.text(60,oy-4,"Outputs",15,NAVY,weight="800")
    outs=[("Coaching recommendations",TEAL),("QA calibration",INDIGO),("Gainshare / performance reporting",AMBER),("Anomaly & risk alerts",ROSE)]
    x=60
    for t,c in outs:
        w=len(t)*9.2+80
        d.toptab(x,oy+10,w,80,c)
        d.badge(x+34,oy+52,"gauge",c,r=16)
        d.text(x+60,oy+56,t,14.5,NAVY,weight="600")
        x+=w+24
    d.arrow(dx+dw/2, ay+470+2, dx+dw/2, oy+8, GRAY, 2, head=True)
    d.save("05-pi-index")

# ============================================================================
# DIAGRAM 6 — Hiring Intelligence funnel
# ============================================================================
def d6_hiring():
    d=SVG(1640, 820, WHITE)
    title(d, "Hiring Intelligence", "An agent at every stage — humans make the decisions")
    stages=[("JD generation","inclusive postings","brain"),
            ("Sourcing & ranking","parse & rank résumés","people"),
            ("Conversational screen","chat + voice pre-screen","mic"),
            ("Scheduling","calendar / ATS","gear"),
            ("Interview scoring","structured · assist","gauge"),
            ("Offer & onboarding","faster, consistent","flow")]
    grad=[CYAN,TEAL,"#1E8E8E",INDIGO,"#3E5C99","#4A6AA8"]
    bw,bh,gap=230,180,26; y=170; sx=60
    for i,((t,sub,ic),c) in enumerate(zip(stages,grad)):
        x=sx+i*(bw+gap)
        d.toptab(x,y,bw,bh,c,tab=8)
        d.els.append(f'<circle cx="{x+38}" cy="{y+40}" r="16" fill="{c}"/>')
        d.text(x+38,y+46,str(i+1),16,WHITE,"middle","800")
        d.badge(x+bw-40,y+40,ic,c,r=17)
        d.tspan_center(x+bw/2,y+96,[t] if len(t)<16 else t.split(" ",1),15.5,NAVY,"700")
        d.text(x+bw/2,y+138,sub,12.5,GRAY,"middle")
        d.rect(x+30,y+150,bw-60,26,LIGHT,rx=13)
        d.text(x+bw/2,y+167,"AI agent",12,c,"middle","700")
        if i<len(stages)-1:
            d.arrow(x+bw+3,y+bh/2,x+bw+gap-3,y+bh/2,AMBER,2.6)
    # candidate fit callout
    d.rect(1120,y+bh+30,460,54,"#EEF3FF",rx=12,stroke="#C9D6F0")
    d.badge(1158,y+bh+57,"gauge",INDIGO,r=17)
    d.text(1188,y+bh+52,"Candidate Fit signal",14,NAVY,weight="700")
    d.text(1188,y+bh+72,"job-related · explainable · advisory",12.5,GRAY)
    # fairness rail
    fy=560
    d.rect(60,fy,1520,150,"#FBF3E4",rx=16,stroke="#F0DFBF")
    d.rect(60,fy,1520,46,AMBER,rx=16); d.rect(60,fy+30,1520,16,AMBER)
    d.text(820,fy+30,"FAIRNESS  &  HUMAN-IN-THE-LOOP  —  AI ASSISTS, HUMANS DECIDE",14.5,"#5A3D00","middle","800",spacing="0.5")
    d.chiprow(120,fy+78,["EEOC","NYC Local Law 144 bias audit","IL AI Video Interview Act","EU AI Act (high-risk)","GDPR","Candidate notice & consent"],13.5,WHITE,"#8A5A00",gap=14,h=34)
    d.text(820,fy+134,"No autonomous rejection · continuous adverse-impact monitoring · explainable decisions",13.5,"#7A5200","middle",italic=True)
    d.save("06-hiring-intelligence")

# ============================================================================
# DIAGRAM 7 — LLMOps lifecycle loop
# ============================================================================
def d7_lifecycle():
    import math
    d=SVG(1180, 1000, WHITE)
    title(d, "LLMOps Lifecycle", "A continuous, governed improvement loop")
    cx,cy,R=590,560,320
    nodes=[("Curate","data & knowledge",CYAN,"db"),
           ("Engineer","versioned prompts & agents",TEAL,"gear"),
           ("Evaluate","offline · online · red-team",INDIGO,"gauge"),
           ("Ship","CI/CD · canary · rollback","#3E5C99","flow"),
           ("Serve","gateway · quotas · cache",GRAY,"gear"),
           ("Observe","quality · cost · drift",GREEN,"gauge")]
    pos=[]
    for i in range(6):
        a=math.radians(-90+i*60)
        pos.append((cx+math.cos(a)*R, cy+math.sin(a)*R))
    # arrows around loop
    for i in range(6):
        x1,y1=pos[i]; x2,y2=pos[(i+1)%6]
        ang=math.atan2(y2-y1,x2-x1)
        sxp=x1+math.cos(ang)*95; syp=y1+math.sin(ang)*70
        exp=x2-math.cos(ang)*95; eyp=y2-math.sin(ang)*70
        mx,my=(sxp+exp)/2+(cy-(y1+y2)/2)*0.0, (syp+eyp)/2
        d.els.append(f'<path d="M{sxp},{syp} Q{(sxp+exp)/2+(cx-(x1+x2)/2)*0.12},{(syp+eyp)/2+(cy-(y1+y2)/2)*0.12} {exp},{eyp}" fill="none" stroke="{AMBER}" stroke-width="3" marker-end="url(#ah)"/>')
    # center
    d.els.append(f'<circle cx="{cx}" cy="{cy}" r="150" fill="{NAVY}"/>')
    d.badge(cx,cy-40,"shield","rgba(255,255,255,0.15)",r=26)
    d.tspan_center(cx,cy+40,["Governance &","Responsible AI"],20,WHITE,"800")
    # nodes
    for (t,sub,c,ic),(x,y) in zip(nodes,pos):
        w,h=210,120
        d.toptab(x-w/2,y-h/2,w,h,c,tab=7)
        d.badge(x-w/2+38,y,ic,c,r=20)
        d.text(x-w/2+70,y-6,t,18,NAVY,weight="800")
        d.text(x-w/2+70,y+18,sub,11.5,GRAY)
    d.save("07-llmops-lifecycle")

# ============================================================================
# DIAGRAM 8 — Roadmap timeline
# ============================================================================
def d8_roadmap():
    d=SVG(1640, 720, WHITE)
    title(d, "Roadmap", "Crawl → Walk → Run  ·  ~9–12 months")
    phases=[("Phase 0","Weeks 0–4",GRAY,["Landing zone & security baseline","Use-case intake & metrics","Data access & guardrail policy"]),
            ("Phase 1 · Crawl","Months 1–3",TEAL,["Voice Agent copilot (1 program)","PI Index MVP on historical data","Hiring screening pilot"]),
            ("Phase 2 · Walk","Months 4–7",INDIGO,["Autonomous voice (scoped calls)","PI Index live + coaching","Hiring voice pre-screen · CoE · FinOps"]),
            ("Phase 3 · Run","Months 8–12",GREEN,["Scale across programs & geos","Add subrogation & knowledge assistant","Full governance · DR · flywheel"])]
    cw,gap=360,26; y=170; sx=60
    # timeline base
    d.rect(60,y-26,1520,6,LINE,rx=3)
    for i,(name,when,c,bl) in enumerate(phases):
        x=sx+i*(cw+gap)
        d.els.append(f'<circle cx="{x+cw/2}" cy="{y-23}" r="10" fill="{c}"/>')
        d.card(x,y,cw,380)
        d.rect(x,y,cw,72,c,rx=14); d.rect(x,y+56,cw,16,c)
        d.text(x+28,y+34,name,18,WHITE,weight="800")
        d.text(x+28,y+58,when,13.5,WHITE)
        yy=y+112
        for b in bl:
            d.els.append(f'<circle cx="{x+34}" cy="{yy-5}" r="4.5" fill="{c}"/>')
            # wrap long lines
            words=b.split(" "); line=""; lines=[]
            for w in words:
                if len(line+" "+w)>30: lines.append(line); line=w
                else: line=(line+" "+w).strip()
            lines.append(line)
            for j,ln in enumerate(lines):
                d.text(x+52,yy+j*22,ln,13.8,INK)
            yy+=len(lines)*22+22
    d.text(820, y+410, "Value delivered from Phase 1 — each phase has explicit exit criteria before the next begins.",13.5,GRAY,"middle",italic=True)
    # big arrow
    d.els.append(f'<path d="M1500,{y-23} l24,0 l-8,-8 m8,8 l-8,8" stroke="{NAVY}" stroke-width="3" fill="none"/>')
    d.save("08-roadmap")

def vtext(d,x,y,s,size,color,weight="700",spacing=None):
    sp=f' letter-spacing="{spacing}"' if spacing else ""
    d.raw(f'<text x="{x}" y="{y}" transform="rotate(-90 {x} {y})" font-family="{FONT}" font-size="{size}" fill="{color}" text-anchor="middle" font-weight="{weight}"{sp}>{esc(s)}</text>')

# ============================================================================
# DIAGRAM 9 — Enterprise GenAI Framework overview (HERO: build the factory)
# ============================================================================
def d9_framework():
    d=SVG(1660, 1010, WHITE)
    title(d, "The Framework", "One reusable platform — onboard any GenAI use case")
    # cross-cutting rails
    d.card(60,120,150,820,NAVY,rx=16,stroke=NAVY)
    d.badge(135,175,"shield","rgba(255,255,255,0.16)",r=22); vtext(d,120,560,"Security & Governance",20,WHITE,"800"); vtext(d,150,560,"Zero Trust · Responsible AI",12.5,CYAN,"600")
    d.card(1450,120,150,820,"#2E7D7D",rx=16,stroke="#2E7D7D")
    d.badge(1525,175,"gear","rgba(255,255,255,0.18)",r=22); vtext(d,1510,560,"GenAIOps · Observability",20,WHITE,"800"); vtext(d,1540,560,"CI/CD · FinOps · Evaluation",12.5,"#CFF0F0","600")
    MX=240; MW=1180
    # top: use cases
    d.text(MX,168,"USE CASES — onboarded via the paved road",14,GRAY,weight="800",spacing="1")
    ucs=[("Voice Agent",TEAL,"mic"),("Performance Intelligence Index",INDIGO,"gauge"),("Hiring Intelligence",AMBER,"people")]
    tw=(MW-3*20)/4
    for i,(t,c,ic) in enumerate(ucs):
        x=MX+i*(tw+20); d.toptab(x,182,tw,96,c,tab=7)
        d.badge(x+34,182+48,ic,c,r=17); d.tspan_center(x+tw/2+18,182+48,[t] if len(t)<20 else t.split(" ",1),13.5,NAVY,"700")
    # any future
    x=MX+3*(tw+20); d.rect(x,182,tw,96,"#F0F3F9",rx=14,stroke="#B9C4DA",sw=2)
    d.raw(f'<rect x="{x}" y="182" width="{tw}" height="96" rx="14" fill="none" stroke="#8FA0BE" stroke-width="2" stroke-dasharray="7,6"/>')
    d.tspan_center(x+tw/2,182+48,["+ Any future","use case"],15,"#5A6B86","800")
    # pattern catalog band
    py=308
    d.rect(MX,py,MW,86,LIGHT,rx=12,stroke=LINE)
    d.text(MX+18,py+30,"GenAI PATTERN CATALOG  ·  beyond chatbots",13,INDIGO,weight="800",spacing="0.5")
    d.chiprow(MX+18,py+46,["RAG","Agentic workflow","Doc intelligence","Batch analytics","Multimodal","Decision support","Real-time voice","Copilot"],12.5,WHITE,INDIGO,gap=10,h=28)
    # platform capabilities
    cy0=428
    d.text(MX,cy0-6,"REUSABLE PLATFORM CAPABILITIES",14,GRAY,weight="800",spacing="1")
    caps=[("Orchestration & agents","Agent Framework · durable · memory",TEAL,"flow"),
          ("Models & Model Router","GPT-5.x · realtime · cost/quality",INDIGO,"route"),
          ("Knowledge & RAG","AI Search · vectorization",'#3E5C99',"db"),
          ("Data platform at scale","Fabric / OneLake · streaming",'#4A6AA8',"grid"),
          ("Tools & interop","MCP tools · A2A agents",PURPLE,"gear")]
    cw=(MW-4*18)/5
    for i,(t,sub,c,ic) in enumerate(caps):
        x=MX+i*(cw+18); d.toptab(x,cy0+12,cw,150,c,tab=7)
        d.badge(x+cw/2,cy0+62,ic,c,r=22)
        d.tspan_center(x+cw/2,cy0+108,t.split(" & ") if " & " in t else [t] if len(t)<16 else t.split(" ",1),13.5,NAVY,"700")
        d.tspan_center(x+cw/2,cy0+140,[sub],10.5,GRAY)
    # onboarding golden-path strip
    gy=640
    d.rect(MX,gy,MW,66,"#EEF3FF",rx=12,stroke="#C9D6F0")
    d.text(MX+18,gy+27,"PAVED ROAD",12.5,INDIGO,weight="800")
    steps=["Intake","Tier","Blueprint","Assemble","Evaluate","Deploy","Operate","Improve"]
    sx=MX+150
    for i,st in enumerate(steps):
        d.chip(sx,gy+20,st,12.5,WHITE,INDIGO,h=28)
        if i<len(steps)-1: d.text(sx+96,gy+40,"›",16,AMBER,"middle","800")
        sx+=118
    # base foundation
    by=730
    d.card(MX,by,MW,90,INDIGO,rx=16,stroke=INDIGO)
    d.badge(MX+45,by+45,"cloud","rgba(255,255,255,0.16)",r=20)
    d.text(MX+80,by+40,"Microsoft Foundry",19,WHITE,weight="800")
    d.text(MX+80,by+66,"Agent Service · Model Router · unified tracing & evaluation · Content Safety — on Azure",12.5,CYAN)
    d.text(MX+MW-20,by+52,"build the factory, not just the features",12.5,"#9FB0CC","end",italic=True)
    # arrows down
    for i in range(5):
        x=MX+i*((MW-4*18)/5+18)+((MW-4*18)/5)/2
        d.arrow(x,gy+66,x,by-2,"#B9C4DA",1.6,head=False)
    d.text(MX,by+120,"Use cases plug into the platform; each new one inherits security, evaluation, observability and cost controls by default.",12.5,GRAY,italic=True)
    d.save("09-framework")

# ============================================================================
# DIAGRAM 10 — Use-case onboarding golden path
# ============================================================================
def d10_onboarding():
    d=SVG(1660, 820, WHITE)
    title(d, "Use-Case Onboarding", "The paved road — from idea to production in weeks")
    steps=[("Intake","request & value hypothesis","flow"),("Value & Risk tier","impact × risk → controls","gauge"),
           ("Blueprint","pick a pattern","grid"),("Assemble","reusable building blocks","gear"),
           ("Evaluate","gates: quality·safety·cost","check"),("Deploy","canary / blue-green","route"),
           ("Operate","observe · FinOps","cloud"),("Improve","feedback → datasets","brain")]
    n=len(steps); bw=176; gap=22; sx=60; y=150; bh=140
    for i,(t,sub,ic) in enumerate(steps):
        x=sx+i*(bw+gap); c=TEAL if i<4 else INDIGO
        d.toptab(x,y,bw,bh,c,tab=7)
        d.els.append(f'<circle cx="{x+34}" cy="{y+38}" r="15" fill="{c}"/>'); d.text(x+34,y+43,str(i+1),15,WHITE,"middle","800")
        d.badge(x+bw-38,y+38,ic,c,r=16)
        d.tspan_center(x+bw/2,y+86,[t] if len(t)<14 else t.split(" ",1),14.5,NAVY,"700")
        d.text(x+bw/2,y+124,sub,11,GRAY,"middle")
        if i<n-1: d.arrow(x+bw+3,y+bh/2,x+bw+gap-3,y+bh/2,AMBER,2.6)
    # building blocks tray feeding "Assemble" (step 4, index 3)
    ty=400
    d.text(60,ty-6,"REUSABLE BUILDING BLOCKS  ·  capability catalog",14,GRAY,weight="800",spacing="0.5")
    blocks=["Agent & workflow templates (YAML)","MCP tool / connector library","Prompt & policy libraries","Guardrail packs","Golden datasets + eval suites","IaC modules","RAG ingestion templates","Dashboards"]
    d.rect(60,ty+12,1540,110,LIGHT,rx=14,stroke=LINE)
    cx=90; cyy=ty+30
    for i,b in enumerate(blocks):
        w=d.chip(cx,cyy,b,13,WHITE,INDIGO,h=32); cx+=w+14
        if cx>1500 and i<len(blocks)-1: cx=90; cyy+=44
    ax=sx+3*(bw+gap)+bw/2
    d.arrow(ax,ty+12,ax,y+bh+3,GRAY,2.2,dash="5,5")
    d.text(ax+10,ty+6,"assemble from catalog",11.5,GRAY,italic=True)
    # improve -> intake loop
    lx0=sx+7*(bw+gap)+bw/2; lx1=sx+bw/2; ly=y+bh+40
    d.raw(f'<path d="M{lx0},{y+bh+3} V{ly} H{lx1} V{y+bh+3}" fill="none" stroke="{GREEN}" stroke-width="2.4" stroke-dasharray="6,5" marker-end="url(#ah)"/>')
    d.text((lx0+lx1)/2,ly-8,"continuous improvement — production feedback becomes the next golden dataset",12.5,GREEN,"middle",italic=True)
    d.text(60,ty+150,"Security, compliance, evaluation and observability are inherited by default at every step — teams focus on the use case, not the plumbing.",12.5,NAVY,weight="600")
    d.save("10-onboarding")

# ============================================================================
# DIAGRAM 11 — GenAI pattern catalog (beyond chatbots)
# ============================================================================
def d11_patterns():
    d=SVG(1660, 900, WHITE)
    title(d, "Pattern Catalog", "GenAI is far more than chatbots")
    pats=[("Conversational copilot","chat & voice assist",TEAL,"mic"),
          ("Agentic workflow","multi-step, tool-using, durable",INDIGO,"flow"),
          ("Retrieval-augmented (RAG)","grounded answers over knowledge","#3E5C99","db"),
          ("Document intelligence","extract · classify · validate",PURPLE,"doc"),
          ("Batch summarization & analytics","100% interaction analysis",AMBER,"grid"),
          ("Structured extraction","unstructured → structured data",GREEN,"doc"),
          ("Multimodal","speech · image · document","#4A6AA8","brain"),
          ("Decision support & forecasting","next-best-action · propensity",ROSE,"gauge"),
          ("Code & developer assist","tooling · tests · migration","#2E7D7D","gear"),
          ("Real-time voice","speech-to-speech agents",CYAN,"mic")]
    cols=5; cw=296; ch=210; gapx=20; gapy=24; sx=60; sy=150
    for i,(t,sub,c,ic) in enumerate(pats):
        r=i//cols; cc=i%cols; x=sx+cc*(cw+gapx); y=sy+r*(ch+gapy)
        d.toptab(x,y,cw,ch,c,tab=8)
        d.badge(x+42,y+52,ic,c,r=22)
        d.tspan_center(x+cw/2+20,y+52,t.split(" & ") if " & " in t and len(t)>18 else [t] if len(t)<22 else t.split(" ",1),15,NAVY,"700")
        d.text(x+24,y+118,sub,12.5,GRAY)
        d.rect(x+24,y+140,cw-48,40,LIGHT,rx=9)
        d.text(x+cw/2,y+165,"reusable blueprint + eval suite",11.5,c,"middle","600")
    d.save("11-patterns")

# ============================================================================
# DIAGRAM 12 — Enterprise multi-agent runtime
# ============================================================================
def d12_runtime():
    d=SVG(1660, 980, WHITE)
    title(d, "Enterprise Agent Runtime", "Durable, governed, interoperable orchestration")
    d.text(830,150,"Orchestration patterns",13,GRAY,"middle","700")
    d.chiprow(560,164,["sequential","concurrent","group-chat","handoff","Magentic"],12.5,LIGHT,INDIGO,gap=10,h=27)
    # orchestrator
    ox,oy,ow,oh=610,210,440,96
    d.card(ox,oy,ow,oh,NAVY,rx=16,stroke=NAVY)
    d.badge(ox+50,oy+oh/2,"flow","rgba(255,255,255,0.16)",r=22)
    d.text(ox+90,oy+40,"ORCHESTRATOR",19,WHITE,weight="800"); d.text(ox+90,oy+66,"Microsoft Agent Framework · agent registry",12.5,CYAN)
    # memory (left)
    d.toptab(60,210,300,150,PURPLE)
    d.badge(100,250,"brain",PURPLE,r=18); d.text(130,238,"Memory",15.5,NAVY,weight="700")
    for i,m in enumerate(["Session memory","User memory","Procedural memory"]):
        d.text(90,278+i*26,"• "+m,12.5,INK)
    d.arrow(360,285,ox-4,285,PURPLE,2.2,dash="5,5")
    # MCP tools + A2A (right)
    d.toptab(1300,210,300,150,"#4A6AA8")
    d.badge(1340,250,"gear","#4A6AA8",r=18); d.text(1370,238,"Tools & interop",15,NAVY,weight="700")
    for i,m in enumerate(["MCP → CRM · HRIS · billing","A2A → cross-team agents","least-privilege scopes"]):
        d.text(1330,278+i*26,"• "+m,12,INK)
    d.arrow(1300,285,ox+ow+4,285,"#4A6AA8",2.2,dash="5,5")
    # specialists
    agents=[("Intent / Router",TEAL,"route"),("Knowledge / RAG",INDIGO,"db"),("Action / Tooling","#4A6AA8","gear"),
            ("Compliance",AMBER,"shield"),("Sentiment",GREEN,"brain"),("Handoff",PURPLE,"people"),("QA & Scoring","#2E7D7D","gauge")]
    cw2=196; gap=20; tot=7*cw2+6*gap; sx=(1660-tot)/2; ay=400
    for i,(t,c,ic) in enumerate(agents):
        x=sx+i*(cw2+gap); d.toptab(x,ay,cw2,110,c,tab=6)
        d.badge(x+34,ay+55,ic,c,r=17); d.tspan_center(x+cw2/2+16,ay+55,[t] if len(t)<13 else t.split(" / "),13,NAVY,"700")
        d.arrow(830,306,x+cw2/2,ay-2,GRAY,1.6)
    # durable workflow strip
    dy=560
    d.rect(60,dy,1540,74,"#FBF3E4",rx=14,stroke="#F0DFBF")
    d.badge(105,dy+37,"gear",AMBER,r=18); d.text(140,dy+32,"Durable execution",15,"#5A3D00",weight="800")
    d.chiprow(140,dy+45,["checkpointing","pause / resume","retries & idempotency","compensation / saga","human-in-the-loop approvals"],12.5,WHITE,"#8A5A00",gap=12,h=30)
    # guardrail + tracing band
    gy=666
    d.rect(60,gy,1540,150,LIGHT,rx=16,stroke=LINE); d.rect(60,gy,1540,44,NAVY,rx=16); d.rect(60,gy+28,1540,16,NAVY)
    d.text(830,gy+29,"DETERMINISTIC GUARDRAILS  +  UNIFIED OPENTELEMETRY TRACING (every model call · tool · sub-agent hop · handoff)",13,WHITE,"middle","700")
    d.chiprow(150,gy+74,["Content Safety / prompt shields","PII redaction","policy (do/ don't say)","groundedness","graduated autonomy","per-hop trace + eval"],13,WHITE,INDIGO,gap=13,h=34)
    d.text(830,gy+130,"Probabilistic agents, wrapped in deterministic controls — with an audit trail for every action.",12.5,GRAY,"middle",italic=True)
    d.save("12-agent-runtime")

# ============================================================================
# DIAGRAM 13 — Security defense-in-depth + OWASP LLM Top 10
# ============================================================================
def d13_security():
    d=SVG(1660, 980, WHITE)
    title(d, "Security by Design", "Zero Trust defense-in-depth for LLM systems")
    layers=[("Identity & network","Entra ID · VNet · private endpoints · no public egress",NAVY),
            ("AI gateway","API Management · auth · rate & cost limits · quotas",INDIGO),
            ("Input guardrails","prompt shields · isolate untrusted content · validation","#2E5A9E"),
            ("Orchestration","least-privilege MCP tools · HITL approvals · graduated autonomy",TEAL),
            ("Output guardrails","output filtering · groundedness · PII redaction","#2E7D7D"),
            ("Data & vectors","per-source RBAC · encryption · tenant isolation","#4A6AA8"),
            ("Monitor & respond","Defender for AI · red-team · audit · incident response",GRAY)]
    x=60; w=760; y=140; lh=112; gap=8
    for i,(t,sub,c) in enumerate(layers):
        d.card(x,y,w,lh-gap); d.rect(x,y,14,lh-gap,c,rx=6)
        d.badge(x+52,y+(lh-gap)/2,"lock",c,r=18)
        d.text(x+86,y+(lh-gap)/2-8,t,17,NAVY,weight="800"); d.text(x+86,y+(lh-gap)/2+16,sub,12,GRAY)
        if i<len(layers)-1: d.text(x+w/2,y+lh-gap+3,"▼",12,"#B9C4DA","middle")
        y+=lh
    # OWASP panel
    ox=880; ow=720
    d.card(ox,140,ow,772,LIGHT,rx=16); d.rect(ox,140,ow,50,NAVY,rx=16); d.rect(ox,166,ow,24,NAVY)
    d.text(ox+ow/2,166,"OWASP TOP 10 FOR LLM APPLICATIONS (2025) → CONTROL",13.5,WHITE,"middle","800")
    owasp=[("LLM01 Prompt injection","prompt shields · isolate untrusted content"),
           ("LLM02 Sensitive info disclosure","PII redaction · output filtering · DLP"),
           ("LLM03 Supply chain","AI-BOM · model & dependency provenance"),
           ("LLM04 Data & model poisoning","curated data · lineage · validation"),
           ("LLM05 Improper output handling","treat output as untrusted · sanitize"),
           ("LLM06 Excessive agency","least-privilege tools · HITL approvals"),
           ("LLM07 System-prompt leakage","no secrets in prompts · guardrails"),
           ("LLM08 Vector / embedding weakness","per-source RBAC on vectors · isolation"),
           ("LLM09 Misinformation","grounding · citations · eval gates"),
           ("LLM10 Unbounded consumption","rate & cost limits · quotas · budgets")]
    yy=210
    for t,ctl in owasp:
        d.rect(ox+20,yy,ow-40,54,WHITE,rx=9,stroke=LINE)
        d.els.append(f'<circle cx="{ox+46}" cy="{yy+27}" r="7" fill="{ROSE}"/>')
        d.text(ox+66,yy+23,t,13.5,NAVY,weight="700"); d.text(ox+66,yy+43,ctl,12,TEAL,weight="600")
        yy+=64
    d.save("13-security")

# ============================================================================
# DIAGRAM 14 — Data platform at scale
# ============================================================================
def d14_data():
    d=SVG(1660, 840, WHITE)
    title(d, "Data at Scale", "Enterprise data platform feeding grounded AI")
    stages=[("Sources","voice · chat · docs · CRM · systems",GRAY,"grid"),
            ("Ingestion","Event Hubs (stream) + batch",INDIGO,"flow"),
            ("Lakehouse","Microsoft Fabric / OneLake","#3E5C99","cloud"),
            ("Processing","chunk · enrich · vectorize · redact PII",TEAL,"gear"),
            ("Stores","AI Search vectors · Cosmos","#4A6AA8","db"),
            ("Serving","RAG retrieval · grounding",CYAN,"route"),
            ("Consumers","agents · PI Index · analytics",GREEN,"brain")]
    n=len(stages); bw=196; gap=32; sx=60; y=170; bh=170
    for i,(t,sub,c,ic) in enumerate(stages):
        x=sx+i*(bw+gap); d.toptab(x,y,bw,bh,c,tab=8)
        d.badge(x+bw/2,y+56,ic,c,r=23); d.tspan_center(x+bw/2,y+108,[t],16,NAVY,"800")
        d.tspan_center(x+bw/2,y+140,[sub] if len(sub)<26 else sub.split(" · ",1),11,GRAY)
        if i<n-1: d.arrow(x+bw+4,y+bh/2,x+bw+gap-4,y+bh/2,AMBER,2.6)
    # streaming/batch note
    d.text(sx+bw+gap/2+bw/2,y+bh+34,"batch + streaming lanes · incremental / CDC refresh · partitioned per domain & tenant",12.5,GRAY,"middle",italic=True)
    # governance band
    gy=500
    d.rect(60,gy,1540,90,"#EEF3FF",rx=16,stroke="#C9D6F0")
    d.badge(110,gy+45,"shield",INDIGO,r=20); d.text(148,gy+40,"Microsoft Purview",16,NAVY,weight="800")
    d.chiprow(148,gy+55,["data governance","lineage","classification","DLP","retention","PII handling"],13,WHITE,INDIGO,gap=13,h=32)
    for i in range(n):
        x=sx+i*(bw+gap)+bw/2
        if i in (0,3,4,5): d.arrow(x,y+bh+3,x,gy-2,"#C9D6F0",1.4,head=False)
    d.text(60,gy+130,"Governance and security are applied across the whole pipeline — not bolted on at the end.",12.5,NAVY,weight="600")
    d.save("14-data-platform")

# ============================================================================
# DIAGRAM 15 — GenAIOps CI/CD pipeline with validation gates
# ============================================================================
def d15_cicd():
    d=SVG(1700, 860, WHITE)
    title(d, "GenAIOps CI/CD", "Nothing ships without passing evaluation gates")
    stages=[("Author","agents & prompts as YAML",TEAL,"doc"),
            ("Commit / PR","version-controlled",INDIGO,"flow"),
            ("CI build","package · IaC","#3E5C99","gear"),
            ("Registry","versioned prompt & model",PURPLE,"db"),
            ("Deploy","canary / blue-green",AMBER,"route"),
            ("Production","behind APIM gateway",GREEN,"cloud")]
    n=len(stages); bw=200; gap=64; sx=60; y=160; bh=120
    for i,(t,sub,c,ic) in enumerate(stages):
        x=sx+i*(bw+gap); d.toptab(x,y,bw,bh,c,tab=7)
        d.badge(x+34,y+52,ic,c,r=17); d.tspan_center(x+bw/2+16,y+52,[t] if len(t)<12 else t.split(" ",1),14.5,NAVY,"700")
        d.text(x+bw/2,y+96,sub,11,GRAY,"middle")
        if i<n-1: d.arrow(x+bw+4,y+bh/2,x+bw+gap-4,y+bh/2,GRAY,2.4)
    # evaluation gates between CI build (2) and Registry (3)
    gxc=sx+2*(bw+gap)+bw+gap/2
    d.raw(f'<circle cx="{gxc}" cy="{y+bh/2}" r="20" fill="{ROSE}"/>'); d.icon(gxc,y+bh/2,"check",WHITE,r=15)
    gy=340
    d.text(60,gy-2,"EVALUATION GATES  ·  block promotion on failure",14,ROSE,"start","800",spacing="0.5")
    gates=[("Unit & contract","tool / schema tests",TEAL),("Prompt regression","golden-set vs baseline",INDIGO),
           ("Groundedness","faithfulness / citations","#3E5C99"),("Safety & red-team","adversarial + Content Safety",ROSE),
           ("Cost & latency","budgets as gates",AMBER)]
    gw=296; ggap=16; gsx=(1700-(5*gw+4*ggap))/2
    for i,(t,sub,c) in enumerate(gates):
        x=gsx+i*(gw+ggap); d.toptab(x,gy+16,gw,120,c,tab=7)
        d.els.append(f'<circle cx="{x+34}" cy="{gy+56}" r="15" fill="{c}"/>'); d.icon(x+34,gy+56,"check",WHITE,r=11)
        d.text(x+60,gy+52,t,14.5,NAVY,weight="700"); d.text(x+60,gy+76,sub,11.5,GRAY)
        d.rect(x+20,gy+94,gw-40,28,LIGHT,rx=7); d.text(x+gw/2,gy+113,"pass required",11,c,"middle","700")
    d.arrow(gxc,y+bh+3,gxc,gy+12,ROSE,2.2,dash="5,5")
    # online eval + feedback loop
    oy=560
    d.rect(60,oy,1580,110,"#EEF3FF",rx=16,stroke="#C9D6F0")
    d.badge(110,oy+55,"gauge",INDIGO,r=20); d.text(148,oy+42,"Post-deploy validation",16,NAVY,weight="800")
    d.chiprow(148,oy+58,["online A/B","shadow testing","guardrail monitors","drift & quality","auto-rollback on regression","user & QA feedback"],13,WHITE,INDIGO,gap=12,h=32)
    prodx=sx+5*(bw+gap)+bw/2
    d.arrow(prodx,y+bh+3,prodx,oy-2,GRAY,2,head=True)
    # feedback back to author/datasets
    d.raw(f'<path d="M{60},{oy+55} H30 V{y+bh/2} H{sx-4}" fill="none" stroke="{GREEN}" stroke-width="2.4" stroke-dasharray="6,5" marker-end="url(#ah)"/>')
    d.text(120,oy+100,"feedback → golden datasets → next iteration (continuous improvement flywheel)",12.5,GREEN,italic=True)
    d.save("15-genaiops-cicd")

# ============================================================================
# DIAGRAM 16 — Model strategy & Model Router
# ============================================================================
def d16_model():
    d=SVG(1660, 820, WHITE)
    title(d, "Model Strategy", "Ride the frontier without rewrites")
    # catalog (left)
    d.toptab(60,160,360,470,INDIGO)
    d.text(240,200,"Model catalog",17,NAVY,"middle","800")
    models=[("GPT-5.5","frontier · agentic"),("GPT-5.4 / 5.2","reasoning · 272k ctx"),("GPT-5.5 Instant","low-latency chat"),
            ("gpt-realtime-1.5","speech-to-speech"),("o-series","deep reasoning"),("Open-weight (Llama/Phi)","cost / edge tiers"),
            ("Fine-tuned / distilled","task-specialized")]
    for i,(m,s) in enumerate(models):
        yy=228+i*54; d.rect(84,yy,312,44,WHITE,rx=9,stroke=LINE)
        d.els.append(f'<circle cx="{108}" cy="{yy+22}" r="6" fill="{INDIGO}"/>')
        d.text(124,yy+19,m,13.5,NAVY,weight="700"); d.text(124,yy+37,s,11.5,GRAY)
    # router (center)
    d.toptab(500,260,340,250,AMBER)
    d.badge(670,318,"route",AMBER,r=28); d.tspan_center(670,392,["Model","Router"],20,NAVY,"800")
    d.text(670,436,"routes by task · quality bar · cost · latency",11.5,GRAY,"middle")
    d.text(670,462,"+ prompt caching",11.5,GRAY,"middle")
    d.arrow(420,395,498,395,GRAY,2.6)
    # consumers (right)
    d.toptab(920,260,340,250,TEAL)
    d.badge(1090,318,"flow",TEAL,r=26); d.tspan_center(1090,392,["Agents &","use cases"],19,NAVY,"800")
    d.text(1090,436,"cheapest model that meets",11.5,GRAY,"middle"); d.text(1090,456,"the measured quality bar",11.5,GRAY,"middle")
    d.arrow(840,395,918,395,GRAY,2.6)
    # frontier adoption loop
    ly=580
    d.rect(60,ly,1540,150,LIGHT,rx=16,stroke=LINE); d.rect(60,ly,1540,44,NAVY,rx=16); d.rect(60,ly+28,1540,16,NAVY)
    d.text(830,ly+29,"FRONTIER-MODEL ADOPTION LOOP — new models absorbed automatically",13,WHITE,"middle","800")
    loop=["New model in catalog","Evaluate vs golden sets","Shadow in production","Router promotes if better","Adopt — no app rewrite"]
    lx=140
    for i,s in enumerate(loop):
        w=d.chip(lx,ly+74,s,13,WHITE,INDIGO,h=34);
        if i<len(loop)-1: d.text(lx+w+8,ly+94,"›",16,AMBER,"middle","800")
        lx+=w+34
    d.text(830,ly+130,"AFNI pins to capabilities and evaluations, not to a single model version.",12.5,GRAY,"middle",italic=True)
    d.save("16-model-strategy")

# ============================================================================
# DIAGRAM 17 — Performance & scalability
# ============================================================================
def d17_perf():
    d=SVG(1660, 780, WHITE)
    title(d, "Performance & Scale", "Engineered for sub-second voice and bulk analytics")
    # latency budget bar
    d.text(60,168,"LATENCY BUDGET — a voice turn (illustrative ~800 ms)",14,NAVY,weight="800",spacing="0.5")
    segs=[("Speech-to-text",120,CYAN),("Retrieval (RAG)",90,INDIGO),("Model inference",380,TEAL),("Guardrails",60,AMBER),("Text-to-speech",150,GREEN)]
    total=sum(s[1] for s in segs); x=60; y=190; W=1540; H=60
    for t,ms,c in segs:
        w=W*ms/total; d.rect(x,y,w-3,H,c,rx=8)
        d.text(x+w/2,y+26,t,12.5,WHITE,"middle","700"); d.text(x+w/2,y+46,f"{ms} ms",12,WHITE,"middle")
        x+=w
    d.text(1600,y+H+22,"budget enforced & traced per turn",12,GRAY,"end",italic=True)
    # levers
    cards=[("Caching","semantic · prompt · response reuse",TEAL,"db"),
           ("Model Router","right-size cost vs latency",INDIGO,"route"),
           ("Elastic scale","provisioned throughput (PTU) + autoscale",AMBER,"cloud"),
           ("Resilience","fallback models · graceful degradation · load & soak tests",GREEN,"shield")]
    cw=370; gap=20; sx=60; cy=330
    for i,(t,sub,c,ic) in enumerate(cards):
        x=sx+i*(cw+gap); d.toptab(x,cy,cw,200,c,tab=8)
        d.badge(x+46,cy+56,ic,c,r=22); d.text(x+82,cy+62,t,17,NAVY,weight="800")
        # wrap sub
        words=sub.split(" "); line=""; lines=[]
        for w in words:
            if len(line+" "+w)>26: lines.append(line); line=w
            else: line=(line+" "+w).strip()
        lines.append(line)
        for j,ln in enumerate(lines): d.text(x+28,cy+118+j*24,ln,13,INK)
    d.rect(60,570,1540,70,"#EEF3FF",rx=14,stroke="#C9D6F0")
    d.text(830,613,"Async + streaming responses · batching for bulk (PI Index) · concurrency & backpressure · continuous load testing against SLOs",13,NAVY,"middle","600")
    d.save("17-performance")

# ============================================================================
# DIAGRAM 18 — Evaluation framework
# ============================================================================
def d18_eval():
    d=SVG(1660, 820, WHITE)
    title(d, "Evaluation Framework", "Measured quality — offline, online, and adversarial")
    cols=[("Offline evaluation",TEAL,"gauge",["Golden datasets","LLM-as-judge","Auto rubric evaluators","Groundedness / faithfulness"]),
          ("Human & red-team",ROSE,"people",["SME review & calibration","Adversarial red-teaming","Safety / Content Safety","Bias & fairness audits"]),
          ("Online evaluation",INDIGO,"flow",["A/B experiments","Shadow testing","Guardrail monitors","User & QA feedback"])]
    cw=470; gap=30; sx=60; y=160; ch=360
    for i,(t,c,ic,items) in enumerate(cols):
        x=sx+i*(cw+gap); d.toptab(x,y,cw,ch,c,tab=8)
        d.badge(x+46,y+54,ic,c,r=22); d.text(x+82,y+60,t,17,NAVY,weight="800")
        for j,it in enumerate(items):
            yy=y+112+j*56; d.rect(x+28,yy,cw-56,44,LIGHT,rx=9)
            d.els.append(f'<circle cx="{x+52}" cy="{yy+22}" r="6" fill="{c}"/>'); d.text(x+70,yy+27,it,13.5,INK,weight="600")
        d.arrow(x+cw/2,y+ch+4,x+cw/2 if i==1 else (830),570,GRAY,2,head=(i==1))
    # release gate
    gy=580
    d.card(560,gy,540,90,NAVY,rx=16,stroke=NAVY)
    d.badge(610,gy+45,"check","rgba(255,255,255,0.16)",r=20)
    d.text(648,gy+40,"Release gate",18,WHITE,weight="800"); d.text(648,gy+66,"regression-blocking · every promotion",12.5,CYAN)
    d.arrow(560,610,300,610,GRAY,2,head=False); d.arrow(1100,610,1360,610,GRAY,2,head=False)
    d.raw(f'<path d="M830,{gy+90} V730 H120 V{y+ch/2} H{sx-4}" fill="none" stroke="{GREEN}" stroke-width="2.2" stroke-dasharray="6,5" marker-end="url(#ah)"/>')
    d.text(200,725,"failures & production signals feed back into golden datasets",12.5,GREEN,italic=True)
    d.save("18-evaluation")

if __name__=="__main__":
    d1_platform(); d2_agents(); d3_three(); d4_voice()
    d5_piindex(); d6_hiring(); d7_lifecycle(); d8_roadmap()
    d9_framework(); d10_onboarding(); d11_patterns(); d12_runtime()
    d13_security(); d14_data(); d15_cicd(); d16_model(); d17_perf(); d18_eval()
    print("done all diagrams")
