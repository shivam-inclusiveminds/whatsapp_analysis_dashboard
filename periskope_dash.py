import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from notif import fetch_all_notification_data
from chats import fetch_all_chat_data
from msg import fetch_all_message_data
from rect import fetch_all_rection_data

# ================= Config / Secrets =================
api_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCIgOiAiZWFlNmZiNTUtYWI1My00ZGJiLTlhODYtMjBiZmVkYTI4NWRkIiwgInJvbGUiIDogImFwaSIsICJ0eXBlIiA6ICJhcGkiLCAibmFtZSIgOiAiZ2dfZGF0YSIsICJleHAiIDogMjA3MjI0OTMxMiwgImlhdCIgOiAxNzU2NzE2NTEyLCAic3ViIiA6ICJjNTIwMDY0Yi03YTQ1LTRkMzAtYWU5ZC1hMzMzMGZmMTI2NGIiLCAiaXNzIiA6ICJwZXJpc2tvcGUuYXBwIiwgIm1ldGFkYXRhIiA6IHt9fQ.MnoQ5SFjRtVmmY3-UROZzb5VLf__mQekvLyzaW0anvc"
ORG_PHONES = ['919435729308','919707089424','919435550003','918134974051']

# ================= Load Data =================
chats_df = fetch_all_chat_data(api_key, ORG_PHONES, endpoint="chats", limit=1000)
msg_df   = fetch_all_message_data(api_key, ORG_PHONES, endpoint="chats/messages", limit=1000)
rec_df   = fetch_all_rection_data(api_key, ORG_PHONES, endpoint="reactions", limit=1000)
noti_df  = fetch_all_notification_data(api_key, ORG_PHONES, limit=1000)

# Fix accidental leading-space column if present
if ' chat_name' in chats_df.columns:
    chats_df.rename(columns={' chat_name': 'chat_name'}, inplace=True)

# Load mapping sheet
df_mapp = pd.read_csv(
    'https://docs.google.com/spreadsheets/d/e/2PACX-1vSz3h-NZludfp1amcsvUogHytljEpvKTXRI138UVu0y1EpJAx67gpWBHhHU_M1ACdoI8dNc-11cm0mk/pub?gid=0&single=true&output=csv'
)

# Merge mapping on chat_id + chat_name
merged_df = pd.merge(chats_df, df_mapp, on=['chat_id', 'chat_name'], how='left')

# Standardize name used across app
merged_df.rename(columns={'chat_name': 'chats_name'}, inplace=True)
merged_df = merged_df[merged_df['chat_type']=='group']
merged_df = merged_df[merged_df['chats_name']!="Cotton' 97 Arts Batch"]
chat_df = merged_df.copy()

# ================= Preprocessing =================
# Keep only group chats
chat_df = chat_df[chat_df['chat_type'] == 'group'].copy()

# Chats
chat_df['chat_created_at'] = pd.to_datetime(chat_df['created_at'], errors="coerce")
chat_df['date_new'] = chat_df['chat_created_at'].dt.date

# Messages
msg_df['timestamp'] = pd.to_datetime(msg_df['timestamp'], errors="coerce")
msg_df['date_new'] = msg_df['timestamp'].dt.date
msg_df['hour'] = msg_df['timestamp'].dt.hour
msg_df['sender_phone'] = msg_df['sender_phone'].str.replace('@c.us', '')

# Map message_type to readable buckets
type_map = {"text": "Text", "image": "Image", "video": "Video", "audio": "Audio"}
if "message_type" in msg_df.columns:
    msg_df['message_type'] = msg_df['message_type'].fillna("Other").map(type_map).fillna("Other")
else:
    msg_df['message_type'] = "Other"

# Reactions
rec_df['timestamp'] = pd.to_datetime(rec_df['timestamp'], errors="coerce")
rec_df['date_new'] = rec_df['timestamp'].dt.date

# Notifications
noti_df['timestamp'] = pd.to_datetime(noti_df['timestamp'], errors="coerce")
noti_df['date_new'] = noti_df['timestamp'].dt.date

