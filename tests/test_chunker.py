from app.ingestion.pdf_loader import PDFLoader
from app.ingestion.chunker import TextChunker


PDF_PATH = "data/raw/employee_policy.pdf"


def main():

    # 1. Load PDF
    loader = PDFLoader()
    documents = loader.load(PDF_PATH)

    print(f"Pages extracted: {len(documents)}")

    # 2. Create chunker
    chunker = TextChunker(
        chunk_size=120,
        chunk_overlap=20
    )

    # 3. Create chunks
    chunks = chunker.chunk_documents(documents)

    print(f"Total chunks created: {len(chunks)}")

    # 4. Display chunks
    for chunk in chunks:

        print("\n" + "=" * 70)

        print(
            f"Chunk ID: "
            f"{chunk['metadata']['chunk_id']}"
        )

        print(
            f"Source: "
            f"{chunk['metadata']['source']}"
        )

        print(
            f"Page: "
            f"{chunk['metadata']['page']}"
        )

        print(
            f"Chunk Index: "
            f"{chunk['metadata']['chunk_index']}"
        )

        print("\nText:")

        print(chunk["text"])


if __name__ == "__main__":
    main()