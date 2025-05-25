import os
from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv()

# Setup Azure OpenAI client
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    api_version=os.getenv("AZURE_OPENAI_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
)

# Call the GPT-4o Model
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "You are a helpful Nestlé assistant."},
        {"role": "user", "content": "How do I make Smarties cookies?"}
    ]
)

print(response.choices[0].message.content)
