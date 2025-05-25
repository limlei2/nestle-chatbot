import os
from dotenv import load_dotenv
from azure.search.documents.models import VectorizedQuery
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

query = "what are some nestle products"
print(f"Query: {query}")

rewrite_prompt = [
    {"role": "system", "content": "You are an AI assistant for a Nestlé recipe chatbot. Users ask vague or informal questions, and you rewrite them into descriptive search queries to help retrieve relevant recipes from a database."},
    {"role": "user", "content": f"Rewrite the following query for better search relevance in a vector database that has scraped information from madewithnestle.ca.\n\nUser query: {query}"}
]

rewrite_response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=rewrite_prompt,
    temperature=0.5
)
rewritten_query = rewrite_response.choices[0].message.content.strip()
print("Rewritten query for embedding:", rewritten_query)

# Generate embedding
print("Creating embedding for query...")
embedding_response = client.embeddings.create(
    input=[rewritten_query],
    model="text-embedding-3-small"
)
query_vector = embedding_response.data[0].embedding

# Create VectorizedQuery
vector_query = VectorizedQuery(
    kind="vector",
    vector=query_vector,
    k_nearest_neighbors=3,
    fields="embedding"
)

print("Searching Azure AI Search index...")
results = search_client.search(
    search_text=None,
    vector_queries=[vector_query]
)

contexts = []
print("\nResults:")
for doc in results:
    print(f"- ID: {doc['id']}")
    print(f"  Text Preview: {doc['text'][:150]}...\n")
    contexts.append(doc['text'])

context = "\n\n".join(contexts)

print("Generating answer using Azure OpenAI...")
chat_response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "You are a helpful Nestlé recipe assistant."},
        {"role": "user", "content": f"Answer the following question using only the context below. I want it to also include the link in the context at the last sentence.\n\nContext:\n{context}\n\nQuestion: {query}"}
    ],
    temperature=0.7
)

print("Response:\n")
print(chat_response.choices[0].message.content)