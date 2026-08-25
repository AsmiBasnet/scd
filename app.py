import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time
import textwrap

DB_NAME = "scd_workforce.db"

# ==========================================
# 1. PAGE CONFIG & SESSION STATE
# ==========================================
st.set_page_config(
    page_title="SCD Workforce Analytics & Sentiment Engine",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="collapsed",
)

if "theme" not in st.session_state:
    st.session_state.theme = "light"

def toggle_theme():
    st.session_state.theme = "dark" if st.session_state.theme == "light" else "light"

IS_DARK = st.session_state.theme == "dark"

# ==========================================
# 2. DESIGN SYSTEM & CSS INJECTION
# ==========================================
bg = "#09090b" if IS_DARK else "#ffffff"
bg_subtle = "#0c0c0f" if IS_DARK else "#f9fafb"
card = "#0c0c0f" if IS_DARK else "#ffffff"
card_hover = "#131316" if IS_DARK else "#f4f4f5"
border = "#1e1e24" if IS_DARK else "#e4e4e7"
border_subtle = "#16161a" if IS_DARK else "#f0f0f2"
text = "#fafafa" if IS_DARK else "#09090b"
text_muted = "#71717a"
text_dim = "#52525b" if IS_DARK else "#a1a1aa"
accent = "#2563eb"
accent_muted = "#1d4ed8"
green = "#22c55e" if IS_DARK else "#16a34a"
green_muted = "rgba(34,197,94,0.12)" if IS_DARK else "rgba(22,163,74,0.08)"
red = "#ef4444" if IS_DARK else "#dc2626"
red_muted = "rgba(239,68,68,0.12)" if IS_DARK else "rgba(220,38,38,0.08)"
amber = "#f59e0b" if IS_DARK else "#d97706"
amber_muted = "rgba(245,158,11,0.12)" if IS_DARK else "rgba(217,119,6,0.08)"
shadow = "none" if IS_DARK else "0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.03)"

