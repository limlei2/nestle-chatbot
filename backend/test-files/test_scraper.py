import asyncio
import json
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

# List of URLs to scrape
URLS = [
    "https://www.madewithnestle.ca/about-us",
    "https://www.madewithnestle.ca/unwrap-some-good",
    "https://www.corporate.nestle.ca/en/aboutus",
    "https://www.corporate.nestle.ca/en/what-creating-shared-value",
    "https://www.corporate.nestle.ca/en/aboutus/community"
]

async def scrape_page(page, url):
    await page.goto(url, wait_until="networkidle", timeout=60000)
    content = await page.content()

    # Parse the HTML
    soup = BeautifulSoup(content, "html.parser")
    for tag in soup(['header', 'footer', 'nav', 'script', 'style']):
        tag.decompose()

    # Extract specific tag content
    blocks = soup.find_all(["h1", "h2", "h3", "p", "li"])
    lines = [el.get_text(strip=True) for el in blocks if el.get_text(strip=True)]

    return {
        "url": url,
        "text": "\n".join(lines)
    }

async def scrape_all():
    results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        for url in URLS:
            print(f"Scraping: {url}")
            try:
                page_result = await scrape_page(page, url)
                results.append(page_result)
            except Exception as e:
                print(f"Failed to scrape {url}: {e}")

        await browser.close()

    # Save all results to JSON file
    with open("nestle_content2.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print("Scraping complete. Data saved to nestle_content.json.")

# Run it
asyncio.run(scrape_all())
