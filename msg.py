import requests
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

def fetch_all_message_data(api_key, org_phones, endpoint="chats/messages", limit=1000, max_workers=10):
    """
    Fast fetch all paginated data from Periskope API for multiple org phones in parallel.
    Pagination per org phone is also fetched concurrently.
    """

    url = f"https://api.periskope.app/v1/{endpoint}"
    session = requests.Session()  # reuse TCP connections

    def fetch_pages_for_org(org_phone):
        headers = {"Authorization": f"Bearer {api_key}", "x-phone": org_phone}
        all_results = []

        # First request to get total count if API provides it
        offset = 0
        while True:
            params = {"offset": offset, "limit": limit}
            resp = session.get(url, headers=headers, params=params)
            if resp.status_code != 200:
                print(f"❌ Error {org_phone}: {resp.status_code}")
                break
            data = resp.json()
            results = data.get("messages") or data.get("results")
            if not results:
                break
            all_results.extend(results)
            offset += limit
            if len(results) < limit:  # no more pages
                break

        # Tag with org_phone
        for r in all_results:
            r["org_phone"] = org_phone
        print(f"[{org_phone}] Total fetched: {len(all_results)}")
        return all_results

    combined_results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(fetch_pages_for_org, phone) for phone in org_phones]
        for future in as_completed(futures):
            combined_results.extend(future.result())

    return pd.DataFrame(combined_results)
