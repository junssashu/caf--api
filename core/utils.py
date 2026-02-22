import random
import re

from django.core.validators import RegexValidator

CHARSET = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'

phone_validator = RegexValidator(
    regex=r'^0[1-9]\d{8}$',
    message='Le numero de telephone doit etre au format ivoirien (ex: 0707070707).',
)


def generate_code(prefix, model_class, field='code'):
    """Generate a unique code like CAF-A7B3K9 or REC-M2N4P6."""
    while True:
        code = prefix + '-' + ''.join(random.choices(CHARSET, k=6))
        if not model_class.objects.filter(**{field: code}).exists():
            return code
