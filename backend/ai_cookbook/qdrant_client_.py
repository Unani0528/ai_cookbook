from qdrant_client import QdrantClient, models

# Connect to a local Qdrant instance
client = QdrantClient(host="localhost", port=6333)

collection_name = "10000-recipe"
vector_size = 4096  # Example size, depends on your embedding model
distance_metric = models.Distance.COSINE # Example distance metric

if not client.collection_exists(collection_name):
    client.create_collection(
        collection_name=collection_name,
        vectors_config=models.VectorParams(
            size=vector_size,
            distance=distance_metric,
        ),
        # Optional: configure sharding, replication, etc.
        # replication_factor=2,
        # shards_number=4,
    )
    print(f"Collection '{collection_name}' created successfully.")
else:
    print(f"Collection '{collection_name}' already exists.")