import requests
import pandas as pd
import time
import concurrent.futures

def fetch_all_rection_data(api_key, org_phones, endpoint="reactions", limit=1000, sleep_time=0.5, max_workers=5):
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
            # Try different keys depending on endpoint
            results = data.get("reactions") or data.get("results")

            if not results:
                print(f"✅ No more data for {org_phone}, stopping.")
                break

            all_results.extend(results)
            print(f"[{org_phone}] Fetched {len(results)} (total: {len(all_results)})")

            offset += limit
            time.sleep(sleep_time)  # avoid hammering API

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

    return pd.DataFrame(combined_results)