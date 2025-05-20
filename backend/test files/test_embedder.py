import os
from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv()

# Setup Azure OpenAI client
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    api_version=os.getenv("AZURE_OPENAI_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

# Call the embedding model
response = client.embeddings.create(
    input=["Recipe: Nescaf\u00e9 Iced Coconut Latte\n\nIngredients:\n2 tsp Nescaf\u00e9 Iced Instant Coffee \n1 tbsp Vanilla Syrup \n200 ml Coconut Milk\nIce\n2 tsp Nescaf\u00e9 Iced Instant Coffee \n1 tbsp Vanilla Syrup \n200 ml Coconut Milk\nIce\n\nInstructions:\nA chilled tropical latte, sweetened with cane sugar\nIn a tall glass, mix the coconut milk, syrup and coffee\nAdd ice to the top and enjoy\nIn a tall glass, mix the coconut milk, syrup and coffee\nAdd ice to the top and enjoy\n\nSkill Level: Beginner\nServings: 1\nTime: 0 mins prep, 5 mins cook"],
    model="text-embedding-3-small"
)

embedding = response.data[0].embedding
print(f"Embedding length: {len(embedding)}")
print(f"First 5 values: {embedding[:5]}")
