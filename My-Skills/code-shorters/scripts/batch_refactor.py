#!/usr/bin/env python3
"""
批处理重构调度器（方案 B：自动串行模式）

按照优先级顺序，自动调用对应的语言专项子skill。
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Any


# 子 Skill 名称映射（相对路径调用）
SUBSKILL_ROUTES = {
    'rust': 'rust-shorter',
    'python': 'python-shorter',
    'cpp': 'cpp-shorter',
    'js': 'js-shorter'
    'md': 'md-shorter'
}


def invoke_subskill(skill_name: str, file_path: str) -> Dict[str, Any]:
    """
    调用对应的语言子skill

    Args:
        skill_name: 子 Skill 名称（如 rust-shorter）
        file_path: 需要重构的文件路径

    Returns:
        重构结果字典
    """
    result = {
        'file_path': file_path,
        'skill_name': skill_name,
        'status': 'pending',
        'message': f'调用子skill: {skill_name} 重构 {file_path}...'
    }

    print(f"→ 调用 {skill_name} 重构 {Path(file_path).name}...")

    return result


def batch_refactor_critical_files(critical_files: List[Dict]) -> List[Dict[str, Any]]:
    """
    批量重构 critical_files（按优先级顺序）

    Args:
        critical_files: 需要重构的文件列表

    Returns:
        重构结果列表
    """
    results = []

    # 按 priority_score 降序排列
    sorted_files = sorted(critical_files, key=lambda x: x.get('priority_score', 0), reverse=True)

    print(f"\n开始批量重构 {len(sorted_files)} 个关键文件...\n")

    for i, file_info in enumerate(sorted_files, 1):
        file_path = file_info.get('path', '')
        language = file_info.get('language', 'unknown')

        # 路由到对应的子skill
        skill_name = SUBSKILL_ROUTES.get(language)

        if not skill_name:
            print(f"⚠️  跳过不支持的文件: {file_path} (语言: {language})")
            results.append({
                'index': i,
                'file_path': file_path,
                'language': language,
                'status': 'skipped',
                'message': f'不支持的语言: {language}'
            })
            continue

        # 调用子skill
        result = invoke_subskill(skill_name, file_path)
        result['index'] = i
        result['language'] = language
        result['original_lines'] = file_info.get('lines', 0)
        results.append(result)

        # 模拟延迟
        import time
        time.sleep(0.1)

    return results


def batch_refactor_warning_files(warning_files: List[Dict]) -> List[Dict[str, Any]]:
    """
    批量重构 warning_files（可选）

    Args:
        warning_files: 需要重构的文件列表

    Returns:
        重构结果列表
    """
    results = []

    if not warning_files:
        return results

    print(f"\n开始批量重构 {len(warning_files)} 个警告文件...\n")

    for i, file_info in enumerate(warning_files, 1):
        file_path = file_info.get('path', '')
        language = file_info.get('language', 'unknown')

        # 路由到对应的子skill
        skill_name = SUBSKILL_ROUTES.get(language)

        if not skill_name:
            print(f"⚠️  跳过不支持的文件: {file_path} (语言: {language})")
            continue

        # 调用子skill
        result = invoke_subskill(skill_name, file_path)
        result['index'] = i
        result['language'] = language
        result['original_lines'] = file_info.get('lines', 0)
        results.append(result)

        # 模拟延迟
        import time
        time.sleep(0.1)

    return results


def load_analysis_report(json_path: str) -> Dict[str, Any]:
    """
    加载主分析器生成的报告

    Args:
        json_path: JSON 报告文件路径

    Returns:
        分析数据字典
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)
    except Exception as e:
        print(f"错误：无法加载分析报告: {e}")
        return {}


