from pathlib import Path

import pandas as pd


class SpreadsheetLoader:
    """Load CSV and Excel files into document-like records."""

    SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls"}

    def load(self, file_path: str) -> list[dict]:
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(
                f"Spreadsheet file not found: {file_path}"
            )

        extension = path.suffix.lower()

        if extension not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(
                "Supported spreadsheet formats are: CSV, XLSX, and XLS."
            )

        if extension == ".csv":
            return self._load_csv(path)

        return self._load_excel(path)

    def _load_csv(self, path: Path) -> list[dict]:
        dataframe = pd.read_csv(path)

        return self._dataframe_to_documents(
            dataframe=dataframe,
            source=path.name,
            file_type="csv",
        )

    def _load_excel(self, path: Path) -> list[dict]:
        sheets = pd.read_excel(
            path,
            sheet_name=None,
        )

        documents = []

        for sheet_name, dataframe in sheets.items():
            documents.extend(
                self._dataframe_to_documents(
                    dataframe=dataframe,
                    source=path.name,
                    file_type="xlsx",
                    sheet_name=str(sheet_name),
                )
            )

        return documents

    def _dataframe_to_documents(
        self,
        dataframe: pd.DataFrame,
        source: str,
        file_type: str,
        sheet_name: str | None = None,
    ) -> list[dict]:
        # Remove completely empty rows.
        dataframe = dataframe.dropna(how="all")

        # Normalize column names.
        dataframe.columns = [
            str(column).strip()
            for column in dataframe.columns
        ]

        documents = []

        for row_number, (_, row) in enumerate(
            dataframe.iterrows(),
            start=1,
        ):
            fields = []

            for column, value in row.items():
                if pd.isna(value):
                    continue

                fields.append(
                    f"{column}: {value}"
                )

            if not fields:
                continue

            text = " | ".join(fields)

            metadata = {
                "source": source,
                "document_type": "spreadsheet",
                "file_type": file_type,
                "row": row_number,
            }

            if sheet_name is not None:
                metadata["sheet"] = sheet_name

            documents.append(
                {
                    "text": text,
                    "metadata": metadata,
                }
            )

        return documents
