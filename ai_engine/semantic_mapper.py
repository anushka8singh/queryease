import json
from pathlib import Path


class SemanticMapper:
    def __init__(self, mapping_path: str | Path) -> None:
        self.mapping_path = Path(mapping_path)
        self.mapping = self._load_mapping()

    def _load_mapping(self) -> dict[str, list[dict[str, str]]]:
        if not self.mapping_path.exists():
            return {}
        with self.mapping_path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def match(self, user_query: str) -> list[dict[str, str]]:
        lowered_query = user_query.lower()
        matches: list[dict[str, str]] = []

        for business_term, definitions in self.mapping.items():
            if business_term.lower() in lowered_query:
                matches.extend(
                    {
                        "business_term": business_term,
                        "table": definition["table"],
                        "column": definition["column"],
                        "description": definition["description"],
                    }
                    for definition in definitions
                )

        return matches

    def describe(self, matches: list[dict[str, str]]) -> str:
        if not matches:
            return "No semantic aliases matched the request."

        return "\n".join(
            f"- {match['business_term']} -> {match['table']}.{match['column']} ({match['description']})"
            for match in matches
        )
