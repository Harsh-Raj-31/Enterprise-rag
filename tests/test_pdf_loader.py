from app.ingestion.pdf_loader import PDFLoader


PDF_PATH = "data/raw/employee_policy.pdf"


def main():
    loader = PDFLoader()

    documents = loader.load(PDF_PATH)

    print(f"\nPages extracted: {len(documents)}")

    for document in documents:
        print("\n" + "=" * 60)

        print(f"Source: {document['metadata']['source']}")
        print(f"Page: {document['metadata']['page']}")

        print("\nText preview:")
        print(document["text"][:500])


if __name__ == "__main__":
    main()