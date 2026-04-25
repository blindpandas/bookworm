import wx
from wx.html2 import WebView, EVT_WEBVIEW_LOADED

class HTMLDialog(wx.Dialog):
    def __init__(self, parent: wx.Window, title: str, text: str):
        super().__init__(parent, title=title, id=wx.ID_ANY)
        self.webview: WebView = WebView.New(self)
        self.webview.Bind(EVT_WEBVIEW_LOADED, self.OnLoaded)
        self.webview.SetPage(text, "")

    def OnLoaded(self, e):
        log.debug(len(self.webview.GetChildren()))
        robot = wx.UIActionSimulator() 
        self.webview.SetFocus() 
        position = self.webview.GetPosition() 
        position = self.webview.ClientToScreen(position) 
        robot.MouseMove(position) 
        robot.MouseClick() 

def browseable_message(message: str, title: str | None = None, is_html: bool = False) -> None:
    with HTMLDialog(wx.GetApp().mainFrame, title, message) as dlg:
        dlg.ShowModal()
