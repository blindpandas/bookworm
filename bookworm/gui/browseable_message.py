# Portions adapted from NonVisual Desktop Access (NVDA).
# Copyright (C) 2006-2026 NV Access Limited, Peter Vágner, Aleksey Sadovoy, Mesar Hameed,
# Joseph Lee, Thomas Stivers, Babbage B.V., Accessolutions, Julien Cochuyt,
# Leonard de Ruijter, James Teh, Dinesh Kaushal, Davy Kager, André-Abush Clause,
# Michael Curran, and Cyrille Bougot.
# Modified for Bookworm on 2026-07-12 and 2026-07-13.
# This file may be used under the terms of the GNU General Public License, version 2 or later,
# as modified by the NVDA license.
# For full terms and any additional permissions, see:
# https://github.com/nvaccess/nvda/blob/master/copying.txt

import re
from collections.abc import Callable
from copy import deepcopy
from html import escape
from typing import ClassVar

import nh3
import wx
import wx.html2
from platform_utils.clipboard import copy as copy_to_clipboard

from bookworm import speech
from bookworm.paths import resources_path

_MATHML_TAGS = {
    "annotation",
    "math",
    "menclose",
    "merror",
    "mfenced",
    "mfrac",
    "mi",
    "mmultiscripts",
    "mlabeledtr",
    "mn",
    "mo",
    "mover",
    "mpadded",
    "mphantom",
    "mprescripts",
    "mroot",
    "mrow",
    "ms",
    "mspace",
    "msqrt",
    "mstyle",
    "msub",
    "msubsup",
    "msup",
    "mtable",
    "mtd",
    "mtext",
    "mtr",
    "munder",
    "munderover",
    "none",
    "semantics",
}
_TABLE_TAGS = {"caption", "col", "colgroup", "table", "tbody", "td", "tfoot", "th", "thead", "tr"}
# Keep the two styles used by Bookworm tables without exposing IE to arbitrary CSS values.
_SAFE_STYLE_WIDTH = re.compile(
    r"(?:0|\d+(?:\.\d+)?(?:%|px|em|rem))",
    re.ASCII | re.IGNORECASE,
)


def _filter_html_attribute(tag: str, attribute: str, value: str) -> str | None:
    if tag == "img" and attribute == "src":
        # EPUB content must not make background network requests from the message WebView.
        return None
    if attribute != "style":
        return value
    if len(value) > 128:
        return None

    declarations = []
    for raw_declaration in value.split(";"):
        declaration = raw_declaration.strip()
        if not declaration:
            continue
        name, separator, declaration_value = declaration.partition(":")
        if not separator:
            return None
        name = name.strip().lower()
        declaration_value = declaration_value.strip().lower()
        if not (
            (name == "text-align" and declaration_value in {"center", "left", "right"})
            or (name == "width" and _SAFE_STYLE_WIDTH.fullmatch(declaration_value))
        ):
            return None
        declarations.append(f"{name}:{declaration_value}")
    return ";".join(declarations) or None


_HTML_ATTRIBUTES = deepcopy(nh3.ALLOWED_ATTRIBUTES)
_HTML_ATTRIBUTES.setdefault("*", set()).update({"dir", "id", "lang", "role", "title"})
for _tag in _TABLE_TAGS:
    _HTML_ATTRIBUTES.setdefault(_tag, set()).add("style")
_HTML_ATTRIBUTES["table"].update(
    {"bgcolor", "border", "cellpadding", "cellspacing", "height", "width"}
)
for _tag in ("col", "colgroup", "td", "th", "tr"):
    _HTML_ATTRIBUTES.setdefault(_tag, set()).update({"bgcolor", "height", "valign", "width"})
_HTML_ATTRIBUTES["th"].add("abbr")
_HTML_ATTRIBUTES.setdefault("math", set()).update({"display", "xmlns"})
_HTML_ATTRIBUTES.setdefault("annotation", set()).add("encoding")
for _tag in ("mi", "mn", "mo", "mtext"):
    _HTML_ATTRIBUTES.setdefault(_tag, set()).add("mathvariant")
