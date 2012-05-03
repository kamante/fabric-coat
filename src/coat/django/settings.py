from django.core.validators import MinLengthValidator

from coat.settings import Settings


__all__ = ("DjangoSettings", )


class DjangoSettings(Settings):
    """
    A settings object for Django based settings.
    """
    DEFAULT_MANAGEMENT_COMMANDS = [
        'syncdb --noinput',
        'migrate'
    ]

    defaults = {
        'management_commands': DEFAULT_MANAGEMENT_COMMANDS,
    }

    required = {
        'django_appname': MinLengthValidator(1),
        'wsgi_file': MinLengthValidator(1),
    }
