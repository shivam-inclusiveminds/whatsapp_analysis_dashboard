# =====================================================================
#                        WHATSAPP DEEP ANALYTICS
# =====================================================================

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import pytz

# =========================== CUSTOM CSS ===============================
st.markdown("""
<style>

    /* ===== MAIN PAGE BACKGROUND ===== */
    .stApp {
        background-color: #f9fafb !important;
    }

    /* ===== MAIN TITLE (st.title) ===== */
    .st-emotion-cache-10trblm, h1 {
        color: #198754 !important;
    }

    /* ===== HEADERS (st.header) ===== */
    h2, h3 {
        color: #198754 !important;
    }

    /* ===== SUBHEADERS (st.subheader) ===== */
    .st-emotion-cache-1v0mbdj,
    .st-emotion-cache-16idsys,
    .stMarkdown h3 {
        color: #198754 !important;
    }

    /* ===== TAB TITLES ===== */
    .stTabs [role="tab"] p {
        color: #198754 !important;
        font-weight: 700 !important;
    }

    /* ===== METRIC LABELS ===== */
    [data-testid="stMetricLabel"] {
        color: #198754 !important;
        font-weight: 700 !important;
        font-size: 1.1rem !important;
    }

    /* ===== METRIC NUMBERS ===== */
    [data-testid="stMetricValue"] {
        color: #198754 !important;
        font-weight: 900 !important;
        font-size: 2rem !important;
    }

</style>
""", unsafe_allow_html=True)

#---------------------------- Chart Layout ------------------------------

def apply_default_plotly_style(fig, title_color="#198754"):
    fig.update_layout(
        plot_bgcolor="#f9fafb",
        paper_bgcolor="#f9fafb",

        font=dict(color="black"),  # all text black

        # Chart Title
        title_font=dict(color=title_color, size=20),

        # Axis styling
        xaxis=dict(
            title_font=dict(color="black"),
            tickfont=dict(color="black"),
            linecolor="black",
            tickcolor="black",
            mirror=True
        ),
        yaxis=dict(
            title_font=dict(color="black"),
            tickfont=dict(color="black"),
            linecolor="black",
            tickcolor="black",
            mirror=True
        ),

        # Legend styling (for discrete legends)
        legend=dict(
            title_font=dict(color="black"),
            font=dict(color="black"),
            bordercolor="black",
            borderwidth=1
        ),

        # ⭐ Color bar styling (for continuous scales)
        coloraxis_colorbar=dict(
            title=dict(font=dict(color="black")),
            tickfont=dict(color="black"),
            outlinecolor="black",
            outlinewidth=1
        ),

        margin=dict(l=40, r=40, t=60, b=40)
    )

    # Bar borders
    fig.update_traces(marker_line_color="black")

    return fig

#------------------------- Layout For DataFrames ------------------------

def apply_default_table_style(df, hide_index=True):
    """
    Display a pandas DataFrame as a fully styled table in Streamlit.
    All headers and numbers are centered, borders visible, background light.
    """
    # Optional: hide index
    if hide_index:
        df = df.reset_index(drop=True)

    # Start table HTML
    table_html = '<table style="border-collapse: collapse; width: 100%;">'

    # Header row
    table_html += '<thead>'
    table_html += '<tr>'
    for col in df.columns:
        table_html += f'<th style="border: 1px solid black; background-color: #f9fafb; color: black; text-align: center; padding: 5px;">{col}</th>'
    table_html += '</tr>'
    table_html += '</thead>'

    # Body rows
    table_html += '<tbody>'
    for i in range(len(df)):
        table_html += '<tr>'
        for col in df.columns:
            table_html += f'<td style="border: 1px solid black; background-color: #f9fafb; color: black; text-align: center; padding: 5px;">{df.iloc[i][col]}</td>'
        table_html += '</tr>'
    table_html += '</tbody>'

    table_html += '</table>'

    st.markdown(table_html, unsafe_allow_html=True)


# ---------------------- DATA IMPORT FUNCTIONS ------------------------
from notif import fetch_all_notification_data
from chats import fetch_all_chat_data
from msg import fetch_all_message_data
from rect import fetch_all_rection_data