_HTML_ATTRIBUTES.setdefault("mo", set()).update({"form", "stretchy"})
_HTML_ATTRIBUTES.setdefault("mspace", set()).add("width")
_HTML_ATTRIBUTES.setdefault("menclose", set()).add("notation")
_HTML_ATTRIBUTES.setdefault("mfenced", set()).update({"close", "open", "separators"})
_HTML_ATTRIBUTES.setdefault("mfrac", set()).update(
    {"bevelled", "denomalign", "linethickness", "numalign"}
)
_HTML_ATTRIBUTES.setdefault("mstyle", set()).update({"displaystyle", "mathvariant", "scriptlevel"})
_HTML_ATTRIBUTES.setdefault("mtd", set()).update(
    {"columnalign", "columnspan", "rowalign", "rowspan"}
)
_HTML_ATTRIBUTES.setdefault("mover", set()).add("accent")
_HTML_ATTRIBUTES.setdefault("munder", set()).add("accentunder")
_HTML_ATTRIBUTES.setdefault("munderover", set()).update({"accent", "accentunder"})
_HTML_CLEANER = nh3.Cleaner(
    tags=nh3.ALLOWED_TAGS | _MATHML_TAGS | _TABLE_TAGS,
    attributes=_HTML_ATTRIBUTES,
    attribute_filter=_filter_html_attribute,
    generic_attribute_prefixes={"aria-"},
    tag_attribute_values={
        "math": {"xmlns": {"http://www.w3.org/1998/Math/MathML"}},
    },
    filter_style_properties={"text-align", "width"},
)


class HtmlMessageDialog(wx.Dialog):
    """Render a complete HTML document in a modeless WebView dialog."""

    _ACTION_URL_PREFIX = "nvda-action://"
    _DEFAULT_WEBVIEW_SIZE = (350, 300)
    _DIALOG_STYLE = (
        wx.DEFAULT_DIALOG_STYLE
        | wx.RESIZE_BORDER
        | wx.MAXIMIZE_BOX
        | wx.MINIMIZE_BOX
        | wx.DIALOG_NO_PARENT
    )
    _web_view_backend = (
        wx.html2.WebViewBackendIE if wx.Platform == "__WXMSW__" else wx.html2.WebViewBackendDefault
    )
    _instances: ClassVar[set["HtmlMessageDialog"]] = set()

    def __init__(self, parent: wx.Window | None, message: str, title: str):
        self._action_handlers: dict[str, Callable[[], None]] = {}
        self._button_sizer: wx.BoxSizer | None = None
        super().__init__(parent, title=title, style=self._DIALOG_STYLE)

        self._message_control = wx.html2.WebView.New(self, backend=self._web_view_backend)
        self._message_control.SetInitialSize(self.FromDIP(wx.Size(*self._DEFAULT_WEBVIEW_SIZE)))
        self._message_control.EnableContextMenu(False)
        self._message_control.EnableHistory(False)
        self._message_control.Bind(wx.html2.EVT_WEBVIEW_NAVIGATING, self._on_navigating)

        self._main_sizer = wx.BoxSizer(wx.VERTICAL)
        self._main_sizer.Add(
            self._message_control,
            proportion=1,
            border=self.FromDIP(10),
            flag=wx.ALL | wx.EXPAND,
        )
        self.SetSizer(self._main_sizer)
        self.set_message(message)
        self.Fit()
        self.CenterOnScreen()

        escape_id = wx.NewIdRef()
        self.Bind(wx.EVT_MENU, lambda _event: self.Close(), id=escape_id)
        self.SetAcceleratorTable(
            wx.AcceleratorTable([wx.AcceleratorEntry(wx.ACCEL_NORMAL, wx.WXK_ESCAPE, escape_id)])
        )
        self.EnableCloseButton(True)
        self.Bind(wx.EVT_SHOW, self._on_show)
        self.Bind(wx.EVT_CLOSE, self._on_close)
        self.Bind(wx.EVT_WINDOW_DESTROY, self._on_destroy, self)
        self._instances.add(self)

    def register_action(self, action: str, handler: Callable[[], None]) -> "HtmlMessageDialog":
        """Register a handler for an ``nvda-action://<action>`` URL."""
        self._action_handlers[action] = handler
        return self

    def add_button(
        self,
        button_id: int,
        label: str,
        callback: Callable[[wx.CommandEvent], None] | None = None,
        *,
        closes_dialog: bool = True,
    ) -> "HtmlMessageDialog":
        button = wx.Button(self, button_id, label)

        def on_button(event: wx.CommandEvent) -> None:
            if callback is not None:
                callback(event)
            if closes_dialog:
                self.Close()

        button.Bind(wx.EVT_BUTTON, on_button)
        if self._button_sizer is None:
            self._button_sizer = wx.BoxSizer(wx.HORIZONTAL)
            self._main_sizer.Add(
                self._button_sizer,
                border=self.FromDIP(10),
                flag=wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.ALIGN_RIGHT,
            )
        self._button_sizer.Add(button, border=self.FromDIP(5), flag=wx.LEFT)
        self.Layout()
        self.Fit()
        return self

    def set_message(self, message: str) -> "HtmlMessageDialog":
        self._message_control.SetPage(message, "")
        return self

    def _on_navigating(self, event: wx.html2.WebViewEvent) -> None:
        url = event.GetURL()
        lower_url = url.lower()
        if lower_url.startswith("data:text/html"):
            # Edge fires this URL for SetPage; allow it so content loads.
            return
        event.Veto()
        if lower_url.startswith(self._ACTION_URL_PREFIX):
            action = url[len(self._ACTION_URL_PREFIX) :]
            if action == "close":
                self.Close()
            elif handler := self._action_handlers.get(action):
                handler()
        elif lower_url.startswith(("http://", "https://")):
            wx.LaunchDefaultBrowser(url)

    def _on_show(self, event: wx.ShowEvent) -> None:
        if event.IsShown():
            self.Raise()
            self._message_control.SetFocus()
        event.Skip()

    def _on_close(self, _event: wx.CloseEvent) -> None:
        self.Hide()
        self.Destroy()

    def _on_destroy(self, event: wx.WindowDestroyEvent) -> None:
        self._instances.discard(self)
        event.Skip()

    @classmethod
    def close_all(cls) -> None:
        for dialog in tuple(cls._instances):
            dialog.Close()


