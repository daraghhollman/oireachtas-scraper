"""
Script to find all debate entires on the Oireactas site

Debate urls are contained within pages in the format:
https://www.oireachtas.ie/en/debates/debate/dail/YYYY-MM-DD/

We want to find all possible dates between a range, find the hyperlinks within,
and save them with some metadata to a csv.
"""

import datetime as dt
from typing import Dict
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm


def main():

    base_url = "https://www.oireachtas.ie/en/debates/debate/dail"

    start_time = dt.datetime(2026, 5, 20).date()
    end_time = dt.datetime.today().date()

    # Create list of all possible dates for debates
    possible_dates = [
        start_time + i * dt.timedelta(days=1)
        for i in range((end_time - start_time).days)
    ]

    possible_urls = [t.strftime(f"{base_url}/%Y-%m-%d/") for t in possible_dates]

    queries = []
    for u in tqdm(
        possible_urls, desc=f"Finding Debates from {start_time} to {end_time}"
    ):
        result = extract_links(u)

        if result["found"]:
            queries.append(result)

    debates = []
    for q in queries:

        # We want to keep track of duplicate titles, which occur sometimes
        # when there are multiple questions sessions in a day. We use a
        # dictionary, where titles are the key, and the value counts the number
        # of times it has appeared that day.
        days_titles: Dict[str, int] = {}

        for debate_dict in q["links"]:

            # Skip sublinks to headings
            if "#" in debate_dict["href"]:
                continue

            debate_entry = {
                "url": debate_dict["href"],
                "title": debate_dict["text"],
                "date": q["url"].split("/")[-2],
            }

            current_title = debate_entry["title"]
            if current_title in days_titles.keys():
                # This title already exists for this day. We must rename it to
                # mark this.
                debate_entry["title"] = (
                    current_title + f" ({days_titles[current_title]})"
                )

                days_titles[current_title] += 1

            else:
                # Else, we add this title to the list, so it can be tracked.
                days_titles[current_title] = 1

            debates.append(debate_entry)

    # Create CSV
    output_file = "debates.csv"
    print(f"Writing to: {output_file}")
    pd.DataFrame(debates).to_csv(output_file)


def extract_links(url: str, div_class: str = "results") -> dict:
    """
    Fetch a URL, find the first <div class='results'>,
    and extract every href at every nesting level inside it.
    """
    result = {"url": url, "title": "", "found": False, "links": []}

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

    except requests.RequestException as e:
        return result

    soup = BeautifulSoup(response.text, "html.parser")

    container = soup.find("div", class_=div_class)

    if not container:
        # print(f"[NOT FOUND] {url} — no <div class='{div_class}'>")
        return result

    result["found"] = True

    # find_all() recurses into nested <ul>/<li> automatically
    links = [
        {
            "href": urljoin(url, tag["href"]),
            "text": tag.get_text(strip=True),
        }
        for tag in container.find_all("a", href=True)
    ]

    result["links"] = links
    # print(f"{url} — found {len(links)} link(s)")

    return result


if __name__ == "__main__":
    main()
