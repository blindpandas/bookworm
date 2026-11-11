"""Loss-conscious tag editing, complete inspection and audio-payload verification.

The editable tree retains typed values, multi-value fields, nested ID3 frames,
cover art and unknown frames. Mutations are staged on a copy and never re-encode
audio. A verified backup is made before an atomic replacement.
"""

import copy
import hashlib
import os
import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from threading import Event
from uuid import uuid4

import mutagen
from mutagen.flac import Picture
from mutagen.id3 import ID3, ID3NoHeaderError, ID3Tags
from mutagen.id3._frames import Frame
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4Cover, MP4FreeForm

from .exporter import _check_cancel, _run_ffmpeg, _signature, ffmpeg_path
from .importer import check_audio_file, fingerprint
from .storage import AudioLibrary


def field_name(name):
    labels = {
        "encoding": _("Text encoding"),
        "text": _("Text"),
        "desc": _("Description"),
        "lang": _("Language code"),
        "url": _("Web address"),
        "data": _("Binary data"),
        "mime": _("MIME type"),
        "type": _("Type code"),
        "owner": _("Owner"),
        "email": _("Email address"),
        "rating": _("Rating"),
        "count": _("Play count"),
        "element_id": _("Chapter identifier"),
        "start_time": _("Start time (milliseconds)"),
        "end_time": _("End time (milliseconds)"),
        "start_offset": _("Start byte offset"),
        "end_offset": _("End byte offset"),
        "sub_frames": _("Embedded ID3 fields"),
        "child_element_ids": _("Child chapter identifiers"),
        "flags": _("Flags"),
        "people": _("Contributors"),
        "width": _("Width (pixels)"),
        "height": _("Height (pixels)"),
        "depth": _("Colour depth (bits)"),
        "colors": _("Indexed colours"),
        "title": _("Title"),
        "artist": _("Artist or narrator"),
        "album": _("Album or book title"),
        "year": _("Year"),
        "comment": _("Comment"),
        "track": _("Track number"),
        "genre": _("Genre code"),
        "TIT2": _("Title (TIT2)"),
        "TALB": _("Album or book title (TALB)"),
        "TPE1": _("Artist or narrator (TPE1)"),
        "TPE2": _("Album artist (TPE2)"),
        "TDRC": _("Recording date (TDRC)"),
        "TRCK": _("Track number (TRCK)"),
        "TPOS": _("Disc number (TPOS)"),
        "TCON": _("Genre (TCON)"),
        "APIC": _("Attached picture (APIC)"),
        "COMM": _("Comment (COMM)"),
        "USLT": _("Lyrics or transcript (USLT)"),
        "CHAP": _("Chapter (CHAP)"),
        "CTOC": _("Table of contents (CTOC)"),
        "TXXX": _("User-defined text (TXXX)"),
        "format": _("Format code"),
        "events": _("Timed events"),
        "frames": _("Frame count"),
        "bytes": _("Byte count"),
        "milliseconds": _("Milliseconds"),
        "bits_for_bytes": _("Bits per byte deviation"),
        "bits_for_milliseconds": _("Bits per time deviation"),
        "channel": _("Channel code"),
        "gain": _("Gain (dB)"),
        "peak": _("Peak level"),
        "method": _("Method code"),
        "adjustments": _("Adjustments"),
        "left": _("Left channel"),
        "right": _("Right channel"),
        "bounce_left": _("Left-channel reflections"),
        "bounce_right": _("Right-channel reflections"),
        "feedback_ltl": _("Feedback: left to left"),
        "feedback_ltr": _("Feedback: left to right"),
        "feedback_rtr": _("Feedback: right to right"),
        "feedback_rtl": _("Feedback: right to left"),
        "premix_ltr": _("Premix: left to right"),
        "premix_rtl": _("Premix: right to left"),
        "value": _("Value"),
        "filename": _("File name"),
        "size": _("Data size"),
        "info": _("Information code"),
        "offset": _("Byte offset"),
        "preview_start": _("Preview start"),
        "preview_length": _("Preview length"),
        "frameid": _("Frame identifier"),
        "position": _("Position"),
        "price": _("Price"),
        "date": _("Date"),
        "seller": _("Seller"),
        "valid_until": _("Valid until"),
        "contact": _("Contact address"),
        "logo": _("Logo data"),
        "group": _("Group identifier"),
        "sig": _("Signature data"),
        "S": _("Index start"),
        "L": _("Indexed data length"),
        "N": _("Index point count"),
        "b": _("Bits per index point"),
        "Fi": _("Index points"),
    }
    return labels.get(name, name)


