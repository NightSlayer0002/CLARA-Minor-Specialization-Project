import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import streamlit as st
from dashboard.utils.data_access import (
    get_risk_by_region, 
    get_port_exposure, 
    get_vulnerability_breakdown, 
    get_security_events_timeline,
    get_all_security_configs,
    get_cloud_providers,
    get_regions,
    check_db_exists
)
from dashboard.components.charts import (
    risk_by_region_heatmap, 
    port_exposure_bar, 
    vulnerability_breakdown_pie, 
    security_events_timeline
)
from dashboard.components.metrics import metric_card

st.set_page_config(
    page_title="Security Analysis - CLARA", 
    layout="wide", 
    page_icon="🛡️",
    initial_sidebar_state="expanded"
)

st.title("Security Analysis")
st.write("Deep-dive security posture evaluation detailing open ports, encryption status, and failed authorization events.")

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
    # Advisory Platform Disclaimer
    st.info(
        "⚠️ **Advisory Platform Scope**: CLARA performs non-intrusive posture evaluation and generates remediation guidance. "
        "It does not autonomously alter firewall rules, modify IAM policies, or disconnect live cloud infrastructure."
    )

    # 1. Posture KPI Highlights
    df_vuln = get_vulnerability_breakdown(provider=selected_provider, region=selected_region)
    
    # Extract counts safely
    def get_cnt(name):
        row = df_vuln[df_vuln["vulnerability"] == name]
        return int(row["count"].iloc[0]) if not row.empty else 0
        
    exposed_count = get_cnt("Internet Exposed")
    unencrypted_count = get_cnt("Unencrypted Volume")
    excessive_iam_count = get_cnt("Excessive IAM")
    brute_force_count = get_cnt("Brute-force attempts")

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        metric_card("Publicly Exposed", exposed_count, help_text="Instances with 0.0.0.0/0 ingress exposure on one or more open ports.")
    with kpi2:
        metric_card("Unencrypted Storage", unencrypted_count, help_text="Instances with unencrypted attached EBS/disk volumes.")
    with kpi3:
        metric_card("Excessive IAM Privileges", excessive_iam_count, help_text="Instances assigned over-privileged IAM roles (e.g. AdministratorAccess or wildcard).")
    with kpi4:
        metric_card("Brute-Force Ingress (>10 Logins)", brute_force_count, help_text="Instances experiencing more than 10 failed login attempts in the past 7 days.")

    st.divider()

    # 2. Charts Row 1: Region Risk & Port Exposure Side-by-side
    col1, col2 = st.columns(2)
    with col1:
        df_region = get_risk_by_region(provider=selected_provider)
        fig_region = risk_by_region_heatmap(df_region)
        st.image(fig_region.to_image(format="png", width=760, height=420, scale=2), use_column_width=True)
    with col2:
        df_ports = get_port_exposure(provider=selected_provider, region=selected_region)
        fig_ports = port_exposure_bar(df_ports)
        st.image(fig_ports.to_image(format="png", width=760, height=420, scale=2), use_column_width=True)
        
    st.divider()
    
    # 3. Vulnerability distribution & Events timeline
    col3, col4 = st.columns(2)
    with col3:
        fig_vuln = vulnerability_breakdown_pie(df_vuln)
        st.image(fig_vuln.to_image(format="png", width=760, height=420, scale=2), use_column_width=True)
    with col4:
        df_events = get_security_events_timeline(provider=selected_provider, region=selected_region)
        fig_events = security_events_timeline(df_events)
        st.image(fig_events.to_image(format="png", width=760, height=420, scale=2), use_column_width=True)
        
    st.divider()
    
    # 4. Detailed Configuration Ledger in Expander
    st.subheader("Security Configuration Ledger")
    st.caption("Fleet configuration records, open ports, and patch compliance.")
    
    with st.expander("📋 Inspect All Security Configurations", expanded=False):
        df_configs = get_all_security_configs(provider=selected_provider, region=selected_region)
        
        if df_configs.empty:
            st.info("No configuration records match the selected filters.")
        else:
            st.dataframe(
                df_configs,
                use_container_width=True,
                column_config={
                    "instance_id": st.column_config.TextColumn("Instance ID"),
                    "cloud_provider": st.column_config.TextColumn("Provider"),
                    "region": st.column_config.TextColumn("Region"),
                    "open_ports": st.column_config.TextColumn("Open Ports"),
                    "internet_exposed": st.column_config.CheckboxColumn("Internet Exposed"),
                    "encryption_enabled": st.column_config.CheckboxColumn("Encrypted Volume"),
                    "iam_permission_level": st.column_config.TextColumn("IAM Level"),
                    "failed_logins_7d": st.column_config.NumberColumn("Failed Logins (7d)"),
                    "last_patch_date": st.column_config.DateColumn("Last Patched")
                },
                hide_index=True
            )