css = f"""
<style>
:root {{
    --bg: {bg};
    --bg-subtle: {bg_subtle};
    --card: {card};
    --card-hover: {card_hover};
    --border: {border};
    --border-subtle: {border_subtle};
    --text: {text};
    --text-muted: {text_muted};
    --text-dim: {text_dim};
    --accent: {accent};
    --accent-muted: {accent_muted};
    --green: {green};
    --green-muted: {green_muted};
    --red: {red};
    --red-muted: {red_muted};
    --amber: {amber};
    --amber-muted: {amber_muted};
    --shadow: {shadow};
    --radius: 10px;
}}

/* Hide Streamlit default components */
header[data-testid="stHeader"], #MainMenu, footer, [data-testid="stToolbar"],
[data-testid="stDecoration"], [data-testid="stStatusWidget"], .stDeployButton,
div[data-testid="stSidebarCollapsedControl"] {{
    display: none !important;
}}

/* Global App Styling */
html, body, [data-testid="stAppViewContainer"], [data-testid="stApp"], .main, .block-container, section[data-testid="stMain"] {{
    background-color: var(--bg) !important;
    color: var(--text) !important;
    font-family: 'DM Sans', -apple-system, sans-serif !important;
}}

.block-container {{
    padding: 1.5rem 2rem 2rem !important;
    max-width: 1360px !important;
}}

/* Gap adjustment */
[data-testid="stHorizontalBlock"] {{
    gap: 1.25rem !important;
}}

/* Metric Cards */
.metric-card {{
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.2rem 1.4rem;
    box-shadow: var(--shadow);
    transition: transform 0.2s ease, border-color 0.2s ease;
}}
.metric-card:hover {{
    border-color: var(--accent);
    transform: translateY(-2px);
}}
.metric-label {{
    font-size: 0.72rem;
    color: var(--text-muted);
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}}
.metric-value {{
    font-size: 1.85rem;
    font-weight: 700;
    color: var(--text);
    letter-spacing: -0.03em;
    margin-top: 0.25rem;
}}
.metric-delta {{
    font-size: 0.72rem;
    font-weight: 500;
    margin-top: 0.4rem;
    padding: 2px 8px;
    border-radius: 6px;
    display: inline-flex;
    align-items: center;
    gap: 3px;
}}
.delta-up {{ color: var(--green); background: var(--green-muted); }}
.delta-down {{ color: var(--red); background: var(--red-muted); }}
.delta-warn {{ color: var(--amber); background: var(--amber-muted); }}

/* Chart Containers */
.chart-wrap {{
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1.2rem;
    box-shadow: var(--shadow);
    margin-bottom: 1.25rem;
}}
.chart-title {{
    font-size: 0.88rem;
    font-weight: 600;
    color: var(--text);
}}
.chart-subtitle {{
    font-size: 0.75rem;
    color: var(--text-dim);
    margin-bottom: 1rem;
}}

/* Data Tables */
.data-table {{
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    font-size: 0.82rem;
    margin-top: 0.5rem;
}}
.data-table th {{
    text-align: left;
    padding: 0.6rem 0.8rem;
    color: var(--text-muted);
    font-weight: 600;
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    border-bottom: 1px solid var(--border);
    background: var(--bg-subtle);
}}
.data-table td {{
    padding: 0.7rem 0.8rem;
    color: var(--text);
    border-bottom: 1px solid var(--border-subtle);
    vertical-align: middle;
}}
.data-table tr:last-child td {{
    border-bottom: none;
}}
.data-table tr:hover td {{
    background-color: var(--card-hover);
}}

/* Badges */
.badge {{
    display: inline-block;
    padding: 2px 8px;
    border-radius: 6px;
    font-size: 0.7rem;
    font-weight: 500;
    text-align: center;
}}
.badge-green {{ color: var(--green); background: var(--green-muted); }}
.badge-red {{ color: var(--red); background: var(--red-muted); }}
.badge-amber {{ color: var(--amber); background: var(--amber-muted); }}
.badge-blue {{ color: var(--accent); background: rgba(37,99,235,0.1); }}

/* Brand Header */
.brand {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.5rem 0 1.25rem 0;
    border-bottom: 1px solid var(--border);
    margin-bottom: 1.5rem;
}}
.brand-left {{
    display: flex;
    align-items: center;
    gap: 0.5rem;
}}
.brand-logo {{
    font-size: 1.5rem;
    color: var(--accent);
    font-weight: 800;
}}
.brand-name {{
    font-size: 1.2rem;
    font-weight: 700;
    color: var(--text);
    letter-spacing: -0.02em;
}}
.brand-tag {{
    font-size: 0.65rem;
    color: var(--text-muted);
    background: var(--bg-subtle);
    padding: 2px 8px;
    border-radius: 5px;
    border: 1px solid var(--border);
    margin-left: 0.5rem;
}}

/* Tabs Styling override */
button[data-baseweb="tab"] {{
    background: transparent !important;
    color: var(--text-muted) !important;
    font-size: 0.825rem !important;
    font-weight: 500 !important;
    padding: 0.5rem 1.1rem !important;
    border: 1px solid transparent !important;
    border-radius: 7px !important;
    margin: 0 !important;
    transition: all 0.2s ease !important;
}}
button[data-baseweb="tab"][aria-selected="true"] {{
    color: var(--text) !important;
    background: var(--card) !important;
    border-color: var(--border) !important;
    box-shadow: var(--shadow) !important;
}}
button[data-baseweb="tab"]:hover {{
    color: var(--text) !important;
    background: var(--card-hover) !important;
}}
[data-baseweb="tab-highlight"], [data-baseweb="tab-border"] {{
    display: none !important;
}}
[data-baseweb="tab-list"] {{
    gap: 4px !important;
    background: var(--bg-subtle) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    padding: 4px !important;
    margin-bottom: 1.5rem !important;
}}

/* Custom container overrides for Streamlit sliders, selectboxes, etc. */
div[data-testid="stForm"] {{
    border: 1px solid var(--border) !important;
    background-color: var(--card) !important;
    border-radius: var(--radius) !important;
}}
</style>
"""
st.markdown(css, unsafe_allow_html=True)

# Plotly styling reference dictionary
PLOT_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="DM Sans, -apple-system, sans-serif", color="#71717a" if not IS_DARK else "#a1a1aa", size=10),
    margin=dict(l=40, r=20, t=20, b=30),
    xaxis=dict(
        gridcolor="rgba(0,0,0,0.04)" if not IS_DARK else "rgba(255,255,255,0.04)",
        zerolinecolor="rgba(0,0,0,0.04)" if not IS_DARK else "rgba(255,255,255,0.04)",
        tickfont=dict(size=10, color="#71717a" if not IS_DARK else "#a1a1aa"),
        showgrid=True,
    ),
    yaxis=dict(
        gridcolor="rgba(0,0,0,0.04)" if not IS_DARK else "rgba(255,255,255,0.04)",
        zerolinecolor="rgba(0,0,0,0.04)" if not IS_DARK else "rgba(255,255,255,0.04)",
        tickfont=dict(size=10, color="#71717a" if not IS_DARK else "#a1a1aa"),
        showgrid=True,
    ),
    legend=dict(
        bgcolor="rgba(0,0,0,0)",
        font=dict(size=10)
    )
)

