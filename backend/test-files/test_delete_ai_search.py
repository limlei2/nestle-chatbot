import os
from dotenv import load_dotenv
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential

# Load environment variables
load_dotenv()

# Initialize the SearchClient
search_client = SearchClient(
    endpoint=os.getenv("AZURE_AI_SEARCH_ENDPOINT"),
    index_name="nestle-test-index",
    credential=AzureKeyCredential(os.getenv("AZURE_AI_SEARCH_KEY"))
)

# Fetch all document IDs
def get_all_doc_ids():
    results = search_client.search(search_text="*", select=["id"], top=1000)
    return [doc["id"] for doc in results]

# Batch delete documents
def delete_documents_by_ids(doc_ids):
    if not doc_ids:
        print("No documents to delete.")
        return
    actions = [{"@search.action": "delete", "id": doc_id} for doc_id in doc_ids]
    result = search_client.upload_documents(documents=actions)
    print(f"Deleted {len(result)} documents.")

# Main routine
if __name__ == "__main__":
    doc_ids = get_all_doc_ids()
    print(f"Found {len(doc_ids)} documents to delete.")
    delete_documents_by_ids(doc_ids)
