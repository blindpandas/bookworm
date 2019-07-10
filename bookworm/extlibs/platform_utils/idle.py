import platform

system = platform.system()


def get_user_idle_time():
    if system == "Windows":
        return get_user_idle_time_windows()
    raise NotImplementedError("This function is not yet implemented for %s" % system)


def get_user_idle_time_windows():
    from ctypes import Structure, windll, c_uint, sizeof, byref

    class LASTINPUTINFO(Structure):
        _fields_ = [("cbSize", c_uint), ("dwTime", c_uint)]

    lastInputInfo = LASTINPUTINFO()
    lastInputInfo.cbSize = sizeof(lastInputInfo)
    windll.user32.GetLastInputInfo(byref(lastInputInfo))
    millis = windll.kernel32.GetTickCount() - lastInputInfo.dwTime
    return millis / 1000.0
