import platform


def set_text_windows(text):
    import win32clipboard
    import win32con

    win32clipboard.OpenClipboard()
    try:
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardText(text, win32con.CF_UNICODETEXT)
    finally:
        win32clipboard.CloseClipboard()


def set_text_gtk(text):
    import gtk

    cb = gtk.Clipboard()
    cb.set_text(text)
    cb.store()


def set_text_osx(text):
    import Carbon.Scrap

    Carbon.Scrap.ClearCurrentScrap()
    scrap = Carbon.Scrap.GetCurrentScrap()
    scrap.PutScrapFlavor("TEXT", 0, text)


def set_text(text):
    """Copies text to the clipboard."""
    plat = platform.system()
    if plat == "Windows":
        set_text_windows(text)
    elif plat == "Linux":
        set_text_gtk(text)
    elif plat == "Darwin":
        set_text_osx(text)
    else:
        raise NotImplementedError("Cannot set clipboard text on platform %s" % plat)


copy = set_text


def get_text_windows():
    import win32clipboard
    import win32con

    win32clipboard.OpenClipboard()
    try:
        text = win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT)
    finally:
        win32clipboard.CloseClipboard()
    return text


def get_text():
    plat = platform.system()
    if plat == "Windows":
        return get_text_windows()
    else:
        raise NotImplementedError(
            "Cannot get text from clipboard on platform %s" % plat
        )