# ==========================================
# 3. HELPER FUNCTIONS
# ==========================================
def get_db_connection():
    return sqlite3.connect(DB_NAME)

def load_sql_queries():
    try:
        with open("transformations.sql", "r") as f:
            content = f.read()
        queries = {}
        # Normalize carriage returns for cross-platform compatibility
        content = content.replace("\r", "")
        parts = content.split("-- @name:")
        for part in parts[1:]:
            lines = part.strip().split("\n")
            name = lines[0].strip()
            query_text = "\n".join(lines[1:]).strip()
            # Extract only up to the first semicolon to clean up trailing comments and spacing
            if ";" in query_text:
                query_text = query_text.split(";")[0].strip() + ";"
            queries[name] = query_text
        return queries
    except Exception as e:
        st.error(f"Error loading SQL file: {e}")
        return {}

def render_html(html_str):
    clean_html = "\n".join(line.lstrip() for line in html_str.split("\n"))
    st.markdown(clean_html, unsafe_allow_html=True)

def metric_card(label, value, delta=None, delta_type="up"):
    cls = f"delta-{delta_type}"
    arrow = "↑" if delta_type == "up" else ("↓" if delta_type == "down" else "→")
    delta_html = f'<div class="metric-delta {cls}">{arrow} {delta}</div>' if delta else ""
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)

# Load SQL queries from external file
SQL_QUERIES = load_sql_queries()

# ==========================================
# 4. BRAND HEADER
# ==========================================
st.markdown(f"""
<div class="brand">
    <div class="brand-left">
        <span class="brand-logo">◆</span>
        <span class="brand-name">SCD Workforce Sentiment & Analytics</span>
        <span class="brand-tag">v1.0.0 Prototyped</span>
    </div>
</div>
""", unsafe_allow_html=True)

# We use standard columns to align the theme toggle neatly
h1, h2 = st.columns([10, 2])
with h2:
    theme_btn_label = "☀️ Light Theme" if IS_DARK else "🌙 Dark Theme"
    st.button(theme_btn_label, on_click=toggle_theme, use_container_width=True)

# Main Page Navigation Tab
tabs = st.tabs([
    "📊 Executive Overview", 
    "🎯 Initiative Deep-Dive", 
    "💬 Qualitative Sentiment Tracker", 
    "⚙️ SQL & Pipeline Engine"
])

# Check if database exists
try:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM Fact_Employee_Events")
    total_records = cursor.fetchone()[0]
    conn.close()
except sqlite3.OperationalError:
    st.warning("Database not initialized. Please run the generation script from the SQL engine page or wait.")
    total_records = 0

