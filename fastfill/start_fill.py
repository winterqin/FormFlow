from playwright.sync_api import sync_playwright
import time
from PIL import Image, ImageDraw, ImageFont
import os
import json

# 简历数据（示例）
resume_data = {
    "Customer name:": "John Doe",
    "Telephone:": "555-123-4567",
    "E-mail address:": "john.doe@example.com",
    "size": "Medium",
    "topping": ["Extra Cheese", "Onion"],
    "Preferred delivery time:": "18:00",
    "Delivery instructions:": "Leave at the front door"
}


def fill_form_with_visualization(form_fields, form_data):
    """使用 Playwright 直接操作元素的表单填写功能"""
    with sync_playwright() as p:
        # 启动浏览器（显示模式）
        browser = p.chromium.launch(headless=False, slow_mo=300)
        context = browser.new_context(viewport={'width': 1280, 'height': 800})
        page = context.new_page()

        # 导航到表单页面
        page.goto('https://httpbin.org/forms/post')

        # 创建可视化记录目录
        os.makedirs('form_fill_visualization', exist_ok=True)

        # 记录操作步骤
        operation_steps = []

        # 按表单结构顺序填写
        for index, field in enumerate(form_fields):
            field_label = field['label']
            current_step = {
                "step": index + 1,
                "field": field_label,
                "action": "",
                "screenshots": []
            }

            try:
                # 高亮当前元素并截图
                highlight_element(page, field['selector'])
                time.sleep(0.3)

                # 捕获操作前截图
                before_screenshot = f'form_fill_visualization/step_{index:02d}_{field_label.replace(":", "")}_before.png'
                page.screenshot(path=before_screenshot)
                current_step["screenshots"].append(before_screenshot)

                # 检查是否需要填写此字段
                if should_skip_field(field, form_data):
                    print(f"⏩ 跳过字段: {field_label}")
                    current_step["action"] = "Skipped"
                    operation_steps.append(current_step)
                    continue

                # 获取字段值
                value = get_field_value(field, form_data)

                # 执行填写操作
                action_result = fill_field(page, field, value)
                print(f"✅ {action_result}")
                current_step["action"] = action_result

                # 捕获操作后截图
                after_screenshot = before_screenshot.replace('_before.png', '_after.png')
                page.screenshot(path=after_screenshot)
                current_step["screenshots"].append(after_screenshot)

                # 添加操作步骤
                operation_steps.append(current_step)

            except Exception as e:
                print(f"❌ 填写失败: {field_label} | 错误: {str(e)}")
                current_step["action"] = f"Error: {str(e)}"
                current_step["screenshots"].append(before_screenshot)
                operation_steps.append(current_step)

        # 提交表单
        print("🚀 提交表单...")
        page.click("input[type='submit']")
        time.sleep(2)
        submit_screenshot = 'form_fill_visualization/submitted.png'
        page.screenshot(path=submit_screenshot)

        # 生成可视化报告
        generate_visual_report(operation_steps, submit_screenshot)

        # 关闭浏览器
        browser.close()
        print("✅ 表单填写完成！")
        print(f"📊 可视化报告已生成: form_fill_visualization/report.html")


def should_skip_field(field, form_data):
    """判断是否需要跳过此字段"""
    field_label = field['label']
    field_name = field.get('name', '')

    # 检查字段是否在简历数据中
    if field_label not in form_data and field_name not in form_data:
        return True

    # 检查单选/复选框是否有匹配项
    if field['type'] in ['radio', 'checkbox']:
        value = form_data.get(field_label) or form_data.get(field_name)
        if not any(opt['text'] == value or opt['value'] == value for opt in field['options']):
            return True

    return False


def get_field_value(field, form_data):
    """获取字段对应的值"""
    field_label = field['label']
    field_name = field.get('name', '')

    # 优先使用标签匹配
    if field_label in form_data:
        return form_data[field_label]

    # 其次使用字段名匹配
    if field_name in form_data:
        return form_data[field_name]

    return ""


