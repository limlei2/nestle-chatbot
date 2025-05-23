import asyncio
import json
import os
import base64
import re
import unicodedata

from playwright.async_api import async_playwright
from dotenv import load_dotenv
from openai import AzureOpenAI
from bs4 import BeautifulSoup
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential

from neo4j import GraphDatabase

load_dotenv()

# Setup OpenAI Client
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    api_version=os.getenv("AZURE_OPENAI_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

# Setup SearchClient
search_client = SearchClient(
    endpoint = os.getenv("AZURE_AI_SEARCH_ENDPOINT"),
    index_name = os.getenv("AZURE_AI_SEARCH_INDEX"),
    credential = AzureKeyCredential(os.getenv("AZURE_AI_SEARCH_KEY"))
)

# Setup Neo4J
URI = os.getenv("NEO4J_URI")
USERNAME = os.getenv("NEO4J_USERNAME")
PASSWORD = os.getenv("NEO4J_PASSWORD")
driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))

# Recipe URLs
BASE_URL = "https://www.madewithnestle.ca"
RECIPE_INDEX = BASE_URL + "/recipes"

# Nestle Page URLs
EXTRA_URLS = [
    {"title": "About Us", "url": "https://www.madewithnestle.ca/about-us"},
    {"title": "Sustainable Cocoa", "url": "https://www.madewithnestle.ca/unwrap-some-good"},
    {"title": "About Us Corporate", "url": "https://www.corporate.nestle.ca/en/aboutus"},
    {"title": "Sustainability", "url": "https://www.corporate.nestle.ca/en/what-creating-shared-value"},
    {"title": "Community", "url": "https://www.corporate.nestle.ca/en/aboutus/community"},
    {"title": "Generation Regeneration", "url": "hhttps://www.corporate.nestle.ca/en/planet/generation-regeneration"},
    {"title": "Sustainable Sourcing", "url": "https://www.corporate.nestle.ca/en/creatingsharedvalue/environment/sustainable%20sourcing"},
    {"title": "Sustainable Packaging", "url": "https://www.corporate.nestle.ca/en/creatingsharedvalue/environment/packaging"},
    {"title": "Child Forced Labour", "url": "https://www.corporate.nestle.ca/en/planet/child-forced-labour"},
    {"title": "Taste and Nutrition", "url": "https://www.corporate.nestle.ca/en/taste-nutrition-our-core-0"}
]

# Scraper for non-recipe URLs
async def scrape_informational_page(page, item):
    try:
        await page.goto(item["url"], wait_until="domcontentloaded", timeout=60000)
        content = await page.content()

        soup = BeautifulSoup(content, "html.parser")
        for tag in soup(['header', 'footer', 'nav', 'script', 'style']):
            tag.decompose()

        blocks = soup.find_all(["h1", "h2", "h3", "h4", "p", "li"])
        lines = [el.get_text(strip=True) for el in blocks if el.get_text(strip=True)]

        combined_text = f"Title: {item['title']}\nLink: {item['url']}\n" + "\n".join(lines)

        embedding = client.embeddings.create(
            input=[combined_text],
            model="text-embedding-3-small"
        )

        return {
            "id": base64.urlsafe_b64encode(item["url"].encode()).decode(),
            "type": "information",
            "text": combined_text,
            "embedding": embedding.data[0].embedding
        }

    except Exception as e:
        print(f"Failed to scrape page: {item['url']}: {e}")
        return None


# Get All Recipe Links
async def get_recipe_links(page, max_pages=30):
    recipes = []

    for page_num in range(max_pages):
        url = f"{RECIPE_INDEX}?_wrapper_format=html&page={page_num}"
        print(f"Scraping recipes: {url}")
        await page.goto(url)
        await page.wait_for_timeout(2000)

        cards = await page.locator('a.recipe-search-block').all()
        if not cards:
            break

        for card in cards:
            try:
                href = await card.get_attribute("href")
                full_url = href if href.startswith("http") else BASE_URL + href

                title = await card.locator("h4.coh-heading").text_content()
                img_src = await card.locator("img").get_attribute("src")
                if img_src and img_src.startswith("/"):
                    img_src = BASE_URL + img_src

                prep = await card.locator("span.stat-prep-time").text_content() if await card.locator("span.stat-prep-time").count() else None
                cook = await card.locator("span.stat-cook-time").text_content() if await card.locator("span.stat-cook-time").count() else None

                time_summary = None
                if prep and cook:
                    time_summary = int(prep.strip())+int(cook.strip())
                elif prep:
                    time_summary = int(prep.strip())
                elif cook:
                    time_summary = int(cook.strip())

                recipes.append({
                    "title": title.strip(),
                    "url": full_url,
                    "image": img_src,
                    "time": time_summary
                })
            except Exception as e:
                print(f"Failed to parse data: {e}")

    return recipes

