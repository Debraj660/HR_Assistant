from qdrant_client import QdrantClient
from qdrant_client.models import Filter

client = QdrantClient(
    url= "",
    api_key="",
)

COLLECTION_NAME = "hr_documents"

client.delete(
    collection_name=COLLECTION_NAME,
    points_selector=Filter(),
)

print("Qdrant data reset successfully.")