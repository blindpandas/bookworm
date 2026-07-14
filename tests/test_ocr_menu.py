from types import SimpleNamespace

import pytest

from bookworm.ocr import ocr_menu


def test_automatic_ocr_displays_current_page_and_keeps_two_pages_prefetched():
    document = object()
    cached_pages = {}
    displayed = []
    prefetched = []

    def show_cached(page_number, set_focus_to_text_ctrl=True):
        assert not set_focus_to_text_ctrl
        displayed.append(cached_pages[page_number])

    menu = SimpleNamespace(
        _automatic_ocr_futures={},
        auto_scan_item=SimpleNamespace(IsChecked=lambda: True),
        service=SimpleNamespace(
            reader=SimpleNamespace(document=document, current_page=4),
            saved_scanned_pages=cached_pages,
        ),
        _show_cached_ocr=show_cached,
        _ensure_automatic_ocr=prefetched.append,
    )

    for page_number in (4, 5, 6):
        result = SimpleNamespace(
            recognized_text=f"page {page_number}",
        )
        task = SimpleNamespace(result=lambda result=result: result)
        key = (document, page_number)
        menu._automatic_ocr_futures[key] = task
        ocr_menu.OCRMenu._process_automatic_ocr_result.__wrapped__(menu, key, task)

    assert cached_pages == {4: "page 4", 5: "page 5", 6: "page 6"}
    assert displayed == ["page 4"]
    assert prefetched == [5, 6]


def test_automatic_ocr_waits_for_the_next_page_before_auto_navigation():
    cached_pages = {4: "current"}
    menu = SimpleNamespace(
        auto_scan_item=SimpleNamespace(IsChecked=lambda: True),
        service=SimpleNamespace(
            reader=SimpleNamespace(document=range(10), current_page=4),
            saved_scanned_pages=cached_pages,
        ),
    )
    view = SimpleNamespace(is_empty=lambda: False)

    assert not ocr_menu.OCRMenu.on_should_auto_navigate_to_next_page(menu, view)

    cached_pages[5] = "next"
    assert ocr_menu.OCRMenu.on_should_auto_navigate_to_next_page(menu, view)

    cached_pages.pop(4)
    view.is_empty = lambda: True
    assert not ocr_menu.OCRMenu.on_should_auto_navigate_to_next_page(menu, view)


def test_canceling_ocr_options_keeps_automatic_ocr_state():
    current_engine = object()
    stored_options = object()
    cached_pages = {1: "recognized"}
    menu = SimpleNamespace(
        service=SimpleNamespace(
            current_ocr_engine=current_engine,
            stored_options=stored_options,
            saved_scanned_pages=cached_pages,
        ),
        _get_ocr_options_from_dlg=lambda **_kwargs: (object(), None),
        _cancel_automatic_ocr=lambda: pytest.fail("automatic OCR was canceled"),
    )

    result = ocr_menu.OCRMenu._get_ocr_options(menu, from_cache=False)

    assert result is None
    assert menu.service.current_ocr_engine is current_engine
    assert menu.service.stored_options is stored_options
    assert menu.service.saved_scanned_pages == {1: "recognized"}
