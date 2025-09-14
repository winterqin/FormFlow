from playwright.sync_api import sync_playwright
import json


def extract_form_fields(url):
    """提取目标页面中的所有表单字段信息"""
    with sync_playwright() as p:
        # 启动浏览器（默认使用 Chromium）
        browser = p.chromium.launch(headless=False)  # 设置为 headless=False 以便调试
        context = browser.new_context()
        page = context.new_page()

        # 导航到目标页面
        page.goto(url)

        # 等待页面加载完成
        page.wait_for_load_state("networkidle")

        # 获取所有可填写的表单元素
        form_elements = page.query_selector_all(
            'input:not([type="hidden"]), select, textarea, [contenteditable="true"]'
        )

        form_fields = []
        for element in form_elements:
            # 获取元素的基本属性
            tag_name = element.evaluate('el => el.tagName.toLowerCase()')
            field_type = element.get_attribute('type') or tag_name
            name = element.get_attribute('name') or element.get_attribute('id') or ''

            # 获取关联标签文本
            label = get_associated_label(page, element)

            # 处理不同类型的字段
            field_info = {
                'selector': get_unique_selector(element),
                'tag': tag_name,
                'type': field_type,
                'name': name,
                'label': label,
                'required': is_element_required(element),
                'placeholder': element.get_attribute('placeholder') or '',
            }

            # 处理特殊字段类型
            if tag_name == 'select':
                field_info['options'] = get_select_options(element)
            elif field_type == 'radio' or field_type == 'checkbox':
                field_info['options'] = get_radio_checkbox_options(page, element)

            form_fields.append(field_info)

        # 关闭浏览器
        browser.close()
        return form_fields


def get_associated_label(page, element):
    """获取与表单元素关联的标签文本"""
    # 方法1: 通过for属性关联
    element_id = element.get_attribute('id')
    if element_id:
        label = page.query_selector(f'label[for="{element_id}"]')
        if label:
            return label.inner_text().strip()

    # 方法2: 查找包裹元素的label标签
    label = element.query_selector('xpath=ancestor::label')
    if label:
        return label.inner_text().strip()

    # 方法3: 查找相邻文本
    text_content = element.evaluate('''el => {
        // 获取前一个文本节点
        let prevText = '';
        let prevSibling = el.previousSibling;
        while (prevSibling) {
            if (prevSibling.nodeType === 3) {
                prevText = prevSibling.textContent.trim() + prevText;
            } else if (prevSibling.nodeType === 1) {
                break;
            }
            prevSibling = prevSibling.previousSibling;
        }

        // 获取后一个文本节点
        let nextText = '';
        let nextSibling = el.nextSibling;
        while (nextSibling) {
            if (nextSibling.nodeType === 3) {
                nextText += nextSibling.textContent.trim();
            } else if (nextSibling.nodeType === 1) {
                break;
            }
            nextSibling = nextSibling.nextSibling;
        }

        // 组合结果
        return (prevText + ' ' + nextText).trim();
    }''')

    if text_content:
        return text_content

    # 方法4: 使用aria-label属性
    return element.get_attribute('aria-label') or ''


def get_unique_selector(element):
    """生成元素的唯一CSS选择器"""
    return element.evaluate('''el => {
        if (el.id) return `#${el.id}`;

        let path = [];
        while (el && el.nodeType === 1) {
            let selector = el.nodeName.toLowerCase();

            if (el.id) {
                selector = `#${el.id}`;
                path.unshift(selector);
                break;
            } else {
                let sib = el, nth = 1;
                while (sib = sib.previousElementSibling) {
                    if (sib.nodeName.toLowerCase() === selector) nth++;
                }

                if (nth !== 1) selector += `:nth-of-type(${nth})`;
                else {
                    let siblings = el.parentNode.children;
                    if (siblings.length === 1) selector += ':only-child';
                }
            }
            path.unshift(selector);
            el = el.parentNode;
        }
        return path.join(' > ');
    }''')


def is_element_required(element):
    """检查元素是否为必填项"""
    required = element.evaluate('''el => {
                                if (el.hasAttribute("required"))
    return true;
    if (el.ariaRequired === "true") return true;

    // 检查父元素是否有必填提示
    const
    parent = el.closest(".required, [data-required]");
    if (parent) return true;

    return false;

    }''')
    return required


def get_select_options(select_element):
    """获取下拉选择框的选项"""
    return select_element.evaluate('''el => {
        return Array.from(el.options).map(option => ({
            value: option.value,
            text: option.textContent.trim(),
            selected: option.selected
        }));
    }''')


def get_radio_checkbox_options(page, element):
    """获取单选/复选框的选项组"""
    # 获取选项组的名称
    name = element.get_attribute('name')
    if not name:
        return []

    # 查找同一组的其他元素
    options = page.query_selector_all(f'input[type="{element.get_attribute("type")}"][name="{name}"]')

    return [{
        'value': option.get_attribute('value') or '',
        'text': get_associated_label(page, option) or option.get_attribute('aria-label') or '',
        'selected': option.is_checked()
    } for option in options]


if __name__ == "__main__":
    # 示例使用 - 替换为你的简历填写页面URL
    resume_form_url = "https://httpbin.org/forms/post"

    # 提取表单信息
    form_data = extract_form_fields(resume_form_url)

    # 保存为JSON文件（方便后续使用）
    with open('resume_form_structure.json', 'w', encoding='utf-8') as f:
        json.dump(form_data, f, ensure_ascii=False, indent=2)

    print(f"成功提取 {len(form_data)} 个表单字段")
    print("表单结构已保存至 resume_form_structure.json")