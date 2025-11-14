class Generator:
    def __init__(self):
        pass

    def generate(self, query, retrieved_docs):
        """
        Very basic stub: just concatenate retrieved docs and return a 'generated' response.
        """
        context = "\n\n".join([doc["text"] for doc in retrieved_docs])
        response = f"Based on your query '{query}', here are some relevant texts:\n\n{context}"
        return response
