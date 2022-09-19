# coding: utf-8


if __name__ == "__main__":
    import multiprocessing

    multiprocessing.freeze_support()
    from bookworm import bookworm

    bookworm.main()
