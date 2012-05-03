from django.core.exceptions import ValidationError

from fabric.utils import abort


class Settings(dict):
    """
    Object that holds setting items and a method of validating required
    settings.

    The class should be subclassed and the key `defaults` should contain a dict
    with default values.

    The dict `required` should contain key => (`validator`, ...) where
    `validator` is a callable that will be called with the value to be
    validated.
    """
    def __init__(self, **kwargs):
        super(dict, self).__init__()

        self.update_and_replace(self.defaults)
        self.update_and_replace(kwargs)

    def update_and_replace(self, other=None, **kwargs):
        """
        Like normal `dict.update` except it allows for value string replacement
        with already defined values in itself.

        Can be called with another `dict`, `**kwargs` or both.
        """
        def replace(v):
            """
            Recursivly replace strings, dicts, tuples and lists.
            """
            if isinstance(v, (tuple, list)):
                return map(replace, v)
            elif isinstance(v, dict):
                for key, value in v.iteritems():
                    v[replace(key)] = replace(value)
                return v
            elif isinstance(v, basestring):
                return v % self
            else:
                return v

        if other is None:
            other = {}

        if kwargs:
            other.update(kwargs)

        for key, value in other.iteritems():
            self[key] = replace(value)

    def validate_or_abort(self):
        """
        Validate the values acording to the list of validators given.
        """
        missing = []

        for key, validators in self.required.iteritems():
            if not isinstance(validators, (list, tuple)):
                validators = (validators, )

            for validator in validators:
                try:
                    validator(self[key])
                except (ValueError, KeyError, ValidationError), exc:
                    missing.append((key, str(exc)))

        if len(missing) > 0:
            abort(
                "missing (or invalid) settings %s for %r" %
                (missing, self.__class__.__name__)
            )

        return len(missing) == 0
