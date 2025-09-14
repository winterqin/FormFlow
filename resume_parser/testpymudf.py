import fitz  # PyMuPDF

doc = fitz.open('example2.pdf')
text = ""
for page in doc:
    text += page.get_text()
print(text)
doc.close()