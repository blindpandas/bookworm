# coding: utf-8

from bookworm.platforms import PLATFORM

if PLATFORM == "win32":
    from bookworm.platforms.win32.controls.richedit import ContentViewCtrl
else:
    from bookworm.gui.text_ctrl_mixin import \
        ContentViewCtrlMixin as ContentViewCtrl
