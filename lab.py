from pathlib import Path
from bookworm.structured_text import StructuredInscriptis as Ins

html_string = Path(r"C:\Users\DELL\Downloads\WWI.html").read_text()
i = Ins.from_string(html_string)
