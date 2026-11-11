# Local audiobooks: architecture and validation

The File menu opens a separate native wx audiobook window with Ctrl+F11.
The service is lazy: document reading does not import libmpv or create an audio
device. Audiobooks have their own SQLite database in
`data_path("audiobooks", "library.sqlite3")`; document positions and annotations
are not migrated or repurposed.

## Components and invariants

* `model.py` defines an ordered, millisecond timeline independent of physical
  files. Relative paths cannot escape the book root. Embedded chapters retain
  their original file offsets, even when the listening order is edited.
* `importer.py` checks existence, nonzero size, readability, real audio headers,
  finite duration and full SHA-256 identity. Folder scanning skips other file
  types and symlinks and reports inaccessible subfolders. The GUI also requests
  complete FFmpeg decoding before import completes. This takes time proportional
  to the recording; it is cancellable and runs outside the GUI thread. A corrupt
  supported file aborts the import instead of silently creating an incomplete book.
* `storage.py` commits positions, rate, volume, boost and annotations
  transactionally. Identical reimports retain the book ID and annotations,
  including after a timestamp-only change. Relocation checks complete file hashes.
  Bookmark JSON validates all entries before writing and deduplicates repeats.
* `player.py` owns state transitions on the GUI thread. Load generations reject
  stale native callbacks. Loading and stalled playback have deadlines. In-file
  seeks reuse the decoder; contiguous embedded chapters do not reopen it. Book
  completion, file EOF, sleep boundaries and repeat boundaries are separate cases.
* `backend.py` dispatches native callbacks through wx.CallAfter. Configuration,
  user and built-in scripts, video, automatic URLs and mpv keyboard bindings are
  disabled for playback, chapter probing and export. libmpv requires the C
  numeric locale for its lifetime; client creation enforces LC_NUMERIC=C without
  changing text, translation or date locales. Seeks
  pause output until a playback-restart event and a position within 50 ms of the
  requested target have both been observed. Failure stops playback. Millisecond
  storage does not promise sample-accurate decoding for every codec/device.
* Non-unit speed uses Rubber Band R3 (`engine=finer`, pitch scale 1). A float
  volume/limiter chain follows stretching, with a -1 dBFS sample-peak ceiling,
  automatic gain disabled and latency compensation enabled. Rate is 0.5–2.0,
  volume 0–100%, and extra boost 0–12 dB. This is not a certified true-peak limiter,
  nor a guarantee of inaudible processing on arbitrary speech.
* `exporter.py` first renders the ordered book to float32 PCM through libmpv/R3,
  then applies gain/limiting and performs one final FFmpeg encode. Direct mpv
  encoding with the combined stretch/lavfi chain produced incorrect M4B
  timestamps during development, so it is deliberately not used. PCM space is
  included in the disk-space estimate. MP3 and M4B chapters are rescaled to the
  exported rate. Output is decoded and checked before atomic replacement; sources
  cannot be overwritten. WAV/FLAC export does not embed chapters. AAC bitrate is
  a target; MP3 uses the chosen constant bitrate, with MPEG rate restrictions.
* `metadata.py` retains typed fields, nested ID3 frames, multi-value lists,
  binary values and cover art. Unknown ID3 frames are preserved, not interpreted.
  Reading never writes tags or invents an ID3v2 version. ID3v1 byte limits and
  encoding are strict; version conversion is rejected if it alters fields.
  Writes use a staged copy, round-trip field/cover/v1 checks, a hash of the encoded
  audio packets before/after, a verified original backup, a concurrent-change
  check, and atomic replacement. Every book referencing the edited recording is
  refreshed in the database while its positions and bookmarks stay unchanged.
  A tag backup is a full original audio file, not just a metadata fragment.

## Accessibility and integration

Controls are native wx menus, buttons, text fields, lists, trees, choices, spin
controls and a percentage slider. ARIA is not applicable to this desktop UI.
Names and labels are explicitly provided. The app does not announce a changed
value when the corresponding native control or its child has focus. Seeking and
automatic time updates never call the speech announcement service. Ctrl+I is an
explicit announcement; Ctrl+F12 opens a live report that can be frozen for
line-by-line reading. A native error dialog supplies its own accessible message.