# Scraper for Recipes
async def scrape_recipe_details(page, recipe):
    try:
        await page.goto(recipe["url"])
        await page.wait_for_selector("main h1", timeout=10000)

        raw_ingredients = await page.locator(".field--name-field-ingredient-fullname").all_text_contents()
        raw_instructions = await page.locator("p.coh-paragraph").all_text_contents()

        # Remove duplicates while preserving order
        def remove_dups(items):
            seen = set()
            return [x for x in items if not (x in seen or seen.add(x))]

        ingredients = remove_dups(raw_ingredients)
        instructions = remove_dups(raw_instructions)

        skill_level = None
        if await page.locator("span.skill-level-value").count():
            skill_level = await page.locator("span.skill-level-value").first.text_content()
            skill_level = skill_level.strip()

        servings = None
        if await page.locator("span.serving-value").count():
            servings = await page.locator("span.serving-value").text_content()
            servings = servings.strip()

        tags = None
        if await page.locator('div.field__item a').count():
            tags = await page.locator('div.field__item a').all_text_contents()

         # Combined text for vector embedding
        combined_text = f"""Recipe: {recipe['title']}
            Ingredients:
            {chr(10).join(ingredients)}

            Instructions:
            {chr(10).join(instructions)}

            Skill Level: {skill_level or "N/A"}
            Servings: {servings or "N/A"}
            Time: {recipe.get("time") or "N/A"}
            Link: {recipe.get("url") or "N/A"}
            Tags: {tags or "N/A"}"""

        # Add details to existing recipe card data
        recipe["ingredients"] = ingredients
        recipe["instructions"] = instructions
        recipe["skill_level"] = skill_level
        recipe["servings"] = servings
        recipe["tags"] = tags or []
        recipe["id"] = base64.urlsafe_b64encode(recipe["url"].encode()).decode()

        response = client.embeddings.create(
            input=[combined_text],
            model="text-embedding-3-small"
        )
        recipe["text"] = combined_text
        recipe["embedding"] = response.data[0].embedding
        recipe["type"] = "recipe"

        return recipe
    except Exception as e:
        print(f"Failed to scrape {recipe['url']}: {e}")
        return None

# Normalize ASCII for Ingredients
def normalize_ascii(text):
    normalized = unicodedata.normalize("NFKD", text)
    ascii_str = normalized.encode("ascii", "ignore").decode("utf-8")
    ascii_str = re.sub(r"[\u200b\u00a0\u202f\u3000]", " ", ascii_str)
    ascii_str = re.sub(r"\s+", " ", ascii_str)
    return ascii_str.strip().lower()

# Ingredient Parser to split Ingredients and Amount
def parse_ingredient(raw):
    raw = normalize_ascii(raw)
    raw = raw.strip()

    match = re.match(r"^([\d\s\/\.\½¼¾]+(?:[a-zA-Z]+)?)\s+(.*)", raw)
    if match:
        amount = match.group(1).strip()
        name = match.group(2).strip()
        return name, amount

    return raw, "N/A"

# Insert Recipe to Neo4J Database
def insert_recipe(tx, recipe):
    parsed_ingredients = [parse_ingredient(i) for i in recipe["ingredients"]]

    tx.run("""
        MERGE (r:Recipe {id: $id})
        SET r.title = $title,
            r.url = $url,
            r.image = $image,
            r.instructions = $instructions

        MERGE (s:SkillLevel {name: $skill_level})
        MERGE (r)-[:HAS_SKILL_LEVEL]->(s)

        MERGE (t:Time {minutes: $time})
        MERGE (r)-[:HAS_TIME]->(t)

        MERGE (v:Servings {count: $servings})
        MERGE (r)-[:HAS_SERVINGS]->(v)

        FOREACH (tag IN $tags |
            MERGE (tagNode:Tag {name: tag})
            MERGE (r)-[:HAS_TAG]->(tagNode)
        )

        FOREACH (entry IN $parsed_ingredients |
            MERGE (i:Ingredient {name: entry.name})
            MERGE (r)-[rel:HAS_INGREDIENT]->(i)
            SET rel.amount = entry.count
        )
    """,
    id=recipe["id"],
    title = (recipe.get("title") or "").strip().lower(),
    url = recipe.get("url") or "",
    image = recipe.get("image") or "",
    time = recipe.get("time") if recipe.get("time") is not None else 0,
    instructions = "\n".join(recipe.get("instructions") or []),
    servings = recipe.get("servings") or 0,
    skill_level=(recipe.get("skill_level") or "Unknown").strip().lower(),
    tags=[tag.strip().lower() for tag in (recipe.get("tags") or [])],
    parsed_ingredients=[
        {"name": name, "count": count}
        for name, count in parsed_ingredients
        if name and name != "N/A"
    ]
)
    
# Main Function
async def scrape_all_links():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        # Get All Recipe Links
        recipes = await get_recipe_links(page)
        print(f"Found {len(recipes)} recipes")

        # Visit Each Recipe Link for Full Recipe
        full_recipes = []
        for recipe in recipes:
            print(f"Scraping full recipe: {recipe['url']}")
            full_data = await scrape_recipe_details(page, recipe)
            if full_data:
                full_recipes.append(full_data)

        # Documents to upload to Azure AI Search
        ai_search_upload_data = []

        # Scrape all non-recipe pages
        for item in EXTRA_URLS:
            print(f"Scraping page: {item['url']}")
            result = await scrape_informational_page(page, item)
            if result:
                ai_search_upload_data.append(result)

        await browser.close()

        # Add Recipes to Documents to Upload
        for recipe in full_recipes:
            ai_search_upload_data.append({
                "text": recipe["text"],
                "id": recipe["id"],
                "type": recipe["type"],
                "embedding": recipe["embedding"]
            })

        # Upload to Azure AI Search
        print("Uploading document to AI Search...")
        result = search_client.upload_documents(documents=ai_search_upload_data)
        print("Upload status:", result[0].status_code)

        # Upload to Neo4J Database
        with driver.session(database="neo4j") as session:
            for recipe in full_recipes:
                session.execute_write(insert_recipe, recipe)

        print(f"Uploaded {len(recipes)} recipes to Neo4j.") 

if __name__ == "__main__":
    asyncio.run(scrape_all_links())
