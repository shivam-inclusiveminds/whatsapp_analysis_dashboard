import requests
import pandas as pd
from datetime import datetime, timedelta
import streamlit as st


@st.cache_data(ttl=7200)
def fetch_all_message_data(api_key, org_phone=None, endpoint="chats/messages", limit=1000):
    """
    Fetch messages from Periskope API within the last 30 days using API-side filtering.

    Args:
        api_key (str): Bearer token.
        org_phone (str, optional): Org phone number for x-phone header (if required).
        endpoint (str): API endpoint (default 'chats/messages').
        limit (int): Page size (default=1000).

    Returns:
        pd.DataFrame: DataFrame of messages filtered for last 30 days.
    """

    url = f"https://api.periskope.app/v1/{endpoint}"
    headers = {"Authorization": f"Bearer {api_key}"}
    if org_phone:
        headers["x-phone"] = org_phone

    # Calculate start and end times
    end_time = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    start_time = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")

    all_results = []
    offset = 0

    while True:
        params = {
            "offset": offset,
            "limit": limit,
            "start_time": start_time,
            "end_time": end_time,
        }

        resp = requests.get(url, headers=headers, params=params)
        if resp.status_code != 200:
            print(f"❌ Error {resp.status_code}: {resp.text}")
            break

        data = resp.json()
        results = data.get("messages") or data.get("results") or data.get("data")

        if not results:
            break

        all_results.extend(results)
        offset += limit

        # If fewer than limit results are returned, stop
        if len(results) < limit:
            break

    if not all_results:
        return pd.DataFrame()

    # Convert to DataFrame
    df = pd.DataFrame(all_results)

    # Handle nested "messages" if present
    if "messages" in df.columns:
        df = df.explode("messages", ignore_index=True)
        df = pd.concat([df.drop(columns="messages"), df["messages"].apply(pd.Series)], axis=1)

    # Ensure timestamp is parsed
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

    return df
