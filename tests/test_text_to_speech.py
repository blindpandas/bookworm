from collections import deque
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from bookworm import text_to_speech as tts
from bookworm.document import Pager, Section
from bookworm.speechdriver.element.enums import SpeechElementKind
from bookworm.speechdriver.utterance import SpeechUtterance
from bookworm.structured_text import TextInfo, TextRange
from bookworm.text_to_speech.tts_config import TTSConfigManager


def current_bookmark(service, **data):
    return {**data, "s": service._speech_session}


def test_page_end_continues_reading_once_after_navigation(monkeypatch):
    service = object.__new__(tts.TextToSpeechService)
    service._speech_session = 1
    service._pause_on_speech_start = False
    service._highlighted_ranges = set()
    service.view = Mock()
    service.reader = Mock()
    service.speak_page = Mock()
    service._requested_play = True
    service.engine = SimpleNamespace(state=tts.SynthState.busy, stop=Mock())
    service.reader.go_to_next.side_effect = lambda: (
        service._change_page_for_tts(service.reader, current=None, prev=None) or True
    )
    monkeypatch.setattr(
        tts.config,
        "conf",
        {"reading": {"reading_mode": 0, "speak_page_number": False}},
    )
    monkeypatch.setattr(
        tts.should_auto_navigate_to_next_page,
        "send",
        lambda _sender: [(None, True)],
    )

    tts.TextToSpeechService.process_bookmark.__wrapped__(
        service,
        current_bookmark(service, t=tts.UT_PAGE_END, isl=False),
    )

    service.reader.go_to_next.assert_called_once_with()
    service.speak_page.assert_called_once_with(init_state=False)
    assert service._requested_play


def test_page_end_clears_continuous_reading_when_navigation_stops(monkeypatch):
    service = object.__new__(tts.TextToSpeechService)
    service._speech_session = 1
    service._requested_play = True
    service.view = object()
    service.reader = Mock()
    service.reader.go_to_next.return_value = False
    monkeypatch.setattr(tts.config, "conf", {"reading": {"reading_mode": 0}})
    monkeypatch.setattr(
        tts.should_auto_navigate_to_next_page,
        "send",
        lambda _sender: [(None, True)],
    )

    tts.TextToSpeechService.process_bookmark.__wrapped__(
        service,
        current_bookmark(service, t=tts.UT_PAGE_END, isl=False),
    )

    assert not service._requested_play


def test_bookmark_from_stopped_session_is_ignored(monkeypatch):
    callbacks = []
    service = object.__new__(tts.TextToSpeechService)
    service._speech_session = 1
    service._highlighted_ranges = set()
    service.view = Mock()
    service.engine = Mock()
    monkeypatch.setattr(
        tts.wx,
        "CallAfter",
        lambda func, *args, **kwargs: callbacks.append((func, args, kwargs)),
    )
    bookmark = service.encode_bookmark({"t": tts.UT_PARAGRAPH_BEGIN, "txr": (3, 7)})

    service.stop_speech()
    service.on_bookmark_reached(None, bookmark)
    for func, args, kwargs in callbacks:
        func(*args, **kwargs)

    service.view.set_insertion_point.assert_not_called()


@pytest.mark.parametrize(("enabled", "clear_calls"), [(False, 0), (True, 1)])
def test_only_applied_speech_highlights_are_cleared(monkeypatch, enabled, clear_calls):
    service = object.__new__(tts.TextToSpeechService)
    service._speech_session = 1
    service._highlighted_ranges = set()
    service.view = Mock()
    monkeypatch.setattr(
        tts.config,
        "conf",
        {"reading": {"highlight_spoken_text": enabled, "select_spoken_text": False}},
    )

    tts.TextToSpeechService.process_bookmark.__wrapped__(
        service,
        current_bookmark(service, t=tts.UT_PARAGRAPH_BEGIN, txr=(3, 7)),
    )
    tts.TextToSpeechService.process_bookmark.__wrapped__(
        service,
        current_bookmark(service, t=tts.UT_PARAGRAPH_END, txr=(3, 7)),
    )
    service.clear_highlighted_ranges()

    service.view.set_insertion_point.assert_called_once_with(3)
    assert service.view.clear_highlight.call_count == clear_calls
    assert not service._highlighted_ranges