# Add chat meta into messages safely
meta_cols = ['chat_id', 'chats_name', 'District Name', 'AC Name', 'Block', 'Group type']
available_cols = [c for c in meta_cols if c in chat_df.columns]
msg_df = msg_df.merge(chat_df[available_cols], on='chat_id', how='left')

# Restrict to group chat_ids
group_ids = chat_df['chat_id'].unique().tolist()
msg_df = msg_df[msg_df['chat_id'].isin(group_ids)].copy()
rec_df = rec_df[rec_df['chat_id'].isin(group_ids)].copy()
noti_df = noti_df[noti_df['chat_id'].isin(group_ids)].copy()

# ================= Streamlit Setup =================
st.set_page_config(page_title="📊 WhatsApp Deep Analytics", layout="wide")
st.title("📊 WhatsApp Deep Analytics Dashboard")

# ================= Sidebar Filters =================
st.sidebar.header("Filters")

# Date range (default: last 30 days)
all_dates = pd.concat([
    chat_df['date_new'].dropna(),
    msg_df['date_new'].dropna(),
    noti_df['date_new'].dropna()
], ignore_index=True)
all_dates = all_dates[all_dates > pd.to_datetime("2000-01-01").date()]
min_date = all_dates.min() if not all_dates.empty else datetime.now().date()
max_date = all_dates.max() if not all_dates.empty else datetime.now().date()
default_start = max_date - timedelta(days=30)
date_range = st.sidebar.date_input("Select Date Range", (default_start, max_date), min_value=min_date, max_value=max_date)
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = default_start, max_date

# Group type filter
if "Group type" in chat_df.columns:
    group_types = sorted([gt for gt in chat_df['Group type'].dropna().unique().tolist()])
    selected_group_type = st.sidebar.selectbox("Select Group Type", ["All"] + group_types)
else:
    selected_group_type = "All"

# District filter
if "District Name" in chat_df.columns:
    districts = sorted([d for d in chat_df['District Name'].dropna().unique().tolist()])
    selected_district = st.sidebar.selectbox("Select District", ["All"] + districts)
else:
    selected_district = "All"

# ================= Apply Filters =================
filtered_chats = chat_df.copy()
filtered_msgs = msg_df[(msg_df['date_new'] >= start_date) & (msg_df['date_new'] <= end_date)].copy()
filtered_reactions = rec_df[(rec_df['date_new'] >= start_date) & (rec_df['date_new'] <= end_date)].copy()
filtered_notifications = noti_df[(noti_df['date_new'] >= start_date) & (noti_df['date_new'] <= end_date)].copy()

# Group type filter
if selected_group_type != "All":
    allowed_chat_ids = filtered_chats.loc[filtered_chats["Group type"] == selected_group_type, "chat_id"].unique()
    filtered_chats = filtered_chats[filtered_chats["chat_id"].isin(allowed_chat_ids)]
    filtered_msgs = filtered_msgs[filtered_msgs["chat_id"].isin(allowed_chat_ids)]
    filtered_reactions = filtered_reactions[filtered_reactions["chat_id"].isin(allowed_chat_ids)]
    filtered_notifications = filtered_notifications[filtered_notifications["chat_id"].isin(allowed_chat_ids)]

# District filter
if selected_district != "All":
    allowed_chat_ids = filtered_chats.loc[filtered_chats["District Name"] == selected_district, "chat_id"].unique()
    filtered_chats = filtered_chats[filtered_chats["chat_id"].isin(allowed_chat_ids)]
    filtered_msgs = filtered_msgs[filtered_msgs["chat_id"].isin(allowed_chat_ids)]
    filtered_reactions = filtered_reactions[filtered_reactions["chat_id"].isin(allowed_chat_ids)]
    filtered_notifications = filtered_notifications[filtered_notifications["chat_id"].isin(allowed_chat_ids)]

# ================= Overview =================
total_groups = filtered_chats['chat_id'].nunique()
total_members = int(filtered_chats['member_count'].fillna(0).sum())
active_participants = filtered_msgs['sender_phone'].nunique() if 'sender_phone' in filtered_msgs.columns else 0
active_groups = filtered_msgs['chat_id'].nunique()
active_group_pct = round((active_groups / total_groups) * 100, 2) if total_groups > 0 else 0.0

