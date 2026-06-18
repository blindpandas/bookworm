# Bookworm

**Bookworm** is an accessible document reader that enables blind and visually impaired individuals to read documents in an easy and hassle free manner. The main highlights of bookworm are:

* Supports over 20 document formats, including EPUB, PDF, MOBI, Microsoft Word documents, HTML, plain text, and Markdown.
* Support for named **bookmarks**, comments, and highlights. You can quickly jump between annotations and export comments or highlights to plain text, HTML, or Markdown.
* Structured navigation with single-letter commands for headings, links, lists, tables, quotes, and figures, plus an element list for browsing supported semantic content.
* Two different styles of viewing pages: plain text and fully rendered, zoomable images for formats that support graphical rendering.
* Full text search with customizable search options, including regular expressions and page or section ranges.
* Book navigation via table of contents is extensively supported for document formats that provide one.
* Bookworm Bookshelf for organizing local documents, importing files or folders, searching titles and indexed content, and bundling documents for offline use.
* Web services for opening URLs in Bookworm, extracting readable article text, and looking up terms in Wikipedia.
* Optical Character Recognition (OCR) for scanned documents and images, with support for Windows OCR, Tesseract, VIVO, and Baidu OCR engines where available.
* Support for reading books aloud using text-to-speech, with configurable voice parameters and voice profiles.
* Support for standard zoom-in, zoom-out, and reset commands in the textual view and rendered page view.
* Support for exporting any document format to a plain text file.

## **IMPORTANT**
Bookworm's official website is currently no more. The domain which has worked up until now has currently not been renewed, and as such bookworm will no longer be provided there until further notice. We urge you not to interact with that domain, as we're no longer in charge of it.
You can keep downloading bookworm from the [releases page](https://github.com/blindpandas/bookworm/releases) for the most recent ones.

## Development

If you would like to contribute to the development of *Bookworm*, follow these steps to run Bookworm on your computer.

### Prerequisites

1.  **Git**: Ensure you have Git installed.
2.  **uv**: This project uses [uv](https://github.com/astral-sh/uv) for dependency management and running tasks. Install it by following the instructions on their website.
3.  **NSIS** (Optional): Only required if you intend to build the Windows installer. Get it from [NSIS download page](https://nsis.sourceforge.io/Download) and add it to your path.

Note: You do **not** need to manually install Python. `uv` will manage the required Python version (3.11) for you.

### Setup and Run

1.  **Clone the repository:**
    ```shell
    git clone https://github.com/blindpandas/bookworm.git
    cd bookworm
    ```

2.  **Initialize the development environment:**
    This command will sync dependencies, set up the virtual environment, and generate necessary resources (icons, guides, etc.).
    ```shell
    uv run invoke dev
    ```

3.  **Run Bookworm:**
    ```shell
    uv run invoke run
    ```
    To run without debug mode:
    ```shell
    uv run invoke run --no-debug
    ```

### Other Commands

*   **List all tasks:**
    ```shell
    uv run invoke --list
    ```

*   **Format and Lint Code:**
    ```shell
    uv run invoke format-code
    ```

*   **Run Tests:**
    ```shell
    uv run --no-sync pytest
    ```

*   **Build Installer:**
    ```shell
    uv run invoke build
    ```

If you've found a bug, or you want to contribute your changes back to bookworm, please create an issue or submit a pull request. We welcome any contribution.

## License

**Bookworm** is copyright (c) 2026 Blind Pandas and Bookworm contributors. It is licensed under the [GNU General Public License version 2 or later](https://github.com/blindpandas/bookworm/blob/master/LICENSE).
