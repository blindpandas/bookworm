# coding: utf-8


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
        raise EnvironmentError(
            "Bookworm is unable to start because some key components are missing from your system.\n"
            "Bookworm requires that the .NET Framework v4.0 or a later version is present in the target system.\n"
            "Head over to the following link to download and install the .NET Framework v4.0:\n"
            "https://www.microsoft.com/en-us/download/details.aspx?id=17718",
        )