def test_document_end_is_announced_only_on_the_last_page():
    service = object.__new__(tts.TextToSpeechService)
    service._speech_session = 1
    root = Section(title="Document", pager=Pager(first=0, last=1))

    class Document:
        def __len__(self):
            return 2

        def is_single_page_document(self):
            return False

    service.reader = SimpleNamespace(document=Document())
    service.config_manager = {"end_of_page_pause": 1, "end_of_section_pause": 1}

    utterances = []
    for index in range(2):
        utterance = SpeechUtterance()
        page = SimpleNamespace(
            index=index,
            section=root,
            is_last_of_section=index == 1,
        )
        service.configure_end_page_utterance(utterance, page)
        utterances.append(utterance)

    end_messages = [
        [element.content for element in utterance if element.kind is SpeechElementKind.text]
        for utterance in utterances
    ]
    assert [len(messages) for messages in end_messages] == [0, 1]


def test_single_page_section_boundary_stops_current_section_reading(monkeypatch):
    root = Section(title="Document", pager=Pager(0, 0))
    first = Section(title="First", pager=Pager(0, 0), text_range=TextRange(0, 6))
    second = Section(title="Second", pager=Pager(0, 0), text_range=TextRange(6, 13))
    root.append(first)
    root.append(second)

    class Document:
        @staticmethod
        def is_single_page_document():
            return True

        @staticmethod
        def get_section_at_position(position):
            return first if position < 6 else second

    service = object.__new__(tts.TextToSpeechService)
    service._speech_session = 1
    service.utterance_queue = deque()
    service.reader = SimpleNamespace(document=Document())
    service.config_manager = {
        "sentence_pause": 0,
        "paragraph_pause": 0,
        "end_of_section_pause": 0,
    }
    service.stop_speech = Mock()
    monkeypatch.setattr(
        tts.config,
        "conf",
        {"reading": {"notify_on_section_end": False, "reading_mode": 1}},
    )

    service.add_text_utterances(TextInfo("First\nSecond\n"))
    bookmarks = [
        service.decode_bookmark(element.content)
        for utterance in service.utterance_queue
        for element in utterance
        if element.kind is SpeechElementKind.bookmark
    ]
    section_end = next(
        bookmark for bookmark in bookmarks if bookmark["t"] == tts.UT_SECTION_END
    )
    tts.TextToSpeechService.process_bookmark.__wrapped__(service, section_end)

    service.stop_speech.assert_called_once_with(user_requested=True)


@pytest.mark.parametrize(
    ("forward", "start_page", "state", "expected_position", "pause_on_start"),
    [
        (True, 0, tts.SynthState.busy, 0, False),
        (False, 1, tts.SynthState.paused, len("Previous first\n"), True),
    ],
)
def test_paragraph_seek_crosses_page_boundaries(
    forward, start_page, state, expected_position, pause_on_start
):
    pages = ["Previous first\nPrevious last", "Next first\nNext last"]

    class Document:
        def __contains__(self, page):
            return 0 <= page < len(pages)

    class Reader:
        document = Document()

        def __init__(self):
            self.current_page = start_page
            self.service = None

        def go_to_next(self):
            self.current_page += 1
            self.service._change_page_for_tts(self, current=None, prev=None)
            return True

        def go_to_prev(self):
            self.current_page -= 1
            self.service._change_page_for_tts(self, current=None, prev=None)
            return True

    reader = Reader()
    view = Mock()
    view.get_text_by_range.side_effect = lambda _start, _stop: pages[reader.current_page]
    view.get_insertion_point.return_value = 0 if not forward else len("Previous first\n")
    service = object.__new__(tts.TextToSpeechService)
    engine = SimpleNamespace(state=state)
    service.engine = engine
    service.reader = reader
    service.view = view
    service.text_info = TextInfo(f"{pages[start_page]}\n")
    service._whole_page_text_info = None
    service._highlighted_ranges = set()
    service._requested_play = True

    def stop_speech():
        engine.state = tts.SynthState.ready
        service.initialize_state()

    service.stop_speech = Mock(side_effect=stop_speech)
    service.speak_page = Mock()
    reader.service = service

    service._seek_paragraph(forward=forward)

    view.set_insertion_point.assert_called_once_with(expected_position)
    service.stop_speech.assert_called_once_with()
    service.speak_page.assert_called_once_with(
        start_pos=expected_position,
        init_state=False,
    )
    assert service._pause_on_speech_start is pause_on_start


