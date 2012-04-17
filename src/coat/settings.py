import re

from fabric.utils import abort


def validate_re(regexp):
    if isinstance(regexp, basestring):
        regexp = re.compile(regexp)

    return lambda value: regexp.match(value)

validate_string = lambda value: (isinstance(value, basestring) and
                                 len(value) > 0)

validate_true = lambda value: bool(value)
validate_list = lambda value: isinstance(value, list)


class Settings(dict):
    def __init__(self, **kwargs):
        super(dict, self).__init__()

        self.update(kwargs)

    def validate_or_abort(self):
        missing = []

        for key, validator in self.required.iteritems():
            if validator is None:
                validator = validate_true

            if (not key in self or
                not validator(self[key])):
                missing.append(key)

        if len(missing) > 0:
            abort("missing (or invalid) settings %s for %r" % (
                missing, self.__class__.__name__)
            )

        return len(missing) == 0


class HostSettings(Settings):
    defaults = {
        'port': 22,
    }

    required = {
        'host': validate_string,
        'user': validate_string,
    }


class LocalSettings(Settings):
    defaults = {

    }


class DjangoSettings(Settings):
    default = {
        'run_commands': [
            'syncdb', 'migrate',
        ],
    }

    required = {
        'wsgi_file': validate_string,
    }


HostSettings(host=12, user="test").validate_or_abort()
