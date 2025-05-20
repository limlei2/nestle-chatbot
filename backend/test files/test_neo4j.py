import json
import os
import re
import unicodedata
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

# Neo4j setup
URI = os.getenv("NEO4J_URI")
USERNAME = os.getenv("NEO4J_USERNAME")
PASSWORD = os.getenv("NEO4J_PASSWORD")
driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))

def normalize_ascii(text):
    normalized = unicodedata.normalize("NFKD", text)
    ascii_str = normalized.encode("ascii", "ignore").decode("utf-8")
    ascii_str = re.sub(r"[\u200b\u00a0\u202f\u3000]", " ", ascii_str)
    ascii_str = re.sub(r"\s+", " ", ascii_str)
    return ascii_str.strip().lower()

def parse_ingredient(raw):
    raw = normalize_ascii(raw)
    raw = raw.strip()

    match = re.match(r"^([\d\s\/\.\½¼¾]+(?:[a-zA-Z]+)?)\s+(.*)", raw)
    if match:
        amount = match.group(1).strip()
        name = match.group(2).strip()
        return name, amount

    return raw, "N/A"

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
    title=recipe["title"].strip().lower(),
    url=recipe["url"],
    image=recipe["image"],
    time=recipe["time"],
    instructions="\n".join(recipe["instructions"]),
    servings=recipe["servings"],
    skill_level=(recipe.get("skill_level") or "Unknown").strip().lower(),
    tags=[tag.strip().lower() for tag in recipe.get("tags", [])],
    parsed_ingredients=[
        {"name": name, "count": count} for name, count in parsed_ingredients
    ]
)

def upload_all_recipes(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        recipes = json.load(f)

    with driver.session(database="neo4j") as session:
        for recipe in recipes:
            session.execute_write(insert_recipe, recipe)

    print(f"Uploaded {len(recipes)} recipes to Neo4j.")

if __name__ == "__main__":
    upload_all_recipes("recipes.json")