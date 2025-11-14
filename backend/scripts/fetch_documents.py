"""
Simple fetcher to download public legal documents and save as plain text + metadata.

Usage:
    python scripts/fetch_documents.py

The script writes files into `backend/data/raw/` as `<slug>.txt` and `<slug>.json`.

Notes:
- This is a best-effort fetcher. It retrieves HTML and strips tags roughly.
- For authoritative PDFs or complex pages, consider downloading manually and placing
  the PDF/HTML in `backend/data/raw/originals/` then updating metadata.
"""
import os
import re
import json
import hashlib
from urllib.parse import urlparse

try:
    import requests
except ImportError:
    raise SystemExit("requests is required. Install with: pip install requests")

RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
os.makedirs(RAW_DIR, exist_ok=True)

# List of documents to fetch. These are public pages (wikipedia / PRS / IndianKanoon links).
# You can edit this list to add/remove documents.
DOCUMENTS = [
    {
        "slug": "it_act_2000",
        "title": "Information Technology Act, 2000 (Wikipedia)",
        "type": "statute",
        "url": "https://en.wikipedia.org/wiki/Information_Technology_Act,_2000",
    },
    {
        "slug": "aadhaar_act_2016",
        "title": "Aadhaar (Targeted Delivery of Financial and Other Subsidies) Act, 2016 (Wikipedia)",
        "type": "statute",
        "url": "https://en.wikipedia.org/wiki/Aadhaar_Act",
    },
    {
        "slug": "constitution_of_india",
        "title": "Constitution of India (Wikipedia)",
        "type": "statute",
        "url": "https://en.wikipedia.org/wiki/Constitution_of_India",
    },
    {
        "slug": "pdp_bill",
        "title": "Personal Data Protection Bill (PRS summary)",
        "type": "regulation",
        "url": "https://prsindia.org/billtrack/personal-data-protection-bill-2019",
    },
    {
        "slug": "it_rules_2011",
        "title": "Information Technology (Reasonable Security Practices and Procedures and Sensitive Personal Data or Information) Rules, 2011 (Wikipedia)",
        "type": "regulation",
        "url": "https://en.wikipedia.org/wiki/Information_Technology_(Reasonable_Security_Practices_and_Procedures_and_Sensitive_Personal_Data_or_Information)_Rules,_2011",
    },
    # Judgments
    {
        "slug": "puttaswamy_2017",
        "title": "Justice K.S. Puttaswamy (Retd.) v Union of India (2017) (Wikipedia)",
        "type": "case",
        "url": "https://en.wikipedia.org/wiki/Justice_K._S._Puttaswamy_(Retd.)_v._Union_of_India",
    },
    {
        "slug": "shreya_singhal_2015",
        "title": "Shreya Singhal v. Union of India (2015) (Wikipedia)",
        "type": "case",
        "url": "https://en.wikipedia.org/wiki/Shreya_Singhal_v._Union_of_India",
    },
    {
        "slug": "anuradha_bhasin",
        "title": "Anuradha Bhasin v. Union of India (Supreme Court) (Wikipedia)",
        "type": "case",
        "url": "https://en.wikipedia.org/wiki/Anuradha_Bhasin_v._Union_of_India",
    },
    {
        "slug": "aadhaar_judgment",
        "title": "Aadhaar (Supreme Court judgments) (Wikipedia)",
        "type": "case",
        "url": "https://en.wikipedia.org/wiki/Aadhaar_judgement",
    },
    {
        "slug": "data_protection_overview",
        "title": "Overview: Privacy and Data Protection in India (multiple sources)",
        "type": "note",
        "url": "https://en.wikipedia.org/wiki/Privacy_law_in_India",
    },
]


def text_from_html(html: str) -> str:
    # Prefer BeautifulSoup for robust HTML -> text extraction
    try:
        from bs4 import BeautifulSoup
    except Exception:
        BeautifulSoup = None

    if BeautifulSoup:
        soup = BeautifulSoup(html, "html.parser")
        # remove script/style tags
        for s in soup(["script", "style"]):
            s.decompose()
        text = soup.get_text(separator=" ")
        # collapse whitespace
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    # Fallback: very simple HTML to text: remove scripts/styles, then tags; collapse whitespace
    html = re.sub(r"(?is)<(script|style).*?>.*?(</\1>)", " ", html)
    # Remove HTML tags
    text = re.sub(r"<[^>]+>", " ", html)
    # Decode HTML entities loosely
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&amp;", "&", text)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def checksum(text: str) -> str:
    h = hashlib.sha256()
    h.update(text.encode('utf-8'))
    return h.hexdigest()


def fetch_and_save(doc: dict):
    url = doc['url']
    slug = doc['slug']
    print(f"Fetching {slug} from {url}")
    # Use a browser-like User-Agent and retry a few times to avoid 403 from some hosts
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    }

    resp = None
    for attempt in range(1, 4):
        try:
            resp = requests.get(url, headers=headers, timeout=30)
            resp.raise_for_status()
            break
        except requests.HTTPError as e:
            print(f"Attempt {attempt}: HTTP error fetching {url}: {e}")
        except requests.RequestException as e:
            print(f"Attempt {attempt}: Network error fetching {url}: {e}")

    if resp is None:
        print(f"Failed to fetch {url} after retries")
        return False
    r = resp

    ct = r.headers.get('Content-Type', '')
    if 'text' in ct or 'html' in ct:
        text = text_from_html(r.text)
    else:
        # For non-text types, save raw bytes as placeholder message
        text = f"[Non-HTML content at {url}; content-type={ct}]"

    # Write txt
    txt_path = os.path.join(RAW_DIR, f"{slug}.txt")
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(text)

    meta = {
        'filename': f"{slug}.txt",
        'title': doc.get('title'),
        'type': doc.get('type'),
        'source_url': url,
        'fetched_from': urlparse(url).netloc,
        'checksum': checksum(text),
    }
    meta_path = os.path.join(RAW_DIR, f"{slug}.json")
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(meta, f, indent=2)

    print(f"Saved {txt_path} and {meta_path}")
    return True


def main():
    for doc in DOCUMENTS:
        fetch_and_save(doc)


if __name__ == '__main__':
    main()
