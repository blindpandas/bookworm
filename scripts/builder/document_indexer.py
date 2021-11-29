# coding: utf-8



if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    from bookworm.library import commandline_app
    commandline_app.main()
