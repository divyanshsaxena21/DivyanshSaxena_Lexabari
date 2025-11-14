class Generator:
    def __init__(self):
        pass

    def generate(self, query, retrieved_docs):
        """
        Very basic stub: just concatenate retrieved docs and return a 'generated' response.
        """
        # Build a concise human-friendly answer by summarizing retrieved snippets
        if not retrieved_docs:
            return "No relevant documents found in the corpus.", []

        # For now, produce a simple synthesis: list top snippets and cite sources
        pieces = []
        sources = []
        for i, doc in enumerate(retrieved_docs, start=1):
            text = doc.get('text') or doc.get('snippet') or ''
            title = doc.get('title') or doc.get('doc_id') or 'Unknown'
            url = doc.get('source_url')
            pieces.append(f"{i}. {text}")
            if title not in sources:
                sources.append(title if not url else f"{title} <{url}>")

        answer = f"I found the following relevant passages for '{query}':\n\n" + "\n\n".join(pieces)
        return answer, sources
