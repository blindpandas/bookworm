# Bookworm User Guide

## Introduction

Bookworm is a document reader that allows you to read PDF, EPUB, MOBI, and many other document formats using a versatile, yet simple, and highly accessible interface.

Bookworm provides you with a rich set of tools for reading your documents. You can search your document, bookmark and highlight content of interest, use text-to-speech, and convert scanned documents to plain text using Optical Character Recognition (OCR).

Bookworm runs on the Microsoft Windows operating system. It works well with your favorite screen readers like NVDA and JAWS. Even when a screen reader is not active, Bookworm can act as a self-voicing application using the built-in text-to-speech features.

## Features

* Supports more than 15 document formats, including EPUB, PDF, MOBI, and Microsoft Word documents
* Supports structured navigation using single-letter navigation commands to jump between headings, lists, tables, and quotes
* Full text search with customizable search options
* Advanced and easy to use annotation tools. You can add named bookmarks to mark places of interest in the text for later reference, and you can add comments to capture an interesting thought or create a summary of the content at a particular position in the text. Bookworm allows you to quickly jump to a specific comment and view it. Later, you can export these comments to a text file or HTML document for later use.
* For PDF documents, Bookworm supports two different styles of viewing pages; plain-text and fully rendered, zoomable, images.
* Support for using OCR to extract text from scanned documents and images using Windows10 builtin OCR engine. You also  have the option of downloading and using the freely available Tesseract OCR Engine within Bookworm.
* Look for term definition in Wikipedia, and read Wikipedia articles from within Bookworm
* A built-in web article extractor that allows you to open URLs and automatically extract the main article from the page.
* Document navigation via Table of content is extensively supported for all document formats
* Support for reading books aloud using Text-to-speech, with customizable voice options using voice profiles
* Support for text zoom using the standard zoom-in/zoom-out/reset commands
* Support for exporting any document format to a plain text file.

## Installation

