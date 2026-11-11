# Bookworm User Guide

## Introduction

Bookworm is a document reader that allows you to read PDF, EPUB, MOBI, and many other document formats using a versatile, simple, and highly accessible interface.

Bookworm provides you with a rich set of tools for reading your documents. You can search your document, bookmark and highlight content of interest, add comments, use text-to-speech, organize documents in Bookworm Bookshelf, open web articles, and convert scanned documents to plain text using Optical Character Recognition (OCR).

Bookworm runs on the Microsoft Windows operating system. It works well with screen readers such as NVDA and JAWS. Even when a screen reader is not active, Bookworm can act as a self-voicing application using the built-in text-to-speech features.

## Features

* Supports over 20 document formats, including EPUB, PDF, MOBI, Microsoft Word documents, HTML, plain text, and Markdown.
* Supports structured navigation using single-letter commands to jump between headings, links, lists, tables, quotes, and figures.
* Full text search with customizable search options, including regular expressions and page or section ranges.
* Advanced and easy to use annotation tools. You can add named bookmarks, comments, and highlights, quickly jump between them, and export comments or highlights to a plain text, HTML, or Markdown document.
* For formats that support graphical rendering, Bookworm supports two different styles of viewing pages: plain text and fully rendered, zoomable images.
* Support for Optical Character Recognition (OCR) to extract text from scanned documents and images. Bookworm integrates the built-in Windows OCR, the open-source Tesseract engine, VIVO General OCR, and Baidu AI Cloud OCR services.
* A built-in web article extractor that allows you to open URLs and automatically extract the main article from the page.
* Support for Wikipedia quick search, including opening Wikipedia articles in Bookworm.
* Bookworm Bookshelf for organizing local documents, importing files or folders, searching titles and indexed content, and bundling documents for offline use.
* Document navigation via table of contents is extensively supported for document formats that provide one.
* Support for reading books aloud using text-to-speech, with customizable voice options using voice profiles.
* Support for text zoom using the standard zoom-in, zoom-out, and reset commands.
* Support for exporting any document format to a plain text file.

## Installation

