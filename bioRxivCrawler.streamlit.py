import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
import time
import random
import streamlit as st

st.title("bioRxiv Deposited Data ID Crawler👽")
st.write("Search and extract papers along with their database IDs from bioRxiv.")

query_input = st.text_input("Enter search keywords (separate by commas):", "")
usage_option = st.radio("Do you want to use each query individually (OR) or as a combined (AND) query?",
                        ("OR", "AND"))

if st.button("Search Papers"):
    if "," not in query_input:
        st.error("Please separate keywords with commas (e.g., RNA-seq, single-cell).")
    else:
        if usage_option == "Individual Query":
            queries = query_input.split(",")
            search_type = "_OR_".join(queries).replace(" ", "%20")
        else:
            queries = ["%252B".join(query_input.split(",")).replace(" ", "%20")]
            search_type = queries[0].replace("%252B", "_AND_")

        BASE_URL = "https://www.biorxiv.org"
        SEARCH_URL_TEMPLATE = "https://www.biorxiv.org/search/{}%20numresults%3A75%20sort%3Arelevance-rank"

        HEADERS = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        }
      
        def get_paper_links(query):
            papers = []
            page_number = 0
            while True:
                search_url = SEARCH_URL_TEMPLATE.format(query) + f"&page={page_number}"
                response = requests.get(search_url, headers=HEADERS)
                if response.status_code != 200:
                    break
                soup = BeautifulSoup(response.text, "html.parser")
                article_divs = soup.find_all("div", class_="highwire-cite")
                if not article_divs:
                    break
                for article in article_divs:
                    title_tag = article.find("span", class_="highwire-cite-title")
                    link_tag = article.find("a", href=True)
                    if title_tag and link_tag:
                        title = title_tag.text.strip()
                        paper_url = BASE_URL + link_tag["href"]
                        papers.append({"Query": query, "Title": title, "URL": paper_url})
                next_page = soup.find("a", class_="pager-next")
                if not next_page:
                    break
                page_number += 1
                time.sleep(random.uniform(1,2))
            return papers

        def extract_deposited_id(paper_url):
            response = requests.get(paper_url, headers=HEADERS)
            if response.status_code != 200:
                return ["Not Found"]
            soup = BeautifulSoup(response.text, "html.parser")
            text = soup.get_text()
            match = re.findall(r"(GSE\d+|PRJNA\d+|ERP\d+|SRP\d+|EGAD\d+|S-BSST\d+)", text)
            return match if match else ["Not Found"]

        all_results = []
        for query in queries:
            papers = get_paper_links(query)
            for paper in papers:
                db_ids = extract_deposited_id(paper["URL"])
                paper["Database IDs"] = ", ".join(db_ids)
                all_results.append(paper)
                time.sleep(random.uniform(1,2))

        df = pd.DataFrame(all_results)

        if not df.empty:
            st.write(f"### Results for '{query_input}':")
            st.dataframe(df)

            csv = df.to_csv(index=False).encode()
            st.download_button("📥 Download CSV", data=csv, file_name=f"{search_type}.csv", mime="text/csv")

        else:
            st.warning("No results found.")
