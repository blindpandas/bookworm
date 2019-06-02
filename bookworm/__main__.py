from .gui import BookReaderApp
from .config import setup_config


def main():
    setup_config()
    app = BookReaderApp(redirect=True)
    app.MainLoop()


if __name__ == "__main__":
    main()