# ============================ CONFIG =================================
api_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCIgOiAiZWFlNmZiNTUtYWI1My00ZGJiLTlhODYtMjBiZmVkYTI4NWRkIiwgInJvbGUiIDogImFwaSIsICJ0eXBlIiA6ICJhcGkiLCAibmFtZSIgOiAiZ2dfZGF0YSIsICJleHAiIDogMjA3MjI0OTMxMiwgImlhdCIgOiAxNzU2NzE2NTEyLCAic3ViIiA6ICJjNTIwMDY0Yi03YTQ1LTRkMzAtYWU5ZC1hMzMzMGZmMTI2NGIiLCAiaXNzIiA6ICJwZXJpc2tvcGUuYXBwIiwgIm1ldGFkYXRhIiA6IHt9fQ.MnoQ5SFjRtVmmY3-UROZzb5VLf__mQekvLyzaW0anvc"# Example API request

# ============================ LOAD DATA ===============================
msg_df = fetch_all_message_data(api_key)
ORG_PHONES = pd.Series(msg_df.org_phone.str.replace('@c.us', '').unique()).to_list()

chats_df = fetch_all_chat_data(api_key, ORG_PHONES, endpoint="chats", limit=1000)
chats_df = chats_df[chats_df['chat_type']=='group']
rec_df   = fetch_all_rection_data(api_key, ORG_PHONES, endpoint="reactions", limit=1000)
noti_df  = fetch_all_notification_data(api_key, ORG_PHONES, limit=1000)

# Fix accidental leading column
if ' chat_name' in chats_df.columns:
    chats_df.rename(columns={' chat_name': 'chat_name'}, inplace=True)

# --------- Load Google Sheet Mapping (State / District / Mandal) -----
df_mapp = pd.read_csv(
    'https://docs.google.com/spreadsheets/d/e/2PACX-1vSz3h-NZludfp1amcsvUogHytljEpvKTXRI138UVu0y1EpJAx67gpWBHhHU_M1ACdoI8dNc-11cm0mk/pub?gid=0&single=true&output=csv'
)
df_mapp = df_mapp[df_mapp['Group type']!= 'Not_Imp']
chatid = df_mapp['chat_id'].tolist()
# Merge metadata
chat_df_new = chats_df[chats_df['chat_id'].isin(chatid)].drop_duplicates(subset=['chat_id'])
merged_df = pd.merge(chat_df_new, df_mapp, on=['chat_id'], how='left')
merged_df.rename(columns={'chat_name_y': 'chats_name'}, inplace=True)

# Keep only WhatsApp Group chats
merged_df = merged_df[merged_df['chat_type'] == 'group'].dropna(subset=['Group type'])
# Drop unwanted groups
merged_df = merged_df[merged_df['chats_name'] != "Cotton' 97 Arts Batch"]
merged_df = merged_df[merged_df['chats_name'] != "DRUG-FREE MIZORAM"]



chat_df = merged_df.copy()

# ============================ PREPROCESSING ===========================
chat_df['chat_created_at'] = pd.to_datetime(chat_df['created_at'], errors="coerce")
chat_df['date_new'] = chat_df['chat_created_at'].dt.date

msg_df['timestamp'] = pd.to_datetime(msg_df['timestamp'], errors="coerce")
msg_df['date_new'] = msg_df['timestamp'].dt.date
msg_df['hour'] = msg_df['timestamp'].dt.hour
msg_df['sender_phone'] = msg_df['sender_phone'].str.replace('@c.us', '')
# ----------- Normalize message type ---------------------------------
type_map = {
    "text": "Text", "conversation": "Text", "chat": "Text",
    "image": "Image", "video": "Video", "audio": "Audio"
}
msg_df['message_type'] = msg_df.get('message_type', 'Other').map(type_map).fillna("Other")

rec_df['timestamp'] = pd.to_datetime(rec_df['timestamp'], errors="coerce")
rec_df['date_new'] = rec_df['timestamp'].dt.date

noti_df['timestamp'] = pd.to_datetime(noti_df['timestamp'], errors="coerce")
noti_df['date_new'] = noti_df['timestamp'].dt.date

