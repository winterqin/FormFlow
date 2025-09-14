import pdfplumber

with pdfplumber.open("example1.pdf") as pdf:
    for page in pdf.pages:
        # 关键：启用布局分析
        text = page.extract_text(
            x_tolerance=1,   # 水平合并阈值
            y_tolerance=3,   # 垂直合并阈值
            layout=True       # 启用布局分析（最重要！）
        )
        print(text)