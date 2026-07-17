import streamlit as st
import asyncio
import plotly.graph_objects as go
import networkx as nx
from src.llm_client import LLMClient
from src.agent.react_loop import InvestigativeAgent
from src.reporting import ReportGenerator, EvidenceExplainer
from src.verification import ContradictionDetector

st.set_page_config(
    page_title="OSINT Investigative Agent",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .claim-card {
        background: #1a1d24;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .claim-card:hover { border-color: #58a6ff; }
    .confidence-high { border-left: 4px solid #3fb950; }
    .confidence-medium { border-left: 4px solid #d2a8ff; }
    .confidence-low { border-left: 4px solid #f85149; }
    .citation-marker {
        color: #58a6ff;
        cursor: pointer;
        font-size: 0.8rem;
        padding: 0.1rem 0.3rem;
        border-radius: 4px;
        background: #0d1117;
    }
    .citation-marker:hover { background: #1f6feb; color: white; }
    .contradiction-badge {
        display: inline-block;
        background: #4a1c1c;
        color: #ff7b72;
        padding: 0.15rem 0.5rem;
        border-radius: 12px;
        font-size: 0.75rem;
    }
    .corroboration-badge {
        display: inline-block;
        background: #1b4026;
        color: #7ee787;
        padding: 0.15rem 0.5rem;
        border-radius: 12px;
        font-size: 0.75rem;
    }
    .stApp { background: #0d1117; }
    h1, h2, h3 { color: #f0f6fc; }
    .report-text { 
        background: #161b22; 
        padding: 1.5rem; 
        border-radius: 8px;
        border: 1px solid #30363d;
        line-height: 1.7;
        font-size: 0.95rem;
    }
</style>
""", unsafe_allow_html=True)


def init_session():
    if "agent" not in st.session_state:
        st.session_state.agent = None
    if "report" not in st.session_state:
        st.session_state.report = None
    if "ledger" not in st.session_state:
        st.session_state.ledger = None
    if "query" not in st.session_state:
        st.session_state.query = ""
    if "selected_claim" not in st.session_state:
        st.session_state.selected_claim = None
    if "history" not in st.session_state:
        st.session_state.history = []


def build_corroboration_graph(ledger):
    if not ledger or not ledger.claims:
        return None
    G = nx.Graph()
    for cid, claim in ledger.claims.items():
        G.add_node(cid, label=claim.text[:50], confidence=claim.confidence)
    for cid, claim in ledger.claims.items():
        for corr_id in claim.corroborating_claim_ids:
            if corr_id in ledger.claims:
                G.add_edge(cid, corr_id, color="green", weight=1)
        for cont_id in claim.contradicting_claim_ids:
            if cont_id in ledger.claims:
                G.add_edge(cid, cont_id, color="red", weight=2)

    pos = nx.spring_layout(G, k=1.5, iterations=50, seed=42)
    edge_trace = []
    for u, v, d in G.edges(data=True):
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        color = d.get("color", "gray")
        edge_trace.append(go.Scatter(
            x=[x0, x1, None], y=[y0, y1, None],
            mode="lines",
            line={"width": d.get("weight", 1), "color": color},
            hoverinfo="none",
        ))

    node_x, node_y, node_text, node_color, node_size = [], [], [], [], []
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        claim = ledger.get_claim(node)
        node_text.append(f"{node}: {claim.text[:100]}..." if claim else node)
        node_color.append(claim.confidence if claim else 0.5)
        node_size.append(15 + (claim.confidence * 15) if claim else 20)

    node_trace = go.Scatter(
        x=node_x, y=node_y, mode="markers+text",
        text=[n for n in G.nodes()],
        textposition="top center",
        hovertext=node_text,
        marker={
            "size": node_size,
            "color": node_color,
            "colorscale": "RdYlGn",
            "showscale": True,
            "colorbar": {"title": "Confidence", "x": 1.1},
            "line": {"width": 1, "color": "white"},
            "cmin": 0, "cmax": 1,
        },
    )

    fig = go.Figure(
        data=edge_trace + [node_trace],
        layout=go.Layout(
            title="Claim Corroboration Graph (green=corroborates, red=contradicts)",
            showlegend=False,
            hovermode="closest",
            paper_bgcolor="#0d1117",
            plot_bgcolor="#0d1117",
            font={"color": "#e1e4e8"},
            margin=dict(b=20, l=20, r=80, t=40),
            xaxis={"showgrid": False, "zeroline": False, "visible": False},
            yaxis={"showgrid": False, "zeroline": False, "visible": False},
            height=600,
        ),
    )
    return fig


async def run_investigation(query):
    llm = LLMClient()
    agent = InvestigativeAgent(llm)
    result = await agent.investigate(query)
    return result


st.title("🔍 Explainable OSINT Investigative Agent")
st.markdown("An autonomous research agent that **proves its findings** — every claim links back to source evidence.")

init_session()

with st.sidebar:
    st.header("Investigation Query")
    query = st.text_area(
        "Enter your investigative question:",
        placeholder='e.g., "Map the corporate network and controversies around Company X"',
        height=100,
        value=st.session_state.query,
    )

    if st.button("🔬 Investigate", type="primary", use_container_width=True):
        if query:
            with st.spinner("Planning research strategy..."):
                st.session_state.query = query
                st.session_state.history.append(("user", query))
                try:
                    result = asyncio.run(run_investigation(query))
                    st.session_state.report = result.get("report", "")
                    st.session_state.ledger = result.get("ledger")
                    st.session_state.agent = True
                    st.session_state.history.append(("agent", f"Investigation complete. {result.get('claim_count', 0)} claims from {result.get('source_count', 0)} sources."))
                    st.success("Investigation complete!")
                except Exception as e:
                    st.error(f"Investigation failed: {e}")
        else:
            st.warning("Please enter a query.")

    st.divider()
    st.subheader("Explainability Controls")
    claim_id = st.text_input("Ask 'why' about a claim (e.g., c_000):", placeholder="c_000")
    if st.button("❓ Explain This Claim", use_container_width=True) and claim_id and st.session_state.ledger:
        explainer = EvidenceExplainer(st.session_state.ledger)
        st.session_state.selected_claim = explainer.explain_claim(claim_id)

    if st.session_state.ledger:
        st.divider()
        explainer = EvidenceExplainer(st.session_state.ledger)
        st.markdown("### Evidence Summary")
        st.markdown(explainer.summary())

tab1, tab2, tab3, tab4 = st.tabs(["📋 Report", "🔗 Evidence Graph", "🔍 Claim Explorer", "📜 History"])

with tab1:
    if st.session_state.report:
        st.markdown(f"## Report: {st.session_state.query[:60]}")
        report_html = st.session_state.report.replace("\n", "<br>")
        report_html = report_html.replace(
            "[c_", "<span class='citation-marker' onclick='navigator.clipboard.writeText(this.textContent)'>c_"
        ).replace("]", "</span>")
        st.markdown(f'<div class="report-text">{report_html}</div>', unsafe_allow_html=True)

        if st.session_state.ledger:
            col1, col2, col3 = st.columns(3)
            claims = st.session_state.ledger.get_all_claims()
            col1.metric("Total Claims", len(claims))
            col2.metric("Sources", len(set(c.source.source_url for c in claims)))
            col3.metric("Avg Confidence", f"{sum(c.confidence for c in claims) / len(claims):.2f}" if claims else "0")

            st.subheader("Contradictions")
            detector = ContradictionDetector()
            contradictions = detector.find_contradictions(st.session_state.ledger)
            if contradictions:
                for c in contradictions[:5]:
                    st.warning(f"**{c['severity'].upper()}**: {c['claim_a']['text'][:100]}... vs {c['claim_b']['text'][:100]}...")
            else:
                st.info("No contradictions detected.")
    else:
        st.info("Enter a query and click 'Investigate' to begin.")

with tab2:
    if st.session_state.ledger and st.session_state.ledger.claims:
        fig = build_corroboration_graph(st.session_state.ledger)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Not enough claims to build a graph.")
    else:
        st.info("Run an investigation first to see the evidence graph.")

with tab3:
    if st.session_state.ledger:
        claims = st.session_state.ledger.get_all_claims()
        if not claims:
            st.info("No claims in ledger.")
        else:
            for c in sorted(claims, key=lambda x: x.confidence, reverse=True):
                conf_class = "confidence-high" if c.confidence >= 0.7 else "confidence-medium" if c.confidence >= 0.4 else "confidence-low"
                badges = []
                if c.corroborating_claim_ids:
                    badges.append(f'<span class="corroboration-badge">✅ {len(c.corroborating_claim_ids)} corroborating</span>')
                if c.contradicting_claim_ids:
                    badges.append(f'<span class="contradiction-badge">⚠️ {len(c.contradicting_claim_ids)} contradicting</span>')

                st.markdown(
                    f'<div class="claim-card {conf_class}">'
                    f'<strong>[{c.claim_id}]</strong> {c.text}<br>'
                    f'<small>Confidence: {c.confidence:.2f} | Source: '
                    f'<a href="{c.source.source_url}" target="_blank" style="color:#58a6ff;">{c.source.source_url[:60]}...</a>'
                    f' | Tool: {c.source.retrieval_tool} | {" ".join(badges)}</small>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

                if st.button(f"Explain {c.claim_id}", key=f"explain_{c.claim_id}"):
                    explainer = EvidenceExplainer(st.session_state.ledger)
                    st.session_state.selected_claim = explainer.explain_claim(c.claim_id)

        if st.session_state.selected_claim:
            st.divider()
            st.markdown(st.session_state.selected_claim)
    else:
        st.info("Run an investigation first to explore claims.")

with tab4:
    for role, msg in st.session_state.history:
        prefix = "🧑‍💻" if role == "user" else "🤖"
        st.markdown(f"{prefix} **{role.title()}:** {msg}")