# Add metadata to message df
meta_cols = ['chat_id', 'chats_name', 'District Name', 'State Name', 'Block']
available_cols = [c for c in meta_cols if c in chat_df.columns]
msg_df = msg_df.merge(chat_df[available_cols], on='chat_id', how='left')

# Restrict to group chats
group_ids = chat_df['chat_id'].unique().tolist()
msg_df = msg_df[msg_df['chat_id'].isin(group_ids)]
rec_df = rec_df[rec_df['chat_id'].isin(group_ids)]
noti_df = noti_df[noti_df['chat_id'].isin(group_ids)]

# ============================ STREAMLIT SETUP =========================
st.set_page_config(page_title="WhatsApp Deep Analytics", layout="wide")
st.title("📊 WhatsApp Deep Analytics Dashboard")

# ============================ SIDEBAR FILTERS =========================
st.sidebar.header("Filters")

all_dates = pd.concat([
    chat_df['date_new'].dropna(),
    msg_df['date_new'].dropna(),
    noti_df['date_new'].dropna()
], ignore_index=True)

all_dates = all_dates[all_dates > pd.to_datetime("2000-01-01").date()]
min_date = all_dates.min()
max_date = all_dates.max()
default_start = max_date - timedelta(days=30)

date_range = st.sidebar.date_input(
    "Select Date Range",
    (default_start, max_date),
    min_value=min_date,
    max_value=max_date
)

start_date, end_date = date_range

# ============================ APPLY FILTERS ===========================
filtered_chats = chat_df.copy()
filtered_msgs  = msg_df[(msg_df['date_new'] >= start_date) &
                        (msg_df['date_new'] <= end_date)]
filtered_reactions = rec_df[(rec_df['date_new'] >= start_date) &
                            (rec_df['date_new'] <= end_date)]
filtered_notifications = noti_df[(noti_df['date_new'] >= start_date) &
                                 (noti_df['date_new'] <= end_date)]

# ======================== METRICS CALCULATIONS =======================

merged_msg_df = pd.merge(chat_df, msg_df, on=['chat_id'], how='left')
# Convert timestamp to datetime (already timezone-aware)
merged_msg_df['timestamp'] = pd.to_datetime(merged_msg_df['timestamp'], errors='coerce')

# Define 7 days ago with UTC timezone
seven_days_ago = datetime.now(pytz.UTC) - timedelta(days=7)

# Add 'last_7days' column
merged_msg_df['last_7days'] = merged_msg_df['timestamp'].apply(lambda x: 'yes' if x >= seven_days_ago else 'no')

weekly_fd = merged_msg_df[merged_msg_df["last_7days"] == 'yes'].copy()

# ----------------------------------------------------
# 2️⃣ ACTIVE MEMBERS (sender_phone sent ≥ 7 messages)
# ----------------------------------------------------
member_msg_counts = (
    weekly_fd.groupby("sender_phone")["message_id"]
    .nunique()
    .reset_index(name="msg_count")
)

total_members = member_msg_counts[member_msg_counts["msg_count"] >= 7]["sender_phone"].nunique()

# Total groups
total_groups = filtered_chats['chat_id'].nunique()
# Total members (sum of member_count)
active_members = member_msg_counts[member_msg_counts["msg_count"] >= 1]["sender_phone"].nunique()
# Unique individuals (unique sender_phone)
unique_individuals = active_members

# ----------------------------------------------------
# 1️⃣ ACTIVE GROUPS (≥ 10 messages in last 7 days)
# ----------------------------------------------------
chat_msg_counts = (
    weekly_fd.groupby("chat_id")["message_id"]
    .nunique()
    .reset_index(name="msg_count")
)

active_chats = chat_msg_counts[chat_msg_counts["msg_count"] >= 10]["chat_id"].tolist()
active_groups = len(active_chats)


today = datetime.now().date()
week_start = today - timedelta(days=7)
weekly_msgs = filtered_msgs[filtered_msgs['date_new'] >= week_start]

# ========================= 5 SLIDES (TABS) ===========================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📌 Slide 1 – Topline Overview",
    "📊 Slide 2 – Active Groups & Members",
    "📈 Slide 3 – Membership Movement",
    "💬 Slide 4 – Message Patterns",
    "🏆 Slide 5 – District Rankings"
])

