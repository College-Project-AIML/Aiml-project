import os
import sys

# Append project root to sys.path so we can import services from scripts/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.api.db import init_pool, get_db, close_pool
from services.api.chatbot.scheme_retriever import build_scheme_embedding_index


def main():
    print("Initializing database connection pool...")
    init_pool()
    try:
        with get_db() as cur:
            print("Building scheme embeddings... This may take a moment.")
            count = build_scheme_embedding_index(cur)
            print(f"Built persistent embedding index for {count} schemes.")
    finally:
        close_pool()


if __name__ == "__main__":
    main()
