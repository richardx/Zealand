import json


class Flat_file_loader:

    def __init__(self, filename: str):
        self._filename = filename

    def load(self) -> dict:
        """Indlæser databasen fra JSON-filen. Returnerer tom dict hvis filen ikke findes."""
        try:
            with open(self._filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save(self, data: dict):
        """Gemmer data til JSON-filen."""
        with open(self._filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
