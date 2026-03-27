"""Tests for Lab 38 — PII Handling"""

import sys
import os
import unittest

_lab_target = os.getenv("LAB_TARGET", "starter")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', _lab_target))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..', 'shared'))


class TestDetectPII(unittest.TestCase):
    def test_detects_email(self):
        from solution import detect_pii
        result = detect_pii("Contact me at john@example.com")
        self.assertIn("email", result)
        self.assertIn("john@example.com", result["email"])

    def test_detects_ssn(self):
        from solution import detect_pii
        result = detect_pii("My SSN is 123-45-6789.")
        self.assertIn("ssn", result)
        self.assertIn("123-45-6789", result["ssn"])

    def test_detects_credit_card(self):
        from solution import detect_pii
        result = detect_pii("Card: 4111-1111-1111-1111")
        self.assertIn("credit_card", result)

    def test_no_pii_returns_empty_dict(self):
        from solution import detect_pii
        result = detect_pii("Hello, how are you?")
        self.assertEqual(result, {})

    def test_returns_dict(self):
        from solution import detect_pii
        result = detect_pii("test@test.com")
        self.assertIsInstance(result, dict)

    def test_detects_multiple_pii_types(self):
        from solution import detect_pii
        result = detect_pii("Email john@example.com, SSN 123-45-6789")
        self.assertIn("email", result)
        self.assertIn("ssn", result)


class TestRedactPII(unittest.TestCase):
    def test_redacts_email(self):
        from solution import redact_pii
        result = redact_pii("My email is john@example.com")
        self.assertNotIn("john@example.com", result)
        self.assertIn("[EMAIL_REDACTED]", result)

    def test_redacts_ssn(self):
        from solution import redact_pii
        result = redact_pii("SSN: 123-45-6789")
        self.assertNotIn("123-45-6789", result)
        self.assertIn("[SSN_REDACTED]", result)

    def test_no_pii_unchanged(self):
        from solution import redact_pii
        text = "Hello world."
        result = redact_pii(text)
        self.assertEqual(result, text)

    def test_returns_string(self):
        from solution import redact_pii
        result = redact_pii("test@example.com")
        self.assertIsInstance(result, str)


class TestPseudonymize(unittest.TestCase):
    def test_returns_tuple(self):
        from solution import pseudonymize
        result = pseudonymize("john@example.com")
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)

    def test_replaces_email_with_placeholder(self):
        from solution import pseudonymize
        text, mapping = pseudonymize("Contact john@example.com")
        self.assertNotIn("john@example.com", text)
        self.assertIn("email_1", text)

    def test_mapping_contains_original(self):
        from solution import pseudonymize
        text, mapping = pseudonymize("Email: john@example.com")
        self.assertIn("john@example.com", mapping.values())

    def test_two_emails_get_different_placeholders(self):
        from solution import pseudonymize
        text, mapping = pseudonymize("john@example.com and jane@example.com")
        placeholders = list(mapping.keys())
        self.assertEqual(len(placeholders), 2)
        self.assertNotEqual(placeholders[0], placeholders[1])


class TestRestorePseudonyms(unittest.TestCase):
    def test_restores_original(self):
        from solution import pseudonymize, restore_pseudonyms
        original = "Contact john@example.com for help."
        pseudo_text, mapping = pseudonymize(original)
        restored = restore_pseudonyms(pseudo_text, mapping)
        self.assertIn("john@example.com", restored)

    def test_restore_with_empty_mapping(self):
        from solution import restore_pseudonyms
        text = "No PII here."
        result = restore_pseudonyms(text, {})
        self.assertEqual(result, text)

    def test_restore_roundtrip(self):
        from solution import pseudonymize, restore_pseudonyms
        original = "SSN 123-45-6789 is flagged."
        pseudo_text, mapping = pseudonymize(original)
        restored = restore_pseudonyms(pseudo_text, mapping)
        self.assertIn("123-45-6789", restored)


if __name__ == "__main__":
    unittest.main()
