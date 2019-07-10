from __future__ import absolute_import
from .base import Output

try:
    import espeak.core
except:
    raise RuntimeError("Cannot find espeak.core. Please install python-espeak")


class ESpeak(Output):
    """Speech output supporting ESpeak on Linux
				Note this requires python-espeak to be installed
				This can be done on Debian distros by using apt-get install python-espeak
				Or through this tarball: https://launchpad.net/python-espeak
	"""

    name = "Linux ESpeak"

    def is_active(self):
        try:
            import espeak.core
        except:
            return False
        return True

    def speak(self, text, interrupt=0):
        if interrupt:
            self.silence()
        espeak.core.synth(text)

    def silence(self):
        espeak.core.cancel()


output_class = ESpeak
