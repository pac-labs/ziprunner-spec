"""Tests the specification's illustrative external handoff contract.

Does not perform network access or assert example.org hosts an actual ZIP.
"""
import re
import unittest
from pathlib import Path
from urllib.parse import urlsplit, unquote

ROOT = Path(__file__).resolve().parents[1]

class DeliveryHandoffDocumentationTests(unittest.TestCase):
    def setUp(self):
        self.example = (ROOT / "examples/DELIVERY_HANDOFF.md").read_text(encoding="utf-8")
        self.contract = (ROOT / "docs/DELIVERY.md").read_text(encoding="utf-8")
        self.spec = (ROOT / "SPECIFICATION.md").read_text(encoding="utf-8")

    def test_required_identity_fields_in_example(self):
        for field in ("Project", "Version", "ZIP filename", "Download", "SHA-256"):
            with self.subTest(field=field):
                self.assertIn(f"**{field}:**", self.example)

    def test_download_is_clickable_markdown_with_exact_zip_basename(self):
        named = re.search(r"\*\*ZIP filename:\*\* `([^`]+)`", self.example)
        link = re.search(r"\*\*Download:\*\* \[([^]]+)\]\(([^)]+)\)", self.example)
        self.assertIsNotNone(named)
        self.assertIsNotNone(link)
        self.assertEqual(named.group(1), link.group(1))
        self.assertEqual(named.group(1), unquote(urlsplit(link.group(2)).path).rsplit("/", 1)[-1])

    def test_digest_is_sha256_shape(self):
        match = re.search(r"\*\*SHA-256:\*\* `([a-fA-F0-9]+)`", self.example)
        self.assertIsNotNone(match)
        self.assertEqual(64, len(match.group(1)))

    def test_example_is_marked_as_nonlive(self):
        self.assertIn("Documentation example only", self.example)
        self.assertIn("illustrative", self.example)

    def test_contract_excludes_in_zip_link_requirement(self):
        self.assertIn("external delivery message", self.contract)
        self.assertIn("not required to include the final link", self.contract)
        self.assertIn("delivery incomplete", self.contract)

    def test_normative_rule_covers_missing_download_links(self):
        self.assertIn("## 10B. Downloadable artifact handoff", self.spec)
        self.assertIn("direct clickable download link", self.spec)
        self.assertIn("MUST NOT invent or guess URLs", self.spec)

if __name__ == "__main__":
    unittest.main()
