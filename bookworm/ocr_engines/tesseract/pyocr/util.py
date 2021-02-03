import re


def digits_only(string):
    """Return all digits that the given string starts with."""
    match = re.match(r'\D*(?P<digits>\d+)', string)
    if match:
        return int(match.group('digits'))
    return 0
