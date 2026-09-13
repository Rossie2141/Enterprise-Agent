from pathlib import Path

from sentence_transformers import SentenceTransformer

from app.db.connection import get_connection
from app.rag.chunker import chunk_text


KNOWLEDGE_DIR = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "knowledge"
)

EMBEDDING_MODEL = "all-MiniLM-L6-v2"


def ingest_knowledge():
    print("Loading embedding model...")

    model = SentenceTransformer(EMBEDDING_MODEL)

    files = list(KNOWLEDGE_DIR.glob("*.txt"))

    if not files:
        print("No knowledge files found.")
        return

    total_chunks = 0

    with get_connection() as conn:
        with conn.cursor() as cur:

            # Clear existing chunks before re-ingestion
            cur.execute("DELETE FROM knowledge")

            for file_path in files:
                document_name = file_path.name
                title = file_path.stem.replace("_", " ").title()

                content = file_path.read_text(
                    encoding="utf-8"
                ).strip()

                chunks = chunk_text(
                    content,
                    chunk_size=500,
                    overlap=100,
                )

                print(
                    f"\nProcessing {document_name}: "
                    f"{len(chunks)} chunks"
                )

                for chunk_index, chunk in enumerate(chunks):

                    embedding = model.encode(
                        chunk
                    ).tolist()

                    cur.execute(
                        """
                        INSERT INTO knowledge (
                            document_name,
                            chunk_index,
                            title,
                            content,
                            embedding
                        )
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (
                            document_name,
                            chunk_index,
                            title,
                            chunk,
                            embedding,
                        ),
                    )

                    total_chunks += 1

    print(
        f"\nSuccessfully ingested "
        f"{len(files)} documents into "
        f"{total_chunks} chunks."
    )


if __name__ == "__main__":
    ingest_knowledge()