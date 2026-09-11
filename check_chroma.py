from app.server.database.db import chroma_client


collection = chroma_client.get_collection("pdf_chunks")

print("Collection:", collection.name)
print("Total documents:", collection.count())

data = collection.get(
    limit=5,
    include=["documents", "metadatas"]
)

for i, doc_id in enumerate(data["ids"]):
    print("\n" + "=" * 80)
    print("ID:", doc_id)
    print("DOCUMENT:")
    print(data["documents"][i][:1000])
    print("METADATA:")
    print(data["metadatas"][i])