#!/usr/bin/env python3
"""
报告生成器

支持 Markdown 和 HTML 两种格式
生成代码模块化重构报告
"""

import json
import sys
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path


def generate_markdown_report(analysis_data: Dict) -> str:
    """
    生成 Markdown 格式的重构报告

    Args:
        analysis_data: 分析数据字典

    Returns:
        Markdown 格式的报告字符串
    """
    stats = analysis_data.get('statistics', {})
    critical_files = analysis_data.get('critical_files', [])
    warning_files = analysis_data.get('warning_files', [])

    report = []
    report.append("# 代码模块化重构报告\n")

    report.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # 统计摘要
    report.append("## 📊 统计摘要\n")
    report.append("| 指标 | 数值 |")
    report.append("|--------|------|")
    for key, value in stats.items():
        report.append(f"| {key} | {value} |")
    report.append("")

    report.append("")

    # 重构列表
    report.append("## 📋 重构列表\n")

    if critical_files:
        report.append("### 🚨 关键文件 (≥250 行)\n")
        for i, file_info in enumerate(critical_files, 1):
            path = file_info.get('path', 'N/A')
            lines = file_info.get('lines', 0)
            priority = file_info.get('priority_score', 0)

            report.append(f"#### {i}. {path}\n")
            report.append(f"- **原行数**: {lines} 行")
            report.append(f"- **语言**: {file_info.get('language', 'unknown')}")
            report.append(f"- **优先级评分**: {priority:.1f}\n")

        if warning_files:
        report.append("### ⚠️  警告文件 (130-250 行)\n")
            for i, file_info in enumerate(warning_files, 1):
                path = file_info.get('path', 'N/A')
                lines = file_info.get('lines', 0)
                priority = file_info.get('priority_score', 0)

                report.append(f"#### {i}. {path}\n")
                report.append(f"- **原行数**: {lines} 行")
                report.append(f"- **语言**: {file_info.get('language', 'unknown')}")
                report.append(f"- **优先级评分**: {priority:.1f}\n")

    if not critical_files and not warning_files:
        report.append("✓ 未发现需要重构的文件")

    report.append("\n---\n")
    report.append("## 💡 建议\n")
    report.append("1. 优先重构关键文件（≥250 行）")
    report.append("2. 使用 `code-shorters` 主 Skill 自动调用对应的子 skill")
    report.append("3. 重构后使用 Git 提交代码")
    report.append("\n")

    return '\n'.join(report)


def generate_html_report(analysis_data: Dict) -> str:
    """
    生成 HTML 格式的重构报告

    Args:
        analysis_data: 分析数据字典

    Returns:
        HTML 格式的报告字符串
    """
    stats = analysis_data.get('statistics', {})
    critical_files = analysis_data.get('critical_files', [])
    warning_files = analysis_data.get('warning_files', [])

    html = []

    # HTML 头部
    html.append("<!DOCTYPE html>")
    html.append("<html lang='zh-CN'>")
    html.append("<head>")
    html.append("    <meta charset='UTF-8'>")
    html.append("    <meta name='viewport' content='width=device-width, initial-scale=1.0'>")
    html.append("    <title>代码模块化重构报告</title>")
    html.append("    <style>")
    html.append("        body { font-family: 'Segoe UI', Arial, sans-serif; margin: 40px; background: #f5f5f5; color: #333; }")
    html.append("        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }")
    html.append("        h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 20px; }")
    html.append("        .stats-table { width: 100%; border-collapse: collapse; margin: 20px 0; }")
    html.append("            .stats-table th, .stats-table td { border: 1px solid #ddd; padding: 12px; text-align: left; }")
    html.append("            .stats-table th { background: #3498db; color: white; }")
    html.append("        .file-card { background: #f8f9fa; border-left: 4px solid #3498db; padding: 20px; margin: 15px 0; border-radius: 5px; }")
    html.append("            .file-card h3 { margin-top: 0; color: #2c3e50; }")
    html.append("        .file-info { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin-top: 15px; }")
    html.append("                .file-info div { margin: 5px 0; }")
    html.append("                    .file-info strong { color: #3498db; }")
    html.append("            .badge { display: inline-block; padding: 5px 12px; border-radius: 3px; font-size: 12px; font-weight: bold; margin-right: 10px; }")
    html.append("            .badge.critical { background: #e74c3c; color: white; }")
    html.append("            .badge.warning { background: #f39c12; color: white; }")
    html.append("        .badge.critical { background: #e74c3c; color: white; }")
    html.append("            .badge.warning { background: #f39c12; color: white; }")
    html.append("        .badge.warning { background: #f39c12; color: white; }")
    html.append("    </div>")
    html.append("        </div>")
    html.append("        <hr style='margin: 40px 0; border: none; border-top: 1px solid #eee;'>")
    html.append("        <h2>💡 建议</h2>")
    html.append("        <ul>")
    html.append("            <li>优先重构关键文件（≥250 行）</li>")
    html.append("            <li>使用 `code-shorters` 主 Skill 自动调用对应的子 skill</li>")
    html.append("            <li>重构后使用 Git 提交代码</li>")
    html.append("        </ul>")
    html.append("        <hr style='margin: 40px 0; border: none; border-top: 1px solid #eee;'>")
    html.append("        <p style='text-align: center; color: #27ae60; font-size: 12px; margin: 40px 0;'>由 code-shorters 自动生成</p>")
    html.append("    </div>")
    html.append("</body>")
    html.append("</html>")

    return '\n'.join(html)


def generate_report(analysis_data: Dict, output_format: str = 'markdown') -> str:
    """
    生成报告（根据格式选择）

    Args:
        analysis_data: 分析数据字典
        output_format: 输出格式（markdown 或 html）

    Returns:
        报告字符串
    """
    if output_format.lower() in ['html', 'htm']:
        return generate_html_report(analysis_data)
    else:
        return generate_markdown_report(analysis_data)


def save_report(analysis_data: Dict, output_path: str) -> str:
    """
    保存报告到文件

    Args:
        analysis_data: 分析数据字典
        output_path: 输出文件路径

    Returns:
        保存的文件路径
    """
    from pathlib import Path
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    report_content = generate_report(analysis_data, output_format)
    Path(output_path).write_text(report_content, encoding='utf-8')

    return output_path


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法: python report_generator.py <analysis_json_file> [format]")
        print("\n格式选项:")
        print("  markdown  (默认)")
        print("  html")
        sys.exit(1)

    json_file = sys.argv[1]
    output_format = sys.argv[2] if len(sys.argv) > 2 else 'markdown'

    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            analysis_data = json.load(f)
    except Exception as e:
        print(f"错误：无法读取分析数据: {e}")
        sys.exit(1)

    from datetime import datetime
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = 'reports'
    from pathlib import Path
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    output_path = f"{output_dir}/refactor_report_{timestamp}.{output_format}"
    saved_path = save_report(analysis_data, output_path)

    print(f"✓ 报告已生成: {saved_path}")
    print(f"✓ 格式: {output_format}")