@dataclass
class TagNode:
    name: str
    kind: str
    value: object = None
    children: list = field(default_factory=list)
    template: object = None


def make_node(name, value):
    if isinstance(value, Frame):
        specs = value._framespec + value._optionalspec
        return TagNode(
            name,
            "frame",
            type(value),
            [make_node(s.name, getattr(value, s.name)) for s in specs if hasattr(value, s.name)],
            copy.deepcopy(value),
        )
    if isinstance(value, ID3Tags):
        return TagNode(
            name,
            "id3",
            children=[make_node(k, v) for k, v in sorted(value.items())],
            template=copy.deepcopy(value),
        )
    if isinstance(value, dict):
        return TagNode(
            name, "mapping", children=[make_node(k, v) for k, v in sorted(value.items())]
        )
    if isinstance(value, (list, tuple)):
        return TagNode(
            name,
            "tuple" if isinstance(value, tuple) else "list",
            children=[make_node(str(i + 1), v) for i, v in enumerate(value)],
        )
    if isinstance(value, bytes):
        return TagNode(name, "binary", bytes(value), template=copy.deepcopy(value))
    if isinstance(value, bool):
        return TagNode(name, "boolean", value)
    if isinstance(value, int):
        return TagNode(name, "integer", int(value))
    if isinstance(value, float):
        return TagNode(name, "number", value)
    return TagNode(name, "text", str(value), template=copy.deepcopy(value))


def node_value(node):
    if node.kind == "frame":
        return node.value(**{c.name: node_value(c) for c in node.children})
    if node.kind == "id3":
        tags = copy.deepcopy(node.template)
        tags.clear()
        for child in node.children:
            value = node_value(child)
            if value.HashKey in tags:
                raise ValueError(
                    _(
                        "Two ID3 frames have the same identifier. Change an identifying field or remove one frame."
                    )
                )
            tags.add(value)
        return tags
    if node.kind == "mapping":
        if len({c.name for c in node.children}) != len(node.children):
            raise ValueError(_("Two tag fields have the same name."))
        return {c.name: node_value(c) for c in node.children}
    if node.kind in ("list", "tuple"):
        values = [node_value(c) for c in node.children]
        return tuple(values) if node.kind == "tuple" else values
    if node.kind == "binary":
        if isinstance(node.template, MP4Cover):
            return MP4Cover(node.value, imageformat=node.template.imageformat)
        if isinstance(node.template, MP4FreeForm):
            return MP4FreeForm(
                node.value, dataformat=node.template.dataformat, version=node.template.version
            )
        return node.value
    return node.value


def _plain(value):
    """Canonical tag values for round-trip checking, excluding text encodings."""
    if isinstance(value, Frame):
        return {
            "frame": type(value).__name__,
            **{
                s.name: _plain(getattr(value, s.name))
                for s in value._framespec + value._optionalspec
                if s.name != "encoding" and hasattr(value, s.name)
            },
        }
    if hasattr(value, "items"):
        return {k: _plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_plain(v) for v in value]
    if isinstance(value, bytes):
        return bytes(value)
    if isinstance(value, (int, float, bool)):
        return value
    return str(value)


