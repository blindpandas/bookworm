# Bookworm

**Bookworm** is an accessible document reader that enables blind and visually impaired individuals to read documents in an easy and hassle free manor. The main highlights of bookworm are:

* Supports over 20 document formats
* Support for named **bookmarks**. This enables you to mark interesting positions in the text for later reference
* Support for adding comments to capture an interesting thought or create a summary of the content at a particular position in the text. Bookworm allows you to quickly jump to a specific comment and view it. Later, you can export these comments to a text file or HTML document for later use.
* Two different styles of viewing pages; plain-text and fully rendered, zoomable, images.
* Full text search with customizable search options
* Book navigation via Table of content is extensively supported for all document formats
* Support for reading books aloud using Text-to-speech, with configurable voice parameters.
* The ability to customize  text-to-speech with voice profiles. Each voice profile configures the style of the speech, and you can freely activate/deactivate a voice profile anytime.
* Support for standard zoom-in/zoom-out/reset commands. This is supported in the textual view and the rendered page view.
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

*   **Build Installer:**
    ```shell
    uv run invoke build
    ```

If you've found a bug, or you want to contribute your changes back to bookworm, please create an issue or submit a pull request. We welcome any contribution.

## License

**Bookworm** is copyright (c) 2019-2025 Blind Pandas Team. It is licensed under the [GNU General Public License](https://github.com/blindpandas/bookworm/blob/master/LICENSE).
