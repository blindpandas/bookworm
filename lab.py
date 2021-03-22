# coding: utf-8

from hashlib import md5
from pathlib import Path
from tempfile import TemporaryDirectory as TD
from bookworm.vendor.epub_parser import ParseEPUB, ParseMOBI


file = r"E:\Backups\Old PC\Downloads\Hands-On-Machine-Learning-with-Scikit-Learn-and-TensorFlow-Concepts-Tools-and-Techniques-to-Build-Intelligent-Systems.epub"
mobifile = r"C:\Users\DELL\Documents\Eric Ries - The Lean Startup_ How Today's Entrepreneurs Use Continuous Innovation to Create Radically Successful Businesses   (2011, Crown Business).mobi"
md = md5(Path(file).read_bytes()).hexdigest()
mobimd = md5(Path(mobifile).read_bytes()).hexdigest() 
temp = TD()
epub = ParseEPUB(file, temp.name, md)
epub.read_book()
t, c, n = epub.generate_content()
mobi = ParseMOBI(mobifile, temp.name, mobimd)
mobi.read_book()
mt, mc, mn = mobi.generate_content()
