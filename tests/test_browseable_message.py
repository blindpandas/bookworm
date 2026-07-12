from types import SimpleNamespace

import wx

from bookworm.gui import browseable_message as browseable_message_module


class FakeWebViewEvent:
    def __init__(self, url: str):
        self.url = url
        self.vetoed = False

    def GetURL(self) -> str:  # noqa: N802 - Mirrors wx.WebViewEvent.
        return self.url

    def Veto(self) -> None:  # noqa: N802 - Mirrors wx.WebViewEvent.
        self.vetoed = True


def test_browseable_message_copy_uses_visible_page_text(monkeypatch):
    dialogs = []
    copied = []

    class FakeMessageControl:
        def GetPageText(self):  # noqa: N802 - Mirrors wx.WebView.
            return "Visible table text"

    class FakeDialog:
        def __init__(self, _parent, _message, _title):
            self._message_control = FakeMessageControl()
            self.copy_button = None
            self.actions = {}
            dialogs.append(self)

        def add_button(self, _button_id, _label, callback=None, *, closes_dialog=True):
            self.copy_button = (callback, closes_dialog)

        def register_action(self, action, handler):
            self.actions[action] = handler

        def Show(self):  # noqa: N802 - Mirrors wx.Dialog.
            pass

    monkeypatch.setattr(browseable_message_module, "HtmlMessageDialog", FakeDialog)
    monkeypatch.setattr(
        browseable_message_module,
        "_copy_browseable_message_to_clipboard",
        copied.append,
    )

    browseable_message_module.browseable_message(
        "<p>Message</p>",
        is_html=True,
        copy_button=True,
    )

    dialog = dialogs[0]
    copy_callback, closes_dialog = dialog.copy_button
    assert closes_dialog is False

    copy_callback(None)
    dialog.actions["copy"]()
    assert copied == ["Visible table text", "Visible table text"]


def test_html_sanitizer_preserves_table_mathml_and_removes_active_content():
    cleaned = browseable_message_module._HTML_CLEANER.clean(
        """
        <table style="width: 100%; text-align: center"
               border="1" cellspacing="2" onclick="alert(1)">
          <tr><td aria-label="Formula">
            <math xmlns="http://www.w3.org/1998/Math/MathML" display="inline"
                  aria-label="x squared">
              <semantics><mfrac><mi mathvariant="italic">x</mi><mn>2</mn></mfrac>
                <annotation encoding="application/x-tex">x/2</annotation>
              </semantics>
            </math>
            <script>alert(2)</script>
            <img src="https://example.com/beacon.png" alt="Cover">
          </td><td style="width: expression(alert(3))">unsafe width</td>
          </tr>
        </table>
        """
    )

    assert '<table style="width:100%;text-align:center" border="1" cellspacing="2">' in cleaned
    assert '<td aria-label="Formula">' in cleaned
    assert '<math xmlns="http://www.w3.org/1998/Math/MathML"' in cleaned
    assert '<mfrac><mi mathvariant="italic">x</mi><mn>2</mn></mfrac>' in cleaned
    assert '<annotation encoding="application/x-tex">x/2</annotation>' in cleaned
    assert '<img alt="Cover">' in cleaned
    assert not any(
        unsafe in cleaned
        for unsafe in ("https://example.com/beacon.png", "expression", "onclick", "alert(2)")
    )


def test_browseable_message_escapes_plain_text(monkeypatch):
    dialogs = []

    class FakeDialog:
        def __init__(self, _parent, message, title):
            dialogs.append(SimpleNamespace(message=message, title=title))

        def Show(self):  # noqa: N802 - Mirrors wx.Dialog.
            pass

    monkeypatch.setattr(browseable_message_module, "HtmlMessageDialog", FakeDialog)

    browseable_message_module.browseable_message("first\n<b>second</b>", title="Text")

    assert "<pre>first\n&lt;b&gt;second&lt;/b&gt;</pre>" in dialogs[0].message


def test_html_message_dialog_lays_out_native_buttons_below_webview():
    app = wx.GetApp() or wx.App(False)
    dialog = browseable_message_module.HtmlMessageDialog(
        None,
        "<html><body>Message</body></html>",
        "Layout test",
    )
    try:
        dialog.add_button(wx.ID_COPY, "&Copy", closes_dialog=False)
        webview_rect = dialog._message_control.GetRect()
        button_rect = dialog.FindWindowById(wx.ID_COPY).GetRect()

        assert button_rect.y >= webview_rect.y + webview_rect.height
    finally:
        dialog.Destroy()
        app.ProcessPendingEvents()


def test_html_message_dialog_routes_actions_and_external_links(monkeypatch):
    closed = []
    copied = []
    opened = []
    dialog = SimpleNamespace(
        _ACTION_URL_PREFIX="nvda-action://",
        _action_handlers={"copy": lambda: copied.append(True)},
        Close=lambda: closed.append(True),
    )
    monkeypatch.setattr(wx, "LaunchDefaultBrowser", opened.append)

    copy_event = FakeWebViewEvent("nvda-action://copy/")
    browseable_message_module.HtmlMessageDialog._on_navigating(dialog, copy_event)
    close_event = FakeWebViewEvent("nvda-action://close/")
    browseable_message_module.HtmlMessageDialog._on_navigating(dialog, close_event)
    link_event = FakeWebViewEvent("https://example.com/path")
    browseable_message_module.HtmlMessageDialog._on_navigating(dialog, link_event)
    data_event = FakeWebViewEvent("data:text/html;charset=utf-8,content")
    browseable_message_module.HtmlMessageDialog._on_navigating(dialog, data_event)

    assert copied == [True]
    assert closed == [True]
    assert opened == ["https://example.com/path"]
    assert copy_event.vetoed
    assert close_event.vetoed
    assert link_event.vetoed
    assert data_event.vetoed is False
