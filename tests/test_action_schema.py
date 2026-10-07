"""Contract checks for the two public, read-only Action imports."""

from pathlib import Path
import re
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]
API_PATHS = {
    "/v1/agent/discover",
    "/v1/agent/capabilities/search",
    "/v2/marketplace/directory",
    "/v2/marketplace/services",
    "/v1/home/public/handles/{handle}",
    "/v1/home/public/profiles/{profileId}",
}
GATEWAY_PATHS = {
    "/v1/services",
    "/v1/services/match",
    "/v1/services/{serviceId}",
}
def references(value):
    if isinstance(value, dict):
        if "$ref" in value:
            yield value["$ref"]
        for child in value.values():
            yield from references(child)
    elif isinstance(value, list):
        for child in value:
            yield from references(child)


class ActionSchemaContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.documents = {
            filename: yaml.safe_load((ROOT / filename).read_text())
            for filename in ("openapi.yaml", "openapi-x402.yaml")
        }

    def test_single_host_and_exact_public_allowlists(self):
        expected = {
            "openapi.yaml": ("https://api.voidly.ai", API_PATHS),
            "openapi-x402.yaml": ("https://x402.voidly.ai", GATEWAY_PATHS),
        }
        for filename, (host, paths) in expected.items():
            with self.subTest(filename=filename):
                document = self.documents[filename]
                self.assertEqual(document["openapi"], "3.1.0")
                self.assertEqual(document["servers"], [{"url": host}])
                self.assertEqual(set(document["paths"]), paths)
                self.assertEqual(document["security"], [])
                for path, item in document["paths"].items():
                    self.assertNotIn("servers", item, path)
                    self.assertEqual(set(item).intersection({"get", "put", "post", "delete", "patch", "head", "options", "trace"}), {"get"}, path)
                    self.assertNotIn("servers", item["get"], path)
                    self.assertNotIn("requestBody", item["get"], path)
                    self.assertEqual(item["get"]["security"], [], path)
                    self.assertIn("200", item["get"]["responses"], path)
                    for parameter in item["get"].get("parameters", []):
                        if parameter.get("name") == "limit" and parameter.get("in") == "query":
                            self.assertEqual(parameter["schema"]["maximum"], 10, path)
                            self.assertEqual(parameter["schema"]["default"], 10, path)
                self.assertNotIn("securitySchemes", document.get("components", {}))

    def test_operation_ids_parameters_and_refs(self):
        ids = []
        for document in self.documents.values():
            for path, item in document["paths"].items():
                operation = item["get"]
                ids.append(operation["operationId"])
                declared = {
                    parameter["name"]
                    for parameter in item.get("parameters", []) + operation.get("parameters", [])
                    if parameter["in"] == "path" and parameter.get("required") is True
                }
                self.assertEqual(declared, set(re.findall(r"\{([^}]+)\}", path)), path)
            for ref in references(document):
                self.assertTrue(ref.startswith("#/components/"), ref)
                target = document
                for part in ref[2:].split("/"):
                    target = target[part.replace("~1", "/").replace("~0", "~")]
                self.assertIsNotNone(target, ref)
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(all(ids))

    def test_availability_is_explicit(self):
        for document in self.documents.values():
            self.assertEqual(document["info"]["version"], "2026-10-07.2")
            self.assertIs(document["x-voidly-coverage"]["servedVerified"], False)
            self.assertIn("not proof of a served release", document["info"]["description"])

        api = self.documents["openapi.yaml"]["paths"]
        for path in API_PATHS:
            if path.startswith("/v1/home/public/"):
                operation = api[path]["get"]
                self.assertEqual(operation["x-voidly-availability"], "feature_gated_unverified")
                description = operation["description"]
                for caveat in ("consent", "indexing", "404"):
                    self.assertIn(caveat, description)
                self.assertIn("404", operation["responses"])
        self.assertIn("EXACT match", api["/v1/agent/discover"]["get"]["description"])
        self.assertIn("grants no checkout", api["/v2/marketplace/services"]["get"]["description"])

        gateway = self.documents["openapi-x402.yaml"]["paths"]
        for path in GATEWAY_PATHS:
            self.assertEqual(gateway[path]["get"]["x-voidly-availability"], "external_gateway_documented")
        self.assertIn("HTTP 402 terms", gateway["/v1/services"]["get"]["description"])

    def test_public_files_do_not_name_internal_provenance(self):
        for filename in ("README.md", "openapi.yaml", "openapi-x402.yaml", "scripts/build_action_schema.py"):
            content = (ROOT / filename).read_text()
            self.assertNotIn("github.com/", content, filename)
            self.assertNotRegex(content, r"\bMigration\s+\d{3,}\b", filename)
        for document in self.documents.values():
            self.assertEqual({key for key in document if key.startswith("x-")}, {"x-voidly-coverage"})
            for item in document["paths"].values():
                self.assertLessEqual(
                    {key for key in item["get"] if key.startswith("x-")},
                    {"x-voidly-availability"},
                )


if __name__ == "__main__":
    unittest.main()
