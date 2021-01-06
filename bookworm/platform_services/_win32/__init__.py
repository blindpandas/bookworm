# coding: utf-8

from .user import *

def check_runtime_components():
    """
    Make sure that critical runtime components are OK.
    Raise EnvironmentError.
    """
    # TODO: Make sure that .NET Framework 4.0 or higher
    # is available in the target system.
    try:
        # This is a basic sanity check
        import clr
        import System
    except:
        raise EnvironmentError