To install and run Bookworm on your computer, first visit the [official website of Bookworm](https://getbookworm.com)

Bookworm comes in three flavors:

* 32-bit installer for computers running 32-bit or 64-bit Windows
* 64-bit installer for computers running 64-bit Windows
* Portable version to run from a flash drive

If you have legacy SAPI5 voices installed on your system and want to use them with Bookworm, we recommend installing the 32-bit version of Bookworm or using the 32-bit portable version.

After selecting the appropriate version that suits you, download it. If you downloaded the installer version of Bookworm, run the .exe file and follow the instructions on the screen, or if you chose to use a portable copy of Bookworm, unzip the contents of the archive wherever you want and run the Bookworm executable to launch the portable copy.


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
* Alt + Page up: navigate to previous section;
* F2: go to the next bookmark;
* Shift + F2: go to the previous bookmark;
* F8: go to the next comment;
* Shift + F8: go to the previous comment;
* F9: go to next highlight;
* Shift + F9: go to previous highlight;
* ctrl + enter: open any internal or external link if the document contains one. Internal links are links created by the document table of contents in some formats, external links are regular links opened by the browser. Depending on the link type, if the link is internal, i.e. the link to the table of contents, then pressing the above keyboard shortcut will move the focus to the desired table of contents, and if the link is external, it will open it in the default system browser.

### Bookmarks & Comments

Bookworm allows you to annotate an open document. You can add a bookmark to remember a specific location in a document and then quickly jump to it. In addition, you can add a comment to capture a thought or summarize the content.

#### Adding Bookmarks

While reading a document, you can press Ctrl + B (or select the Add Bookmark menu item) from the Annotations menu to add a bookmark. The bookmark will be added at the current cursor position. Alternatively, you can add a Named bookmark by pressing ctrl+shift+b, a window will open and ask for the name of the bookmark or, alternatively, choose Add Named Bookmark from the Annotations menu.

#### Viewing Bookmarks

Go to the Annotations menu and select "View Bookmarks" menu item. A dialog containing added bookmarks will be shown. Clicking any item in the bookmarks list will immediately take you to the position of that bookmark. Alternatively, to quickly jump through added bookmarks, you can use f2 and shift+f2 keys, which will directly go to the cursor position of the bookmark.

#### Adding comments

While reading a document, you can press Ctrl+m (or select the Add Comment menu item) from the Annotations menu to add a comment. You will be prompted for the content of the comment. Enter the content and click "OK". The comment will be added at the current location.

When you go to a page that contains at least one comment, you will hear a small sound indicating that there is a comment on the current page.

#### Managing comments

Select the "Saved Comments" menu item from the "Annotations" menu. A dialog box will appear with added comments. Clicking on any item in the list of comments will immediately jump to the position of that comment. Clicking the View button will open a dialog box showing the tag and contents of the selected comment.

Alternatively, you can click the "Edit" button to change the tag and content of the selected comment, press F2 to edit the tag of the selected comment in place, or you can press the Delete key on your keyboard or Alt+d shortcut to delete the selected comment.

#### Exporting comments

Bookworm allows you to export your comments to a plain text file or an HTML document, which can then be opened in a web browser. Optionally, Bookworm allows you to export your comments to Markdown, which is a text format for writing structured documents popular among computer power users.

To export comments, follow these steps:

1. In the annotation menu, navigate to Saved Comments;
2. Search for "Export" and press enter or alternatively, you can use the keyboard shortcut Alt+x to open the export menu;

You then have the following options, you can uncheck or leave checked any option you want:

* Include book title – this option allows you to include the title of the book in the final output file when you export comments;
* Include section title – an option that is used to include the title of the section in which the comment is left;
* Include  page number – this option is used to include the page numbers on which the comment was made;
* Include tags – this option is used to include or not include comment tags that were made during the annotation.

After specifying the correct option according to your needs, you must select the file output format, of which there are currently three – plain text format, Html, and Markdown.
After selecting the desired format, a read-only text area appears called "Output File" and is empty by default. You must click the Browse button, or alternatively, use alt+b to open an explorer window to specify the filename and folder where the output file will be saved.
When specifying a file name and file folder, there is an "Open file after exporting" checkbox that allows Bookworm to automatically open the output file after saving. Clear this check box if you don't want to automatically open the saved file and click OK. The file will be saved in the specified folder and you can open it with either Bookworm or any other text editor, like "Notepad".


### Reading Aloud

Bookworm supports reading the content of the opened document aloud using an installed text-to-speech voice. Just press F5 to start the speech, F6 to pause or resume the speech, and F7 to stop the speech entirely.

You can configure the speech in two ways:
1. Using A Voice Profile: A voice profile contains your custom speech configurations, you can activate/deactivate the voice profile at any time. You can access voice profiles from the speech menu or by pressing Ctrl + Shift + V. Note that Bookworm comes with some exemplary, built-in voice profiles.
2. The Global speech settings: these settings will be used by default when no voice profile is active. You can configure the global speech settings from the application preferences. 

During reading aloud, you can skip backward or foreword by paragraph by pressing Alt plus the left and right arrow  keys.


### Configuring The Reading Style

In addition to the speech settings, Bookworm gives you the ability to fine-tune its reading behavior through these settings. All of the following settings could be found in the reading page of the application preferences.

* When Pressing Play: This setting determines what happens when you tell Bookworm to "Play" the current document. You can select "Read Entire Document", "Read Current Section", or read only "Current Page". By default, Bookworm continuously reads the entire document unless you tell it to stop when it reaches the end of the page or the end of the current section.
* Start reading from: this option determines the position from which to start reading aloud. You can start reading from "Cursor position" or "Start of current page".
* During Reading Aloud: this set of options control how Bookworm behave during reading aloud. You can turn on/off any one of the following options by checking/unchecking its respective checkbox:

* Speak page number – text-to-speech will speak each page as you navigate to it;
* Announce the end of sections – when a section is finished, text-to-speech will let you know;
* Ask to switch to a voice that speaks the language of the current book – this option will determine whether or not Bookworm will warn about an incompatible voice, what happens by default when the selected text-to-speech language voice differs from the language of the open document;
* Highlight spoken text: if this option is turned on, the currently spoken text is visually highlighted.
* Select spoken text: if this option is turned on, the currently spoken text is selected. This enables you, for instance, to press Ctrl + C to copy the currently spoken paragraph.



### Continuous Reading Mode

In addition to Bookworm's built-in text-to-speech features, you can take advantage of your screen reader's continuous reading functionality (also known as "say all"). Bookworm provides support for this functionality through its "continuous reading mode". This mode is active by default, and you can disable it from the reading page of the application preferences. While the continuous reading mode is active, pages are turned automatically as the screen reader progresses through the document.

Note that due to the way this feature is currently implemented, the following limitations should be expected:

* Continuous reading will be interrupted if an empty page is reached. If you reached an empty page, simply navigate to a non-empty page and reactivate your screen reader's continuous reading functionality from there.
* Moving the caret to the last character in the page will immediately switch to the next page



### Viewing A Fully Rendered Version of The Current Page

Bookworm allows you to view a fully rendered version of the document. While a document is opened, you can press Ctrl + R or select the "Render Page" menu item from the document menu. We call this view "The Render View" as oppose to the, default, Textual View.

When you are in the Render View, you can use the usual zoom commands to zoom the page in and out:

* Ctrl + = zoom-in 
* Ctrl + - zoom-out
* Ctrl + 0 reset the zoom level

Note that you can also use the document navigation commands, mentioned above,  to navigate the render view as well. You can also press the escape key to dismiss this view and return to the default textual view.


### Navigating To A Specific Page

To navigate to a specific page in the currently opened document., press Ctrl + G, or select the "Go To Page..." menu item from the search menu to show the "Go To Page" dialog. In this dialog you can type the number of any page you want to navigate to, and Bookworm will take you to it. Note that this dialog will indicate to you the total number of pages found in the current document.

 
### Searching The document

To find a specific term, or a portion of text in the currently opened document, you can press Ctrl + F to bring up the "Search Document Dialog". This Dialog allows you to type the text you want to search for as well as configuring the  search process itself. The following options are available:

* Case Sensitive: The search will take into account the case of the letters in the search term.
* Match whole word only: The search term must be found as a whole word, i.e. not as a part of another word
* Search Range: This allows you to confine the search to certain pages or a specific section.

After clicking the OK button in the "Search document Dialog", another dialog containing search results will be shown. Clicking any item in the search results list will immediately take you to the position of that result with the search term highlighted for you.

Note that if you've closed the search results window, you can press F3 and Shift + F3 to move to the next and previous occurrence of the last search respectively.


## Managing File Associations

The "Manage File Associations" button, found in the general page in the application preferences, helps you to manage which file types are associated with Bookworm. Associating files with Bookworm means that when you click on a file in Windows explorer, that file would be opened in Bookworm by default. Please note that this dialog box is always shown to the user at the first launch of the program and is available only when using the installer, in the portable version this option is not required, respectively, in the portable version, the ability to associate files is disabled and a few tricks are required if you still want Bookworm to open any supported document by default.

Once you launch the file associations manager, you will have the following options:

* Associate all: this changes your settings so that if a file is supported by Bookworm, Windows will use Bookworm to open it. 
* Dissociate all supported file types: this will remove previously registered file associations
* Individual buttons for each supported file type: clicking any button of those will associate its respective file type with Bookworm.


## Updating Bookworm

By default, Bookworm checks for new versions upon startup. This ensures that you get the latest and greatest of Bookworm as early as possible. You can disable this default behavior from the application preferences.   You can also check for updates manually by clicking the "Check for updates" menu item found under the "Help" menu.

Either way, when a new version is found, Bookworm will ask you if you want to install it. If you click "Yes", the application will go ahead and download the update bundle, and will show a dialog indicating the progress of download. After the update is downloaded, Bookworm will alert you with a message, telling you it will restart the application in order to update. Just click "OK" to complete the update process.


## Reporting Problems & Issues

As blind developers, our responsibility is to develop applications that provide independence for us, and for our fellow blind friends all over the world. So, if you've found Bookworm useful in any way, please help us in making Bookworm better for you and for others. At this initial stage, we want you to tell us about any errors you may encounter during your use of Bookworm. To do so, open a new issue with the details of the error at [the issue tracker](https://github.com/blindpandas/bookworm/issues/). Your help is greatly appreciated.

Before submitting a new issue, make sure that you ran Bookworm in debug mode. To turn on debug mode, go to the "Help" menu and then click "Restart with debug-mode enabled" and try to reproduce the issue with debug mode enabled. In the majority of cases, when the error happens again with debug mode enabled, a dialog will be shown with the details of that error. You can then copy this information and include it with your problem report.

Note that some issues could be tricky to reproduce, they go away when you restart the program. In this case, it is okay to report the issue without the detailed information from the debug mode. Just make sure you include as much information as possible about the particulars of your system and usage scenario.


## News & Updates

To keep yourself updated with the latest news about Bookworm, you can visit Bookworm's website at: [getbookworm.com](https://getbookworm.com/). You can also follow the lead developer, Musharraf Omer, at [@mush42](https://twitter.com/mush42/) on Twitter.


## License

**Bookworm** is copyright (c) 2019-2023 Musharraf Omer and Bookworm Contributors. It is licensed under the [MIT License](https://github.com/blindpandas/bookworm/blob/master/LICENSE).