def highlight_element(page, selector):
    """使用 Playwright 直接高亮元素（不依赖 pyautogui）"""
    # 添加红色边框
    page.eval_on_selector(selector, '''el => {
        el.style.border = '3px solid red';
        el.style.boxShadow = '0 0 10px rgba(255, 0, 0, 0.5)';
    }''')

    # 滚动到元素位置
    page.evaluate('''(selector) => {
        const element = document.querySelector(selector);
        if (element) {
            element.scrollIntoView({behavior: 'smooth', block: 'center'});
        }
    }''', selector)


def fill_field(page, field, value):
    """根据字段类型填写内容"""
    selector = field['selector']

    if field['type'] in ['radio', 'checkbox']:
        return handle_radio_checkbox(page, field, value)

    elif field['tag'] == 'select':
        return handle_select(page, field, value)

    else:
        # 输入框和文本域
        page.fill(selector, str(value))
        return f"填写: {field['label']} = {value}"


def handle_radio_checkbox(page, field, value):
    """处理单选按钮和复选框"""
    field_label = field['label']

    if isinstance(value, list):
        # 多选情况（复选框）
        selected_count = 0
        for val in value:
            option = next((opt for opt in field['options'] if opt['text'] == val or opt['value'] == val), None)
            if option:
                option_selector = f"{field['selector']}[value='{option['value']}']"
                page.check(option_selector)
                selected_count += 1
        return f"选择 {selected_count} 项: {field_label} = {', '.join(value)}"
    else:
        # 单选情况
        option = next((opt for opt in field['options'] if opt['text'] == value or opt['value'] == value), None)
        if option:
            option_selector = f"{field['selector']}[value='{option['value']}']"
            page.check(option_selector)
            return f"选择: {field_label} = {option['text']}"
        else:
            raise ValueError(f"无匹配选项: {value}")


def handle_select(page, field, value):
    """处理下拉选择框"""
    option = next((opt for opt in field['options'] if opt['text'] == value or opt['value'] == value), None)
    if option:
        page.select_option(field['selector'], value=option['value'])
        return f"选择下拉: {field['label']} = {option['text']}"
    else:
        # 尝试部分匹配
        for opt in field['options']:
            if value.lower() in opt['text'].lower():
                page.select_option(field['selector'], value=opt['value'])
                return f"选择下拉(近似): {field['label']} = {opt['text']}"
        # 默认选择第一项
        first_option = field['options'][0]['value']
        page.select_option(field['selector'], value=first_option)
        return f"选择下拉(默认): {field['label']} = {field['options'][0]['text']}"


