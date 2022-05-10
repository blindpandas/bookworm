# coding: utf-8


from dataclasses import dataclass

from bookworm import app
from bookworm import typehints as t
from bookworm.paths import app_path
from bookworm.reader import get_document_format_info

from . import PLATFORM


@dataclass
class SupportedFileFormat:
    format: str
    ext: str
    name: str

    @property
    def icon(self):
        ficos_path = app_path("resources", "icons")
        icon = ficos_path.joinpath(f"{self.format}.ico")
        return icon if icon.exists() else ficos_path.joinpath("file.ico")

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
    shell_integratable_docs = [
        doc_cls
        for doc_cls in get_document_format_info().values()
        if (not doc_cls.__internal__) and (doc_cls.extensions is not None)
    ]
    for cls in shell_integratable_docs:
        for ext in cls.extensions:
            cext = ext.replace("*", "")
            if (supported == "*") or (cext in supported):
                doctypes[cext] = SupportedFileFormat(
                    cls.format, ext, cls.name
                ).astuple()
    return doctypes


if PLATFORM == "win32":
    from ._win32.shell import shell_disintegrate, shell_integrate
elif PLATFORM == "linux":
    from ._linux.shell import shell_disintegrate, shell_integrate
