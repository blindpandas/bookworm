from __future__ import absolute_import
import accessible_output2
from .base import Output, OutputError


class Auto(Output):
    def __init__(self):
        output_classes = accessible_output2.get_output_classes()
        self.outputs = []
        for output in output_classes:
            try:
                self.outputs.append(output())
            except OutputError:
                pass

    def get_first_available_output(self):
        for output in self.outputs:
            if output.is_active():
                return output
        return None

    def speak(self, *args, **kwargs):
        output = self.get_first_available_output()
        if output:
            output.speak(*args, **kwargs)

    def braille(self, *args, **kwargs):
        output = self.get_first_available_output()
        if output:
            output.braille(*args, **kwargs)

    def output(self, *args, **kwargs):
        output = self.get_first_available_output()
        if output:
            output.speak(*args, **kwargs)

    def is_system_output(self):
        output = self.get_first_available_output()
        if output:
            return output.is_system_output()
