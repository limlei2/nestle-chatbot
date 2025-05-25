import os
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from langchain_neo4j import Neo4jGraph
from langchain_neo4j.chains.graph_qa.cypher import GraphCypherQAChain
from langchain.prompts import PromptTemplate

load_dotenv()

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

# Ask question
question = "What are recipes with quik?"
response = chain.invoke(question)

# Extract Cypher and results
cypher = response["intermediate_steps"][0].get("query", "")
context = response["intermediate_steps"][1].get("context", [])

# Output
print("Cypher:\n", cypher)
print("\nNeo4j Results:\n", context)