def read_v1(path):
    with Path(path).open("rb") as stream:
        stream.seek(0, 2)
        if stream.tell() < 128:
            return b""
        stream.seek(-128, 2)
        raw = stream.read(128)
    return raw if raw[:3] == b"TAG" else b""


def decode_v1(raw, encoding="latin-1"):
    fields = {
        "title": "",
        "artist": "",
        "album": "",
        "year": "",
        "comment": "",
        "track": 0,
        "genre": 255,
    }
    if not raw:
        return fields
    for key, start, end in (
        ("title", 3, 33),
        ("artist", 33, 63),
        ("album", 63, 93),
        ("year", 93, 97),
    ):
        fields[key] = raw[start:end].rstrip(b"\x00 ").decode(encoding, errors="strict")
    v11 = raw[125] == 0 and raw[126] != 0
    fields["comment"] = (
        raw[97 : 125 if v11 else 127].rstrip(b"\x00 ").decode(encoding, errors="strict")
    )
    fields["track"] = raw[126] if v11 else 0
    fields["genre"] = raw[127]
    return fields


def encode_v1(fields, encoding="latin-1"):
    track, genre = int(fields["track"]), int(fields["genre"])
    if not 0 <= track <= 255 or not 0 <= genre <= 255:
        raise ValueError(_("ID3v1 track and genre numbers must be between 0 and 255."))
    data = b"TAG"
    for key, limit in (
        ("title", 30),
        ("artist", 30),
        ("album", 30),
        ("year", 4),
        ("comment", 28 if track else 30),
    ):
        text = fields[key]
        if "\x00" in text:
            raise ValueError(_("ID3v1 text cannot contain a null character."))
        try:
            encoded = text.encode(encoding, errors="strict")
        except UnicodeEncodeError as exc:
            raise ValueError(
                _(
                    "This text cannot be represented in the selected ID3v1 encoding. Use ID3v2 for full Unicode support."
                )
            ) from exc
        if len(encoded) > limit:
            raise ValueError(
                _(
                    "ID3v1 field {field} exceeds its {limit}-byte limit. No text has been truncated."
                ).format(field=field_name(key), limit=limit)
            )
        data += encoded.ljust(limit, b"\x00")
    if track:
        data += bytes((0, track))
    return data + bytes((genre,))


def _write_v1(path, raw):
    with path.open("r+b") as stream:
        if read_v1(path):
            stream.seek(-128, 2)
            stream.truncate()
        stream.seek(0, 2)
        stream.write(raw)