To install and run Bookworm on your computer, visit the [Bookworm releases page](https://github.com/blindpandas/bookworm/releases) and download the latest release.

Current builds require Windows 8.1 or later. Windows 7 and earlier are not supported.

Bookworm comes in three flavors:

* 32-bit installer for computers running 32-bit or 64-bit Windows
* 64-bit installer for computers running 64-bit Windows
* Portable version to run from a flash drive

If you have legacy SAPI5 voices installed on your system and want to use them with Bookworm, we recommend installing the 32-bit version of Bookworm or using the 32-bit portable version.

After selecting the appropriate version that suits you, download it. If you downloaded the installer version of Bookworm, run the .exe file and follow the instructions on the screen. If you chose to use a portable copy of Bookworm, unzip the contents of the archive wherever you want and run the Bookworm executable to launch the portable copy.

## Usage

### Opening A Document

You can open a document by selecting the "Open..." menu item from the "File" menu. Alternatively, you can use the Ctrl+O shortcut. Either way, the familiar "open file" dialog is shown. Browse to your document, and click open to load it.

From the "File" menu, you can also open a new Bookworm window with Ctrl+N, close the current document with Ctrl+W, or pin the current document with Ctrl+P. Pinned documents and recently opened documents are available from their own submenus. Both lists can be cleared from the same menu.

The "File" menu also contains an "Import" submenu. The "Import QRD file" item imports reading position information from a QRead QRD file and opens the original document at the saved position. The "Preferences..." item opens Bookworm preferences; it is also available with Ctrl+Shift+P.

### The Reader Window

The main window of Bookworm consists of the following parts:

1. The "Table of Contents": This part shows the document chapters. It allows you to explore the content structure. Use navigation keys to navigate chapters, and press enter to navigate to a specific chapter. You can move focus to the table of contents from the text view by pressing Ctrl+T.

2. The "Textual View" area: This part contains the text of the current page. In this part you can use your usual reading commands to navigate the text. Additionally, you can use the following keyboard shortcuts to navigate the document:

* Enter or Space: navigate to the next page in the current section
* Backspace: navigate to the previous page in the current section
* Page Down and Page Up: move forward or backward by a large amount of text within the current page
* While the caret is at the first line, pressing the up arrow two times in succession navigates to the previous page.
* While the caret is at the last line, pressing the down arrow two times in succession navigates to the next page.
* Alt + Home: navigate to the first page of the current section
* Alt + End: navigate to the last page of the current section
* Alt + Page Down: navigate to the next section
* Alt + Page Up: navigate to the previous section
* F2: go to the next bookmark
* Shift + F2: go to the previous bookmark
* F8: go to the next comment
* Shift + F8: go to the previous comment
* F9: go to the next highlight
* Shift + F9: go to the previous highlight
* Ctrl + Enter: perform the special action at the current position. Bookworm can follow an internal link, open an external link in your default browser, show a table in a browsable dialog, or open an embedded image.
* Ctrl + Shift + Enter: return to the previous position after following an internal link.

3. The reading progress slider: When the "Show reading progress percentage" option is enabled in preferences, Bookworm shows the reading progress in the status bar and lets you move through the document by percentage from the slider.

### Structured Navigation

When the current document provides semantic structure, you can move by elements directly from the textual view. Press the letter to move to the next element, or press Shift with the same letter to move to the previous element.

* H: heading
* 1 through 6: heading levels 1 through 6
* K: link
* L: list
* T: table
* Q: quote
* I: image or figure

You can also open the "Element list..." item from the "Document" menu, or press Ctrl+F7. The element list can show headings, links, lists, tables, quotes, and figures. Activating an item moves the reader to that element.

### Document Commands

The "Document" menu contains commands that depend on the current document:

* "Document Info..." shows metadata and document statistics when available.
* "Element list..." opens the structured element list with Ctrl+F7.
* "Change Reading Mode..." opens the reading mode dialog with Ctrl+Shift+M. Available modes depend on the document format and may include default mode, reading order, physical layout, paginated, chapter by chapter, clean text, and full text.
* "Render Page..." opens a fully rendered image of the current page with Ctrl+R when the document format supports graphical rendering.

### Bookmarks, Comments, and Highlights

Bookworm allows you to annotate an open document. You can add a bookmark to remember a specific location in a document and then quickly jump to it. In addition, you can add comments to capture thoughts or summaries, and you can highlight selected text for later review.

#### Adding Bookmarks

While reading a document, you can press Ctrl+B or select the "Add Bookmark" menu item from the "Annotation" menu to add a bookmark. The bookmark will be added at the current cursor position. Alternatively, you can add a named bookmark by pressing Ctrl+Shift+B, or by choosing "Add Named Bookmark..." from the "Annotation" menu.

#### Viewing Bookmarks

Go to the "Annotation" menu and select "Saved Bookmarks...". A dialog containing added bookmarks will be shown. Activating any item in the bookmarks list will immediately take you to the position of that bookmark. To quickly jump through added bookmarks from the text view, use F2 and Shift+F2.

In the saved bookmarks dialog, press F2 to rename the selected bookmark or Delete to remove it.

#### Adding Comments

While reading a document, you can press Ctrl+M or select the "Add Comment..." menu item from the "Annotation" menu to add a comment. You will be prompted for the content of the comment. Enter the content and click "OK". The comment will be added at the current location. If text is selected, the comment is attached to the selected range.

Hold Shift while adding a comment if you want Bookworm to ask for tags after the comment is created.

When you go to a page that contains at least one comment, Bookworm can play a small sound indicating that there is a comment on the current page. This behavior can be changed from the "Annotation" page in preferences.

#### Adding Highlights

Select text and press Ctrl+H, or select "Highlight Selection" from the "Annotation" menu, to save the selected text as a highlight. If the same selection is already highlighted, the highlight is removed. If the selection overlaps an existing highlight, Bookworm can extend the existing highlight.

Hold Shift while adding a highlight if you want Bookworm to ask for tags after the highlight is created. Use F9 and Shift+F9 to move to the next and previous highlight.

#### Managing Comments and Highlights

Select "Saved Comments..." or "Saved Highlights..." from the "Annotation" menu. A dialog box will appear with the saved items. Activating any item in the list will immediately jump to its position. Clicking the "View" button opens a dialog showing the tags and contents of the selected item.

You can filter saved comments or highlights by tag, section, or content. You can sort them by date, page, position, or book when those fields are available. Press F6 to move to the filter controls, F2 to edit tags, Delete to delete the selected item, or Ctrl+C to copy the annotation text.

#### Exporting Comments and Highlights

Bookworm allows you to export saved comments and highlights to a plain text file, an HTML document, or a Markdown document.

To export comments or highlights, follow these steps:

1. In the "Annotation" menu, navigate to "Saved Comments..." or "Saved Highlights...".
2. Search for "Export" and press enter, or use the keyboard shortcut Alt+X to open the export menu.

You then have the following options. You can uncheck or leave checked any option you want:

* Include book title - this option allows you to include the title of the book in the final output file.
* Include section title - this option allows you to include the title of the section in which the annotation is found.
* Include page number - this option allows you to include the page number on which the annotation was made.
* Include tags - this option allows you to include or not include annotation tags.

After specifying the correct options according to your needs, select the output file format: plain text, HTML, or Markdown. Then choose the output file. The "Open file after exporting" checkbox allows Bookworm to automatically open the output file after saving.

### Bookworm Bookshelf

Bookworm Bookshelf is a local library for organizing documents you read with Bookworm. You can open it from the "Bookshelf" submenu in the "File" menu by selecting "Open Bookshelf". You can add the current local document by selecting "Add to local bookshelf...".

When adding or importing documents, Bookworm can ask for a reading list, collections, and whether to add the document to the full-text search index. The "Bookshelf" page in preferences contains an option to automatically add opened books to the local bookshelf.

The local bookshelf contains categories such as "Recently Added", "Currently Reading", "Want to Read", "Favorites", "Reading Lists", "Collections", and "Authors". The bookshelf "File" menu allows you to import documents with Ctrl+O, import documents from a folder, search the bookshelf, bundle documents, and clear invalid documents.

In the bookshelf document list:

* Press Enter to open the selected document in a new Bookworm window.
* Press F2 to rename the selected document when renaming is available.
* Press F5 to refresh the list.
* Press Ctrl+F to move to the quick filter.
* Start typing while focused on the document list to filter by title.
* Press Alt+Left to return from a nested folder or container.

The bookshelf context menu can open a document in Bookworm, open it in the system viewer, edit its title, show document information, edit reading list or collections, toggle currently reading, want to read, or favorites, and remove the document from the bookshelf.

The "Search Bookshelf..." command searches document titles and indexed content. Search results can open matching documents at the page and position where the match was found.

### Opening URLs and Wikipedia

Bookworm can open web pages as readable documents. Select "Open URL" from the "Web Services" menu and enter a URL, or press Ctrl+Shift+U to open the URL currently on the clipboard. Bookworm loads the page and extracts the main readable article text when possible. Web pages support reading modes such as clean text and full text.

The "Wikipedia quick search" command is available from the "Web Services" menu with Ctrl+Shift+W. If text is selected, Bookworm uses it as the search term. You can choose the Wikipedia language, read the summary, open the article in Bookworm, or open it in your browser. When text is selected, the context menu also contains "Define using Wikipedia".

## Optical Character Recognition (OCR)

Bookworm can extract text from images and scanned documents using its OCR features. This is especially useful for making image-based PDFs or pictures of documents readable and searchable. Bookworm supports multiple OCR engines, allowing you to choose the one that best suits your needs.

You can access OCR features from the "OCR" menu in the menu bar. The primary functions are:

* "Scan Current Page..." (F4): Performs OCR on the current page of your document.
* "Automatic OCR" (Ctrl+F4): Automatically performs OCR on each new page as you navigate through a document.
* "Change OCR Options...": Lets you change OCR options for the current book.
* "Scan To Text File...": Scans pages and saves the recognized text to a .txt file.
* "Image To Text...": Allows you to select an image file from your computer and open the recognized text as a virtual document in Bookworm.

The OCR options dialog lets you choose the primary recognition language, and a secondary recognition language when the selected engine supports multilingual recognition. You can also change the supplied image resolution, enable image enhancements, and save the selected options until the current book is closed.

Available image pre-processing filters include increasing image resolution, binarization, splitting two-in-one scans to individual pages, combining images, blurring, deskewing, erosion, dilation, sharpening, and color inversion. Available filters and engine-specific options depend on the OCR engine.

Bookworm supports the following OCR engines:

### Windows 10/11 OCR

If you are using Windows 10 or a later version, Bookworm can use the OCR engine that is built directly into the operating system. This is the default engine when available and requires no additional setup. It provides good results, especially for languages that are installed on your system.

### Tesseract OCR Engine

For users who need support for a wider range of languages, Bookworm supports integration with the Tesseract OCR Engine, a powerful open-source engine maintained by Google.

If Tesseract is not already installed for Bookworm, you can download and set it up from within the application:

1. Go to "File > Preferences..." and select the "OCR" page.
2. Under the "Tesseract OCR Engine" section, click the "Download Tesseract OCR Engine" button and follow the prompts.
3. Once installed, you can manage languages by clicking the "Manage Tesseract OCR Languages" button.

### VIVO General OCR Engine (via NVDA-CN)

Through a partnership with VIVO (vivo.com.cn) and the NVDA Chinese Community (NVDACN), Bookworm offers access to the VIVO OCR engine. This service is provided free of charge and delivers high-quality recognition for both Chinese and English content.

To use the VIVO OCR engine, you will need a free NVDA-CN account.

#### Setting Up VIVO OCR

1. Create an account at the NVDA-CN registration page: [https://nvdacn.com/admin/register.php](https://nvdacn.com/admin/register.php).
2. Verify your email address by clicking the link in the verification email.
3. Open Bookworm preferences by navigating to "File > Preferences..." or by pressing Ctrl+Shift+P.
4. Go to the "OCR" settings page and enter your username and password under the "VIVO OCR Engine" section.
5. Select "VIVO OCR" as your default OCR engine from the "Default OCR Engine" list.

Once configured, the VIVO engine will be used for OCR operations in Bookworm. For account-related issues, you can contact the NVDA-CN team at support@nvdacn.com.

### Baidu AI Cloud OCR

For high accuracy, especially with mixed Chinese and English text or complex layouts, Bookworm integrates with the Baidu AI Cloud OCR service. This is a web-based service that provides both a standard and a high-precision engine.

To use the Baidu OCR engines, you will need to obtain a free API Key and Secret Key.

#### Setting Up Baidu OCR

1. Register for an account at the [Baidu AI Cloud OCR page](https://ai.baidu.com/tech/ocr/general) to get your keys.
2. Open Bookworm preferences by navigating to "File > Preferences..." or by pressing Ctrl+Shift+P.
3. Go to the "OCR" settings page and enter your API Key and Secret Key under the "Baidu OCR Engine" section.
4. Select either "Baidu General OCR (Standard)" or "Baidu General OCR (Accurate)" as your default OCR engine in the "Default OCR Engine" list.

Once configured, the Baidu engine will be used for OCR operations in Bookworm.

### Reading Aloud

Bookworm supports reading the content of the opened document aloud using an installed text-to-speech voice. Press F5 to start speech, F6 to pause or resume speech, and F7 to stop speech entirely.

You can configure speech in two ways:

1. Using a voice profile: A voice profile contains your custom speech configuration. You can activate or deactivate the voice profile at any time. You can access voice profiles from the "Speech" menu or by pressing Ctrl+Shift+V. Bookworm comes with some built-in example voice profiles.
2. The global speech settings: These settings will be used by default when no voice profile is active. You can configure the global speech settings from the application preferences.

During reading aloud, press Alt+Left Arrow to rewind to the previous paragraph, or Alt+Right Arrow to fast forward to the next paragraph.

### Media Keys Behavior

Media keys are mapped to core text-to-speech actions:

* Play/Pause: toggles TTS play, pause, and resume.
* Next Track: fast forwards to the next paragraph. This is equivalent to Alt+Right Arrow.
* Previous Track: rewinds to the previous paragraph. This is equivalent to Alt+Left Arrow.

By default, media keys are handled when the Bookworm window has focus. You can enable global media keys from the "Reading" page in preferences by checking "Enable global media keys". This allows Bookworm to control playback while it is running in the background.

Media key functionality can be unreliable when multiple media applications are running simultaneously.

### Configuring The Reading Style

In addition to the speech settings, Bookworm gives you the ability to fine-tune its reading behavior. All of the following settings can be found in the "Reading" page of the application preferences.

* When Pressing Play: This setting determines what happens when you tell Bookworm to play the current document. You can select "Read Entire Document", "Read Current Section", or "Read Current Page".
* Start reading from: This option determines the position from which to start reading aloud. You can start reading from the cursor position or the start of the current page.
* During Reading Aloud: This set of options controls how Bookworm behaves during reading aloud.
* Speak page number: Text-to-speech will speak each page as you navigate to it.
* Announce the end of sections: When a section is finished, text-to-speech will let you know.
* Ask to switch to a voice that speaks the language of the current book: This option determines whether Bookworm asks you to switch voices when the selected text-to-speech voice differs from the language of the open document.
* Highlight spoken text: If this option is turned on, the currently spoken text is visually highlighted.
* Select spoken text: If this option is turned on, the currently spoken text is selected. This enables you, for instance, to press Ctrl+C to copy the currently spoken paragraph.

The "Reading" page also contains options for image feedback while navigating text, including playing a sound when navigating to an image and including images with empty alternative text in image navigation.

### Continuous Reading Mode

In addition to Bookworm's built-in text-to-speech features, you can take advantage of your screen reader's continuous reading functionality, also known as "say all". Bookworm provides support for this functionality through its "continuous reading mode". This mode is active by default, and you can disable it from the "Reading" page of the application preferences. While continuous reading mode is active, pages are turned automatically as the screen reader progresses through the document.

The following limitations should be expected:

* Continuous reading will be interrupted if an empty page is reached. If you reached an empty page, navigate to a non-empty page and reactivate your screen reader's continuous reading functionality from there.
* Moving the caret to the last character in the page will immediately switch to the next page.

### Viewing A Fully Rendered Version of The Current Page

Bookworm allows you to view a fully rendered version of the current page when the document supports graphical rendering. While a document is opened, you can press Ctrl+R or select the "Render Page..." menu item from the "Document" menu. We call this view the "Render View" as opposed to the default textual view.

When you are in the Render View, you can use the usual zoom commands:

* Ctrl + =: zoom in
* Ctrl + -: zoom out
* Ctrl + 0: reset the zoom level

You can also use the document navigation commands mentioned above to navigate the render view. Press Escape to dismiss this view and return to the textual view.

When Ctrl+Enter opens an embedded image, the image dialog provides additional commands:

* Ctrl + =: zoom in
* Ctrl + -: zoom out
* Ctrl + 0: actual size
* Ctrl + S: save the image
* Ctrl + C: copy the image
* Escape, Ctrl+W, or Alt+C: close the image dialog

When Ctrl+Enter opens a table, Bookworm shows it in a browsable HTML dialog.

### Navigating To A Specific Page

To navigate to a specific page in the currently opened document, press Ctrl+G or select the "Go To Page..." menu item from the "Search" menu to show the "Go To Page" dialog. In this dialog you can type the number of any page you want to navigate to, and Bookworm will take you to it. This dialog indicates the total number of pages found in the current document.

For documents that provide page labels, such as some PDF documents, you can press Ctrl+Shift+G or select "Go To Page By Label..." from the "Search" menu and enter the page label.

To move to a line within the current page or document, press Ctrl+L or select "Jump to Line..." from the "Search" menu.

### Searching The Document

To find a specific term or a portion of text in the currently opened document, press Ctrl+F to bring up the "Search Document" dialog. This dialog allows you to type the text you want to search for and configure the search process itself. The following options are available:

* Case sensitive: The search will take into account the case of the letters in the search term.
* Match whole word only: The search term must be found as a whole word, not as part of another word.
* Regular expression: The search term is treated as a regular expression. When this option is enabled, whole-word matching is disabled.
* Search range: This allows you to confine the search to certain pages, a specific section, or a text range depending on the document.

After clicking the OK button in the "Search Document" dialog, another dialog containing search results will be shown. Activating any item in the search results list will immediately take you to the position of that result with the search term highlighted for you.

If you have closed the search results window, press F3 and Shift+F3 to move to the next and previous occurrence of the last search respectively.

## Managing File Associations

The "Manage File Associations" button, found in the "General" page in application preferences, helps you manage which file types are associated with Bookworm. Associating files with Bookworm means that when you click on a file in Windows Explorer, that file will be opened in Bookworm by default. This dialog is shown at first launch and is available only when using the installer. In the portable version, file association management is disabled.

Once you launch the file associations manager, you will have the following options:

* Associate all: This changes your settings so that if a file is supported by Bookworm, Windows will use Bookworm to open it.
* Dissociate all supported file types: This removes previously registered file associations.
* Individual buttons for each supported file type: Clicking any button will associate its respective file type with Bookworm.

<a id="audiobooks"></a>

## Audiobooks

Open **File → Audiobooks**, or press **Ctrl+F11** in Bookworm's main window. The audiobook shelf and player have their own window. Tab and Shift+Tab move between native controls; Alt opens the menu bar. F1 opens this help section. Alt+F4 closes the player and saves its position. The shortcuts below apply to the audiobook window, not to the document reader or modal editing dialogs.

### Adding and organising books

Add one audio file or a folder containing one book, including its disc subfolders. Supported formats are MP3, M4B, M4A, WAV, FLAC, Ogg Vorbis and Opus. The file picker filters these extensions; folder import ignores documents, images and other files. Paths escaping the selected folder through links are not imported.

Fast checks reject missing, empty and unreadable files. Import also performs a complete decode in the background before offering the book for addition. Full verification takes time proportional to the recording and machine performance; it can be cancelled without blocking player controls. A failed file aborts the import rather than silently omitting part of a book. Errors are shown in a native, accessible dialog with an OK button.

Review the title, author/narrator and chapter order before accepting. File names use natural numeric order (2 before 10). Complete, unique disc/track metadata takes precedence. Move Up and Move Down change the proposed listening order. MP3 ID3 chapters and supported Nero/QuickTime M4B/M4A chapter data are imported, including any introduction before the first chapter marker. This feature handles local audio files, not DAISY packages, DRM-protected books, network streams, archives or playlists.

Search filters the shelf by title and author. Enter, Ctrl+O or Open Selected Book loads the selected book in a paused state. F5 starts playback. Removing a book from the shelf removes its stored position and bookmarks after confirmation; it never deletes the audio recordings.

### Playback and navigation shortcuts

| Shortcut | Action |
| --- | --- |
| F5 | Play/pause; open the selected book if necessary |
| F6 | Pause |
| F9 | Full stop and return to the beginning of the book |
| F7 / F8 | Short backward/forward jump |
| Shift+F7 / Shift+F8 | Long backward/forward jump |
| Ctrl+PageUp / Ctrl+PageDown | Previous/next chapter |
| Ctrl+G | Go to a time measured from the beginning of the book |
| Alt+Down / Alt+Up | Decrease/increase speed by 5 percentage points |
| Ctrl+0 | Reset speed to 100% |
| Alt+PageDown / Alt+PageUp | Decrease/increase volume by 5 percentage points |
| Alt+Home / Alt+End | Decrease/increase speech boost by 1 dB |
| Ctrl+I | Announce listening information on demand |
| Ctrl+F12 | Show detailed, live listening times |
| Ctrl+Shift+I | Inspect the current physical audio file |
| Ctrl+Shift+T | Edit that file's tags |
| Ctrl+B | Add a bookmark at the current position |
| Ctrl+Shift+B | Browse, edit or delete bookmarks |

The Stop button and F9 close the audio engine and reset the saved position to the beginning of the book. They cancel the sleep timer and A–B repeat. F5 then starts from the beginning; Pause keeps the current position.

Short and long jumps default to 10 and 60 seconds. Settings allow 1–60 and 10–600 seconds respectively; the long jump must exceed the short jump. Jumps cross physical file boundaries. Go to Time accepts seconds, mm:ss or hh:mm:ss; 90, 1:30 and 0:01:30 identify the same point. Up to three decimal places are accepted with a dot or comma: 1:30.125 is 90 seconds and 125 milliseconds.

Positions are stored as integer milliseconds. The player requests an exact native seek and checks the reported position before resuming. A seek that cannot be verified within 50 ms produces an error instead of silently continuing at a different point. This is an acceptance tolerance, not a universal sample-accuracy guarantee for every format and output device. Within an open physical file, jumping reuses the decoder. Contiguous embedded chapters also avoid decoder reloads.

Seeking does not trigger automatic position speech. Ctrl+I reports the current chapter, file position/duration/remaining time, book position/duration and remaining listening time at the current rate. The detailed window updates every second without an extra program announcement. It shows milliseconds and preserves text selection during updates. Uncheck Update Times Automatically to read or copy a fixed snapshot. Calculated listening time excludes future pauses and section repeats. Codec duration estimates and playback timestamps limit accuracy; additional displayed digits do not establish measurement accuracy.

### Speed, volume and speech boost

Playback speed ranges from 50 to 200%, using Rubber Band R3 pitch-preserving stretching. A typed spin-control value takes effect when Apply Speed is activated; shortcuts apply immediately. Processing quality depends on the source and rate. No algorithm can promise imperceptible artefacts on all recordings at every rate.

The native volume slider ranges from 0 to 100% and applies changes directly. Focused native slider/spin values are left to the screen reader: the program does not repeat them. A shortcut used away from the corresponding control sends one value announcement through Bookworm's existing speech route.

Speech boost adds 0–12 dB for quiet recordings. A look-ahead sample-peak limiter targets −1 dBFS after stretching/boosting. This is not certified true-peak loudness processing and cannot repair pre-existing clipping or noise. Strong limiting may change speech dynamics. Volume, rate and boost are remembered separately for each book.

### Resume, annotations, sleep and repeat

Position is checkpointed during playback and on pause, jumps and close. Reopening defaults to the exact stored position. Optional rewind on reopening can be configured from 0 to 30 seconds; the default is 0. It never affects explicit bookmarks or Go to Time. Reaching the end marks a book finished without automatically restarting it; select a chapter to listen again.

Ctrl+B captures the position when invoked, before opening the name/note editor. Notes may span several lines. The bookmark list supports jumping, renaming, note editing and confirmed deletion. Export/import uses JSON with book/timeline identity checks. Repeated import does not duplicate identical entries. Editing a bookmark's label or note does not change its time.

The Playback menu provides a sleep timer in real elapsed minutes, pause at chapter end, timer cancellation, and A–B section repeat. Use 0 minutes to cancel. The repeat end must follow its start. Rate changes do not extend the elapsed-time sleep deadline.

Multimedia keys follow Bookworm's existing global-media-key preference. Play/pause goes to the active audiobook or text-to-speech session; previous/next make short jumps for audiobooks. Starting an audiobook stops document speech; starting document speech pauses the audiobook and returns multimedia-key ownership to speech.

### Relocation and backups

Relocate Selected Book reconnects a moved folder. Full-file SHA-256 identity is checked, not merely names or sizes. Successful relocation preserves positions and bookmarks. The work is cancellable and performed off the GUI thread.

Library Backup copies the SQLite shelf database, including references, positions and bookmarks. It does **not** include recordings. To restore it, close Bookworm, keep a copy of the current `audiobooks/library.sqlite3` in Bookworm's user-data folder, then replace it with the backup. Back up audio files separately.

### Saving copies and exporting audio

Save Original Recordings As makes verified, byte-identical copies. A one-file book is saved as a file; a multi-file book goes into a new folder preserving relative subfolders. The original extension must be retained. Original recordings cannot be overwritten.

Export Audiobook encodes the entire book, in listening order, into one MP3, M4B/AAC, 16-bit FLAC or 16-bit WAV file. Select mono/stereo and 22050, 44100 or 48000 Hz. MP3/AAC expose bitrate settings; MP3 at 22050 Hz is limited to 160 kbit/s. AAC bitrate is a target, so its actual average can differ. WAV/FLAC do not use a lossy-encoding bitrate control.

Export defaults to original speed and no added boost. A checkbox applies the current speed/boost settings. Playback volume is never baked in. MP3 and M4B retain chapter titles with rate-adjusted times; WAV/FLAC exports do not embed chapters. Increasing bitrate, sample rate or channel count cannot recover lost source detail.

A floating-point PCM intermediate avoids lossy intermediate encoding and may require much more temporary space than the final file. Free space is checked before starting. The operation removes its own temporary files when done or cancelled. Only after encoding, metadata writing and complete decode verification succeeds is the requested destination replaced. Cancellation leaves an existing destination intact.

### File information and tag editing

Ctrl+Shift+I opens a read-only, line-readable report with path, size, format, reported duration, sample rate, channels, bitrate and available tags. It can be copied or saved as UTF-8 text. VBR bitrate may be approximate. Inspection never modifies the source and never fabricates ID3v2 fields/version data when no v2 tag exists. Binary fields show size and SHA-256; their contents can be exported separately from the editor.

Ctrl+Shift+T pauses playback and opens a native tree of tag fields. Arrow keys navigate groups; Enter expands a group or edits a scalar. Text, numbers, language codes, descriptions, URLs, multiline comments, multi-value lists, nested ID3 chapter frames and supported binary values can be edited separately. Add/remove operations are explicit. Less common fields retain their standard technical identifiers and should only be changed with an understanding of that format. Unknown ID3 frames are retained, not guessed or rewritten.

MP3 ID3v1 has a separate editor. Choose ISO-8859-1 or Windows-1250 for Hungarian legacy files; other players may interpret Windows-1250 differently. Oversized or unrepresentable v1 text is rejected rather than silently truncated or substituted. ID3v2 supports full Unicode. Changing between v2.3/v2.4 is rejected if fields would be lost/changed or unknown frames cannot be preserved.

Saving creates a verified `.bookworm-tags-….bak` copy, rereads edited tags, and compares the encoded audio payload before and after editing. Audio is not re-encoded. Only a successful result replaces the source; shelf file references are refreshed while positions and bookmarks remain. Previously imported chapter order/layout is not automatically rebuilt from edited tags. Reopen the book after saving.

### Troubleshooting

Missing engines, unavailable audio output, decoding failures, failed seek verification and stalled playback generate accessible OK dialogs instead of remaining in a misleading playing state. Native engine details may be in their original language. If a source changed, inspect it and relocate or reimport it; if only its location changed, use relocation. When the latest position cannot be saved, closing offers an explicit choice to stay open or exit without that last update.

## Updating Bookworm

By default, Bookworm checks for new versions upon startup. This ensures that you get new versions of Bookworm as early as possible. You can disable this default behavior from the application preferences. You can also check for updates manually by clicking the "Check for updates" menu item found under the "Help" menu.

Either way, when a new version is found, Bookworm will ask you if you want to install it. If you click "Yes", the application will download the update bundle and show a dialog indicating the progress of the download. After the update is downloaded, Bookworm will alert you with a message telling you it will restart the application in order to update. Click "OK" to complete the update process.

## Reporting Problems & Issues

As blind developers, our responsibility is to develop applications that provide independence for us and for our fellow blind friends all over the world. If you have found Bookworm useful in any way, please help us make Bookworm better for you and for others. If you encounter an error while using Bookworm, open a new issue with the details of the error at [the issue tracker](https://github.com/blindpandas/bookworm/issues/).

Before submitting a new issue, make sure that you ran Bookworm in debug mode. To turn on debug mode, go to the "Help" menu and click "Restart with debug-mode enabled", then try to reproduce the issue with debug mode enabled. In many cases, when the error happens again with debug mode enabled, a dialog will be shown with the details of that error. You can then copy this information and include it with your problem report.

Some issues can be tricky to reproduce and go away when you restart the program. In this case, it is okay to report the issue without the detailed information from debug mode. Make sure you include as much information as possible about your system and usage scenario.

## News & Updates

To keep yourself updated with the latest news about Bookworm, visit the [Bookworm repository](https://github.com/blindpandas/bookworm/) or the [Bookworm releases page](https://github.com/blindpandas/bookworm/releases).

## License

**Bookworm** is copyright (c) 2026 Blind Pandas and Bookworm contributors. It is licensed under the [GNU General Public License version 2 or later](https://github.com/blindpandas/bookworm/blob/master/LICENSE).
