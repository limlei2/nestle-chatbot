import asyncio
from graph_scraper import scrape_recipes as run_graph_scraper
from ai_search_scraper import main as run_ai_search_scraper

async def main():
    print("Starting Azure AI Search scraper...")
    await run_ai_search_scraper()
    print("Azure AI Search indexing complete.")

    print("Starting Neo4j graph scraper...")
    await run_graph_scraper()
    print("Neo4j graph scraping complete.\n")

if __name__ == "__main__":
    asyncio.run(main())