# ==========================================
# TAB 1: EXECUTIVE OVERVIEW
# ==========================================
with tabs[0]:
    if total_records > 0:
        # Load high-level database stats
        conn = get_db_connection()
        
        # 1. Total Active Staff
        active_staff = pd.read_sql("SELECT COUNT(*) FROM Fact_Employee_Events WHERE retention_status='Active'", conn).iloc[0,0]
        exited_staff = pd.read_sql("SELECT COUNT(*) FROM Fact_Employee_Events WHERE retention_status='Exited'", conn).iloc[0,0]
        total_staff = active_staff + exited_staff
        exit_pct = (exited_staff / total_staff) * 100.0 if total_staff > 0 else 0
        
        # 2. Overall 90-Day Retention post-Orientation
        ret_90_query = """
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN retention_status = 'Exited' AND (julianday(exit_date) - julianday(orientation_date)) <= 90 THEN 1 ELSE 0 END) as exits
            FROM Fact_Employee_Events
            WHERE orientation_completed = 1 AND orientation_date IS NOT NULL
        """
        ret_90_df = pd.read_sql(ret_90_query, conn)
        ret_90_total = ret_90_df.iloc[0, 0]
        ret_90_exits = ret_90_df.iloc[0, 1]
        overall_ret_90 = ((ret_90_total - ret_90_exits) / ret_90_total) * 100.0 if ret_90_total > 0 else 0
        
        # 3. Average Sentiment
        avg_sentiment = pd.read_sql("SELECT AVG(sentiment_score) FROM Fact_Sentiment_Feedback WHERE relevance_score >= 0.2", conn).iloc[0,0]
        
        # 4. SCD Event Attendance (Orientation + Navigator School)
        event_attendance = pd.read_sql("SELECT SUM(orientation_completed) + SUM(navigator_school_completed) FROM Fact_Employee_Events", conn).iloc[0,0]
        
        conn.close()
        
        # Metric Cards Row
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            metric_card("Active Employee Base", f"{active_staff:,}", f"{(100 - exit_pct):.1f}% Retention", "up")
        with c2:
            metric_card("90-Day Orientation Retention", f"{overall_ret_90:.1f}%", "-0.8% QoQ Delta", "warn")
        with c3:
            metric_card("Average Sentiment Score", f"{avg_sentiment:.2f}", "+0.12 vs Target", "up")
        with c4:
            metric_card("Total SCD Program Attendance", f"{int(event_attendance):,}", "88.2% Active Completion", "up")
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Main Visualizations Row
        col_left, col_right = st.columns([7, 5])
        
        with col_left:
            st.markdown("""
            <div class="chart-wrap">
                <div class="chart-title">Orientation Rolling Retention Rates</div>
                <div class="chart-subtitle">30-day and 90-day post-orientation employee retention rates (3-month rolling averages).</div>
            """, unsafe_allow_html=True)
            
            # Execute rolling retention query
            conn = get_db_connection()
            df_rolling = pd.read_sql(SQL_QUERIES["rolling_retention"], conn)
            conn.close()
            
            # Plot
            fig_rolling = go.Figure()
            fig_rolling.add_trace(go.Scatter(
                x=df_rolling["orientation_month"], 
                y=df_rolling["rolling_3m_retention_30"], 
                mode='lines', 
                name='30-Day Rolling',
                line=dict(color=accent, width=2.5)
            ))
            fig_rolling.add_trace(go.Scatter(
                x=df_rolling["orientation_month"], 
                y=df_rolling["rolling_3m_retention_90"], 
                mode='lines', 
                name='90-Day Rolling',
                line=dict(color=green, width=2.5)
            ))
            fig_rolling.update_layout(PLOT_LAYOUT, height=320)
            fig_rolling.update_yaxes(title="Retention Rate %", range=[75, 101])
            st.plotly_chart(fig_rolling, use_container_width=True, config={"displayModeBar": False})
            st.markdown("</div>", unsafe_allow_html=True)

        with col_right:
            st.markdown("""
            <div class="chart-wrap">
                <div class="chart-title">Hiring Cohort Retention Curves</div>
                <div class="chart-subtitle">Survival curve indicating active employee percentages over a 12-month window.</div>
            """, unsafe_allow_html=True)
            
            # Execute cohort retention query
            conn = get_db_connection()
            df_cohort = pd.read_sql(SQL_QUERIES["cohort_retention"], conn)
            conn.close()
            
            # Keep latest 5 complete cohorts for cleaner chart
            cohorts_to_plot = df_cohort.dropna().tail(5)
            
            fig_cohort = go.Figure()
            colors = [accent, green, "#8b5cf6", amber, "#ec4899"]
            offsets = ["m0_pct", "m1_pct", "m2_pct", "m3_pct", "m4_pct", "m5_pct", "m6_pct", "m9_pct", "m12_pct"]
            offset_labels = [0, 1, 2, 3, 4, 5, 6, 9, 12]
            
            for i, (_, row) in enumerate(cohorts_to_plot.iterrows()):
                y_vals = [row[off] for off in offsets]
                fig_cohort.add_trace(go.Scatter(
                    x=offset_labels, 
                    y=y_vals, 
                    mode='lines+markers', 
                    name=f"Cohort {row['cohort_month']}",
                    line=dict(color=colors[i % len(colors)], width=2),
                    marker=dict(size=5)
                ))
            fig_cohort.update_layout(PLOT_LAYOUT, height=320)
            fig_cohort.update_xaxes(title="Months Since Hire", tickvals=offset_labels)
            fig_cohort.update_yaxes(title="Active %", range=[50, 105])
            st.plotly_chart(fig_cohort, use_container_width=True, config={"displayModeBar": False})
            st.markdown("</div>", unsafe_allow_html=True)
            
        # Additional Overview Stats
        conn = get_db_connection()
        div_df = pd.read_sql("""
            SELECT 
                d.division,
                COUNT(e.employee_id) as total_headcount,
                SUM(CASE WHEN e.retention_status = 'Active' THEN 1 ELSE 0 END) as active_headcount,
                ROUND(AVG(e.performance_rating), 2) as avg_perf_rating,
                SUM(e.orientation_completed) as orientation_total,
                SUM(e.navigator_school_completed) as navigator_total
            FROM Dim_Department d
            JOIN Fact_Employee_Events e ON d.dept_id = e.dept_id
            GROUP BY d.division
        """, conn)
        conn.close()
        
        rows_html = ""
        for _, row in div_df.iterrows():
            retention_rate = (row['active_headcount'] / row['total_headcount']) * 100.0 if row['total_headcount'] > 0 else 0
            orient_rate = (row['orientation_total'] / row['total_headcount']) * 100.0 if row['total_headcount'] > 0 else 0
            nav_rate = (row['navigator_total'] / row['total_headcount']) * 100.0 if row['total_headcount'] > 0 else 0
            
            badge_class = "badge-green" if retention_rate > 90 else ("badge-amber" if retention_rate > 85 else "badge-red")
            
            rows_html += f"""
            <tr>
                <td><b>{row['division']}</b></td>
                <td>{row['total_headcount']:,}</td>
                <td>{row['active_headcount']:,}</td>
                <td><span class="badge {badge_class}">{retention_rate:.1f}%</span></td>
                <td>★ {row['avg_perf_rating']:.2f}</td>
                <td>{orient_rate:.1f}%</td>
                <td>{nav_rate:.1f}%</td>
            </tr>
            """
            
        div_table_html = textwrap.dedent(f"""
        <div class="chart-wrap">
            <div class="chart-title">Executive Breakdown by Division</div>
            <div class="chart-subtitle">Staff counts and performance ratings across academic, operations, and support divisions.</div>
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Division</th>
                        <th>Total Headcount</th>
                        <th>Active Headcount</th>
                        <th>Retention Rate %</th>
                        <th>Average Performance Rating</th>
                        <th>Orientation Completion %</th>
                        <th>Navigator School Completion %</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
        </div>
        """)
        render_html(div_table_html)