def _copy_browseable_message_to_clipboard(text: str) -> None:
    copy_to_clipboard(text)
    # Translators: Reported when the content of a browseable message is copied to the clipboard.
    speech.announce(_("Copied to clipboard"))


def browseable_message(
    message: str,
    title: str | None = None,
    is_html: bool = False,
    close_button: bool = False,
    copy_button: bool = False,
    sanitize_html_func: Callable[[str], str] = _HTML_CLEANER.clean,
) -> None:
    """Present a message in an HTML document that a screen reader can browse.

    ``sanitize_html_func`` must sanitize any HTML that may contain translated or
    user-provided content.
    """
    if title is None:
        # Translators: The title for the dialog used to present general messages in browse mode.
        title = _("Message")

    if not is_html:
        message_sanitized = f"<pre>{escape(message)}</pre>"
    else:
        message_sanitized = sanitize_html_func(message)

    template = resources_path("message.html").read_text(encoding="utf-8")
    templated_message = template.replace("{{TITLE}}", escape(title)).replace(
        "{{MESSAGE}}", message_sanitized
    )
    dialog = HtmlMessageDialog(None, templated_message, title)

    if copy_button:
        dialog.add_button(
            wx.ID_COPY,
            # Translators: The label of a button to copy the text of the window to the clipboard.
            _("&Copy"),
            callback=lambda _event: _copy_browseable_message_to_clipboard(
                dialog._message_control.GetPageText()
            ),
            closes_dialog=False,
        )
        dialog.register_action(
            "copy",
            lambda: _copy_browseable_message_to_clipboard(dialog._message_control.GetPageText()),
        )
    if close_button:
        dialog.add_button(
            wx.ID_CLOSE,
            # Translators: The label of a button that closes the browseable message window.
            _("&Close"),
        )

    dialog.Show()


def close_browseable_messages() -> None:
    """Close all modeless browseable messages before the application exits."""
    HtmlMessageDialog.close_all()