@dataclass
class TagDocument:
    path: Path
    signature: tuple
    audio: object
    tags: TagNode
    v1: bytes
    version: int
    pictures: list
    has_tags: bool
    has_v2: bool

    @classmethod
    def read(cls, path):
        path = Path(path).resolve()
        check_audio_file(path)
        signature = _signature(path)
        audio = mutagen.File(path)
        if audio is None:
            raise ValueError(_("This file does not contain a supported audio stream."))
        has_tags = audio.tags is not None
        has_v2 = isinstance(audio.tags, ID3Tags) and getattr(audio.tags, "version", (0,))[0] == 2
        if audio.tags is None:
            audio.add_tags()
        if isinstance(audio.tags, ID3):
            try:
                audio.tags.load(path, translate=False, load_v1=False)
            except ID3NoHeaderError:
                audio.tags.clear()
        tags = (
            make_node(_("ID3v2 fields"), audio.tags)
            if isinstance(audio.tags, ID3Tags)
            else make_node(_("Tag fields"), dict(audio.tags))
        )
        version = getattr(audio.tags, "version", (2, 4, 0))[1] if has_v2 else 0
        pictures = [
            make_node(
                str(i + 1),
                {
                    key: getattr(p, key)
                    for key in (
                        "type",
                        "mime",
                        "desc",
                        "width",
                        "height",
                        "depth",
                        "colors",
                        "data",
                    )
                },
            )
            for i, p in enumerate(getattr(audio, "pictures", []))
        ]
        return cls(
            path,
            signature,
            audio,
            tags,
            read_v1(path) if isinstance(audio, MP3) else b"",
            version,
            pictures,
            has_tags,
            has_v2,
        )

    def report(self):
        info = self.audio.info
        values = [
            (_("File"), str(self.path)),
            (_("File size (bytes)"), str(self.signature[0])),
            (_("Audio format"), type(self.audio).__name__),
            (_("Duration reported by the audio format (seconds)"), f"{info.length:.6f}"),
            (_("Sample rate (Hz)"), str(getattr(info, "sample_rate", ""))),
            (_("Channels"), str(getattr(info, "channels", ""))),
            (
                _("Bitrate reported by the audio format (bit/s; approximate for VBR)"),
                str(getattr(info, "bitrate", "")),
            ),
        ]
        if hasattr(info, "bits_per_sample"):
            values.append((_("Bits per sample"), str(info.bits_per_sample)))
        if self.has_v2:
            values.append((_("ID3v2 version"), f"2.{self.version}"))
        elif isinstance(self.audio.tags, ID3Tags):
            values.append((_("ID3v2"), _("Not present in this file")))
        lines = [f"{label}: {value}" for label, value in values]
        if isinstance(self.audio, MP3):
            lines.append(_("ID3v1: present") if self.v1 else _("ID3v1: absent"))
            if self.v1:
                lines.append(
                    _(
                        "ID3v1 text below is decoded as ISO-8859-1; use the editor to select Windows-1250 for Hungarian legacy tags."
                    )
                )
                lines.extend(
                    f"ID3v1 / {field_name(key)}: {value}"
                    for key, value in decode_v1(self.v1).items()
                )
        if self.has_tags and (self.tags.kind != "id3" or self.has_v2):
            lines.extend(self._node_lines(self.tags))
        for node in self.pictures:
            lines.extend(self._node_lines(node, _("Cover art") + " / "))
        for i, data in enumerate(getattr(self.audio.tags, "unknown_frames", [])):
            lines.append(
                _("Unknown ID3 frame {index}: {size} bytes, SHA-256 {digest}").format(
                    index=i + 1, size=len(data), digest=hashlib.sha256(data).hexdigest()
                )
            )
        return "\n".join(lines) + "\n"

    def _node_lines(self, node, prefix=""):
        name = prefix + field_name(node.name)
        if node.kind in ("id3", "frame", "list", "tuple", "mapping"):
            for child in node.children:
                yield from self._node_lines(child, name + " / ")
        elif node.kind == "binary":
            yield _("{field}: {size} bytes, SHA-256 {digest}").format(
                field=name, size=len(node.value), digest=hashlib.sha256(node.value).hexdigest()
            )
        else:
            yield f"{name}: {node.value}"


def _hash_file(path, cancel):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        while block := stream.read(1024 * 1024):
            _check_cancel(cancel)
            digest.update(block)
    return digest.digest()


def _audio_hash(path, folder, cancel):
    result = folder / (uuid4().hex + ".hash")
    _run_ffmpeg(
        [
            ffmpeg_path(),
            "-nostdin",
            "-v",
            "error",
            "-xerror",
            "-i",
            str(path),
            "-map",
            "0:a:0",
            "-c:a",
            "copy",
            "-f",
            "hash",
            "-hash",
            "sha256",
            str(result),
        ],
        cancel,
    )
    return result.read_text(encoding="ascii").strip()


