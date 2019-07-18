[![Appveyor Build Status](https://ci.appveyor.com/api/projects/status/github/mush42/bookworm?branch=master&svg=true)

# Bookworm

**Bookworm** is an accessible e-book reader that enables blind and visually impaired individuals to read ebooks in an easy and hassle free manor. The main highlights of bookworm are:

* Supports popular e-book formats, including EPUB and PDF
* You can add named bookmarks to mark interesting positions in the text for later reference
* You can add notes to capture an interesting thought or create a summary of the content at a specific position of the text. Bookworm allows you to quickly jump to a specific note and view it. Later on, you can export these notes to a text file or an HTML document for future reference.
* Two different styles of viewing pages; plain-text and fully rendered, zoomable, images.
* Full text search with customizable search options
* Book navigation via Table of content is extensively supported for all e-book formats
* Support for reading books aloud using Text-to-speech, with configurable voice parameters.
* The ability to customize  text-to-speech with voice profiles. Each voice profile configures the style of the speech, and you can freely activate/deactivate any voice profile, even while reading aloud!
* Support for standard zoom-in/zoom-out/reset commands, Ctrl + =, Ctrl + -, and Ctrl + 0 respectively. This functionality is supported in the textual view and the rendered page view.
* Support for exporting any e-book format to a plain text file.


## Development

If you would like to contribute to *Bookworm's* development, please follow the following steps to get bookworm running on your computer:

* Make sure you are running Windows 7 or later, and you've installed Python 3.7 or a later version:
* Create a virtual environment:
```bash
py -m venv .env
.env\\scripts\\activate
``
* Get the source code by cloneing this repo:
```shell
git clone https://github.com/mush42/bookworm.git
cd bookworm
```
* Install the requirements from *PyPI* using *pip*:
```shell
pip install -r requirements-dev.txt
```
This should install the, pip installable, application and development dependencies.
* After installing dependencies, run the following command to prepare your environment:
```shell
invoke dev
```
* Run bookworm:
```shell
invoke run
```
To run the app with debug mode disabled you can do:
```shell
invoke run --no-debug
```
Another way to run the app is to execute the package directly. In this case, you should turn on/off debug mode yourself using the environment variable `BOOKWORM_DEBUG`.
To execute the package, you can do:
```shell
set BOOKWORM_DEBUG=1
py -m bookworm
```
* If you've found a bug, or you want to contribute your changes back to bookworm, please create an issue or submit a pull request. We welcome any contribution, no matter how small it is.


## License

**Bookworm** is copyright (c) 2019 Musharraf Omer. It is licensed under the [MIT License](https://github.com/mush42/bookworm/blob/master/LICENSE).