def test_pending_pause_is_applied_when_async_speech_starts(monkeypatch):
    service = object.__new__(tts.TextToSpeechService)
    service._pause_on_speech_start = True
    service.engine = Mock()
    service.view = object()
    service.on_engine_state_changed = Mock()
    monkeypatch.setattr(tts.speech_engine_state_changed, "send", Mock())

    service.on_state_changed(None, tts.SynthState.busy)

    service.engine.pause.assert_called_once_with()
    assert not service._pause_on_speech_start


def test_pending_async_speech_can_be_paused_resumed_and_stopped(monkeypatch):
    service = object.__new__(tts.TextToSpeechService)
    service.engine = SimpleNamespace(state=tts.SynthState.ready)
    service._requested_play = True
    service._pause_on_speech_start = False
    service.speak_page = Mock()
    service.stop_speech = Mock()
    monkeypatch.setattr(tts.speech, "announce", Mock())

    service.pause_or_resume()
    assert service._pause_on_speech_start
    service.play_or_resume()
    assert not service._pause_on_speech_start
    service.stop_playback()

    service.speak_page.assert_not_called()
    service.stop_speech.assert_called_once_with(user_requested=True)


def test_restart_uses_requested_position_while_async_speech_is_pending():
    service = object.__new__(tts.TextToSpeechService)
    service.engine = SimpleNamespace(state=tts.SynthState.ready)
    service._requested_play = True
    service._pause_on_speech_start = True

    def stop_speech():
        service._pause_on_speech_start = False

    service.stop_speech = Mock(side_effect=stop_speech)
    service.speak_page = Mock()

    service.on_restart_speech(None, start_speech_from=42)

    service.stop_speech.assert_called_once_with()
    service.speak_page.assert_called_once_with(start_pos=42, init_state=False)
    assert service._pause_on_speech_start


@pytest.mark.parametrize(
    ("state", "requested_play", "pause_pending", "configured", "expected_calls"),
    [
        (tts.SynthState.ready, False, False, True, ["configure", "language"]),
        (tts.SynthState.paused, True, False, True, ["configure", "language", "speak"]),
        (tts.SynthState.ready, True, True, True, ["configure", "language", "speak"]),
        (tts.SynthState.paused, True, False, False, ["configure", "close"]),
    ],
)
def test_engine_reconfiguration_selects_language_before_resuming(
    state, requested_play, pause_pending, configured, expected_calls
):
    calls = []
    service = object.__new__(tts.TextToSpeechService)
    service.engine = SimpleNamespace(name="onecore", state=state)
    service.config_manager = {"engine": "onecore"}
    service.reader = SimpleNamespace(ready=True)
    service._requested_play = requested_play
    service._pause_on_speech_start = pause_pending
    service.configure_engine = lambda: calls.append("configure") or configured
    service.close = lambda: calls.append("close")
    service._try_set_tts_language = lambda: calls.append("language")
    service.speak_page = lambda **_kwargs: calls.append("speak")

    service.initialize_engine()

    assert calls == expected_calls
    assert service._requested_play is (
        configured and (state is not tts.SynthState.ready or requested_play)
    )
    assert service._pause_on_speech_start is (
        configured and (state is tts.SynthState.paused or pause_pending)
    )


def test_active_voice_profile_updates_its_speech_settings():
    manager = object.__new__(TTSConfigManager)
    manager.active_profile = {"speech": {"engine": "onecore"}}

    manager["engine"] = "sapi5"

    assert manager["engine"] == "sapi5"
    assert "engine" not in manager.active_profile
