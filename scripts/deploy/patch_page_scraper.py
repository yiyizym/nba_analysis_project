#!/usr/bin/env python3
"""
临时补丁：在 PageScraper.go_to_url 中添加固定等待时间
让 JavaScript 有时间渲染页面
"""

import sys
from pathlib import Path

def patch_page_scraper():
    """修补 page_scraper.py"""

    file_path = Path(__file__).parent.parent.parent / "src/nba_app/webscraping/page_scraper.py"

    print(f"读取文件: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 备份原文件
    backup_path = file_path.with_suffix('.py.backup')
    print(f"备份到: {backup_path}")
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)

    # 检查是否已经打过补丁
    if "time.sleep(5)  # VPS patch:" in content:
        print("✅ 补丁已经应用过了")
        return

    # 查找并替换
    old_code = """            self.app_logger.structured_log( logging.INFO, "Navigation to URL completed successfully", url=url)
            return True"""

    new_code = """            self.app_logger.structured_log( logging.INFO, "Navigation to URL completed successfully", url=url)
            # VPS patch: Add fixed wait time for JavaScript rendering
            time.sleep(5)  # VPS patch: Wait for JavaScript to render page content
            return True"""

    if old_code in content:
        content = content.replace(old_code, new_code)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print("✅ 补丁应用成功！")
        print("")
        print("修改内容:")
        print("  在 go_to_url() 方法中添加了 time.sleep(5)")
        print("  让页面有 5 秒时间执行 JavaScript 和渲染内容")
        print("")
        print("如需恢复原文件:")
        print(f"  cp {backup_path} {file_path}")
    else:
        print("❌ 未找到目标代码，可能文件已被修改")
        print("请手动检查 page_scraper.py 的 go_to_url 方法")
        sys.exit(1)

if __name__ == "__main__":
    print("==========================================")
    print("🔧 PageScraper 补丁程序")
    print("==========================================")
    print("")

    patch_page_scraper()

    print("")
    print("==========================================")
    print("✅ 完成")
    print("==========================================")
