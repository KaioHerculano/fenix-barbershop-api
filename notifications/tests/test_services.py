import json
from unittest.mock import MagicMock, patch

from django.test import TestCase

from notifications.services import resend_payload, send_email


class ResendServiceTests(TestCase):
    def test_resend_payload_uses_expected_shape(self):
        payload = resend_payload(
            {
                "to": "user@example.com",
                "subject": "Subject",
                "html": "<p>Hello</p>",
                "text": "Hello",
            }
        )

        self.assertEqual(payload["to"], ["user@example.com"])
        self.assertEqual(payload["subject"], "Subject")

    @patch.dict("os.environ", {}, clear=True)
    def test_send_email_skips_without_api_key(self):
        result = send_email(
            {
                "to": "user@example.com",
                "subject": "Subject",
                "html": "<p>Hello</p>",
                "text": "Hello",
            }
        )

        self.assertFalse(result["sent"])
        self.assertEqual(result["reason"], "missing_api_key")

    @patch.dict("os.environ", {"RESEND_API_KEY": "secret"}, clear=True)
    @patch("notifications.services.urlopen")
    def test_send_email_posts_to_resend(self, urlopen_mock):
        response = MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps(
            {"id": "email-id"}
        ).encode("utf-8")
        urlopen_mock.return_value = response

        result = send_email(
            {
                "to": "user@example.com",
                "subject": "Subject",
                "html": "<p>Hello</p>",
                "text": "Hello",
            }
        )

        self.assertEqual(result["id"], "email-id")
