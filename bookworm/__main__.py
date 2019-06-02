from .bookworm import BookwormApp


def main():
    app = BookwormApp(redirect=True)
    app.MainLoop()


if __name__ == "__main__":
    main()
