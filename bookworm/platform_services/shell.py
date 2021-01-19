# coding: utf-8


from dataclasses import dataclass
from bookworm import typehints as t
from bookworm import app
from bookworm.paths import app_path
from bookworm.reader import EBookReader
from . import PLATFORM


@dataclass
class SupportedFileFormat:
    format: str
    ext: str
    name: str

    @property
    def icon(self):
        ficos_path = app_path("resources", "icons")
        icon = ficos_path.joinpath(self.format + ".ico")
        return icon if icon.exists() else None

    @property
    def ext_prog_id(self):
        return f"{app.prog_id}.{self.format}"

    @property
    def display_name(self):
        return _(self.name)

    def astuple(self):
        return (self.ext_prog_id, _(self.display_name), str(self.icon))


def get_ext_info(supported="*"):
    doctypes = {}
    for cls in EBookReader.document_classes:
        for ext in cls.extensions:
            cext = ext.replace("*", "")
            if (supported == "*") or (cext in supported):
                doctypes[cext] = SupportedFileFormat(cls.format, ext, cls.name).astuple()
    return doctypes



if PLATFORM == "win32":
    from ._win32.shell import shell_integrate, shell_disintegrate
elif PLATFORM == "linux":
    from ._linux.shell import shell_integrate, shell_disintegrate


