from django.test import TestCase

from company.models import StaffInvitation


class StaffInvitationModelTests(TestCase):
    def test_generates_token_and_digest(self):
        token, digest = StaffInvitation.build_token()

        self.assertNotEqual(token, digest)
        self.assertEqual(StaffInvitation.digest_token(token), digest)
        self.assertEqual(len(digest), 64)