st.header("📌 Overview")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Groups", total_groups)
c2.metric("Total Members", total_members)
c3.metric("Active Participants", active_participants)
c4.metric("Active Groups %", f"{active_group_pct}%")

# ================= Group Level Categorisation =================
st.header("📊 Group Level Categorisation")
if "Group type" in filtered_chats.columns:
    cat_counts = (
        filtered_chats['Group type']
        .fillna("Unspecified")
        .value_counts()
        .reset_index()
        .rename(columns={"index": "Group type", "count": "Count"})
    )
    fig = px.bar(cat_counts, x="Group type", y="Count", text="Count", color="Count")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Group type column not available.")

# ================= Messages & Reactions =================
st.header("💬 Messages & Reactions")
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("📦 Messages by Type")
    if not filtered_msgs.empty:
        msg_types = (
            filtered_msgs['message_type']
            .fillna("Other")
            .value_counts()
            .reset_index()
        )
        msg_types.columns = ['message_type', 'Count']
        fig = px.pie(msg_types, values="Count", names="message_type", hole=0.4)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No messages available.")

with col_b:
    st.subheader("😃 Reactions by Type")
    if not filtered_reactions.empty and "reaction" in filtered_reactions.columns:
        reaction_counts = (
            filtered_reactions['reaction']
            .fillna("None")
            .value_counts()
            .reset_index()
        )
        reaction_counts.columns = ['Reaction', 'Count']
        fig = px.bar(reaction_counts, x="Reaction", y="Count", text="Count", color="Count")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No reactions available.")

# ================= Membership Movement (Last 2 Weeks) =================
st.header("🚦 Membership Movement (Last 2 Weeks)")
two_weeks_ago = end_date - timedelta(days=14)
movement = filtered_notifications[(filtered_notifications['date_new'] >= two_weeks_ago)]
if not movement.empty:
    trend = (
        movement[movement['type'].isin(['add', 'leave'])]
        .groupby(['date_new', 'type'])
        .size()
        .reset_index(name="Count")
        .sort_values('date_new')
    )
    if not trend.empty:
        fig = px.line(trend, x="date_new", y="Count", color="type", markers=True, title="Adds vs Leaves (last 14 days)")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No add/leave events in the past 2 weeks.")
else:
    st.info("No membership movement data.")

# ================= Top 10 Messages by Reactions =================
st.header("🔥 Top 10 Messages by Reactions")
if not filtered_reactions.empty and 'message_id' in filtered_reactions.columns:
    top_reacted = (
        filtered_reactions.groupby('message_id')['reaction']
        .count()
        .reset_index(name='Reaction Count')
        .sort_values('Reaction Count', ascending=False)
        .head(10)
    )
    top_reacted = top_reacted.merge(
        filtered_msgs[['message_id', 'body', 'chats_name']],
        on='message_id', how='left'
    )
    st.dataframe(
        top_reacted[['chats_name', 'body', 'Reaction Count']].rename(
            columns={'chats_name': 'Group', 'body': 'Message'}
        ),
        hide_index=True
    )
else:
    st.info("No reacted messages.")

# ================= Top 10 Posters =================
st.header("🏆 Top 10 Posters")
if 'sender_phone' in filtered_msgs.columns and not filtered_msgs.empty:
    posters = (
        filtered_msgs.groupby('sender_phone')['message_id']
        .count()
        .reset_index(name='Message Count')
        .sort_values('Message Count', ascending=False)
        .head(10)
    )
    posters.rename(columns={'sender_phone': 'Sender'}, inplace=True)
    st.dataframe(posters, hide_index=True)
else:
    st.info("No sender information.")

# ================= Messages per Group =================
st.header("📊 Messages Sent by Group")
if 'chats_name' in filtered_msgs.columns and not filtered_msgs.empty:
    msgs_by_group = (
        filtered_msgs.groupby('chats_name')['message_id']
        .count()
        .reset_index(name='Message Count')
        .sort_values('Message Count', ascending=False)
    )
    st.dataframe(msgs_by_group, hide_index=True)
else:
    st.info("No messages available.")