# ========================= CUSTOM COLOR SCALE ========================
custom_scale = [
    "#8B0000",  # dark red (highest)
    "#CD0000",  # little dark red
    "#FF6347",  # little dark light red
    "#FFA07A",  # light red
    "#00FF00",  # light green
    "#00e500",  # dark light green
    "#00b200",  # less dark green
    "#007f00"   # dark green (lowest)
]
#------------------------------------------------
#for district

# Keep only District type
district_df = merged_df[merged_df['Group type'] == 'District']

# Remove duplicates per chat per district
district_df_unique = district_df.drop_duplicates(subset=['chat_id', 'District Name'])

# Count unique chat IDs per district
dist_grp = district_df_unique.groupby("District Name")["chat_id"].nunique().reset_index(name="Group Count")


# =====================================================================
#                            SLIDE 1
# =====================================================================
with tab1:
    st.header("📌 Topline Overview")
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Groups", total_groups)
    c2.metric("Total Members", unique_individuals)
    c3.metric("Active Members", total_members)

    # Groups by District
    fig = px.bar(dist_grp, x="District Name", y="Group Count",
             color="Group Count", text="Group Count",
             title="Groups by District",
             color_continuous_scale=custom_scale)
    fig = apply_default_plotly_style(fig)
    st.plotly_chart(fig, use_container_width=True)


    # Groups by State
    if "State Name" in filtered_chats.columns:
        state_grp = filtered_chats.groupby("State Name")["chat_id"].nunique().reset_index(name="Group Count")
        fig2 = px.bar(state_grp, x="State Name", y="Group Count",
                      color="Group Count", text="Group Count",title='Groups by State',
                      color_continuous_scale=custom_scale)
        fig2 = apply_default_plotly_style(fig2)
        st.plotly_chart(fig2, use_container_width=True)

    # Groups by Mandal / Group Type
    if "Block" in filtered_chats.columns and filtered_chats["Block"].notna().any():
        mandal_col = "Block"
    elif "Group type" in filtered_chats.columns:
        mandal_col = "Group type"
    else:
        mandal_col = None

    if mandal_col:
        mandal_grp = filtered_chats.groupby(mandal_col)["chat_id"].nunique().reset_index(name="Group Count")
        fig3 = px.bar(mandal_grp, x=mandal_col, y="Group Count",
                      color="Group Count", text="Group Count",title='Groups By Type',
                      color_continuous_scale=custom_scale)
        fig3 = apply_default_plotly_style(fig3)
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("⚠️ No Mandal / Group Type column found.")

# =====================================================================
#                            SLIDE 2
# =====================================================================
with tab2:
    st.header("📊 Top 5 Active Groups & Members by District")
    district_cols = [c for c in weekly_fd.columns if "district" in c.lower()]
    if len(district_cols) > 1:
        weekly_fd["District Name"] = weekly_fd[district_cols].bfill(axis=1).iloc[:, 0]
    elif len(district_cols) == 1:
        weekly_fd.rename(columns={district_cols[0]: "District Name"}, inplace=True)
    else:
        st.error("❌ District Name column missing in weekly data.")
        st.stop()

    weekly_fd["District Name"] = weekly_fd["District Name"].astype(str).str.strip().str.title()

    # -------------------------------------------------------
    # 1️⃣ Active Members
    # -------------------------------------------------------
    if not weekly_fd.empty:
        member_counts_dist = (
            weekly_fd.groupby(["District Name", "sender_phone"])["message_id"]
            .nunique()
            .reset_index(name="msg_count")
        )
        active_members_district = (
            member_counts_dist[member_counts_dist["msg_count"] >= 7]
            .groupby("District Name")["sender_phone"]
            .nunique()
            .reset_index(name="Active Members")
        )

        # -------------------------------------------------------
        # 2️⃣ Merge with Slide 1 Group Counts
        # -------------------------------------------------------
        combined = pd.merge(
            active_members_district,
            dist_grp,  # Slide 1 cleaned group counts
            on="District Name",
            how="right"
        ).fillna(0)

        # -------------------------------------------------------
        # 3️⃣ Keep only top 5 districts by Group Count
        # -------------------------------------------------------
        top5 = combined.sort_values("Group Count", ascending=False).head(5)

        # -------------------------------------------------------
        # 4️⃣ Display table
        # -------------------------------------------------------
        apply_default_table_style(top5)

        # -------------------------------------------------------
        # 5️⃣ Prepare data for grouped bar chart
        # -------------------------------------------------------
        melted = top5.melt(
            id_vars="District Name",
            value_vars=["Active Members", "Group Count"],
            var_name="Type",
            value_name="Count"
        )

        # -------------------------------------------------------
        # 6️⃣ Plot with custom color scale
        # -------------------------------------------------------
        fig4 = px.bar(
            melted,
            x="District Name",
            y="Count",
            color="Count",  # numeric for color scale
            text="Count",
            barmode="group",
            title="Top 5 Districts: Active Members vs Groups",
            color_continuous_scale=custom_scale
        )
        fig4 = apply_default_plotly_style(fig4)
        st.plotly_chart(fig4, use_container_width=True)

    else:
        st.info("No activity in last 7 days.")

