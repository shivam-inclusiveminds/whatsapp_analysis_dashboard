import requests
import pandas as pd
import time
import concurrent.futures
import streamlit as st


@st.cache_data(ttl=700)
def fetch_all_notification_data(
    api_key,
    org_phones,
    start_time=None,
    end_time=None,
    endpoint="chats/notifications",
    limit=1000,
    sleep_time=0.5,
    max_workers=5,
):
    """
    Fetch notification data from Periskope API for multiple org phones in parallel.
    Uses start_time and end_time to reduce payload size.

    Args:
        api_key (str): Your Bearer token.
        org_phones (list): List of org phones.
        start_time (str): Start date (e.g. "2025-04-25T00:00:00Z").
        end_time (str): End date (e.g. "2025-04-30T23:59:59Z").
        endpoint (str): API endpoint (default='chats/notifications').
        limit (int): Page size (default=1000).
        sleep_time (float): Delay between requests (default=0.5s).
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
            if start_time:
                params["start_time"] = start_time
            if end_time:
                params["end_time"] = end_time

            response = requests.get(url, headers=headers, params=params)

            if response.status_code != 200:
                print(f"❌ Error for {org_phone}: {response.status_code} {response.text}")
                break

            data = response.json()
            results = data.get("notifications") or data.get("results") or data.get("messages") or []

            if not results:
                print(f"✅ No more notifications for {org_phone}, stopping.")
                break

            all_results.extend(results)
            print(f"[{org_phone}] Fetched {len(results)} (total: {len(all_results)})")

            offset += limit
            time.sleep(sleep_time)

        for r in all_results:
            r["org_phone"] = org_phone

        return all_results

    combined_results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = executor.map(fetch_single_org, org_phones)
        for res in results:
            combined_results.extend(res)

    return pd.DataFrame(combined_results)