Accelerators are scoped to the audiobook window and checked for duplicates when
its menu is built. Standard text editing shortcuts are retained. Global media
keys obey Bookworm's existing setting and route to whichever of audiobook
playback or TTS owns them. Starting one pauses/stops the other.
Printable Ctrl+Alt combinations are avoided because they can consume AltGr
characters on Windows; see [Microsoft's keyboard guidance](https://devblogs.microsoft.com/oldnewthing/20040329-00/?p=40003).

The Hungarian catalog adds 410 translated strings and reuses 11 existing ones.
The original 797 entries and all pre-existing manual sections are retained.
The English and Hungarian guides document the same controls, ranges and limits.
Technical identifiers, user file names and diagnostic output from third-party
engines are not translated as if they were application labels.

## Reproducible tests

On Windows, use the architecture of the Python interpreter for both binaries:

```powershell
python scripts/prepare_audio_engine.py --arch x64
$env:PATH = "$PWD\scripts\dlls\mpv\x64;$env:PATH"
$env:BOOKWORM_TEST_AUDIO = '1'
$env:BOOKWORM_TEST_GUI = '1'
python -m pytest --confcutdir=tests/audiobooks tests/audiobooks -q
```

The dedicated `audiobooks.yml` workflow exercises x64 and x86. Isolated audio
tests avoid importing the document/OCR subsystem. Minimal dependencies are
pytest, numpy, wxPython, mutagen and mpv. Native GUI tests need an interactive
desktop. Without the opt-in variables, native tests are explicitly skipped.
Do not count skipped tests as successful engine or screen-reader tests.
Each suite runs in a separate process with native stderr visible; a native
crash fails the job while preserving the other suites' reports. A child-process
test repeatedly creates/closes the engine with fault reporting enabled and,
on Windows, begins with Hungarian numeric settings.

The implementation session used Linux libmpv 0.40/FFmpeg, Python 3.12 for audio
tests, and real wxGTK 4.2.3/Python 3.13 controls under Xvfb for GUI tests. Real PCM
capture verifies duration, pitch and sample peaks; tests cover WAV/MP3/M4B exact
seeks at multiple rates, rapid successive seeks, real export codecs, chapters,
tag round trips, backups, cancellation and state errors. Native key simulation
checks F5/F6/F8 and that in-file seeking retains the native decoder instance.
GUI fixtures isolate only application settings, paths and announcement capture;
the widgets and audio engine are real. No physical sound card is used in CI.

## Required before a release

1. Obtain passing Windows x64/x86 audio and full Bookworm test/build results.
   The first Windows runs on 2026-11-11 failed: the full suite rejected a missing
   path-validation exception (290 passed, one failed, 54 skipped), while both
   native jobs terminated inside the engine. x64 reported a LuaJIT SEH exception
   and access violation; x86 reported an abort at mpv_create. The follow-up fixes
   portable path validation, disables every built-in script in the pinned
   runtime, and enforces its numeric-locale requirement. A Windows rerun must
   confirm whether these initialization changes resolve both native failures;
   the original captured output does not establish the x86 abort's cause.
   The second run passed the full application tests and 114/115 x64 audio/GUI
   cases. x86 now exposed `OpenSSL internal error: assertion failed: lock != NULL`
   at mpv_create. The follow-up pins i686 to retained build 20260419/06f4ce7,
   before global libcurl initialization was merged on May 16, and adds a native
   build-time decode/R3/limiter smoke test before freezing. This is a targeted
   dependency replacement, not evidence of a passing Windows rerun yet.
   The keyboard path now has an explicit wx accelerator table; its simulated
   key test verifies desktop activation first. DLL discovery is pinned to the
   bundled library even if another mpv-2.dll occurs earlier on PATH. A child
   regression test creates that conflicting library name and checks cleanup.
   The third Windows run verified both native runtimes: 114 of 115 audiobook
   tests passed on both x86 and x64, including exports, tags and exact seeks.
   Only the simulated F5 test failed. The fixture lacked an active event loop:
   on MSW app.Yield creates a temporary loop without activating it, while native
   message dispatch uses EventLoopBase.GetActive. The corrected fixture keeps
   EventLoopActivator alive through setup, the test and teardown. All native
   key simulation and response-time assertions remain enabled.

Full stop is available as a native button, menu item and F9 shortcut. It closes
the decoder, resets and saves book position zero, clears completion, cancels
sleep/A–B state and invalidates late callbacks. F5 subsequently reopens the first
recording at zero; Pause retains the listening position. Tests cover stopping
while loading, after completion, and when the position save fails.
2. Test the packaged installer and portable application on the Windows versions
   the release claims to support, with a normal account and without developer
   tools. Verify the DLL/FFmpeg are present and that opening audio works offline.
3. Listen with NVDA and JAWS: focus order, tree fields, modal error messages,
   slider percentage changes, spin-control editing, no duplicate announcements,
   frozen/live time reports, menu accelerators and TTS/media-key ownership.
   Native Linux widget tests are not Windows MSAA/UIA listening tests.
4. Listen to representative narrated speech at slow/fast rates, with quiet and
   already limited sources. Exercise device loss, device switching, removable
   drives, read-only folders, long Unicode paths and large real books. Subjective
   chorus/transient quality and device latency need this test.
5. Retain and distribute all required third-party license notices and
   corresponding source for the chosen libmpv, Rubber Band, FFmpeg and bundled
   dependencies. The pinned preparation script records origins and verifies
   archive SHA-256 and PE architecture. Those URL records alone are not a complete
   corresponding-source distribution. This change set contains source code and
   build recipes, not a ready-to-distribute native binary package.

The preparation script fails on missing/mismatched archives, and the PyInstaller
spec fails if either native engine is absent. It does not download anything when
the user starts Bookworm. Native dependency availability, distribution size and
release/source-compliance work need maintainer review before merging/releasing
this substantial feature. DRM, DAISY packages, streams and arbitrary proprietary
tag semantics are outside this local-audio implementation.
