import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import streamlit as st
import pandas as pd
from dashboard.utils.data_access import (
    get_cost_by_instance_type, 
    get_utilization_scatter_data, 
    get_wasteful_instances,
    get_cost_trend,
    get_fleet_spend_breakdown,
    get_cloud_providers,
    get_regions,
    check_db_exists
)
from dashboard.components.charts import (
    cost_by_type_donut, 
    utilization_scatter,
    utilized_vs_wasted_bar,
    cost_forecast_chart
)
from dashboard.components.metrics import metric_card

st.set_page_config(
    page_title="Cost Analysis - CLARA", 
    layout="wide", 
    page_icon="💰",
    initial_sidebar_state="expanded"
)

st.title("Financial & Cost Optimization")
st.write("Identifies idle compute resources, calculates estimated financial leakage, and ranks cost-saving opportunities.")

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
    # FinOps Projection Disclaimer
    st.info(
        "ℹ️ **FinOps Projection Scope**: Projected savings are statistical estimates derived from idle compute heuristics "
        "and rightsizing baselines. Actual realization depends on reserved instance commitments, savings plans, "
        "and cloud provider enterprise discount agreements (EDAs). Savings are not contractually guaranteed."
    )

    # 1. Fleet FinOps KPI Summary Row
    df_spend_breakdown = get_fleet_spend_breakdown(provider=selected_provider, region=selected_region)
    total_spend = float(df_spend_breakdown["total_monthly_spend"].iloc[0])
    wasted_spend = float(df_spend_breakdown["wasted_spend"].iloc[0])
    utilized_spend = float(df_spend_breakdown["utilized_spend"].iloc[0])
    savings_pct = (wasted_spend / total_spend * 100.0) if total_spend > 0 else 0.0

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        metric_card(
            label="30-Day Fleet Spend", 
            value=total_spend, 
            format_as_currency=True,
            help_text="Total cloud compute spend recorded across the fleet over the past 30 days."
        )
    with kpi2:
        metric_card(
            label="Utilized Efficient Spend", 
            value=utilized_spend, 
            format_as_currency=True,
            help_text="Compute spend supporting productive workloads within normal utilization limits."
        )
    with kpi3:
        metric_card(
            label="All Recommendation Savings", 
            value=wasted_spend, 
            format_as_currency=True,
            help_text="Monthly savings across all stored cost, anomaly, and security recommendations."
        )
    with kpi4:
        metric_card(
            label="Optimization Potential", 
            value=savings_pct, 
            format_as_percent=True,
            help_text="Potential percentage reduction in monthly fleet compute expenditure."
        )

    st.divider()

    # 2. Charts Row 1: Donut spend by instance type & 2D utilization scatter
    col1, col2 = st.columns(2)
    with col1:
        df_type = get_cost_by_instance_type(provider=selected_provider, region=selected_region)
        fig_type = cost_by_type_donut(df_type)
        st.image(fig_type.to_image(format="png", width=760, height=420, scale=2), use_column_width=True)
    with col2:
        df_scatter = get_utilization_scatter_data(provider=selected_provider, region=selected_region)
        fig_scatter = utilization_scatter(df_scatter)
        st.image(fig_scatter.to_image(format="png", width=760, height=420, scale=2), use_column_width=True)
        
    st.divider()
    
    # 3. Charts Row 2: Fleet-Wide Utilized vs Wasted Spend & 90-Day Cost Forecast
    col3, col4 = st.columns(2)
    with col3:
        fig_stacked = utilized_vs_wasted_bar(df_spend_breakdown)
        st.image(fig_stacked.to_image(format="png", width=760, height=420, scale=2), use_column_width=True)
    with col4:
        df_trend_90 = get_cost_trend(days=90, provider=selected_provider, region=selected_region)
        fig_forecast = cost_forecast_chart(df_trend_90, forecast_days=90)
        st.image(fig_forecast.to_image(format="png", width=760, height=420, scale=2), use_column_width=True)
        
    st.divider()
    
    # 4. Interactive What-If Savings Calculator
    st.subheader("💡 Interactive Rightsizing Calculator")
    st.caption("Select identified wasteful instances to simulate rightsizing or termination savings.")
    
    df_waste = get_wasteful_instances(limit=50, provider=selected_provider, region=selected_region)
    
    if df_waste.empty:
        st.info("No wasteful instances identified for rightsizing in the selected view.")
    else:
        waste_options = df_waste["instance_id"].tolist()
        selected_instances = st.multiselect(
            "Select wasteful instances to simulate rightsizing / termination:",
            options=waste_options,
            default=waste_options[:2] if len(waste_options) >= 2 else waste_options
        )
        
        # Calculate monthly savings for selected instances
        total_reclaimed = 0.0
        selected_monthly_cost = 0.0
        if selected_instances:
            reclaimed_df = df_waste[df_waste["instance_id"].isin(selected_instances)]
            total_reclaimed = float(reclaimed_df["estimated_savings"].sum())
            selected_monthly_cost = float(reclaimed_df["monthly_cost"].sum())
            
        calc_col1, calc_col2 = st.columns(2)
        with calc_col1:
            metric_card(
                label="Simulated Monthly Savings", 
                value=total_reclaimed, 
                format_as_currency=True,
                delta=f"{len(selected_instances)} instances selected"
            )
        with calc_col2:
            metric_card(
                label="Current Monthly Cost of Selected", 
                value=selected_monthly_cost, 
                format_as_currency=True
            )
            
    st.divider()
    
    # 5. Ranked Wasteful Instances list
    st.subheader("Top 20 Ranked Wasteful Instances")
    st.caption("Ranked by Cost Waste Score (derived from utilization and idle duration heuristics).")
    
    df_waste_20 = get_wasteful_instances(limit=20, provider=selected_provider, region=selected_region)
    if df_waste_20.empty:
        st.info("No wasteful instances found matching the selected filters.")
    else:
        st.dataframe(
            df_waste_20[[
                "instance_id", "cloud_provider", "instance_type", "region",
                "avg_utilization", "monthly_cost", "estimated_savings", "cost_waste_score"
            ]],
            use_container_width=True,
            column_config={
                "instance_id": st.column_config.TextColumn("Instance ID"),
                "cloud_provider": st.column_config.TextColumn("Provider"),
                "instance_type": st.column_config.TextColumn("Instance Type"),
                "region": st.column_config.TextColumn("Region"),
                "avg_utilization": st.column_config.NumberColumn("Avg Utilization", format="%.1f%%"),
                "monthly_cost": st.column_config.NumberColumn("Monthly Cost", format="$%.2f"),
                "estimated_savings": st.column_config.NumberColumn("Projected Savings", format="$%.2f"),
                "cost_waste_score": st.column_config.NumberColumn("Waste Score", format="%.1f")
            },
            hide_index=True
        )