# ==========================================
# TAB 2: INITIATIVE DEEP-DIVE
# ==========================================
with tabs[1]:
    if total_records > 0:
        conn = get_db_connection()
        
        # Fetch department completion details
        dept_rates = pd.read_sql("""
            SELECT 
                d.dept_name,
                d.division,
                COUNT(e.employee_id) as total_staff,
                SUM(e.orientation_completed) as orient_completed,
                SUM(e.navigator_school_completed) as nav_completed,
                SUM(CASE WHEN e.retention_status = 'Active' THEN 1 ELSE 0 END) as active_staff
            FROM Dim_Department d
            JOIN Fact_Employee_Events e ON d.dept_id = e.dept_id
            GROUP BY d.dept_id, d.dept_name
        """, conn)
        
        conn.close()
        
        dept_rates["Orientation %"] = (dept_rates["orient_completed"] / dept_rates["total_staff"]) * 100.0
        dept_rates["Navigator %"] = (dept_rates["nav_completed"] / dept_rates["total_staff"]) * 100.0
        dept_rates["Retention %"] = (dept_rates["active_staff"] / dept_rates["total_staff"]) * 100.0
        
        col_d1, col_d2 = st.columns(2)
        
        with col_d1:
            st.markdown("""
            <div class="chart-wrap">
                <div class="chart-title">New Employee Orientation Completion Rate %</div>
                <div class="chart-subtitle">Orientation completion status across major Full Sail departments.</div>
            """, unsafe_allow_html=True)
            
            fig_orient = px.bar(
                dept_rates.sort_values(by="Orientation %"),
                x="Orientation %",
                y="dept_name",
                orientation='h',
                color_discrete_sequence=[accent]
            )
            fig_orient.update_layout(PLOT_LAYOUT, height=340)
            fig_orient.update_xaxes(title="Completion %", range=[0, 105])
            fig_orient.update_yaxes(title="")
            st.plotly_chart(fig_orient, use_container_width=True, config={"displayModeBar": False})
            st.markdown("</div>", unsafe_allow_html=True)
            
        with col_d2:
            st.markdown("""
            <div class="chart-wrap">
                <div class="chart-title">Navigator School Completion vs Subsequent Retention Rate</div>
                <div class="chart-subtitle">Evaluating the correlation between Navigator training completion and departmental retention.</div>
            """, unsafe_allow_html=True)
            
            fig_scatter = px.scatter(
                dept_rates,
                x="Navigator %",
                y="Retention %",
                size="total_staff",
                color="division",
                hover_name="dept_name",
                color_discrete_sequence=[accent, green, amber],
                size_max=35
            )
            fig_scatter.update_layout(PLOT_LAYOUT, height=340)
            fig_scatter.update_xaxes(title="Navigator School Completion %", range=[0, 100])
            fig_scatter.update_yaxes(title="Department Retention %", range=[60, 105])
            st.plotly_chart(fig_scatter, use_container_width=True, config={"displayModeBar": False})
            st.markdown("</div>", unsafe_allow_html=True)

        # Department Rankings Table
        conn = get_db_connection()
        dept_rankings_df = pd.read_sql(SQL_QUERIES["dept_rankings"], conn)
        conn.close()
        
        table_rows = ""
        for _, row in dept_rankings_df.iterrows():
            delta = row['retention_delta']
            delta_badge = f'<span class="badge badge-green">+{delta:.1f}%</span>' if delta > 10 else (
                f'<span class="badge badge-blue">+{delta:.1f}%</span>' if delta > 0 else f'<span class="badge badge-red">{delta:.1f}%</span>'
            )
            
            table_rows += f"""
            <tr>
                <td><b>{row['delta_rank']}</b></td>
                <td>{row['dept_name']}</td>
                <td>{row['division']}</td>
                <td>{row['total_employees']:,}</td>
                <td>{row['orientation_participation_rate']:.1f}%</td>
                <td>{row['navigator_participation_rate']:.1f}%</td>
                <td>{row['trained_retention_rate']:.1f}%</td>
                <td>{row['untrained_retention_rate']:.1f}%</td>
                <td>{delta_badge}</td>
            </tr>
            """
            
        rank_table_html = textwrap.dedent(f"""
        <div class="chart-wrap">
            <div class="chart-title">Department Rankings & Training Performance Impact</div>
            <div class="chart-subtitle">Trained vs Untrained retention rates and the delta retention benefit (measured by Dense Window Rankings).</div>
            <table class="data-table">
                <thead>
                    <tr>
                        <th>Rank</th>
                        <th>Department</th>
                        <th>Division</th>
                        <th>Total Staff</th>
                        <th>Orientation Completers %</th>
                        <th>Navigator School Completers %</th>
                        <th>Trained Retention %</th>
                        <th>Untrained Retention %</th>
                        <th>Retention Delta Benefit</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>
        </div>
        """)
        render_html(rank_table_html)

