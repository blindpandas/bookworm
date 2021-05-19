# Bookworm User Guide

## Introduction

Bookworm is a document reader that allows you to read PDF, EPUB, MOBI, and many other document formats using a versatile, yet simple, and highly accessible interface.
Bookworm provides you with a rich set of tools for reading your documents. You can search the document, bookmark and highlight interesting content, use text-to-speech, and convert scanned documents to plain text using Optical Character Recgonition (OCR).
Bookworm runs on Microsoft's Windows operating system. It works well with your favorite screen reader such as NVDA and JAWS. Even if no screen reader is active, Bookworm can function as a self-voicing application using its builtin text-to-speech features.

## Features

* Supports more than 15 document formats, including EPUB, PDF, MOBI, and Microsoft Word documents
* Supports structured navigation using single-letter navigation commands to jump between headings, lists, tables, and quotes
* Full text search with customizable search options
* Advanced and simple to use annotation tools. You can add named bookmarks to mark interesting positions in the text for later reference, and you can add notes to capture an interesting thought or create a summary of the content at a specific position of the text. Bookworm allows you to quickly jump to a specific note and view it. Later on, you can export these notes to a text file or an HTML document for future reference.
* For PDF documents, Bookworm supports two different styles of viewing pages; plain-text and fully rendered, zoomable, images.
* Support for using OCR to extract text from scanned documents and images using Windows10 builtin OCR engine. You also  have the option of downloading and using the freely available Tesseract OCR Engine within Bookworm.
* Look for term definition in Wikipedia, and read Wikipedia articles from within Bookworm
* Integrated web article extractor, which allows you to open URLs and have Bookworm automatically extract the main article from the page
* Document navigation via Table of content is extensively supported for all document formats
* Support for reading books aloud using Text-to-speech, with customizable voice options using voice profiles
* Support for text zoom using the standard zoom-in/zoom-out/reset commands
* Support for exporting any document format to a plain text file.

## Installation

To get Bookworm up and running on your computer, follow these steps:

