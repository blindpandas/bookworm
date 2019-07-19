# Bookworm

## Introduction

**Bookworm** is an ACCESSIBLEebook reader that enables blind and visually impaired individuals to read ebooks in an easy and hassle free manor. The main highlights of bookworm are:

* Supports popular e-book formats, including EPUB and PDF
* You can add named bookmarks to mark interesting positions in the text for later reference
* You can add notes to capture an interesting thought or create a summary of the content at a specific position of the text. Bookworm allows you to quickly jump to a specific note and view it. Later on, you can export these notes to a text file or an HTML document for future reference.
* Two different styles of viewing pages; plain-text and fully rendered, zoomable, images.
* Full text search with customizable search options
* Book navigation via Table of content is extensively supported for all e-book formats
* Support for reading books aloud using Text-to-speech, with configurable voice parameters.
* The ability to customize  text-to-speech with voice profiles. Each voice profile configures the style of the speech, and you can freely activate/deactivate any voice profile, even while reading aloud!
* Support for standard zoom-in/zoom-out/reset commands, Ctrl + =, Ctrl + -, and Ctrl + 0 respectively. This functionality is supported in the plain text view and the rendered page view.
* Support for exporting any e-book format to a plain text file.


# User Guide

## Installation

To get Bookworm up and running on your computer, follow these steps:

1. Point your web browser to the [official website of Bookworm](https://mush42.github.io/bookworm/) and download the installer that suits your operating system. Bookworm comes in two flavors:

* A 32-bit installer for computers running a 32-bit variant of Windows 
* A 64-bit installer for computers running a 64-bit variant of Windows 

2. Run the installer and follow the prompts
3. After the installation has finished successfully , you can launch Bookworm from the *Desktop* or from the program list found in the Start Menu


### Opening A Book

You can open a book by selecting the "Open..." menu item from the "File" Menu. Alternatively you can use the Ctrl+O shortcut. Either way, the familiar "open file" dialog will be shown. Browse to your e-book, and click open to load it.

### The Reader Window

The main window of bookworm consists of the following two parts:

1. The "Table of contents": This part shows the e-book chapters'. It allows you to explore the content structure. Use navigation keys to navigate chapters, and press enter to navigate to specific chapter.

2. The "Textual View" area: This part contains the text of the current page. In this part you can use your usual reading commands to navigate the text. Additionally, you can use the following keyboard  shortcuts to navigate the e-book:

* Enter: navigate to the next page in the current section
* Backspace: navigate to the previous page in the current section
* Home: navigate to the first page of the current section
* End: navigate to the last page of the current section
* Alt + Page down: navigate to next section
* Alt + Page up: navigate to previous section


### Bookmarks & Notes

Bookworm allows you to annotate the opened book.  You can add a bookmark to remember a specific location in the book, and later on, quickly jump to  it. Also, you can take a note to capture a thought or summarize some content.

#### Adding Bookmarks

While reading a book, you can press Ctrl + B (or select the "Add Bookmark" menu item from the "Annotations" menu to add a bookmark. The bookmark will be added at the current position of the cursor. You'll be asked to provide a title for the bookmark. Type the desired title and click the OK Button. A bookmark will be added at the current location, and the current line will be visually highlighted.

#### Viewing Bookmarks

Press Ctrl + Shift + B, or select the "View Bookmarks" menu item from the "Annotations" menu. A dialog containing added bookmarks will be shown. Clicking any item in the bookmarks list will immediately take you to the position of that bookmark.

Additionally, you can press F2 to edit the title of the selected bookmark in place, or you can click the "Delete" button or the "Delete" key on your keyboard to remove the selected bookmark.

#### Taking Notes

While reading a book, you can press Ctrl + N (or select the "Take Note" menu item from the "Annotations" menu to take a note. The note will be added at the current position of the cursor. You'll be asked to provide the title and the content for the note. Type the desired title and content, and then click the Ok button. A note will be added at the current location.

When you navigate to a page containing at least one note, you will hear a little sound indicating the existence of a note in the current page..

#### Managing Notes

Press Ctrl + Shift + N, or select the "Manage Notes" menu item from the "Annotations" menu. A dialog containing added notes will be shown. Clicking any item in the notes list will immediately take you to the position of that note. Clicking the "View" button will bring up a dialog showing the title and the content of the selected note.

Additionally, you can click the "Edit" button to edit the title and the content of the selected note, or press  F2 to edit the title of the selected note in place, or you can click the "Delete" button or the "Delete" key on your keyboard to remove the selected note.

#### Exporting Notes

Bookworm allows you to export your notes to a plain-text file, or to an HTML document which you can then open in your web browser.  Optionally, bookworm allows you to export your notes to markdown, which is a text-base format for writing structured documents popular among expert computer users.

To export your notes, follow these steps:

1. From the "Annotations" menu select the "Notes Exporter..." menu item
2. Select the export range. This tells Bookworm whether you want to export the notes of the whole book, or you just want to export the notes of the current section. 
3. Select the output format. This determines the format of the file you get after exporting. Exporting to a plain-text will give you a simple, nicely formatted text file, exporting to HTML gives you a web page, and exporting to markdown will give you a .md file which is a text format popular among expert computer users.
4. If you want Bookworm to open the file to which your notes have been exported, you can check the "Open file after exporting" checkbox.
5. Click Export. You will be asked to select the file name of the exported file, and the location to which the file is saved. Clicking "Save" will save the file, and open it if you have instructed Bookworm to do so.


### Reading Aloud

Bookworm supports reading the content of the opened book aloud using an installed text-to-speech voice. Just press F5 to start the speech, F6 to pause or resume the speech, and F7 to stop the speech entirely.

You can configure the speech in two ways:
1. Using A Voice Profile: A voice profile contains your custom speech configurations, you can activate/deactivate the voice profile at any time. You can access voice profiles from the speech menu or by pressing Ctrl + Shift + V. 
2. The Global speech settings: these settings will be used by default when no voice profile is active. You can configure the global speech settings from the application preferences. 

During reading aloud, you can skip backward or foreword by paragraph by pressing Alt plus the left and right arrow  keys.


### Fully Rendered Pages

Bookworm allows you to view a fully rendered version of the book. While a book is opened, you can press Ctrl + R or select the "Render Page" menu item from the tools menu.

When you are in the Render View, you can use the usual zoom commands to zoom in and out:

* Ctrl + = will zoom-in 
* Ctrl + - will zoom-out
* Ctrl + 0 reset the zoom level

Note that the usual navigation commands work in the render view as well.


### Navigating To A Page

Press Ctrl + G, or select the "Go To..." menu item from the tools menu, to navigate to a specific page in the currently opened book.

 
### Searching The Book

To find a specific term, or a portion of text in the currently opened book, you can press Ctrl + F to bring up the "Search Book Dialog". This Dialog allows you to type the text you want to search for as well as configuring the  search process itself. The following options are available:

* Case Sensitive: The search will take into account the case of the letters in the search term.
* Whole Word Only: The search term must be found as a whole word, i.e. not as a part of another word
* Search Range: This allows you to confine the search to certain pages or a specific section.

After clicking the OK button in the "Search Book Dialog", another dialog containing search results will be shown. Clicking any item in the search results list will immediately take you to the position of that result with the search term highlighted for you.


## License

**Bookworm** is copyright (c) 2019 Musharraf Omer. It is licensed under the [MIT License](https://github.com/mush42/bookworm/blob/master/LICENSE).