def update_analysis_with_refactor_results(analysis_data: Dict, refactor_results: List[Dict]) -> Dict[str, Any]:
    """
    用重构结果更新分析报告

    Args:
        analysis_data: 原始分析数据
        refactor_results: 重构结果列表

    Returns:
        更新后的分析数据
    """
    updated_data = analysis_data.copy()

    # 汇总重构数量
    total_refactored = len(refactor_results)

    updated_data['statistics']['total_files'] = analysis_data['statistics'].get('total_files', 0)
    updated_data['statistics']['refactored'] = total_refactored

    # 更新统计信息
    updated_data['statistics']['success_count'] = sum(1 for r in refactor_results if r.get('status') == 'success')
    updated_data['statistics']['failed_count'] = sum(1 for r in refactor_results if r.get('status') == 'failed')

    # 添加重构结果摘要
    updated_data['refactor_summary'] = []

    for result in refactor_results:
        if result.get('status') == 'success':
            updated_data['refactor_summary'].append(f"✓ {result['file_path']} 重构成功 ({result['language'])")
        elif result.get('status') == 'skipped':
            updated_data['refactor_summary'].append(f"⚠️  {result['file_path']} 跳过（{result['message']}")

    return updated_data


def save_refactor_results(refactor_results: List[Dict], output_path: str) -> str:
    """
    保存批处理结果

    Args:
        refactor_results: 重构结果列表
        output_path: 输出文件路径

    Returns:
        保存的文件路径
    """
    from pathlib import Path
    from datetime import datetime

    # 确保输出目录存在
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    file_path = f"{output_path}/batch_refactor_{timestamp}.json"

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(refactor_results, f, indent=2, ensure_ascii=False)

    print(f"✓ 批处理结果已保存: {file_path}")

    return file_path


def generate_final_report(analysis_data: Dict, refactor_results: List[Dict]) -> str:
    """
    生成最终重构报告

    Args:
        analysis_data: 分析数据（含重构结果）
        output_format: 输出格式（markdown 或 html）

    Returns:
        报告字符串
    """
    if output_format.lower() in ['html', 'htm']:
        return generate_html_report(analysis_data, refactor_results)
    else:
        return generate_markdown_report(analysis_data, refactor_results)


def generate_markdown_report(analysis_data: Dict, refactor_results: List[Dict]) -> str:
    """
    生成 Markdown 格式的报告

    Args:
        analysis_data: 分析数据
        refactor_results: 重构结果列表

    Returns:
        Markdown 报告字符串
    """
    lines = []

    # 标题
    lines.append("# 代码模块化重构报告")
    lines.append("")

    # 时间戳
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    lines.append(f"**生成时间**: {timestamp}")

    # 统计摘要
    stats = analysis_data.get('statistics', {})
    lines.append("## 📊 统计摘要\n")
    lines.append("| 指标 | 数值 |")
    lines.append("|--------|------|")
    for key, value in stats.items():
        lines.append(f"| {key} | {value} |")
    lines.append("")

    lines.append("")

    # 重构列表
    refactored_files = [r for r in refactor_results if r.get('status') == 'success']
    skipped_files = [r for r in refactor_results if r.get('status') == 'skipped']

    if refactored_files:
        lines.append("### ✅ 已重构文件\n")
        for i, result in enumerate(refactored_files, 1):
            lines.append(f"{i+1}. {result['file_path']} ({result['language']})")
        lines.append(f"   - 原行数: {result['original_lines']} → 重构完成")
        lines.append(f"   - 状态: {result.get('message']}")

    if skipped_files:
        lines.append("### ⚠️ 跳过文件\n")
        for i, result in enumerate(skipped_files, 1):
            lines.append(f"{i+1}. {result['file_path']}")
            lines.append(f"   - 原因: {result.get('message')}")

    if not refactored_files and not skipped_files:
        lines.append("✓ 未发现需要重构的文件")

    lines.append("\n---")

    # Git 提交信息
    if analysis_data.get('refactor_summary'):
        lines.append("## 💾 Git 提交信息\n")
        for summary_item in analysis_data.get('refactor_summary', []):
            lines.append(f"- {summary_item}")

    lines.append("\n" + "="*70)
    lines.append("## 使用建议\n")
    lines.append("1. 优先重构关键文件（≥250 行）")
        lines.append("2. 使用 `code-shorters` 主 Skill 自动调用子 skill")
        lines.append("3. 重构后使用 Git 提交代码")
        lines.append("4. 查看重构报告")

    lines.append("\n---")

    return '\n'.join(lines)