def generate_visual_report(operation_steps, final_screenshot):
    """生成可视化报告HTML"""
    html_content = """
    <html>
    <head>
        <title>表单填写过程可视化报告</title>
        <style>
            :root {
                --primary-color: #4361ee;
                --secondary-color: #3f37c9;
                --success-color: #4cc9f0;
                --error-color: #f72585;
                --warning-color: #ff9e00;
                --bg-color: #f8f9fa;
                --text-color: #212529;
            }

            body {
                font-family: 'Segoe UI', system-ui, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: var(--bg-color);
                color: var(--text-color);
            }

            .container {
                max-width: 1200px;
                margin: 0 auto;
                background-color: white;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                padding: 30px;
            }

            header {
                text-align: center;
                margin-bottom: 30px;
                border-bottom: 2px solid var(--primary-color);
                padding-bottom: 20px;
            }

            h1 {
                color: var(--primary-color);
                font-size: 2.5rem;
                margin-bottom: 10px;
            }

            .stats {
                display: flex;
                justify-content: center;
                gap: 20px;
                margin-top: 20px;
                flex-wrap: wrap;
            }

            .stat-card {
                background-color: var(--primary-color);
                color: white;
                border-radius: 8px;
                padding: 15px 25px;
                text-align: center;
                min-width: 150px;
            }

            .stat-card.success {
                background-color: var(--success-color);
            }

            .stat-card.error {
                background-color: var(--error-color);
            }

            .stat-number {
                font-size: 2rem;
                font-weight: bold;
            }

            .step {
                margin-bottom: 40px;
                border-bottom: 1px solid #eee;
                padding-bottom: 20px;
            }

            .step-header {
                background-color: var(--primary-color);
                color: white;
                padding: 12px 15px;
                border-radius: 5px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }

            .step-info {
                display: flex;
                gap: 15px;
                align-items: center;
            }

            .step-number {
                background-color: white;
                color: var(--primary-color);
                width: 32px;
                height: 32px;
                border-radius: 50%;
                display: flex;
                justify-content: center;
                align-items: center;
                font-weight: bold;
            }

            .field-name {
                font-weight: bold;
                font-size: 1.2rem;
            }

            .action-info {
                background-color: var(--bg-color);
                padding: 8px 15px;
                border-radius: 5px;
                font-family: monospace;
            }

            .images {
                display: flex;
                gap: 20px;
                margin-top: 15px;
                flex-wrap: wrap;
            }

            .image-container {
                flex: 1;
                min-width: 300px;
            }

            .image-container img {
                width: 100%;
                border: 1px solid #ddd;
                border-radius: 5px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            }

            .caption {
                font-size: 0.9rem;
                color: #6c757d;
                margin-top: 5px;
                text-align: center;
            }

            .final-result {
                margin-top: 40px;
                background-color: #e8f4f8;
                padding: 20px;
                border-radius: 8px;
            }

            @media (max-width: 768px) {
                .images {
                    flex-direction: column;
                }

                .image-container {
                    min-width: 100%;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>表单填写过程可视化报告</h1>
                <p>基于Playwright自动化操作生成</p>

                <div class="stats">
                    <div class="stat-card">
                        <div class="stat-label">总步骤</div>
                        <div class="stat-number">$total_steps$</div>
                    </div>
                    <div class="stat-card success">
                        <div class="stat-label">成功步骤</div>
                        <div class="stat-number">$success_steps$</div>
                    </div>
                    <div class="stat-card error">
                        <div class="stat-label">失败步骤</div>
                        <div class="stat-number">$error_steps$</div>
                    </div>
                </div>
            </header>

            <main>
                <h2>详细操作步骤</h2>
                $step_content$

                <div class="final-result">
                    <h2>最终结果</h2>
                    <div class="image-container">

                        <div class="caption">表单提交后页面</div>
                    </div>
                </div>
            </main>
        </div>
    </body>
    </html>
    """

    # 计算统计信息
    total_steps = len(operation_steps)
    success_steps = sum(1 for step in operation_steps if not step['action'].startswith('Error'))
    error_steps = total_steps - success_steps

    # 替换统计信息
    html_content = html_content.replace('$total_steps$', str(total_steps))
    html_content = html_content.replace('$success_steps$', str(success_steps))
    html_content = html_content.replace('$error_steps$', str(error_steps))

    # 生成步骤内容
    step_content = ""
    for step in operation_steps:
        step_html = f"""
        <div class="step">
            <div class="step-header">
                <div class="step-info">
                    <div class="step-number">{step['step']}</div>
                    <div class="field-name">{step['field']}</div>
                </div>
                <div class="action-info">{step['action']}</div>
            </div>
            <div class="images">
        """

        for i, screenshot in enumerate(step['screenshots']):
            caption = "操作前" if i == 0 and len(step['screenshots']) > 1 else "操作后"
            step_html += f"""
                <div class="image-container">

                    <div class="caption">{caption}</div>
                </div>
            """

        step_html += "</div></div>"
        step_content += step_html

    # 替换步骤内容和最终截图
    html_content = html_content.replace('$step_content$', step_content)
    html_content = html_content.replace('$final_screenshot$', final_screenshot)

    # 保存报告
    with open("form_fill_visualization/report.html", "w", encoding="utf-8") as f:
        f.write(html_content)


# 使用示例
if __name__ == "__main__":
    # 加载表单结构（您提供的JSON）
    form_fields = [...]  # 这里放您获取的表单结构数据

    # 执行表单填写
    fill_form_with_visualization(form_fields, resume_data)