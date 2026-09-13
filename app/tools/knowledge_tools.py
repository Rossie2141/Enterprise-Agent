import json

from sentence_transformers import SentenceTransformer
from langchain_core.tools import tool

from app.db.connection import get_connection
from app.utils.errors import handle_tool_error


EMBEDDING_MODEL = "all-MiniLM-L6-v2"

model = SentenceTransformer(EMBEDDING_MODEL)


@tool
def search_knowledge(
    query: str,
    limit: int = 3,
    min_similarity: float = 0.40,
) -> str:
    """Search the internal knowledge base using semantic similarity.

    Args:
        query: Natural-language question or search query.
        limit: Maximum number of results to return.
        min_similarity: Minimum similarity score required.

    Returns:
        Relevant knowledge chunks as JSON.
    """

    try:
        # Validate query
        if not query.strip():
            return json.dumps({
                "error": "Knowledge search query cannot be empty."
            })

        # Validate limit
        if limit <= 0:
            return json.dumps({
                "error": "Limit must be greater than 0."
            })

        # Validate similarity threshold
        if not 0 <= min_similarity <= 1:
            return json.dumps({
                "error": "min_similarity must be between 0 and 1."
            })

        # Generate query embedding
        query_embedding = model.encode(query).tolist()

        # Search PostgreSQL / pgvector
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        id,
                        document_name,
                        chunk_index,
                        title,
                        content,
                        1 - (embedding <=> %s::vector) AS similarity
                    FROM knowledge
                    WHERE 1 - (embedding <=> %s::vector) >= %s
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                    """,
                    (
                        query_embedding,
                        query_embedding,
                        min_similarity,
                        query_embedding,
                        limit,
                    ),
                )

                rows = cur.fetchall()

                columns = [
                    description.name
                    for description in cur.description
                ]

        # Convert database rows to dictionaries
        results = [
            dict(zip(columns, row))
            for row in rows
        ]

        # No relevant knowledge found
        if not results:
            return json.dumps({
                "message": (
                    "No relevant internal knowledge "
                    "was found for this query."
                )
            })

        # Serialize results for the LLM tool message
        return json.dumps(
            results,
            default=str,
        )

    except Exception as e:
        return handle_tool_error(
            "search_knowledge",
            e,
        )