import json
import os
from dotenv import load_dotenv
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential

from openai import AzureOpenAI

load_dotenv()

# Setup Azure OpenAI Client
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    api_version=os.getenv("AZURE_OPENAI_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

# Setup the SearchClient
search_client = SearchClient(
    endpoint = os.getenv("AZURE_AI_SEARCH_ENDPOINT"),
    index_name = "nestle-test-index",
    credential = AzureKeyCredential(os.getenv("AZURE_AI_SEARCH_KEY"))
)

# Load your recipes.json file
with open("recipes.json", "r", encoding="utf-8") as f:
    recipes = json.load(f)

texts_to_embed = []
docs_to_upload = []

# Sample test document
for i, recipe in enumerate(recipes[:5]):
    combined_text = f"""Recipe: {recipe.get('title', 'N/A')}

Ingredients:
{chr(10).join(recipe.get('ingredients', []))}

Instructions:
{chr(10).join(recipe.get('instructions', []))}

Skill Level: {recipe.get('skill_level') or 'N/A'}
Servings: {recipe.get('servings') or 'N/A'}
Time: {recipe.get('time') or 'N/A'}
Link: {recipe.get('url') or 'N/A'}
Tags: {", ".join(recipe.get('tags', [])) or "N/A"}"""

    texts_to_embed.append(combined_text)
    
response = client.embeddings.create(
    input=texts_to_embed,
    model="text-embedding-3-small"
)

for i, recipe in enumerate(recipes[:5]):
    docs_to_upload.append({
        "id": f"recipe-{i+1}",
        "type": "test",
        "text": texts_to_embed[i],
        "embedding": response.data[i].embedding
    })

# Upload the test document
print("Uploading test document...")
result = search_client.upload_documents(documents=docs_to_upload)
print("Upload status:", result[0].status_code)
