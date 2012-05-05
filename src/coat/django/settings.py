from django.core.validators import MinLengthValidator

from coat.settings import Settings


__all__ = ("DjangoSettings", )


class VirtualenvSettings(Settings):
    """
    A settings object for a python virtualenv based envorinment.
    """
    DEFAULT_COMMANDS = [
        "pip -q install -r django/requirements.txt"
    ]

    defaults = {
        'commands': DEFAULT_COMMANDS,
    }


class DjangoSettings(Settings):
    """
    A settings object for a Django project.
    """
    DEFAULT_MANAGEMENT_COMMANDS = [
        'syncdb --noinput',
        'migrate',
    ]

    defaults = {
        'management_commands': DEFAULT_MANAGEMENT_COMMANDS,
        'versions_dir': 'app/versions',
    }

    required = {
        'django_appname': MinLengthValidator(1),
        'wsgi_file': MinLengthValidator(1),
        'settings_file': MinLengthValidator(1),
    }
