import os
import json

from fastapi import FastAPI
from pydantic import BaseModel

from dotenv import load_dotenv

from openai import AzureOpenAI
from azure.search.documents.models import VectorizedQuery
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential

from langchain_openai import AzureChatOpenAI
from langchain_neo4j import Neo4jGraph
from langchain_neo4j.chains.graph_qa.cypher import GraphCypherQAChain
from langchain.prompts import PromptTemplate

# Load environment variables from .env file
load_dotenv()

# Setup Azure OpenAI client
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    api_version=os.getenv("AZURE_OPENAI_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
)

# Setup the SearchClient
search_client = SearchClient(
    endpoint = os.getenv("AZURE_AI_SEARCH_ENDPOINT"),
    index_name = "nestle-test",
    credential = AzureKeyCredential(os.getenv("AZURE_AI_SEARCH_KEY"))
)

# Setup Neo4j connection
graph = Neo4jGraph(
    url=os.getenv("NEO4J_URI"),
    username=os.getenv("NEO4J_USERNAME"),
    password=os.getenv("NEO4J_PASSWORD")
)

# Setup Azure OpenAI Chat model
llm = AzureChatOpenAI(
    azure_deployment="gpt-4o-mini", 
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    api_version=os.getenv("AZURE_OPENAI_VERSION"),
    temperature=0
)

# Create FastAPI app instance
app = FastAPI()

# Define the structure of incoming JSON data
class ChatRequest(BaseModel):
    message: str

# Create a POST endpoint at /chat
@app.post("/chat")
async def chat(req: ChatRequest):
    prompt = req.message

    rewrite_prompt = [
        {
            "role": "system",
            "content": (
                "You are an AI assistant for the MadeWithNestle.ca website. "
                "Users often ask vague or informal questions about recipes. "
                "Your task is to determine whether a user's query is best served by:\n"
                "1. The vector database (for general non-recipe related, or recipes where the user has no direction or specific ingredients they want), or\n"
                "2. The graph database (for recipe queries that include ingredients, time requests, tags such as Drinks or difficulties) Make the prompt simple and don't ask for anything extra.\n\n"
                "First, classify the query as either 'vector' or 'graph' depending on its structure and specificity. "
                "Then, rewrite the query to make it more relevant and descriptive for retrieval.\n\n"
                "Respond in the following format:\n"
                "```\n"
                "{\n"
                "  \"target\": \"vector\" | \"graph\",\n"
                "  \"rewritten_query\": \"...\"\n"
                "}\n"
                "```"
            )
        },
        {
            "role": "user",
            "content": f"User query: {prompt}"
        }
    ]

    rewrite_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=rewrite_prompt,
        temperature=0.5
    )

    try:
        content = rewrite_response.choices[0].message.content.strip()

        if content.startswith("```"):
            content = content.strip("```").strip()
        parsed = json.loads(content)
        target = parsed.get("target")
        rewritten_query = parsed.get("rewritten_query")
    except Exception as e:
        return {"error": f"Failed to parse response: {str(e)}"}
    
    if target == "vector":
        # Generate embedding for the query
        embedding_response = client.embeddings.create(
            input=[rewritten_query],
            model="text-embedding-3-small"
        )
        query_vector = embedding_response.data[0].embedding
        # Creating VectorizedQuery with embedding
        vector_query = VectorizedQuery(
            kind="vector",
            vector=query_vector,
            k_nearest_neighbors=3,
            fields="embedding"
        )
        # Search Azure AI Search index
        results = search_client.search(
            search_text=None,
            vector_queries=[vector_query]
        )
        context = "\n\n".join(
            doc["text"] for doc in results if "text" in doc
        )

    else:
        # Custom Cypher prompt that enforces CONTAINS instead of =
        cypher_prompt = PromptTemplate.from_template("""
        You are an expert Cypher query generator for a recipe knowledge graph.
        you should generalize by using `toLower(variable) CONTAINS 'substring'` instead of exact matches.
        Avoid `=` at all times.
        Normalize all text comparisons using `toLower()`.

        Graph Schema:
        {schema}

        Question:
        {question}

        Cypher query:
        """)

        # Build custom chain with prompt
        chain = GraphCypherQAChain.from_llm(
            llm=llm,
            graph=graph,
            cypher_prompt=cypher_prompt,
            verbose=True,
            allow_dangerous_requests=True,
            return_intermediate_steps=True
        )
        # Invoke Chain to get Response
        response = chain.invoke(rewritten_query)
        # Extract context from response
        context = response["intermediate_steps"][1].get("context", [])

    # Create chat response
    chat_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful madewithnestle.ca assistant."},
            {"role": "user", "content": f"Answer the following question using only the context below. I want it to also include the link in the context at the last sentence.\n\nContext:\n{context}\n\nQuestion: {prompt}"}
        ],
        temperature=0.7
    )

    return {
        "target": target,
        "rewritten_query": rewritten_query,
        "context": context,
        "response": chat_response.choices[0].message.content
    }