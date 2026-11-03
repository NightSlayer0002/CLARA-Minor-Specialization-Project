import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
from dashboard.utils.data_access import get_overview_metrics, check_db_exists, get_audit_metadata
from dashboard.components.metrics import metric_card

# Set root Streamlit configurations
st.set_page_config(
    page_title="CLARA - Cloud Risk & Cost Intelligence", 
    layout="wide", 
    page_icon="☁️",
    initial_sidebar_state="expanded"
)

st.sidebar.title("CLARA")
st.sidebar.caption("MIT Bengaluru · CSE 4191")
st.sidebar.divider()
st.sidebar.caption("Choose a page to explore the demo fleet.")

st.caption("CLARA / CLOUD OPERATIONS")
st.title("Fleet briefing")
st.markdown("Explore security risks, unusual activity and savings across AWS, Azure and Google Cloud.")

# Synthetic Demonstration Environment Banner
st.info(
    "🧪 **Synthetic Demonstration Environment**: CLARA operates on a reproducible 300-instance synthetic cloud infrastructure "
    "corpus spanning AWS, Azure, and GCP over a 90-day telemetry history (27,000 daily metrics and cost records). "
    "All telemetry patterns, security misconfigurations, and FinOps metrics are generated for rigorous, reproducible evaluation."
)

# Validate DB exists before executing queries
exists, _ = check_db_exists()
if exists:
    metrics = get_overview_metrics()
    audit_data = get_audit_metadata()
    
    st.subheader("Fleet Health & Operations Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        metric_card(
            label="Monitored Fleet Instances", 
            value=metrics["total_instances"],
            help_text="Total cloud compute instances actively monitored across AWS, Azure, and GCP."
        )
    with col2:
        metric_card(
            label="Critical Risk Instances (Score ≥ 80)", 
            value=metrics["critical_risk_count"],
            help_text="Instances in the Critical operational risk tier (score ≥ 80.0 out of 100.0)."
        )
    with col3:
        metric_card(
            label="Cost Recommendation Savings", 
            value=metrics["total_monthly_waste_usd"], 
            format_as_currency=True,
            help_text="Monthly savings attached specifically to cost and rightsizing recommendations."
        )
    with col4:
        metric_card(
            label="All Recommendation Savings", 
            value=metrics["total_potential_savings_usd"], 
            format_as_currency=True,
            help_text="Monthly savings across cost, anomaly, and security recommendations combined."
        )
        
    st.divider()

    # System Status & Metadata Panel
    st.subheader("System Architecture & Pipeline Status")
    sc1, sc2, sc3 = st.columns(3)
    
    with sc1:
        st.markdown("##### 🗄️ Analytics Warehouse")
        st.markdown(f"- **Engine**: DuckDB Embedded Columnar")
        st.markdown(f"- **Fleet Coverage**: {audit_data['total_instances']} instances (100% fleet)")
        st.markdown(f"- **Daily Telemetry**: {audit_data['total_metrics_records']:,} daily metric rows")
        st.markdown(f"- **Status**: `{audit_data['db_status']}`")

    with sc2:
        st.markdown("##### 🤖 ML Analytics Models")
        st.markdown("- **Anomaly Detection**: Multi-Modal Isolation Forest")
        st.markdown("- **Security Scoring**: Deterministic Security Posture Model")
        st.markdown("- **FinOps Waste**: K-Means Compute Rightsizing Model")
        st.markdown(f"- **Last Run**: `{audit_data['calc_time_str']}`")

    with sc3:
        st.markdown("##### 🧠 GenAI Configuration & History")
        sources_str = ", ".join(audit_data.get("generation_sources", [])) or "offline_fallback"
        st.markdown("- **Configured Generation Mode**: Hybrid (Live Gemini with Offline Rule Fallback)")
        st.markdown("- **Configured Model**: `gemini-3.8-flash`")
        st.markdown(f"- **Last Recommendation Source**: `{sources_str}`")
        st.markdown(f"- **Ingested Recommendations**: {audit_data['recommendation_count']} actionable items")

    st.divider()

    # Module Directory Cards
    st.subheader("Platform Modules")
    mc1, mc2 = st.columns(2)
    
    with mc1:
        with st.container(border=True):
            st.page_link("pages/1_Overview.py", label="Executive overview")
            st.markdown(
                "Fleet-wide operational risk rankings, 30-day spend trends, and top high-risk nodes. "
                "Filterable by cloud provider and region."
            )
        with st.container(border=True):
            st.page_link("pages/2_Security_Analysis.py", label="Security analysis")
            st.markdown(
                "Deep-dive security posture evaluation: public port exposure, unencrypted volumes, "
                "excessive IAM privileges, failed authentication events, and audit logs."
            )

    with mc2:
        with st.container(border=True):
            st.page_link("pages/3_Cost_Analysis.py", label="Cost analysis")
            st.markdown(
                "FinOps analytics: 30-day fleet spend by instance type, resource utilization scatter, "
                "utilized vs. wasted spend, 90-day linear cost projections, and an interactive rightsizing calculator."
            )
        with st.container(border=True):
            st.page_link("pages/4_Recommendations.py", label="Recommendations")
            st.markdown(
                "Prioritized remediation action plans with transparent tri-modal provenance tracking "
                "(Gemini Live, Deterministic Offline Fallback, Legacy), actionable step-by-step guidance, and governance audit trails."
            )

    st.caption(
        "⚠️ **Platform Scope & Semantics**: CLARA is an advisory decision-support platform. "
        "Operational risk tiers (0–100 scale) are project-defined composite indices distinct from CVSS or NIST scales. "
        "Financial savings are FinOps heuristic projections based on rightsizing idle capacity and do not constitute contractually guaranteed figures. "
        "Plan approvals update internal governance states and do not modify external cloud infrastructure directly."
    )
