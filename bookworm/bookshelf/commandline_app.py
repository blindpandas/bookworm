# coding: utf-8

import argparse
from bookworm.library.tasks import add_document_to_library


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("uri", help="Document URI to open")
    parser.add_argument("--category", help="Category of the given document", type=str)
    parser.add_argument("--tags", help="Tags of the given document", type=str)
    args = parser.parse_args()
    print(
        f"Opening document: {args.uri}\n"
        f"Document category: {args.category}\n"
        f"Document tags: {args.tags}"
    )

if __name__ == '__main__':
    main()
