import os
import subprocess

import mutagen
import pytest
from mutagen.id3 import CHAP, COMM, PRIV, TIT2, TXXX

from bookworm.audiobooks.metadata import (
    TagDocument,
    _plain,
    decode_v1,
    encode_v1,
    make_node,
    node_value,
    read_v1,
    save_tags,
)


@pytest.mark.parametrize("text", ("árvíztűrő", "a" * 31))
def test_v1_does_not_silently_replace_or_truncate_text(text):
    fields = decode_v1(b"")
    fields["title"] = text
    with pytest.raises(ValueError, match="ID3v1"):
        encode_v1(fields)


def test_v1_hungarian_code_page_and_11_track_round_trip():
    fields = decode_v1(b"")
    fields.update(title="Árvíztűrő tükörfúrógép", track=12, genre=255)
    raw = encode_v1(fields, "cp1250")
    assert len(raw) == 128
    assert decode_v1(raw, "cp1250") == fields


def test_nested_id3_values_are_preserved_by_the_editable_tree():
    value = CHAP(
        element_id="first",
        start_time=0,
        end_time=2000,
        sub_frames=[TIT2(text=["Árvíztűrő"]), TXXX(desc="Egyéni", text=["Első", "Második"])],
    )
    restored = node_value(make_node("chapter", value))
    assert _plain(restored) == _plain(value)


native = pytest.mark.skipif(
    os.environ.get("BOOKWORM_TEST_AUDIO") != "1", reason="Native audio tests are opt-in"
)


@native
@pytest.mark.parametrize("format_name", ("mp3", "m4b", "flac", "ogg", "opus", "wav"))
def test_tag_save_round_trip_and_verified_backup(tmp_path, format_name):
    source = tmp_path / ("Árvíztűrő." + format_name)
    subprocess.run(
        ["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "sine=duration=2", str(source)], check=True
    )
    original = source.read_bytes()
    document = TagDocument.read(source)
    if document.tags.kind == "id3":
        document.tags.children.extend(
            [
                make_node("TIT2", TIT2(text=["Árvíztűrő tükörfúrógép"])),
                make_node(
                    "COMM", COMM(lang="hun", desc="Megjegyzés", text=["Első sor\nMásodik sor"])
                ),
                make_node("PRIV", PRIV(owner="Bookworm test", data=b"\x00\x01\xff\x00")),
            ]
        )
    else:
        key = "\xa9nam" if format_name == "m4b" else "title"
        document.tags.children.append(make_node(key, ["Árvíztűrő tükörfúrógép"]))
    result = save_tags(document)
    assert result["backup"].read_bytes() == original
    assert "Árvíztűrő tükörfúrógép" in TagDocument.read(source).report()
    assert not list(tmp_path.glob(".bookworm-tags-*"))
    if format_name == "mp3":
        assert mutagen.File(source).tags.getall("PRIV")[0].data == b"\x00\x01\xff\x00"


@native
def test_mp3_v1_and_v2_are_saved_independently(tmp_path):
    source = tmp_path / "v1.mp3"
    subprocess.run(
        ["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "sine=duration=1", str(source)], check=True
    )
    document = TagDocument.read(source)
    document.tags.children.append(make_node("TIT2", TIT2(text=["Teljes magyar cím: árvíztűrő"])))
    v1 = decode_v1(b"")
    v1["title"] = "Legacy title"
    raw = encode_v1(v1)
    save_tags(document, v1=raw)
    assert read_v1(source) == raw
    assert "árvíztűrő" in str(mutagen.File(source).tags["TIT2"])


@native
def test_external_file_change_prevents_tag_overwrite(tmp_path):
    source = tmp_path / "change.mp3"
    subprocess.run(
        ["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "sine=duration=1", str(source)], check=True
    )
    document = TagDocument.read(source)
    with source.open("ab") as stream:
        stream.write(b"external change")
    changed = source.read_bytes()
    with pytest.raises(ValueError, match="changed"):
        save_tags(document)
    assert source.read_bytes() == changed


@native
def test_flac_cover_art_fields_and_audio_survive_tag_save(tmp_path):
    import base64

    source = tmp_path / "cover.flac"
    subprocess.run(
        ["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "sine=duration=1", str(source)], check=True
    )
    image = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aV6sAAAAASUVORK5CYII="
    )
    fields = dict(
        type=3,
        mime="image/png",
        desc="Magyar borítókép",
        width=1,
        height=1,
        depth=16,
        colors=0,
        data=image,
    )
    document = TagDocument.read(source)
    document.pictures.append(make_node("1", fields))
    save_tags(document)
    restored = TagDocument.read(source)
    assert node_value(restored.pictures[0]) == fields
    assert mutagen.File(source).pictures[0].data == image


@native
@pytest.mark.parametrize("with_v1", (False, True))
def test_read_only_inspection_does_not_invent_id3v2_or_modify_file(tmp_path, with_v1):
    source = tmp_path / "original.mp3"
    subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-f",
            "lavfi",
            "-i",
            "sine=duration=1",
            "-id3v2_version",
            "0",
            "-write_id3v1",
            "0",
            str(source),
        ],
        check=True,
    )
    if with_v1:
        fields = decode_v1(b"")
        fields["title"] = "Only version one"
        with source.open("ab") as stream:
            stream.write(encode_v1(fields))
    original = source.read_bytes()
    document = TagDocument.read(source)
    assert not document.has_v2
    assert "ID3v2 version:" not in document.report()
    assert "ID3v2 fields /" not in document.report()
    assert ("Only version one" in document.report()) is with_v1
    assert source.read_bytes() == original
