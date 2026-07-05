import re

from django.core.exceptions import ValidationError


class ComplexPasswordValidator:
    def validate(self, password, user=None):
        if not re.findall(r"[A-Z]", password):
            raise ValidationError(
                "A senha deve conter pelo menos uma letra maiúscula (A-Z).",
                code="password_no_upper",
            )
        if not re.findall(r"[a-z]", password):
            raise ValidationError(
                "A senha deve conter pelo menos uma letra minúscula (a-z).",
                code="password_no_lower",
            )
        if not re.findall(r"\d", password):
            raise ValidationError(
                "A senha deve conter pelo menos um número (0-9).",
                code="password_no_number",
            )
        if not re.findall(r"[()[\]{}|\\`~!@#$%^&*_\-+=;:'\",<>./?]", password):
            raise ValidationError(
                "A senha deve conter pelo menos um caractere especial.",
                code="password_no_symbol",
            )

    def get_help_text(self):
        return (
            "A senha deve conter pelo menos uma letra maiúscula, uma minúscula, "
            "um número e um caractere especial."
        )
