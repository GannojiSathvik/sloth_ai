def query_channel(question, collection, n_results=5):
    results = collection.query(
        query_texts=[question],
        n_results=n_results
    )
    
    # Build context with source attribution
    context_parts = []
    for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
        context_parts.append(
            f'[From: "{meta["title"]}" — {meta["url"]}]\n{doc}'
        )
    
    return "\n\n---\n\n".join(context_parts)