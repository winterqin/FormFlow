import pdfplumber

with pdfplumber.open('example1.pdf') as pdf:
    for page in pdf.pages:
        # 使用布局分析（尝试不同的x_tolerance和y_tolerance）
        text = page.extract_text(x_tolerance=3, y_tolerance=3)
        print(text)