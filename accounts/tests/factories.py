from django.utils.crypto import get_random_string

from accounts.models import User


class FakeData:
    def email(self):
        return f"{get_random_string(10).lower()}@example.com"

    def password(self):
        return "StrongPass123!"

    def user(self, full_name=None):
        value = get_random_string(8)
        return User.objects.create_user(
            email=self.email(),
            full_name=full_name or f"Pessoa {value}",
            password=self.password(),
        )

    def owner_payload(self):
        value = get_random_string(8).lower()
        return {
            "company_name": f"Barbearia {value}",
            "company_slug": f"barbearia-{value}",
            "full_name": f"Owner {value}",
            "email": self.email(),
            "password": self.password(),
        }

    def customer_payload(self):
        value = get_random_string(8)
        return {
            "full_name": f"Cliente {value}",
            "email": self.email(),
            "phone": "65999999999",
            "password": self.password(),
            "password_confirmation": self.password(),
        }