def generate_html_report(analysis_data: Dict, refactor_results: List[Dict]) -> str:
    """
    生成 HTML 格式的报告

    Args:
        analysis_data: 分析数据
        refactor_results: 重构结果列表

    Returns:
        HTML 报告字符串
    """
    html = []

    # HTML 头部
    html.append("<!DOCTYPE html>")
    html.append("<html lang='zh-CN'>")
    html.append("<head>")
    html.append("    <meta charset='UTF-8'>")
    html.append("    <meta name='viewport' content='width=device-width, initial-scale=1.0'>")

    # 样式
    html.append("    <style>")
    html.append("        body { font-family: 'Segoe UI', Arial, sans-serif; margin: 40px; background: #f5f5f5; color: #333; }")
    html.append("            .container { max-width: 1200px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }")
    html.append("        h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 20px; }")
    html.append("        .stats-table { width: 100%; border-collapse: collapse; margin: 20px 0; }")
    html.append("            .stats-table th, .stats-table td { border: 1px solid #ddd; padding: 12px; text-align: left; }")
    html.append("            .stats-table th { background: #3498db; color: white; }")
    html.append("        .file-card { background: #f8f9fa; border-left: 4px solid #3498db; padding: 20px; margin: 15px 0; border-radius: 5px; }")
    html.append("            .file-card h3 { margin-top: 0; color: #2c3e50; font-size: 18px; }")
    html.append("            .file-info { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin-top: 15px; }")
    html.append("                .file-info div { margin: 5px 0; }")
    html.append("                    .file-info strong { color: #3498db; }")
    html.append("            .badge { display: inline-block; padding: 5px 12px; border-radius: 3px; font-size: 12px; font-weight: bold; margin-right: 10px; }")
    html.append("        .badge.success { background: #27ae60; color: white; }")
    html.append("        .badge.warning { background: #f39c12; color: white; }")
    html.append("        .badge.critical { background: #e74c3c; color: white; }")
    html.append("    </div>")
    html.append("        </div>")
    html.append("        <hr style='margin: 40px 0; border: none; border-top: 1px solid #eee;'>")
    html.append("        <p style='text-align: center; color: #27ae60; font-size: 14px; margin: 40px 0;'>✓ 批处理完成！</p>")
    html.append("    </body>")
    html.append("</html>")

    return '\n'.join(html)


def main():
    """主函数：加载分析报告并生成最终报告"""
    if len(sys.argv) < 2:
        print("用法: python batch_refactor.py <analysis_json_file> [format]")
        print("\n格式选项:")
        print("  markdown (默认)")
        print("  html")
        print("\n示例:")
        print("  python batch_refactor.py reports/analysis_YYYYMMDD_HHMMSS.json markdown")
        print("  python batch_refactor.py reports/analysis_YYYYMMDD_HHMMSS.html")
        sys.exit(1)

    analysis_file = sys.argv[1]
    output_format = sys.argv[2] if len(sys.argv) > 2 else 'markdown'

    # 加载分析报告
    analysis_data = load_analysis_report(analysis_file)

    # 如果没有重构结果（测试用）
    refactor_results = []

    # 生成最终报告
    report = generate_final_report(analysis_data, refactor_results, output_format)

    print(report)

    # 保存结果（如果重构结果不为空）
    if refactor_results:
        saved_path = save_refactor_results(refactor_results, 'reports/batch_refactor_results.json')
        print(f"\n✓ 批处理结果已保存: {saved_path}")