# =====================================================================
#                            SLIDE 3
# =====================================================================
with tab3:
    st.header("📈 Member Join/Leave Dynamics")

    # ------------------------
    # Past week net joins
    # ------------------------
    one_week_ago = end_date - timedelta(days=7)
    weekly_moves = filtered_notifications[
        (filtered_notifications['date_new'] >= one_week_ago) &
        (filtered_notifications['type'].isin(['add', 'leave']))
    ]

    add_count = weekly_moves[weekly_moves['type'] == 'add']['chat_id'].count()
    leave_count = weekly_moves[weekly_moves['type'] == 'leave']['chat_id'].count()
    net_joins = int(add_count - leave_count)  # convert to int

    color = "green" if net_joins >= 0 else "red"
    sign = "+" if net_joins >= 0 else ""

    st.markdown(
        f"""
        <div style="text-align: center;">
            <h4 style="color: #198754;">📈 Past Week – Joins vs Leaves</h4>
            <span style="font-size: 36px; font-weight: bold; color: {color};">
                {sign}{net_joins}
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )

    # ------------------------
    # 6-week trend
    # ------------------------
    six_week_ago = end_date - timedelta(days=42)
    movement_long = filtered_notifications[
        (filtered_notifications['date_new'] >= six_week_ago) &
        (filtered_notifications['type'].isin(['add', 'leave']))
    ]

    trend = movement_long.groupby(["date_new", "type"]).size().reset_index(name="Count")

    # ------------------------
    # Custom color mapping: add=green, leave=red
    # ------------------------
    color_map = {
        "add": "green",
        "leave": "red"
    }

    fig5 = px.line(
        trend,
        x="date_new",
        y="Count",
        color="type",
        markers=True,
        title="6-Week Join/Leave Trend",
        color_discrete_map=color_map
    )

    fig5 = apply_default_plotly_style(fig5)
    st.plotly_chart(fig5, use_container_width=True)

# =====================================================================
#                            SLIDE 4
# =====================================================================
# ================= Top 10 Messages by Reactions =================
with tab4:
    col1, col2 = st.columns(2)

    # -------------------------------
    # Top Disseminators
    # -------------------------------
    with col1:
        st.subheader("Top Disseminators")
        top_posters = (
            filtered_msgs.groupby("sender_phone")["message_id"]
            .count()
            .reset_index(name="Message Count")
        )
        # Keep last 10 digits only
        top_posters["sender_phone"] = top_posters["sender_phone"].astype(str).str[-10:]
        top_posters = top_posters.sort_values("Message Count", ascending=False).head(10)
        apply_default_table_style(top_posters)

    # -------------------------------
    # Reactions by Type
    # -------------------------------
    with col2:
        st.subheader("😃 Reactions by Type")
        if not filtered_reactions.empty and "reaction" in filtered_reactions.columns:
            reaction_counts = (
                filtered_reactions['reaction'].fillna("None")
                .value_counts()
                .reset_index()
            )
            reaction_counts.columns = ['Reaction','Count']
            reaction_counts = reaction_counts.head(5)  # top 5
            fig6 = px.bar(
                reaction_counts,
                x='Reaction', y='Count', text='Count',
                color='Count', color_continuous_scale=custom_scale,
                title="Top Reactions to Messages"
            )
            fig6 = apply_default_plotly_style(fig6)
            st.plotly_chart(fig6, use_container_width=True)
        else:
            st.info("No reactions available.")

    # -------------------------------
    # Top Messages by Reactions
    # -------------------------------
    st.header("🔥 Top Messages by Reactions")
    if not filtered_reactions.empty and 'message_id' in filtered_reactions.columns:

        # ---- Deduplicate messages by text + group ----
        clean_msgs = (
            filtered_msgs[['message_id', 'body', 'chats_name']]
            .drop_duplicates(subset=['body','chats_name'])
        )

        # ---- Count reactions per unique message ----
        top_reacted = (
            filtered_reactions.merge(clean_msgs, on='message_id', how='left')
            .groupby(['chats_name','body'])
            .agg({'reaction':'count'})
            .reset_index()
            .rename(columns={'reaction':'Reaction Count'})
            .sort_values('Reaction Count', ascending=False)
            .head(5)
        )

        # ---- Truncate long messages ----
        def truncate(text, max_len=120):
            if isinstance(text, str) and len(text) > max_len:
                return text[:max_len] + "..."
            return text
        top_reacted['Message'] = top_reacted['body'].apply(lambda x: truncate(x, 120))

        # ---- Apply CSS to limit table cell size ----
        st.markdown("""
        <style>
        .full-width-table table td {
            max-width: 350px;
            white-space: normal !important;
        }
        </style>
        """, unsafe_allow_html=True)

        # ---- Show table ----
        styled_table = apply_default_table_style(
            top_reacted[['chats_name', 'Message', 'Reaction Count']].rename(
                columns={'chats_name': 'Group'}
            )
        )
        st.markdown(
            f"<div class='full-width-table'>{styled_table}</div>",
            unsafe_allow_html=True
        )
    else:
        st.info("No reacted messages.")

# =====================================================================
#                            SLIDE 5
# =====================================================================
with tab5:
    st.header("🏆 Top 5 Performing Districts")

    # ---------------------------
    # Use the cleaned dist_grp from Slide 1
    # ---------------------------
    district_groups = dist_grp.copy()  # already cleaned, deduplicated

    # ---------------------------
    # Message counts per district
    # ---------------------------
    district_msgs = (
        filtered_msgs.copy()
        .assign(District_Name=lambda df: df["District Name"].astype(str).str.strip().str.title())
        .groupby("District Name")["message_id"]
        .count()
        .reset_index(name="Message Count")
    )

    # ---------------------------
    # Merge groups & messages
    # ---------------------------
    perf = pd.merge(district_groups, district_msgs, on="District Name", how="left").fillna(0)

    # ---------------------------
    # Ranking
    # ---------------------------
    perf["Group Rank"] = perf["Group Count"].rank(ascending=False)
    perf["Msg Rank"]   = perf["Message Count"].rank(ascending=False)

    perf["Composite Score"] = (0.25 * perf["Group Rank"]) + (0.75 * perf["Msg Rank"])
    perf["Comp Score"] = round((1 / perf["Composite Score"]) * 10, 2)

    # ---------------------------
    # Top 5 districts
    # ---------------------------
    top5 = perf.sort_values("Composite Score").head(5)

    # ---------------------------
    # Table (styled)
    # ---------------------------
    show_cols = [c for c in top5.columns if c not in ["Composite Score", "Comp Score"]]
    apply_default_table_style(top5[show_cols])

    # ---------------------------
    # Chart
    # ---------------------------
    fig7 = px.bar(
        top5,
        x="District Name",
        y="Comp Score",
        title="Top 5 Districts by Composite Score",
        color="Comp Score",
        color_continuous_scale=custom_scale,
        text="Comp Score"
    )
    fig7 = apply_default_plotly_style(fig7)
    st.plotly_chart(fig7, use_container_width=True)

# =====================================================================
#                                END
# =====================================================================
