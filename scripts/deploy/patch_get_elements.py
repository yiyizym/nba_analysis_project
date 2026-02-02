#!/usr/bin/env python3
"""
彻底的补丁：修改 get_elements_by_class 使用直接查找
替换 WebDriverWait 为简单的 find_elements
"""

import sys
from pathlib import Path

def patch_get_elements_by_class():
    """修补 page_scraper.py 的 get_elements_by_class 方法"""

    file_path = Path(__file__).parent.parent.parent / "src/nba_app/webscraping/page_scraper.py"

    print(f"读取文件: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 备份原文件
    backup_path = file_path.with_suffix('.py.backup2')
    print(f"备份到: {backup_path}")
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)

    # 检查是否已经打过补丁
    if "# VPS PATCH: Use direct find_elements" in content:
        print("✅ 补丁已经应用过了")
        return

    # 查找并替换 get_elements_by_class 方法中的查找逻辑
    old_code = """        for attempt in range(self.config.max_retries):
            try:
                if parent_element:
                    elements = parent_element.find_elements(By.CLASS_NAME, class_name)
                else:
                    elements = self.wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, class_name)))
                if not elements:
                    self.app_logger.structured_log( logging.INFO, "No elements found",
                                   class_name=class_name, attempt=attempt+1)
                    return None
                self.app_logger.structured_log( logging.INFO, "Elements found",
                               class_name=class_name, element_count=len(elements))
                return elements
            except (TimeoutException, NoSuchElementException, StaleElementReferenceException):
                self.app_logger.structured_log( logging.INFO, "Element not found or stale",
                               class_name=class_name, attempt=attempt+1)"""

    new_code = """        for attempt in range(self.config.max_retries):
            try:
                # VPS PATCH: Use direct find_elements instead of WebDriverWait
                # WebDriverWait.until() seems to have issues on VPS for dynamic content
                if parent_element:
                    elements = parent_element.find_elements(By.CLASS_NAME, class_name)
                else:
                    # Direct find - much more reliable on VPS
                    elements = self.web_driver.find_elements(By.CLASS_NAME, class_name)

                if not elements:
                    self.app_logger.structured_log( logging.INFO, "No elements found",
                                   class_name=class_name, attempt=attempt+1)
                    # Don't return None immediately, let it retry
                    raise NoSuchElementException(f"No elements with class {class_name}")

                self.app_logger.structured_log( logging.INFO, "Elements found",
                               class_name=class_name, element_count=len(elements))
                return elements
            except (TimeoutException, NoSuchElementException, StaleElementReferenceException):
                self.app_logger.structured_log( logging.INFO, "Element not found or stale",
                               class_name=class_name, attempt=attempt+1)"""

    if old_code in content:
        content = content.replace(old_code, new_code)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print("✅ 补丁应用成功！")
        print("")
        print("修改内容:")
        print("  替换 WebDriverWait.until() 为直接的 find_elements()")
        print("  这在 VPS 上更可靠，避免了 WebDriverWait 的超时问题")
        print("")
        print("原理:")
        print("  调试脚本证明直接 find_elements 可以工作")
        print("  但 WebDriverWait.until(EC.presence_of_all_elements_located) 在 VPS 上失败")
        print("  可能是 Selenium 版本或 VPS 环境的特殊问题")
        print("")
        print("如需恢复原文件:")
        print(f"  cp {backup_path} {file_path}")
    else:
        print("❌ 未找到目标代码，可能文件已被修改")
        print("")
        print("尝试查找方法定义...")
        if "def get_elements_by_class" in content:
            print("✅ 找到了 get_elements_by_class 方法")
            print("但是方法体的代码和预期不匹配")
            print("请手动检查文件")
        else:
            print("❌ 连方法定义都找不到")
        sys.exit(1)

if __name__ == "__main__":
    print("==========================================")
    print("🔧 get_elements_by_class 补丁程序")
    print("==========================================")
    print("")

    patch_get_elements_by_class()

    print("")
    print("==========================================")
    print("✅ 完成")
    print("==========================================")
