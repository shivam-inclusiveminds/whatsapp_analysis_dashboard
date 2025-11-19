import requests
import pandas as pd
import time
import concurrent.futures
import streamlit as st
import json
import os


@st.cache_data(ttl=7200)
def fetch_all_chat_data(api_key, org_phones, endpoint="chats", limit=1000, sleep_time=0.5, max_workers=5):
    """
    Fetch all paginated data from Periskope API for multiple org phones in parallel.

    Args:
        api_key (str): Your Bearer token.
        org_phones (list): List of org phones (e.g., ['919435729308','919707089424']).
        endpoint (str): API endpoint (default='chats').
        limit (int): Page size (default=1000).
        sleep_time (float): Delay between requests in seconds.
        max_workers (int): Number of parallel threads (default=5).

    Returns:
        pd.DataFrame: Combined DataFrame of all results with org_phone column.
    """
    url = f"https://api.periskope.app/v1/{endpoint}"

    def fetch_single_org(org_phone):
        headers = {
            "Authorization": f"Bearer {api_key}",
            "x-phone": org_phone
        }

        offset = 0
        all_results = []

        while True:
            params = {"offset": offset, "limit": limit}
            response = requests.get(url, headers=headers, params=params)

            if response.status_code != 200:
                print(f"❌ Error for {org_phone}: {response.status_code} {response.text}")
                break

            data = response.json()
            results = data.get("chats") or data.get("results") or data.get("notifications") or []

            if not results:
                print(f"✅ No more data for {org_phone}, stopping.")
                break

            all_results.extend(results)
            print(f"[{org_phone}] Fetched {len(results)} (total: {len(all_results)})")

            offset += limit
            time.sleep(sleep_time)

        # Tag with org_phone for identification
        for r in all_results:
            r["org_phone"] = org_phone

        return all_results

    # Run all org phones in parallel
    combined_results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = executor.map(fetch_single_org, org_phones)
        for res in results:
            combined_results.extend(res)

    df = pd.DataFrame(combined_results)

    if not df.empty:
        # 🔧 Convert nested dict/list fields into JSON strings (Parquet safe)
        for col in df.columns:
            if df[col].apply(lambda x: isinstance(x, (dict, list))).any():
                df[col] = df[col].apply(lambda x: json.dumps(x) if isinstance(x, (dict, list)) else x)

        # ensure cache folder exists
        os.makedirs("cache", exist_ok=True)

        # save parquet safely
        df.to_parquet("cache/chats.parquet", index=False)

    return df