def save_tags(document, cancel=None, progress=None, *, v2_version=None, v1=None, library_path=None):
    cancel = cancel or Event()
    path = document.path
    _check_cancel(cancel)
    if _signature(path) != document.signature:
        raise ValueError(
            _("The file changed after its tags were opened. Open the tag editor again.")
        )
    if shutil.disk_usage(path.parent).free < document.signature[0] * 2 + 16 * 1024 * 1024:
        raise OSError(_("There is not enough free space for a verified tag backup."))
    tags = node_value(document.tags)
    version = v2_version or (document.version if document.version in (3, 4) else 4)
    if isinstance(tags, ID3Tags):
        original_values = _plain(tags)
        if version != document.version and getattr(tags, "unknown_frames", []):
            raise ValueError(
                _("The ID3 version cannot be changed while unknown frames are present.")
            )
        if version == 3:
            tags.update_to_v23()
        else:
            tags.update_to_v24()
        if _plain(tags) != original_values:
            raise ValueError(
                _(
                    "This ID3 version change would alter or remove fields. Keep the original version or edit those fields explicitly."
                )
            )
    with tempfile.TemporaryDirectory(prefix=".bookworm-tags-", dir=path.parent) as folder:
        folder = Path(folder)
        staged = folder / path.name
        shutil.copy2(path, staged)
        _check_cancel(cancel)
        original_hash = _hash_file(path, cancel)
        if _hash_file(staged, cancel) != original_hash:
            raise OSError(_("The saved copy failed verification."))
        if progress:
            progress(_("Checking the original audio data"), 0)
        original_audio = _audio_hash(path, folder, cancel)
        audio = copy.deepcopy(document.audio)
        if isinstance(audio.tags, ID3Tags):
            audio.tags = tags
            if isinstance(audio, MP3):
                if document.has_v2 or len(tags):
                    tags.save(staged, v1=0, v2_version=version)
                _write_v1(staged, document.v1 if v1 is None else v1)
            else:
                audio.save(staged, v2_version=version)
        else:
            audio.tags.clear()
            audio.tags.update(tags)
            if hasattr(audio, "clear_pictures"):
                audio.clear_pictures()
                for node in document.pictures:
                    picture = Picture()
                    for key, value in node_value(node).items():
                        setattr(picture, key, value)
                    audio.add_picture(picture)
            audio.save(staged)
        _check_cancel(cancel)
        actual = TagDocument.read(staged)
        if (
            _plain(node_value(actual.tags)) != _plain(tags)
            or [_plain(node_value(node)) for node in actual.pictures]
            != [_plain(node_value(node)) for node in document.pictures]
            or (isinstance(audio, MP3) and actual.v1 != (document.v1 if v1 is None else v1))
        ):
            raise ValueError(
                _(
                    "The saved tags did not match the requested values. The original file has been kept."
                )
            )
        if getattr(actual.audio.tags, "unknown_frames", []) != getattr(
            document.audio.tags, "unknown_frames", []
        ):
            raise ValueError(
                _("Unknown tag data could not be preserved. The original file has been kept.")
            )
        if _audio_hash(staged, folder, cancel) != original_audio:
            raise ValueError(
                _("Audio data changed during tag editing. The original file has been kept.")
            )
        if _signature(path) != document.signature or _hash_file(path, cancel) != original_hash:
            raise ValueError(
                _("The file changed during tag editing. No changes have been applied.")
            )
        backup = path.with_name(path.name + ".bookworm-tags-" + uuid4().hex[:12] + ".bak")
        shutil.copy2(path, backup)
        if _hash_file(backup, cancel) != original_hash:
            raise OSError(_("The tag backup failed verification. The original file has been kept."))
        _check_cancel(cancel)
        with staged.open("r+b") as stream:
            os.fsync(stream.fileno())
        staged.replace(path)
    result = {
        "path": path,
        "backup": backup,
        "size": path.stat().st_size,
        "fingerprint": fingerprint(path),
        "mtime_ns": path.stat().st_mtime_ns,
    }
    if library_path is not None:
        library = AudioLibrary(library_path)
        try:
            library.update_file(path, result["size"], result["fingerprint"], result["mtime_ns"])
        finally:
            library.close()
    return result
