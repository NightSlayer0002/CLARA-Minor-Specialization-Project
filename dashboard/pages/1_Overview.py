import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import streamlit as st
import pandas as pd
from dashboard.utils.data_access import (
    get_overview_metrics, 
    get_risk_distribution, 
    get_cost_trend, 
    get_top_critical_instances,
    get_cloud_providers,
    get_regions,
    check_db_exists
)
from dashboard.components.metrics import metric_card
from dashboard.components.charts import risk_distribution_pie, cost_trend_line
from dashboard.utils.risk_tiers import TIER_BADGES

st.set_page_config(
    page_title="Executive Overview - CLARA", 
    layout="wide", 
    page_icon="📊",
    initial_sidebar_state="expanded"
)

st.title("Executive Overview")
st.write("Fleet-wide operational risk posture, daily spend histories, and ranked high-risk infrastructure assets.")

# Global Filters in Sidebar
st.sidebar.header("🔍 Fleet Filters")
providers = get_cloud_providers()
selected_provider = st.sidebar.selectbox("Cloud Provider:", options=providers, index=0)

regions = get_regions(selected_provider if selected_provider != "All" else None)
selected_region = st.sidebar.selectbox("Region:", options=regions, index=0)

if selected_provider != "All" or selected_region != "All":
    st.sidebar.info(f"Filtering by: Provider=`{selected_provider}`, Region=`{selected_region}`")

exists, _ = check_db_exists()
if exists:
    # 1. Metric Cards Row
    metrics = get_overview_metrics(
        provider=selected_provider, 
        region=selected_region
    )
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        metric_card(
            label="Monitored Instances", 
            value=metrics["total_instances"],
            help_text="Count of instances matching the selected provider/region filters."
        )
    with col2:
        metric_card(
            label="Critical Risk (Score ≥ 80)", 
            value=metrics["critical_risk_count"],
            help_text="Instances in the Critical operational risk tier (score ≥ 80.0 out of 100.0)."
        )
    with col3:
        metric_card(
            label="Cost Recommendation Savings", 
            value=metrics["total_monthly_waste_usd"], 
            format_as_currency=True,
            help_text="Monthly savings from cost and rightsizing recommendations for matching instances."
        )
    with col4:
        metric_card(
            label="All Recommendation Savings", 
            value=metrics["total_potential_savings_usd"], 
            format_as_currency=True,
            help_text="Monthly savings across all recommendation types for matching instances."
        )
        
    st.divider()

    # Risk Score Methodology Banner
    with st.expander("ℹ️ Risk Scoring Methodology & Operational Tiers (Click to expand)", expanded=False):
        st.markdown(r"""
        **Composite Risk Formulation**:
        $$\text{Overall Risk Score} = 0.5 \times \text{Security Risk} + 0.3 \times \text{Telemetry Anomaly} + 0.2 \times \text{Cost Waste}$$

        **Project-Defined Operational Risk Tiers**:
        - 🔴 **Critical** ($\ge 80.0$): Urgent intervention required. High exposure combined with behavioral anomaly or extreme resource waste.
        - 🟠 **High** ($60.0 \le \text{Score} < 80.0$): Elevated operational or configuration exposure requiring prioritized remediation.
        - 🟡 **Medium** ($40.0 \le \text{Score} < 60.0$): Moderate deviations or minor misconfigurations to be reviewed in routine cycles.
        - 🟢 **Low** ($0.0 \le \text{Score} < 40.0$): Normal operations within standard baseline boundaries.
        - ⚪ **Unknown**: Missing (NULL), NaN, non-numeric, or negative scores. Never silently clamped into Low.

        *Note: CLARA's 0.0–100.0 risk score is an operational triage index, not a CVSS or NIST metric.*
        """)

    # 2. Charts Row
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        df_risk = get_risk_distribution(
            provider=selected_provider, 
            region=selected_region
        )
        fig_risk = risk_distribution_pie(df_risk)
        st.image(fig_risk.to_image(format="png", width=760, height=420, scale=2), use_column_width=True)
        
    with chart_col2:
        df_trend = get_cost_trend(
            days=30, 
            provider=selected_provider, 
            region=selected_region
        )
        fig_trend = cost_trend_line(df_trend)
        st.image(fig_trend.to_image(format="png", width=760, height=420, scale=2), use_column_width=True)
        
    st.divider()
    
    # 3. Top Critical Instances List
    st.subheader("Top 10 Highest Risk Instances (Fleet Ranking)")
    st.caption("Ranked by composite operational risk score. Tier reflects project-defined operational thresholds.")
    
    df_critical = get_top_critical_instances(
        limit=10, 
        provider=selected_provider, 
        region=selected_region
    )
    
    if df_critical.empty:
        st.info("No instances found matching the selected provider and region filters.")
    else:
        # Add visual tier badge
        df_display = df_critical.copy()
        df_display["Tier"] = df_display["operational_tier"].apply(lambda t: f"{TIER_BADGES.get(t, '⚪')} {t}")
        
        st.dataframe(
            df_display[[
                "instance_id", "cloud_provider", "instance_type", "region", "Tier",
                "security_risk_score", "anomaly_score", "cost_waste_score", "overall_risk_score"
            ]],
            use_container_width=True,
            column_config={
                "instance_id": st.column_config.TextColumn("Instance ID"),
                "cloud_provider": st.column_config.TextColumn("Provider"),
                "instance_type": st.column_config.TextColumn("Type"),
                "region": st.column_config.TextColumn("Region"),
                "Tier": st.column_config.TextColumn("Operational Tier"),
                "security_risk_score": st.column_config.NumberColumn("Security (50%)", format="%.1f"),
                "anomaly_score": st.column_config.NumberColumn("Anomaly (30%)", format="%.1f"),
                "cost_waste_score": st.column_config.NumberColumn("Cost Waste (20%)", format="%.1f"),
                "overall_risk_score": st.column_config.NumberColumn("Overall Risk", format="%.1f")
            },
            hide_index=True
        )
