import asyncio
import base64
import json
import os
import re
import unicodedata
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from dotenv import load_dotenv
from playwright.async_api import async_playwright
from openai import AzureOpenAI
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential

load_dotenv()

BASE_URL = "https://www.madewithnestle.ca"

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    api_version=os.getenv("AZURE_OPENAI_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

search_client = SearchClient(
    endpoint=os.getenv("AZURE_AI_SEARCH_ENDPOINT"),
    index_name=os.getenv("AZURE_AI_SEARCH_INDEX"),
    credential=AzureKeyCredential(os.getenv("AZURE_AI_SEARCH_KEY"))
)

def normalize_url(url):
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

def is_internal(url):
    return url.startswith("/") or BASE_URL in url

async def extract_text_and_embed(page, url):
    await page.goto(url, wait_until="domcontentloaded")
    soup = BeautifulSoup(await page.content(), "html.parser")
    for tag in soup(['header', 'footer', 'nav', 'script', 'style']):
        tag.decompose()
    blocks = soup.find_all(["h1", "h2", "h3", "p", "li"])
    lines = [el.get_text(strip=True) for el in blocks if el.get_text(strip=True)]
    combined = f"Link: {url}\n" + "\n".join(lines)
    emb = client.embeddings.create(input=[combined], model="text-embedding-3-small")
    return {
        "id": base64.urlsafe_b64encode(url.encode()).decode(),
        "type": "recipe" if "/recipe/" in url else "information",
        "text": combined, "embedding": emb.data[0].embedding
    }

async def main():
    visited, documents, recipes = set(), [], []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        to_visit = [BASE_URL]

        while to_visit and len(visited) < 1000:
            url = normalize_url(to_visit.pop(0))
            if url in visited:
                continue
            visited.add(url)
            print(f"Scraping: {url}")
            try:
                doc = await extract_text_and_embed(page, url)
                documents.append(doc)
            except Exception as e:
                print(f"Failed to scrape {url}: {e}")

            try:
                await page.goto(url)
                links = await page.eval_on_selector_all("a[href]", "els => els.map(e => e.href)")
                for link in links:
                    norm = normalize_url(urljoin(BASE_URL, link.split('#')[0].strip()))
                    if is_internal(norm) and norm not in visited and norm not in to_visit:
                        to_visit.append(norm)
            except Exception:
                continue

        await browser.close()

    print(f"Uploading {len(documents)} documents to Azure AI Search...")
    results = search_client.upload_documents(documents=documents)

    failed = [r for r in results if r.status_code not in (200, 201)]
    if failed:
        print(f"{len(failed)} documents failed to upload.")
    else:
        print("All documents uploaded successfully.")

if __name__ == "__main__":
    asyncio.run(main())