# ==========================================
# TAB 3: QUALITATIVE SENTIMENT TRACKER
# ==========================================
with tabs[2]:
    if total_records > 0:
        # Dynamic guardrail UI block
        st.markdown("""
        <div class="chart-wrap" style="padding-bottom: 1.5rem;">
            <div class="chart-title">NLP Sentiment Relevance Guardrail Settings</div>
            <div class="chart-subtitle">Filter out outlier comments (e.g. food requests, badge losses) using TF-IDF Cosine Similarity Thresholding. Adjust the slider to see dynamic statistical adjustments.</div>
        """, unsafe_allow_html=True)
        
        g1, g2 = st.columns([7, 3])
        with g1:
            threshold = st.slider(
                "Similarity Relevance Threshold (Guardrail)", 
                min_value=0.0, 
                max_value=1.0, 
                value=0.20, 
                step=0.05,
                help="Adjusting this slider updates the dashboard. A higher threshold excludes outlier comments, focusing exclusively on core HR/SCD topics."
            )
        with g2:
            # Calculate metrics based on slider threshold
            conn = get_db_connection()
            total_comments = pd.read_sql("SELECT COUNT(*) FROM Fact_Sentiment_Feedback", conn).iloc[0,0]
            filtered_comments_df = pd.read_sql(f"""
                SELECT 
                    COUNT(*) as cnt, 
                    AVG(sentiment_score) as avg_sent,
                    SUM(CASE WHEN sentiment_class = 'Positive' THEN 1 ELSE 0 END) as pos,
                    SUM(CASE WHEN sentiment_class = 'Negative' THEN 1 ELSE 0 END) as neg,
                    SUM(CASE WHEN sentiment_class = 'Neutral' THEN 1 ELSE 0 END) as neu
                FROM Fact_Sentiment_Feedback 
                WHERE relevance_score >= {threshold}
            """, conn)
            conn.close()
            
            cnt = filtered_comments_df.iloc[0, 0]
            avg_sent = filtered_comments_df.iloc[0, 1] or 0.0
            
            st.markdown(f"""
            <div style="text-align: right; padding-top: 0.5rem;">
                <span style="font-size: 0.8rem; color: var(--text-muted); font-weight:600;">FILTERED:</span>
                <span style="font-size: 1.1rem; font-weight:700; color: var(--accent); margin-left: 0.25rem;">{cnt} / {total_comments} Comments ({cnt/total_comments*100:.1f}%)</span>
                <br>
                <span style="font-size: 0.8rem; color: var(--text-muted); font-weight:600;">AGGREGATE SENTIMENT:</span>
                <span style="font-size: 1.1rem; font-weight:700; color: {green if avg_sent >= 0.05 else (red if avg_sent <= -0.05 else text)}; margin-left: 0.25rem;">{avg_sent:.3f}</span>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Sentiment Graphs Row
        col_s1, col_s2 = st.columns(2)
        
        with col_s1:
            st.markdown("""
            <div class="chart-wrap">
                <div class="chart-title">Monthly Sentiment Trend mapped against SCD Events</div>
                <div class="chart-subtitle">Averaged monthly sentiment rating. Vertical bars mark major Learn & Grow events.</div>
            """, unsafe_allow_html=True)
            
            conn = get_db_connection()
            monthly_trend = pd.read_sql(f"""
                SELECT 
                    strftime('%Y-%m', survey_date) as month,
                    AVG(sentiment_score) as avg_sentiment
                FROM Fact_Sentiment_Feedback
                WHERE relevance_score >= {threshold}
                GROUP BY month
                ORDER BY month
            """, conn)
            conn.close()
            
            fig_trend = go.Figure()
            fig_trend.add_trace(go.Scatter(
                x=monthly_trend["month"],
                y=monthly_trend["avg_sentiment"],
                mode='lines+markers',
                line=dict(color=accent, width=2.5),
                marker=dict(size=6),
                name='Average Sentiment'
            ))
            
            # Add vertical lines for key events
            # Spring Learn & Grow event: May
            # Summer Learn & Grow event: August
            # New Orientation Launch: January
            event_marks = [
                ("2023-08", "Summer L&G", green),
                ("2024-01", "Orientation Update", amber),
                ("2024-05", "Spring L&G", green),
                ("2024-08", "Summer L&G", green),
                ("2025-05", "Spring L&G", green),
                ("2025-08", "Summer L&G", green),
                ("2026-05", "Spring L&G", green)
            ]
            
            for m, label, col in event_marks:
                if m in monthly_trend["month"].values:
                    fig_trend.add_vline(
                        x=m, 
                        line_width=1, 
                        line_dash="dash", 
                        line_color=col,
                    )
                    
            fig_trend.update_layout(PLOT_LAYOUT, height=300)
            fig_trend.update_yaxes(title="Sentiment Index", range=[-1.05, 1.05])
            st.plotly_chart(fig_trend, use_container_width=True, config={"displayModeBar": False})
            st.markdown("</div>", unsafe_allow_html=True)
            
        with col_s2:
            st.markdown("""
            <div class="chart-wrap">
                <div class="chart-title">Theme Sentiment Breakdown</div>
                <div class="chart-subtitle">Extracted qualitative categories mapped to sentiment ratings.</div>
            """, unsafe_allow_html=True)
            
            conn = get_db_connection()
            theme_dist = pd.read_sql(f"""
                SELECT 
                    theme,
                    COUNT(*) as count,
                    AVG(sentiment_score) as avg_sentiment
                FROM Fact_Sentiment_Feedback
                WHERE relevance_score >= {threshold}
                GROUP BY theme
                ORDER BY count DESC
            """, conn)
            conn.close()
            
            fig_theme = px.bar(
                theme_dist,
                x="count",
                y="theme",
                color="avg_sentiment",
                color_continuous_scale=px.colors.diverging.RdYlGn,
                color_continuous_midpoint=0.0,
                labels={"avg_sentiment": "Sentiment", "count": "Frequency"},
                orientation='h'
            )
            fig_theme.update_layout(PLOT_LAYOUT, height=300)
            fig_theme.update_yaxes(title="")
            st.plotly_chart(fig_theme, use_container_width=True, config={"displayModeBar": False})
            st.markdown("</div>", unsafe_allow_html=True)
            
        # Feedback Explorer list
        st.markdown("""
        <div class="chart-wrap">
            <div class="chart-title">Qualitative Feedback Explorer & Relevance Indicators</div>
            <div class="chart-subtitle">Showing database records. Search comments, view computed scores, and see relevance flags. Outliers with low relevance scores (< 0.20) are flagged in red.</div>
        """, unsafe_allow_html=True)
        
        search_query = st.text_input("🔍 Search comments text...", "")
        
        conn = get_db_connection()
        filter_str = f"AND raw_text LIKE '%{search_query}%'" if search_query else ""
        feedback_list = pd.read_sql(f"""
            SELECT 
                f.raw_text,
                f.source,
                f.survey_date,
                f.theme,
                f.sentiment_score,
                f.relevance_score
            FROM Fact_Sentiment_Feedback f
            WHERE 1=1 {filter_str}
            ORDER BY f.survey_date DESC
            LIMIT 50
        """, conn)
        conn.close()
        
        exp_rows = ""
        for _, row in feedback_list.iterrows():
            sent_val = row['sentiment_score']
            rel_val = row['relevance_score']
            
            sent_badge = f'<span class="badge badge-green">Pos ({sent_val:.2f})</span>' if sent_val >= 0.05 else (
                f'<span class="badge badge-red">Neg ({sent_val:.2f})</span>' if sent_val <= -0.05 else f'<span class="badge badge-amber">Neu ({sent_val:.2f})</span>'
            )
            
            rel_badge = f'<span class="badge badge-green">High ({rel_val:.2f})</span>' if rel_val >= threshold else (
                f'<span class="badge badge-red" style="font-weight:600;">Outlier ({rel_val:.2f})</span>'
            )
            
            exp_rows += f"""
            <tr>
                <td style="font-size:0.75rem;">{datetime.strptime(row['survey_date'], "%Y-%m-%d").strftime("%b %d, %Y")}</td>
                <td><span class="badge badge-blue">{row['source']}</span></td>
                <td><b>{row['theme']}</b></td>
                <td>{row['raw_text']}</td>
                <td>{sent_badge}</td>
                <td>{rel_badge}</td>
            </tr>
            """
            
        exp_table_html = textwrap.dedent(f"""
        <table class="data-table">
            <thead>
                <tr>
                    <th style="width: 10%;">Date</th>
                    <th style="width: 12%;">Source</th>
                    <th style="width: 15%;">Theme</th>
                    <th>Raw Comment</th>
                    <th style="width: 12%;">Sentiment</th>
                    <th style="width: 12%;">Guardrail Status</th>
                </tr>
            </thead>
            <tbody>
                {exp_rows}
            </tbody>
        </table>
        """)
        render_html(exp_table_html)
        st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# TAB 4: SQL & PIPELINE ENGINE
# ==========================================
with tabs[3]:
    st.markdown("""
    <div class="chart-wrap">
        <div class="chart-title">Database Pipeline Execution & Custom SQL queries</div>
        <div class="chart-subtitle">Inspect SQL transforms from <code>transformations.sql</code>, execute query scripts against SQLite, and run custom queries.</div>
    """, unsafe_allow_html=True)
    
    q_choice = st.selectbox(
        "Select Pipeline SQL Script",
        ["rolling_retention", "cohort_retention", "dept_rankings", "Run Custom Query..."]
    )
    
    query_text = ""
    if q_choice != "Run Custom Query...":
        current_queries = load_sql_queries()
        query_text = current_queries.get(q_choice, "")
    else:
        query_text = st.text_area("Write Custom SQL Query...", "SELECT * FROM Dim_Department LIMIT 5;")
        
    st.code(query_text, language="sql")
    
    if st.button("▶ Execute Query", use_container_width=True):
        if not query_text:
            st.error("Query is empty!")
        else:
            try:
                start_time = time.time()
                conn = get_db_connection()
                df_result = pd.read_sql(query_text, conn)
                conn.close()
                elapsed = time.time() - start_time
                
                st.success(f"Query returned {len(df_result)} rows in {elapsed*1000:.2f} ms")
                st.dataframe(df_result, use_container_width=True)
            except Exception as e:
                st.error(f"SQL Execution Error: {e}")
                
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Table Schema Inspect
    st.markdown("""
    <div class="chart-wrap">
        <div class="chart-title">Database Schema Inspector</div>
        <div class="chart-subtitle">List SQLite tables and view columns/data types.</div>
    """, unsafe_allow_html=True)
    
    conn = get_db_connection()
    tables_list = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';", conn)
    conn.close()
    
    t_inspect = st.selectbox("Select Table to Inspect Schema", tables_list["name"].values if not tables_list.empty else [])
    
    if t_inspect:
        conn = get_db_connection()
        schema_df = pd.read_sql(f"PRAGMA table_info({t_inspect});", conn)
        conn.close()
        
        st.table(schema_df[["cid", "name", "type", "notnull", "dflt_value", "pk"]])
        
    st.markdown("</div>", unsafe_allow_html=True)
