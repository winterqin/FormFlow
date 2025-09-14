import PyPDF2

with open('example.pdf', 'rb') as file:
    reader = PyPDF2.PdfReader(file)
    for page in reader.pages:
        text = page.extract_text()
        print(text)

