# coding: utf-8


import os
import sys

sys.stdout = open(os.devnull, "w+")
sys.stderr = open(os.devnull, "w+")

import multiprocessing

multiprocessing.freeze_support()


if __name__ == "__main__":
    from bookworm import bookworm

    bookworm.main()
