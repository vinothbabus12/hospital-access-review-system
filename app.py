import os
import sys
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.data_generator import generate_synthetic_data, DATA_DIR
from src.database import (
    load_csv_data_to_db,
    get_db_connection,
    execute_query,
    save_review_decision,
    retrieve_review_decisions,
    retrieve_users,
    retrieve_entitlements,
    retrieve_usage_events
)
from src.data_processor import DataProcessor
from src.evidence_engine import evaluate_all_entitlements, generate_evidence_record
from src.risk_engine import get_risk_summary, get_high_risk_privileges_by_role, evaluate_risk
from src.audit import record_reviewer_decision, get_audit_trail
from src.baseline import run_baseline_experiment
from experiments.before_after_analysis import (
    load_experiment_inputs,
    calculate_before_after_metrics,
    create_approval_rate_chart,
    create_decision_distribution_chart,
    create_risk_distribution_chart,
    create_scenario_comparison_chart
)

# Configure Streamlit page layout
st.set_page_config(
    page_title="Hospital Access Review System",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for polished medical dashboard look
st.markdown("""
<style>
    .main-header {
        font-size: 2.1rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .evidence-box {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 1.2rem;
        margin-bottom: 1.5rem;
    }
    .risk-high-badge {
        background-color: #FEE2E2;
        color: #991B1B;
        padding: 0.3rem 0.8rem;
        border-radius: 6px;
        font-weight: 700;
        display: inline-block;
    }
    .risk-med-badge {
        background-color: #FEF3C7;
        color: #92400E;
        padding: 0.3rem 0.8rem;
        border-radius: 6px;
        font-weight: 700;
        display: inline-block;
    }
    .risk-low-badge {
        background-color: #D1FAE5;
        color: #065F46;
        padding: 0.3rem 0.8rem;
        border-radius: 6px;
        font-weight: 700;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_and_process_data():
    users_csv = os.path.join(DATA_DIR, "users.csv")
    if not os.path.exists(users_csv):
        generate_synthetic_data()
        load_csv_data_to_db()

    df_users = retrieve_users()
    df_entitlements = retrieve_entitlements()
    df_events = retrieve_usage_events()
    df_decisions = retrieve_review_decisions()

    processor = DataProcessor(df_users, df_entitlements, df_events)
    df_baseline = processor.get_peer_usage_baseline()
    df_evaluated = evaluate_all_entitlements(df_baseline)

    return df_users, df_entitlements, df_events, df_decisions, processor, df_evaluated


try:
    df_users, df_entitlements, df_events, df_decisions, processor, df_evaluated = load_and_process_data()
except Exception:
    generate_synthetic_data()
    load_csv_data_to_db()
    df_users, df_entitlements, df_events, df_decisions, processor, df_evaluated = load_and_process_data()

# Sidebar Navigation
st.sidebar.image("https://img.icons8.com/color/96/hospital-2.png", width=65)
st.sidebar.title("Hospital Access Review")
st.sidebar.caption("Semester 5 Industry Project")

page = st.sidebar.radio(
    "Navigation Menu",
    [
        "1. Dashboard",
        "2. Privilege Review",
        "3. Evidence Details",
        "4. Reviewer Decision",
        "5. Audit Trail",
        "6. Data Quality",
        "7. Baseline Comparison"
    ]
)

st.sidebar.markdown("---")
st.sidebar.write("**Database Pipeline**")
st.sidebar.success("✓ SQLite Connected")
st.sidebar.caption(f"Users: {len(df_users)} | Entitlements: {len(df_entitlements)}")

if st.sidebar.button("🔄 Regenerate Data"):
    generate_synthetic_data()
    load_csv_data_to_db()
    st.cache_data.clear()
    st.rerun()

COLOR_MAP = {"LOW": "#10B981", "MEDIUM": "#F59E0B", "HIGH": "#EF4444"}


def render_evidence_card(row):
    """
    Renders the detailed evidence-review interface required for entitlement evaluation.
    """
    eval_rec = generate_evidence_record(row)
    risk_level = eval_rec["risk_level"]

    if risk_level == "HIGH":
        badge_html = f'<div class="risk-high-badge">🚨 HIGH RISK (Score: {eval_rec["risk_score"]})</div>'
    elif risk_level == "MEDIUM":
        badge_html = f'<div class="risk-med-badge">⚠️ MEDIUM RISK (Score: {eval_rec["risk_score"]})</div>'
    else:
        badge_html = f'<div class="risk-low-badge">✅ LOW RISK (Score: {eval_rec["risk_score"]})</div>'

    st.markdown(badge_html, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("#### 👤 USER INFORMATION")
        st.write(f"• **User ID:** `{row['user_id']}`")
        st.write(f"• **Name:** {row['name']}")
        st.write(f"• **Role:** {row['role']}")
        st.write(f"• **Department:** {row['department']}")
        st.write(f"• **Staff Type:** {row['staff_type']}")
        st.write(f"• **Status:** {row['status']}")

    with col2:
        st.markdown("#### 🔑 ENTITLEMENT")
        st.write(f"• **Application:** {row['application']}")
        st.write(f"• **Permission:** `{row['permission']}`")
        st.write(f"• **Granted Date:** {row.get('granted_date', 'N/A')}")
        st.write(f"• **Current Status:** {row.get('entitlement_status', row.get('status', 'ACTIVE'))}")

    with col3:
        st.markdown("#### 📊 USAGE EVIDENCE")
        st.write(f"• **Usage count:** {eval_rec['user_usage']}")
        st.write(f"• **Last used date:** {eval_rec['last_usage_date']}")
        st.write(f"• **Peer average:** {eval_rec['peer_average']:.1f}")
        st.write(f"• **Peer median:** {eval_rec['peer_median']:.1f}")
        st.write(f"• **Difference from peer usage:** {eval_rec['difference_from_peer']:+.1f}")

    with col4:
        st.markdown("#### ⚠️ RISK & RECOMMENDATION")
        st.write(f"• **Risk Score:** `{eval_rec['risk_score']}`")
        st.write(f"• **Risk Level:** **{eval_rec['risk_level']}**")
        st.write(f"• **Recommendation:** **{eval_rec['recommendation']}**")

    st.markdown("---")
    st.markdown("#### 📜 EVIDENCE REASONS")
    if eval_rec["evidence_list"]:
        for item in eval_rec["evidence_list"]:
            st.write(f"✓ {item}")
    else:
        st.write("✓ Standard low-risk usage aligned with role peer baseline")

    st.markdown(f"**System Recommendation:** `{eval_rec['recommendation']}`")
    st.caption(f"Calculated Baseline Rationale: {eval_rec['explanation']}")


# ====================================================
# PAGE 1: DASHBOARD
# ====================================================
if page == "1. Dashboard":
    st.markdown('<div class="main-header">🏥 Executive Access Review Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Overview of hospital staff access privileges, usage baselines, and risk metrics</div>', unsafe_allow_html=True)
    # Short explanation
    st.info("Evidence-based access review replaces blanket approval by combining usage history, peer‑role comparison, privilege level, and user status.")

    summary = get_risk_summary(df_evaluated)

    # Retrieve completed decisions count from audit trail
    audit_df = get_audit_trail()
    completed_decisions = len(audit_df) if audit_df is not None else 0

    # 7 Required Top Metric Cards (added Completed Decisions)
    c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
    with c1:
        st.metric("Total Users", f"{summary['total_users']:,}")
    with c2:
        st.metric("Total Entitlements", f"{summary['total_entitlements']:,}")
    with c3:
        st.metric("Total Usage Events", f"{processor.quality_summary['total_events']:,}")
    with c4:
        st.metric("High Risk Privileges", f"{summary['high_risk_count']:,}", delta_color="inverse")
    with c5:
        st.metric("Unused Privileges", f"{summary['unused_count']:,}")
    with c6:
        st.metric("Pending Reviews", f"{summary['pending_reviews']:,}")
    with c7:
        st.metric("Completed Decisions", f"{completed_decisions:,}")

    st.markdown("---")

    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.subheader("Risk Level Distribution")
        if not df_evaluated.empty:
            risk_counts = df_evaluated["risk_level"].value_counts().reset_index()
            risk_counts.columns = ["Risk Level", "Count"]
            fig_risk = px.pie(
                risk_counts, values="Count", names="Risk Level",
                color="Risk Level", color_discrete_map=COLOR_MAP,
                hole=0.4, title="Overall Privilege Risk Levels"
            )
            st.plotly_chart(fig_risk, use_container_width=True)

    with col_chart2:
        st.subheader("Risk Distribution by Staff Type")
        if not df_evaluated.empty:
            staff_risk = df_evaluated.groupby(["staff_type", "risk_level"]).size().reset_index(name="Count")
            fig_staff = px.bar(
                staff_risk, x="staff_type", y="Count", color="risk_level",
                color_discrete_map=COLOR_MAP, barmode="group",
                title="Risk Breakdown Across Staff Types",
                labels={"staff_type": "Staff Type", "Count": "Privileges"}
            )
            st.plotly_chart(fig_staff, use_container_width=True)

    col_chart3, col_chart4 = st.columns(2)

    with col_chart3:
        st.subheader("Risk Count by Role")
        if not df_evaluated.empty:
            role_risk = df_evaluated.groupby(["role", "risk_level"]).size().reset_index(name="Count")
            fig_role = px.bar(
                role_risk, x="role", y="Count", color="risk_level",
                color_discrete_map=COLOR_MAP,
                title="Privilege Risk Levels Grouped by Role",
                labels={"role": "Staff Role", "Count": "Privilege Count"}
            )
            st.plotly_chart(fig_role, use_container_width=True)

    with col_chart4:
        st.subheader("Usage Events by Application")
        if not processor.clean_events.empty:
            app_usage = processor.clean_events.groupby("application").size().reset_index(name="Events")
            fig_app = px.bar(
                app_usage, x="application", y="Events", color="application",
                title="Total Verified Log Events per Application",
                labels={"application": "Application", "Events": "Log Event Count"}
            )
            st.plotly_chart(fig_app, use_container_width=True)


# ====================================================
# PAGE 2: PRIVILEGE REVIEW
# ====================================================
elif page == "2. Privilege Review":
    st.markdown('<div class="main-header">📋 Privilege Review Table</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Filterable access entitlements review list with usage baselines and risk indicators</div>', unsafe_allow_html=True)

    # Filter Controls Bar
    st.subheader("Filter Entitlements")
    f_col1, f_col2, f_col3, f_col4, f_col5, f_col6 = st.columns(6)

    all_roles = ["All"] + sorted(list(df_evaluated["role"].dropna().unique())) if not df_evaluated.empty else ["All"]
    all_staff = ["All"] + sorted(list(df_evaluated["staff_type"].dropna().unique())) if not df_evaluated.empty else ["All"]
    all_depts = ["All"] + sorted(list(df_evaluated["department"].dropna().unique())) if not df_evaluated.empty else ["All"]
    all_apps = ["All"] + sorted(list(df_evaluated["application"].dropna().unique())) if not df_evaluated.empty else ["All"]
    all_risks = ["All", "HIGH", "MEDIUM", "LOW"]
    all_recs = ["All", "REVOKE", "REVIEW", "APPROVE"]

    with f_col1:
        sel_role = st.selectbox("Role", all_roles)
    with f_col2:
        sel_staff = st.selectbox("Staff Type", all_staff)
    with f_col3:
        sel_dept = st.selectbox("Department", all_depts)
    with f_col4:
        sel_app = st.selectbox("Application", all_apps)
    with f_col5:
        sel_risk = st.selectbox("Risk Level", all_risks)
    with f_col6:
        sel_rec = st.selectbox("Recommendation", all_recs)

    # Filter dataset
    filtered = df_evaluated.copy()
    if sel_role != "All":
        filtered = filtered[filtered["role"] == sel_role]
    if sel_staff != "All":
        filtered = filtered[filtered["staff_type"] == sel_staff]
    if sel_dept != "All":
        filtered = filtered[filtered["department"] == sel_dept]
    if sel_app != "All":
        filtered = filtered[filtered["application"] == sel_app]
    if sel_risk != "All":
        filtered = filtered[filtered["risk_level"] == sel_risk]
    if sel_rec != "All":
        filtered = filtered[filtered["recommendation"] == sel_rec]

    st.write(f"Showing **{len(filtered)}** matching entitlements out of **{len(df_evaluated)}** total.")

    # Privilege review table with requested columns
    display_cols = [
        "user_id", "name", "role", "staff_type", "application",
        "permission", "user_usage", "peer_average", "risk_score",
        "risk_level", "recommendation"
    ]
    renamed_cols = {
        "user_id": "User ID",
        "name": "User Name",
        "role": "Role",
        "staff_type": "Staff Type",
        "application": "Application",
        "permission": "Permission",
        "user_usage": "Usage Count",
        "peer_average": "Peer Average",
        "risk_score": "Risk Score",
        "risk_level": "Risk Level",
        "recommendation": "Recommendation"
    }

    view_df = filtered[display_cols].rename(columns=renamed_cols)
    st.dataframe(view_df, use_container_width=True)


# ====================================================
# PAGE 3: EVIDENCE DETAILS
# ====================================================
elif page == "3. Evidence Details":
    st.markdown('<div class="main-header">🔍 Detailed Evidence Review</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Transparent evidence analysis, user information, entitlement level, and peer usage statistics</div>', unsafe_allow_html=True)

    if not df_evaluated.empty:
        user_options = df_evaluated.apply(lambda r: f"{r['entitlement_id']} - {r['name']} ({r['role']}) - {r['application']}", axis=1).tolist()
        sel_option = st.selectbox("Select Entitlement to Review Evidence", user_options)

        sel_ent_id = sel_option.split(" - ")[0]
        row = df_evaluated[df_evaluated["entitlement_id"] == sel_ent_id].iloc[0]

        render_evidence_card(row)
        # Added explanation of why this entitlement was flagged based on evidence metrics
        st.subheader("🔎 Why was this entitlement flagged?")
        st.write(f"- **Risk Score:** {row['risk_score']} (higher indicates greater risk)")
        st.write(f"- **System Recommendation:** `{row['recommendation']}`")
        st.write(f"- **Risk Level:** {row['risk_level']}")


# ====================================================
# PAGE 4: REVIEWER DECISION
# ====================================================
elif page == "4. Reviewer Decision":
    st.markdown('<div class="main-header">✍️ Reviewer Decision Panel</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Review evidence details and submit access review decisions to SQLite</div>', unsafe_allow_html=True)

    if not df_evaluated.empty:
        ent_options = df_evaluated.apply(lambda r: f"{r['entitlement_id']} | {r['name']} ({r['role']}) | {r['application']} [Rec: {r['recommendation']}]", axis=1).tolist()
        sel_target = st.selectbox("Select Entitlement to Review & Decide", ent_options)

        target_ent_id = sel_target.split(" | ")[0]
        t_row = df_evaluated[df_evaluated["entitlement_id"] == target_ent_id].iloc[0]

        # 1. DISPLAY DETAILED EVIDENCE FIRST (Reviewer must see evidence before deciding)
        st.subheader("📋 Evidence Review")
        render_evidence_card(t_row)

        st.markdown("---")
        st.subheader("✍️ Submit Reviewer Decision")

        # Display System Recommendation clearly
        system_rec = str(t_row["recommendation"])
        st.markdown(f"### **System Recommendation:** `{system_rec}`")

        with st.form("reviewer_decision_form"):
            reviewer_name = st.text_input("Reviewer Name", value="Security Auditor Admin")
            
            # Reviewer Decision choices: APPROVE, REVOKE, MODIFY, OVERRIDE
            decision_options = ["APPROVE", "REVOKE", "MODIFY", "OVERRIDE"]
            reviewer_decision = st.radio("Reviewer Decision", decision_options, index=0)

            reason_comment = st.text_area(
                "Reason / Comment",
                placeholder="Enter justification or comments for this decision..."
            )

            # Determine override flag based on user selection
            if reviewer_decision == "OVERRIDE":
                save_override = True
                st.info("ℹ️ OVERRIDE selected: Save override = TRUE. A reason/comment is required.")
            else:
                save_override = False

            submitted = st.form_submit_button("Save Review Decision")

            if submitted:
                # Validation checks
                if not reviewer_name.strip():
                    st.error("❌ Reviewer Name cannot be empty.")
                elif reviewer_decision == "OVERRIDE" and not reason_comment.strip():
                    st.error("❌ An override reason is required when OVERRIDE is selected.")
                else:
                    # Save decision to SQLite database review_decisions and audit_log
                    decision_id = record_reviewer_decision(
                        user_id=t_row["user_id"],
                        entitlement_id=t_row["entitlement_id"],
                        system_rec=system_rec,
                        reviewer_decision=reviewer_decision,
                        override=save_override,
                        reason=reason_comment.strip() if reason_comment.strip() else "Standard review decision",
                        reviewer=reviewer_name.strip(),
                        risk_score=int(t_row["risk_score"])
                    )

                    st.success(f"✅ Decision successfully saved to SQLite review_decisions table! (Decision ID: {decision_id}, Override: {save_override})")
                    st.cache_data.clear()


# ====================================================
# PAGE 5: AUDIT TRAIL
# ====================================================
elif page == "5. Audit Trail":
    st.markdown('<div class="main-header">📜 Immutable Audit Log Trail</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Historical record of all reviewer access decisions stored immutably in SQLite</div>', unsafe_allow_html=True)

    audit_df = get_audit_trail()

    if audit_df is None or audit_df.empty:
        st.info("No reviewer decision records found in SQLite audit trail yet. Submit a decision from Page 4 to populate.")
    else:
        # Prepare Audit Trail Metrics Summary
        total_decisions = len(audit_df)
        approvals = len(audit_df[audit_df["reviewer_decision"] == "APPROVE"])
        revocations = len(audit_df[audit_df["reviewer_decision"] == "REVOKE"])
        modifications = len(audit_df[audit_df["reviewer_decision"] == "MODIFY"])
        overrides = len(audit_df[(audit_df["override"] == 1) | (audit_df["reviewer_decision"] == "OVERRIDE")])

        # Summary Metric Cards Bar
        m1, m2, m3, m4, m5 = st.columns(5)
        with m1:
            st.metric("Total Decisions", f"{total_decisions:,}")
        with m2:
            st.metric("Approvals", f"{approvals:,}")
        with m3:
            st.metric("Revocations", f"{revocations:,}")
        with m4:
            st.metric("Modifications", f"{modifications:,}")
        with m5:
            st.metric("Overrides", f"{overrides:,}")

        st.markdown("---")
        st.subheader("Filter Audit Trail")

        af_col1, af_col2, af_col3, af_col4 = st.columns(4)

        all_reviewers = ["All"] + sorted(list(audit_df["reviewer"].dropna().astype(str).unique()))
        all_decisions = ["All", "APPROVE", "REVOKE", "MODIFY", "OVERRIDE"]
        all_overrides = ["All", "YES", "NO"]

        with af_col1:
            sel_audit_reviewer = st.selectbox("Filter by Reviewer", all_reviewers)
        with af_col2:
            sel_audit_decision = st.selectbox("Filter by Decision", all_decisions)
        with af_col3:
            sel_audit_override = st.selectbox("Filter by Override", all_overrides)
        with af_col4:
            sel_audit_date = st.text_input("Filter by Date (YYYY-MM-DD)", value="")

        # Apply Filters
        filtered_audit = audit_df.copy()

        if sel_audit_reviewer != "All":
            filtered_audit = filtered_audit[filtered_audit["reviewer"] == sel_audit_reviewer]

        if sel_audit_decision != "All":
            filtered_audit = filtered_audit[filtered_audit["reviewer_decision"] == sel_audit_decision]

        if sel_audit_override == "YES":
            filtered_audit = filtered_audit[(filtered_audit["override"] == 1) | (filtered_audit["reviewer_decision"] == "OVERRIDE")]
        elif sel_audit_override == "NO":
            filtered_audit = filtered_audit[(filtered_audit["override"] == 0) & (filtered_audit["reviewer_decision"] != "OVERRIDE")]

        if sel_audit_date.strip():
            filtered_audit = filtered_audit[filtered_audit["timestamp"].astype(str).str.contains(sel_audit_date.strip())]

        # Format Display DataFrame
        filtered_audit["Override_Display"] = filtered_audit["override"].apply(lambda v: "YES" if v == 1 else "NO")

        display_audit_cols = [
            "decision_id", "user_name", "entitlement_id", "risk_score",
            "system_recommendation", "reviewer_decision", "Override_Display",
            "reason", "reviewer", "timestamp"
        ]

        renamed_audit_cols = {
            "decision_id": "Decision ID",
            "user_name": "User",
            "entitlement_id": "Entitlement",
            "risk_score": "Risk Score",
            "system_recommendation": "System Recommendation",
            "reviewer_decision": "Reviewer Decision",
            "Override_Display": "Override",
            "reason": "Reason",
            "reviewer": "Reviewer",
            "timestamp": "Decision Timestamp"
        }

        view_audit_df = filtered_audit[display_audit_cols].rename(columns=renamed_audit_cols)

        st.write(f"Showing **{len(view_audit_df)}** matching audit entries (newest decisions listed first).")
        st.dataframe(view_audit_df, use_container_width=True)
    # CSV download button for filtered audit trail
    csv = filtered_audit.to_csv(index=False).encode('utf-8')
    st.download_button(label="Download CSV", data=csv, file_name='audit_trail_filtered.csv', mime='text/csv')


# ====================================================
# PAGE 6: DATA QUALITY
# ====================================================
elif page == "6. Data Quality":
    st.markdown('<div class="main-header">🧪 Data Quality & Ingestion Report</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Event validation, deduplication stats, timestamp lag, and corrupt record detection</div>', unsafe_allow_html=True)

    qs = processor.quality_summary

    q1, q2, q3, q4, q5, q6 = st.columns(6)
    with q1:
        st.metric("Total Raw Events", f"{qs.get('total_events', 0):,}")
    with q2:
        st.metric("Duplicate Events", f"{qs.get('duplicate_events', 0):,}")
    with q3:
        st.metric("Invalid Events", f"{qs.get('invalid_events', 0):,}")
    with q4:
        st.metric("Delayed Events", f"{qs.get('delayed_events', 0):,}")
    with q5:
        st.metric("Out-of-Order Events", f"{qs.get('out_of_order_events', 0):,}")
    with q6:
        st.metric("Clean Valid Events", f"{qs.get('valid_events', 0):,}")

    st.markdown("---")
    st.subheader("Data Cleaning Summary")
    # Failure Handling & Recovery subsection
    st.subheader("Failure Handling & Recovery")
    st.write("- **Delayed Events**: Events arriving later than expected timestamps are re‑ordered correctly.\n- **Duplicate Events**: Duplicates are identified and removed without affecting usage stats.\n- **Out‑of‑Order Events**: Chronological normalization ensures accurate baseline counters.\n- **Invalid Events**: Missing IDs or malformed timestamps are flagged and excluded safely.")
    st.write("• **Deduplication:** Dropped duplicate `event_id` and duplicate payload events without double-counting usage statistics.")
    st.write("• **Corrupt Record Protection:** Flagged missing user IDs and bad timestamp strings safely without crashing pipeline.")
    st.write("• **Chronological Normalization:** Re-ordered valid log events strictly by `event_timestamp` to maintain accurate baseline counters.")


# ====================================================
# PAGE 7: BASELINE COMPARISON EXPERIMENT
# ====================================================
elif page == "7. Baseline Comparison":
    st.markdown('<div class="main-header">📈 Baseline vs. Prototype Experiment</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Evaluating reduction in blanket approvals: Traditional Spreadsheet Process vs. Evidence-Based Prototype</div>', unsafe_allow_html=True)

    exp_res = run_baseline_experiment(df_evaluated)

    # Load actual calculated before/after metrics
    ba_inputs = load_experiment_inputs()
    ba_metrics = calculate_before_after_metrics(ba_inputs)

    # ----------------------------------------------------
    # MEASURED IMPACT SUMMARY SECTION
    # ----------------------------------------------------
    st.markdown("---")
    st.subheader("🎯 Measured Impact")
    # Explicit statement about reduction
    st.write(f"The prototype reduces approvals by **{ba_metrics['approval_rate_reduction_percentage_points']} pp** (baseline **{ba_metrics['baseline_approval_rate']}%** → prototype **{ba_metrics['prototype_approval_rate']}%**).")
    # Show prototype decision breakdown counts
    st.write(f"Prototype Decision Distribution: APPROVE={ba_metrics.get('prototype_approvals', 'N/A')}, REVOKE={ba_metrics.get('prototype_revocations', 'N/A')}, MODIFY={ba_metrics.get('prototype_modifications', 'N/A')}")
    st.caption("Quantitative reduction in approvals from evidence-based automation vs spreadsheet baseline.")

    mi1, mi2, mi3, mi4, mi5 = st.columns(5)
    with mi1:
        st.metric("Baseline Approval Rate", f"{ba_metrics['baseline_approval_rate']}%")
    with mi2:
        st.metric("Evidence-Based Approval Rate", f"{ba_metrics['prototype_approval_rate']}%")
    with mi3:
        st.metric(
            "Reduction (Percentage Points)",
            f"{ba_metrics['approval_rate_reduction_percentage_points']} pp",
            delta=f"-{ba_metrics['approval_rate_reduction_percentage_points']} pp",
            delta_color="normal"
        )
    with mi4:
        st.metric(
            "Relative Reduction",
            f"{ba_metrics['relative_approval_rate_reduction']}%",
            delta=f"-{ba_metrics['relative_approval_rate_reduction']}%",
            delta_color="normal"
        )
    with mi5:
        st.metric("Total Cases Evaluated", f"{ba_metrics['total_cases']:,}")

    # Mandatory Methodology Disclaimer
    st.info(
        "ℹ️ **Methodology Note:** This comparison uses controlled synthetic hospital access-review data. "
        "The baseline represents a simulated spreadsheet-style review approach and does not represent historical hospital data."
    )

    # ----------------------------------------------------
    # VISUALIZATIONS SECTION (4 REQUIRED CHARTS)
    # ----------------------------------------------------
    st.markdown("---")
    st.subheader("📉 Experiment Visualization Charts")

    v_row1_col1, v_row1_col2 = st.columns(2)
    with v_row1_col1:
        # Chart 1: Baseline vs Prototype Approval Rate
        fig_approval = create_approval_rate_chart(ba_metrics)
        st.plotly_chart(fig_approval, use_container_width=True)

    with v_row1_col2:
        # Chart 2: Prototype Decision Distribution
        fig_decisions = create_decision_distribution_chart(ba_metrics)
        st.plotly_chart(fig_decisions, use_container_width=True)

    v_row2_col1, v_row2_col2 = st.columns(2)
    with v_row2_col1:
        # Chart 3: Risk Distribution
        fig_risk = create_risk_distribution_chart(ba_metrics)
        st.plotly_chart(fig_risk, use_container_width=True)

    with v_row2_col2:
        # Chart 4: Expanded Experiment Scenario Comparison (E1 to E10)
        fig_scenarios = create_scenario_comparison_chart(ba_inputs.get("expanded", {}))
        st.plotly_chart(fig_scenarios, use_container_width=True)

    st.markdown("---")
    st.subheader("📊 Before-vs-After Comparison Table")
    st.write("All metrics calculated dynamically from the actual generated dataset.")
    st.dataframe(exp_res["summary_df"], use_container_width=True)

    st.markdown("---")
    st.subheader("📋 Role-Level Baseline Metrics & Usage Distribution")
    if not df_evaluated.empty:
        role_stats = df_evaluated.groupby(["role", "application"]).agg(
            Avg_User_Usage=("user_usage", "mean"),
            Role_Peer_Average=("peer_average", "mean"),
            Role_Peer_Median=("peer_median", "mean")
        ).reset_index()

        fig_base = px.bar(
            role_stats, x="role", y="Avg_User_Usage", color="application",
            barmode="group", title="Average Usage Count by Role & Application",
            labels={"role": "Hospital Role", "Avg_User_Usage": "Average Accesses"}
        )
        st.plotly_chart(fig_base, use_container_width=True)
        st.dataframe(role_stats.round(1), use_container_width=True)
