# NOTE: This file must remain Python 2 compatible for the foreseeable future,
# to ensure that we error out properly for existing editable installs.

import sys
if sys.version_info < (3, 4):  # noqa: E402
    raise ImportError("""
PyOCR 0.7+ does not support Python 2.x, 3.0, 3.1, 3.2, or 3.3.
Beginning with PyOCR 0.7, Python 3.4 and above is required.

See PyOCR `README.markdown` file for more information:

    https://gitlab.gnome.org/World/OpenPaperwork/pyocr/blob/master/README.markdown

""")

from .pyocr import *  # noqa
from .error import PyocrException

__all__ = [
    'get_available_tools',
    'PyocrException',
    'TOOLS',
    'VERSION',
]
