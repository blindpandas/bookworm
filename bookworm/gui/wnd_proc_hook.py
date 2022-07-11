import win32gui
import win32con
import win32api


class WndProcHookMixin:
    """
    This class can be mixed in with any wxWindows window class in order to hook it's WndProc function.
    You supply a set of message handler functions with the function addMsgHandler. When the window receives that
    message, the specified handler function is invoked. If the handler explicitly returns False then the standard
    WindowProc will not be invoked with the message. You can really screw things up this way, so be careful.
    This is not the correct way to deal with standard windows messages in wxPython (i.e. button click, paint, etc)
    use the standard wxWindows method of binding events for that. This is really for capturing custom windows messages
    or windows messages that are outside of the wxWindows world.
    """

    def __init__(self):
        self.msgDict = {}

    def hookWndProc(self):
        self.oldWndProc = win32gui.SetWindowLong(
            self.GetHandle(), win32con.GWL_WNDPROC, self.localWndProc
        )

    def unhookWndProc(self):
        # Notice the use of wxin32api instead of win32gui here.  This is to avoid an error due to not passing a
        # callable object.
        win32api.SetWindowLong(self.GetHandle(), win32con.GWL_WNDPROC, self.oldWndProc)

    def addMsgHandler(self, messageNumber, messageName, handler):
        self.msgDict[messageNumber] = (messageName, handler)

    def localWndProc(self, hWnd, msg, wParam, lParam):
        # call the handler if one exists
        if msg in self.msgDict:
            # if the handler returns false, we terminate the message here
            if self.msgDict[msg][1](wParam, lParam) == False:
                return

        # Restore the old WndProc on Destroy.
        if msg == win32con.WM_DESTROY and self:
            self.unhookWndProc()

        # Pass all messages (in this case, yours may be different) on
        # to the original WndProc
        return win32gui.CallWindowProc(self.oldWndProc, hWnd, msg, wParam, lParam)
