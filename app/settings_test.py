from app import settings as base_settings

globals().update(
    {
        name: getattr(base_settings, name)
        for name in dir(base_settings)
        if name.isupper()
    }
)

BASE_DIR = base_settings.BASE_DIR

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

MEDIA_ROOT = BASE_DIR / "test_media"


class DisableMigrations(dict):
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None


MIGRATION_MODULES = DisableMigrations()
