# coding: utf-8

import sys
import os


name = "bookworm"
display_name = "Bookworm"
author = "Musharraf Omer"
author_email = "ibnomer2011@hotmail.com"
version = "0.1-beta"
url = "https://github.com/mush42/bookworm/"
website = "https://mush42.github.io/bookworm/"
copyright = f"Copyright (c) 2019 {author}."
debug = bool(int(os.environ.get("BOOKWORM_DEBUG", 0)))

# About Message
about_msg = f"""
{display_name}
Version: {version}
Website: {website}

{display_name} is an ACCESSIBLEebook reader that enables blind and visually impaired individuals to read ebooks in an easy and accessible manor. It is being developed by {author} with some contributions from the community.


{copyright}
This software is offered to you under the terms of The MIT license.
You can view the license text from the help menu.


THIS SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""