1. Point your web browser to the [(getbookworm.com), the official website of Bookworm](https://getbookworm.com/)
2. Bookworm comes in three flavors. Download the one that sutes you:
* 32-bit installer for computers running a 32-bit or 64-bit variant of Windows
* 64-bit installer for computers running a 64-bit variant of Windows
* Portable version for running from a USB thumb drive
If you have some legacy SAPI5 voices installed in your system, and you want to use them with Bookworm, we recommend installing the 32-bit variant of Bookworm.

2. Run the installer and follow the prompts
3. After the installation has finished successfully , you can launch Bookworm from the *Desktop* or from the program list found in the Start Menu


## Usage

### Opening A Document

You can open a document by selecting the "Open..." menu item from the "File" Menu. Alternatively you can use the Ctrl+O shortcut. Either way, the familiar "open file" dialog is shown. Browse to your document, and click open to load it.

### The Reader Window

The main window of Bookworm consists of the following two parts:

1. The "Table of contents": This part shows the document chapters'. It allows you to explore the content structure. Use navigation keys to navigate chapters, and press enter to navigate to specific chapter.

2. The "Textual View" area: This part contains the text of the current page. In this part you can use your usual reading commands to navigate the text. Additionally, you can use the following keyboard  shortcuts to navigate the document:

* Enter: navigate to the next page in the current section
* Backspace: navigate to the previous page in the current section
* While the caret is at the first line, pressing the up arrow two times in succession navigates to the previous page.
* While the caret is at the last line, pressing the down arrow two times in succession navigates to the next page.
* Alt + Home: navigate to the first page of the current section
* Alt + End: navigate to the last page of the current section
* Alt + Page down: navigate to next section
* Alt + Page up: navigate to previous section


### Bookmarks & Notes

Bookworm allows you to annotate the opened document.  You can add a bookmark to remember a specific location in the document, and later on, quickly jump to  it. Also, you can take a note to capture a thought or summarize some content.

#### Adding Bookmarks

While reading a document, you can press Ctrl + B (or select the "Add Bookmark" menu item from the "Annotations" menu to add a bookmark. The bookmark is added at the current position of the cursor. You'll be asked to provide a title for the bookmark. Type the desired title and click the OK Button. A bookmark will be added at the current location, and the current line will be visually highlighted.

#### Viewing Bookmarks

Press Ctrl + Shift + B, or select the "View Bookmarks" menu item from the "Annotations" menu. A dialog containing added bookmarks will be shown. Clicking any item in the bookmarks list will immediately take you to the position of that bookmark.

Additionally, you can press F2 to edit the title of the selected bookmark in place, or you can click the "Delete" button or the "Delete" key on your keyboard to remove the selected bookmark.

#### Taking Notes

While reading a document, you can press Ctrl + N (or select the "Take Note" menu item from the "Annotations" menu to take a note. The note will be added at the current position of the cursor. You'll be asked to provide the title and the content for the note. Type the desired title and content, and then click the OK button. A note will be added at the current location.

When you navigate to a page containing at least one note, you will hear a little sound indicating the existence of a note in the current page..

#### Managing Notes

Press Ctrl + Shift + N, or select the "Manage Notes" menu item from the "Annotations" menu. A dialog containing added notes will be shown. Clicking any item in the notes list will immediately take you to the position of that note. Clicking the "View" button will bring up a dialog showing the title and the content of the selected note.

Additionally, you can click the "Edit" button to edit the title and the content of the selected note, press  F2 to edit the title of the selected note in place, or you can click the "Delete" button or the "Delete" key on your keyboard to remove the selected note.

#### Exporting Notes

Bookworm allows you to export your notes to a plain-text file, or to an HTML document which you can then open in your web browser.  Optionally, Bookworm allows you to export your notes to markdown, which is a text-base format for writing structured documents popular among expert computer users.

To export your notes, follow these steps:

1. From the "Annotations" menu select the "Notes Exporter..." menu item
2. Select the export range. This tells Bookworm whether you want to export the notes of the whole document, or you just want to export the notes of the current section. 
3. Select the output format. This determines the format of the file you get after exporting. Exporting to a plain-text gives you a simple, nicely formatted text file, exporting to HTML gives you a web page, and exporting to markdown gives you a markdown document which is a text format popular among expert computer users.
4. If you want Bookworm to open the file to which your notes have been exported, you can check the "Open file after exporting" checkbox.
5. Click Export. You will be asked to select the file name of the exported file, and the location to which the file is saved. Clicking "Save" will save the file, and open it if you have instructed Bookworm to do so.


### Reading Aloud

Bookworm supports reading the content of the opened document aloud using an installed text-to-speech voice. Just press F5 to start the speech, F6 to pause or resume the speech, and F7 to stop the speech entirely.

You can configure the speech in two ways:
1. Using A Voice Profile: A voice profile contains your custom speech configurations, you can activate/deactivate the voice profile at any time. You can access voice profiles from the speech menu or by pressing Ctrl + Shift + V. Note that Bookworm comes with some exemplary, built-in voice profiles.
2. The Global speech settings: these settings will be used by default when no voice profile is active. You can configure the global speech settings from the application preferences. 

During reading aloud, you can skip backward or foreword by paragraph by pressing Alt plus the left and right arrow  keys.


### Configuring The Reading Style

In addition to the speech settings, Bookworm gives you the ability to fine-tune its reading behavior through these settings. All of the following settings could be found in the reading page of the application preferences.

* What to read: this option controls what happens when you instruct Bookworm to "Play" the current document. You can choose to "Read the entire document", "Read the current section", or read just "The current page". By default, Bookworm reads the entire document in a continuous manner, unless you instruct it to stop when it reaches the end of the page or the end of the current section.
* Where to start: this option controls the position from which to start reading aloud. You can choose to start reading from the "Position of the caret" or the "Start of the current page".
* How to read: this set of options control how Bookworm behave during reading aloud. You can turn on/off any one of the following options by checking/unchecking its respective checkbox:

* Highlight spoken text: if this option is turned on, the currently spoken text is visually highlighted.
* Select spoken text: if this option is turned on, the currently spoken text is selected. This enables you, for instance, to press Ctrl + C to copy the currently spoken paragraph.
* Play end-of-section sound: if this option is turned on, Bookworm plays a little sound when it reaches the end of a section.


### Continuous Reading Mode

In addition to Bookworm's built-in text-to-speech features, you can take advantage of your screen reader's continuous reading functionality (also known as "say all"). Bookworm provides support for this functionality through its "continuous reading mode". This mode is active by default, and you can disable it from the reading page of the application preferences. While the continuous reading mode is active, pages are turned automatically as the screen reader progresses through the document.

Note that due to the way this feature is currently implemented, the following limitations should be expected:

* Continuous reading will be interrupted if an empty page is reached. If you reached an empty page, simply navigate to a non-empty page and reactivate your screen reader's continuous reading functionality from there.
* Moving the caret to the last character in the page will immediately switch to the next page



### Viewing A Fully Rendered Version of The Current Page

Bookworm allows you to view a fully rendered version of the document. While a document is opened, you can press Ctrl + R or select the "Render Page" menu item from the tools menu. We call this view "The Render View" as oppose to the, default, Textual View.

When you are in the Render View, you can use the usual zoom commands to zoom the page in and out:

* Ctrl + = zoom-in 
* Ctrl + - zoom-out
* Ctrl + 0 reset the zoom level

Note that you can also use the document navigation commands, mentioned above,  to navigate the render view as well. You can also press the escape key to dismiss this view and return to the default textual view.


### Navigating To A Specific Page

To navigate to a specific page in the currently opened document., press Ctrl + G, or select the "Go To..." menu item from the tools menu to show the "Go To Page" dialog. In this dialog you can type the number of any page you want to navigate to, and Bookworm will take you to it. Note that this dialog will indicate to you the total number of pages found in the current document.

 
### Searching The document

To find a specific term, or a portion of text in the currently opened document, you can press Ctrl + F to bring up the "Search Document Dialog". This Dialog allows you to type the text you want to search for as well as configuring the  search process itself. The following options are available:

* Case Sensitive: The search will take into account the case of the letters in the search term.
* Whole Word Only: The search term must be found as a whole word, i.e. not as a part of another word
* Search Range: This allows you to confine the search to certain pages or a specific section.

After clicking the OK button in the "Search document Dialog", another dialog containing search results will be shown. Clicking any item in the search results list will immediately take you to the position of that result with the search term highlighted for you.

Note that if you've closed the search results window, you can press F3 and Shift + F3 to move to the next and previous occurrence of the last search respectively.


## Managing File Associations

The "Manage File Associations" button, found in the general page in the application preferences, helps you to manage which file types are associated with Bookworm. Associating files with Bookworm means that when you click on a file in Windows explorer, that file would be opened in Bookworm by default. Note that this dialog is always shown to the user in the first run of the program.

Once you launch the file associations manager, you will have the following options:

* Associate all: this changes your settings so that if a file is supported by Bookworm, Windows will use Bookworm to open it. 
* Dissociate all supported file types: this will remove previously registered file associations
* Individual buttons for each supported file type: clicking any button of those will associate its respective file type with Bookworm.


## Updating Bookworm

By default, Bookworm checks for new versions upon startup. This ensures that you get the latest and greatest of Bookworm as early as possible. You can disable this default behavior from the application preferences.   You can also check for updates manually by clicking the "Check for updates" menu item found under the "Help" menu.

Either way, when a new version is found, Bookworm will ask you if you want to install it. If you click "Yes", the application will go ahead and download the update bundle, and will show a dialog indicating the progress of download. After the update is downloaded, Bookworm will alert you with a message, telling you it will restart the application in order to update. Just click "OK" to complete the update process.


## Reporting Problems & Issues

As blind developers, our responsibility is to develop applications that provide independence for us, and for our fellow blind friends all over the world. So, if you've found Bookworm useful in any way, please help us in making Bookworm better for you and for others. At this initial stage, we want you to tell us about any errors you may encounter during your use of Bookworm. To do so, open a new issue with the details of the error at [the issue tracker](https://github.com/mush42/bookworm/issues/). Your help is greatly appreciated.

Before submitting a new issue, make sure that you ran Bookworm in debug mode. To turn on debug mode, go to the "Help" menu and then click "Restart with debug-mode enabled" and try to reproduce the issue with debug mode enabled. In the majority of cases, when the error happens again with debug mode enabled, a dialog will be shown with the details of that error. You can then copy this information and include it with your problem report.

Note that some issues could be tricky to reproduce, they go away when you restart the program. In this case, it is okay to report the issue without the detailed information from the debug mode. Just make sure you include as much information as possible about the particulars of your system and usage scenario.


## News & Updates

To keep yourself updated with the latest news about Bookworm, you can visit Bookworm's website at: [mush42.github.io/bookworm](https://mush42.github.io/bookworm/). You can also follow the lead developer, Musharraf Omer, at [@mush42](https://twitter.com/mush42/) on Twitter.


## License

**Bookworm** is copyright (c) 2019 Musharraf Omer and Bookworm Contributors. It is licensed under the [MIT License](https://github.com/mush42/bookworm/blob/master/LICENSE).
