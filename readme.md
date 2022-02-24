![Appveyor Build Status](https://ci.appveyor.com/api/projects/status/github/blindpandas/bookworm?branch=develop&svg=true)

# Bookworm

**Bookworm** is an accessible document reader that enables blind and visually impaired individuals to read documents in an easy and hassle free manor. The main highlights of bookworm are:

* Supports over 15 document formats
* Support for named **bookmarks**. This enables you to mark interesting positions in the text for later reference
* Support for taking notes, this helps you to capture an interesting thought or create a summary of the content at a specific position of the text. Bookworm allows you to quickly jump to a specific note and view it. Later on, you can export these notes to a text file or an HTML document for future reference.
* Two different styles of viewing pages; plain-text and fully rendered, zoomable, images.
* Full text search with customizable search options
* Book navigation via Table of content is extensively supported for all document formats
* Support for reading books aloud using Text-to-speech, with configurable voice parameters.
* The ability to customize  text-to-speech with voice profiles. Each voice profile configures the style of the speech, and you can freely activate/deactivate a voice profile anytime.
* Support for standard zoom-in/zoom-out/reset commands. This is supported in the textual view and the rendered page view.
* Support for exporting any document format to a plain text file.


## Resources

* The official website: [getbookworm.com](https://getbookworm.com/)
* User guide: [Bookworm user guide](https://getbookworm.com/user-guide/)


## Development

If you would like to contribute to *Bookworm's* development, please follow the following steps to get bookworm up and running on your computer:


### Required Binaries

You need the following binaries to develop Bookworm:

1. Python: currently we use Python 3.9 series: Grap the latest version from [python.org](https://www.python.org/downloads/)
2. GNU win32 tools: the easiest way to get those is to install Git. Since Git comes with these binaries you can simply add them to your path.
For example, if git was installed to: "C:\Program Files\Git". Then you need to add the following directory to your path: "C:\Program Files\Git\mingw64\bin".
3. NSIS: for creating Windows installers. Get it from [NSIS download page](https://nsis.sourceforge.io/Download) and add it to your path.
4. Optionally, you need Visual Studio 2019 with the Windows 10 development workload to compile some libraries.

###  Prepare the source tree

Bookworm is composed of many components. To prepare your source tree and run Bookworm for the first time, follow these steps:

* Get the source code by cloneing this repo:
```shell
git clone https://github.com/blindpandas/bookworm.git
cd bookworm
```
* Create a virtual environment:
```bash
python -m venv .env
.env\\scripts\\activate
```
* Install "invoke" : invoke is the command runner we use to define and run the build process. Install it from pip using:
```bash
pip install invoke
``
* Then run the following command to prepare your development environment:
```shell
invoke dev
```
This should install the development and application dependencies and prepare the source tree.
* If everything worked as expected, you can now run Bookworm using the following command:
```shell
invoke run
```
This should run Bookworm with debug mode enabled. To run the app with debug mode disabled you can do:
```shell
invoke run --no-debug
```
Another way to run the app is to execute the package directly. In this case, you can turn on debug mode yourself using the "--debug" flag.
To execute the package, you can do:
```shell
py -m bookworm --debug
```
* All the build/deployment commands are available in the `tasks.py` script. To view a list of these commands, issue the following in your terminal:
```shell
invoke --list
```
As an example, to build Bookworm, issue the following command:
```shell
invoke build
```
* If you've found a bug, or you want to contribute your changes back to bookworm, please create an issue or submit a pull request. We welcome any contribution, no matter how small it is.


## License

**Bookworm** is copyright (c) 2022 Blind Pandas Team. It is licensed under the [GNU General Public License](https://github.com/blindpandas/bookworm/blob/master/LICENSE).
