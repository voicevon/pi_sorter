#!/usr/bin/env python3
"""
Pi Sorter - 测试覆盖率分析器
分析测试覆盖率并生成报告
"""

import os
import sys
import json
import subprocess
from typing import Dict, Any, List, Optional
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '../src/external'))


class CoverageAnalyzer:
    """测试覆盖率分析器"""
    
    def __init__(self, source_dir: str = "src/external", test_dir: str = "tests"):
        """初始化覆盖率分析器"""
        self.source_dir = source_dir
        self.test_dir = test_dir
        self.coverage_data = {}
        self.analysis_results = {}
        
    def run_coverage_analysis(self, output_file: str = "coverage_report.json") -> bool:
        """运行覆盖率分析"""
        try:
            # 检查是否安装了coverage工具
            result = subprocess.run(['coverage', '--version'], capture_output=True, text=True)
            if result.returncode != 0:
                print("❌ coverage工具未安装，请先安装: pip install coverage")
                return False
                
            print("🔍 运行覆盖率分析...")
            
            # 运行覆盖率测试
            commands = [
                # 清理之前的覆盖率数据
                ['coverage', 'erase'],
                
                # 运行测试并收集覆盖率数据
                ['coverage', 'run', '--source', self.source_dir, '-m', 'pytest', self.test_dir, '-v'],
                
                # 生成覆盖率报告
                ['coverage', 'json', '-o', output_file],
                
                # 生成HTML报告
                ['coverage', 'html', '-d', 'htmlcov']
            ]
            
            for cmd in commands:
                print(f"执行命令: {' '.join(cmd)}")
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0 and 'html' not in cmd[1]:  # HTML生成失败不是致命错误
                    print(f"❌ 命令执行失败: {result.stderr}")
                    return False
                    
            # 读取覆盖率数据
            with open(output_file, 'r', encoding='utf-8') as f:
                self.coverage_data = json.load(f)
                
            print(f"✅ 覆盖率分析完成，报告保存到: {output_file}")
            return True
            
        except Exception as e:
            print(f"❌ 覆盖率分析失败: {e}")
            return False
            
    def analyze_coverage_results(self) -> Dict[str, Any]:
        """分析覆盖率结果"""
        if not self.coverage_data:
            print("❌ 没有覆盖率数据可分析")
            return {}
            
        try:
            results = {
                'summary': {
                    'total_files': len(self.coverage_data.get('files', {})),
                    'total_lines': 0,
                    'covered_lines': 0,
                    'missing_lines': 0,
                    'excluded_lines': 0,
                    'coverage_percentage': 0.0
                },
                'files': {},
                'modules': {},
                'recommendations': []
            }
            
            # 分析每个文件
            for filename, file_data in self.coverage_data.get('files', {}).items():
                summary_data = file_data.get('summary', {})
                
                file_info = {
                    'lines': summary_data.get('num_statements', 0),
                    'covered': summary_data.get('covered_lines', 0),
                    'missing': summary_data.get('missing_lines', 0),
                    'excluded': summary_data.get('excluded_lines', 0),
                    'coverage_percentage': summary_data.get('percent_covered', 0.0)
                }
                
                results['files'][filename] = file_info
                
                # 更新总计
                results['summary']['total_lines'] += file_info['lines']
                results['summary']['covered_lines'] += file_info['covered']
                results['summary']['missing_lines'] += file_info['missing']
                results['summary']['excluded_lines'] += file_info['excluded']
                
            # 计算总体覆盖率
            if results['summary']['total_lines'] > 0:
                results['summary']['coverage_percentage'] = (
                    results['summary']['covered_lines'] / results['summary']['total_lines'] * 100
                )
                
            # 按模块分组
            for filename, file_info in results['files'].items():
                module_name = self._get_module_name(filename)
                if module_name not in results['modules']:
                    results['modules'][module_name] = {
                        'files': [],
                        'total_lines': 0,
                        'covered_lines': 0,
                        'coverage_percentage': 0.0
                    }
                    
                results['modules'][module_name]['files'].append(filename)
                results['modules'][module_name]['total_lines'] += file_info['lines']
                results['modules'][module_name]['covered_lines'] += file_info['covered']
                
            # 计算模块覆盖率
            for module, data in results['modules'].items():
                if data['total_lines'] > 0:
                    data['coverage_percentage'] = (
                        data['covered_lines'] / data['total_lines'] * 100
                    )
                    
            # 生成建议
            results['recommendations'] = self._generate_coverage_recommendations(results)
            
            self.analysis_results = results
            return results
            
        except Exception as e:
            print(f"❌ 覆盖率结果分析失败: {e}")
            return {}
            
    def _get_module_name(self, filename: str) -> str:
        """获取模块名称"""
        basename = os.path.basename(filename)
        if '_' in basename:
            return basename.split('_')[0]
        return basename.replace('.py', '')
        
    def _generate_coverage_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """生成覆盖率改进建议"""
        recommendations = []
        
        overall_coverage = results['summary']['coverage_percentage']
        
        # 总体覆盖率建议
        if overall_coverage < 50:
            recommendations.append("🔴 总体覆盖率较低，建议增加更多单元测试")
        elif overall_coverage < 70:
            recommendations.append("🟡 总体覆盖率中等，建议完善测试覆盖")
        elif overall_coverage < 85:
            recommendations.append("🟢 总体覆盖率良好，可以进一步优化关键模块")
        else:
            recommendations.append("✅ 总体覆盖率优秀，继续保持")
            
        # 模块级别建议
        for module, data in results['modules'].items():
            module_coverage = data['coverage_percentage']
            
            if module_coverage < 30:
                recommendations.append(f"🔴 模块 {module} 覆盖率过低 ({module_coverage:.1f}%)，需要重点测试")
            elif module_coverage < 60:
                recommendations.append(f"🟡 模块 {module} 覆盖率偏低 ({module_coverage:.1f}%)，建议增加测试")
                
        # 文件级别建议
        low_coverage_files = []
        for filename, file_info in results['files'].items():
            if file_info['coverage_percentage'] < 50 and file_info['lines'] > 10:
                low_coverage_files.append((filename, file_info['coverage_percentage']))
                
        if low_coverage_files:
            recommendations.append(f"🔍 发现 {len(low_coverage_files)} 个低覆盖率文件，建议优先处理")
            
        # 具体改进建议
        if overall_coverage < 80:
            recommendations.extend([
                "💡 建议为所有公共API编写单元测试",
                "💡 增加边界条件和异常处理的测试",
                "💡 使用模拟对象(Mock)来隔离外部依赖",
                "💡 考虑使用参数化测试减少重复代码"
            ])
            
        return recommendations
        
    def print_coverage_summary(self):
        """打印覆盖率摘要"""
        if not self.analysis_results:
            print("❌ 没有分析结果可显示")
            return
            
        results = self.analysis_results
        
        print("\n" + "="*60)
        print("📊 测试覆盖率分析报告")
        print("="*60)
        
        # 总体摘要
        summary = results['summary']
        print(f"总体覆盖率: {summary['coverage_percentage']:.1f}%")
        print(f"总文件数: {summary['total_files']}")
        print(f"总代码行: {summary['total_lines']}")
        print(f"覆盖行数: {summary['covered_lines']}")
        print(f"未覆盖行数: {summary['missing_lines']}")
        print(f"排除行数: {summary['excluded_lines']}")
        
        print("\n" + "-"*40)
        print("📁 模块覆盖率")
        print("-"*40)
        
        # 模块覆盖率
        for module, data in sorted(results['modules'].items(), key=lambda x: x[1]['coverage_percentage'], reverse=True):
            coverage = data['coverage_percentage']
            status_icon = "🔴" if coverage < 50 else "🟡" if coverage < 80 else "🟢"
            print(f"{status_icon} {module:<20} {coverage:>6.1f}% ({data['covered_lines']}/{data['total_lines']})")
            
        print("\n" + "-"*40)
        print("🔍 文件覆盖率详情")
        print("-"*40)
        
        # 文件覆盖率（只显示覆盖率<80%的文件）
        low_coverage_files = [
            (filename, data) for filename, data in results['files'].items()
            if data['coverage_percentage'] < 80
        ]
        
        for filename, data in sorted(low_coverage_files, key=lambda x: x[1]['coverage_percentage']):
            coverage = data['coverage_percentage']
            status_icon = "🔴" if coverage < 50 else "🟡"
            basename = os.path.basename(filename)
            print(f"{status_icon} {basename:<30} {coverage:>6.1f}% ({data['covered']}/{data['lines']})")
            
        print("\n" + "-"*40)
        print("💡 改进建议")
        print("-"*40)
        
        for recommendation in results['recommendations']:
            print(f"• {recommendation}")
            
        print("\n" + "="*60)
        
    def generate_html_report(self, output_file: str = "coverage_analysis_report.html"):
        """生成HTML报告"""
        if not self.analysis_results:
            print("❌ 没有分析结果可生成HTML报告")
            return False
            
        try:
            html_content = self._create_html_report()
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
                
            print(f"🌐 HTML报告已生成: {output_file}")
            return True
            
        except Exception as e:
            print(f"❌ HTML报告生成失败: {e}")
            return False
            
    def _create_html_report(self) -> str:
        """创建HTML报告内容"""
        results = self.analysis_results
        
        # 生成CSS样式
        css_style = """
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 20px;
                background-color: #f5f5f5;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                background-color: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            .header {
                text-align: center;
                color: #333;
                margin-bottom: 30px;
            }
            .summary-card {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                border-radius: 8px;
                margin-bottom: 20px;
            }
            .metric {
                display: inline-block;
                margin: 10px 20px;
                text-align: center;
            }
            .metric-value {
                font-size: 2em;
                font-weight: bold;
                display: block;
            }
            .metric-label {
                font-size: 0.9em;
                opacity: 0.9;
            }
            .section {
                margin: 20px 0;
                padding: 15px;
                border: 1px solid #ddd;
                border-radius: 5px;
            }
            .section h3 {
                color: #333;
                margin-top: 0;
                border-bottom: 2px solid #667eea;
                padding-bottom: 5px;
            }
            .coverage-good { color: #28a745; }
            .coverage-medium { color: #ffc107; }
            .coverage-poor { color: #dc3545; }
            table {
                width: 100%;
                border-collapse: collapse;
                margin: 10px 0;
            }
            th, td {
                padding: 8px 12px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }
            th {
                background-color: #f8f9fa;
                font-weight: bold;
            }
            .recommendation {
                background-color: #e3f2fd;
                padding: 10px;
                margin: 5px 0;
                border-left: 4px solid #2196f3;
                border-radius: 3px;
            }
            .progress-bar {
                width: 100%;
                height: 20px;
                background-color: #e0e0e0;
                border-radius: 10px;
                overflow: hidden;
                margin: 5px 0;
            }
            .progress-fill {
                height: 100%;
                background: linear-gradient(90deg, #4CAF50, #8BC34A);
                transition: width 0.3s ease;
            }
        </style>
        """
        
        # 生成HTML内容
        html = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Pi Sorter 测试覆盖率分析报告</title>
            {css_style}
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🧪 Pi Sorter 测试覆盖率分析报告</h1>
                    <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
                
                <div class="summary-card">
                    <h2>📊 总体覆盖率摘要</h2>
                    <div class="metric">
                        <span class="metric-value">{results['summary']['coverage_percentage']:.1f}%</span>
                        <span class="metric-label">总体覆盖率</span>
                    </div>
                    <div class="metric">
                        <span class="metric-value">{results['summary']['total_files']}</span>
                        <span class="metric-label">文件总数</span>
                    </div>
                    <div class="metric">
                        <span class="metric-value">{results['summary']['total_lines']}</span>
                        <span class="metric-label">总代码行</span>
                    </div>
                    <div class="metric">
                        <span class="metric-value">{results['summary']['covered_lines']}</span>
                        <span class="metric-label">覆盖行数</span>
                    </div>
                </div>
                
                <div class="section">
                    <h3>📁 模块覆盖率详情</h3>
                    <table>
                        <thead>
                            <tr>
                                <th>模块</th>
                                <th>文件数</th>
                                <th>代码行</th>
                                <th>覆盖行</th>
                                <th>覆盖率</th>
                                <th>进度</th>
                            </tr>
                        </thead>
                        <tbody>
        """
        
        # 添加模块数据
        for module, data in sorted(results['modules'].items(), key=lambda x: x[1]['coverage_percentage'], reverse=True):
            coverage = data['coverage_percentage']
            coverage_class = 'coverage-good' if coverage >= 80 else 'coverage-medium' if coverage >= 50 else 'coverage-poor'
            
            html += f"""
                            <tr>
                                <td><strong>{module}</strong></td>
                                <td>{len(data['files'])}</td>
                                <td>{data['total_lines']}</td>
                                <td>{data['covered_lines']}</td>
                                <td class="{coverage_class}"><strong>{coverage:.1f}%</strong></td>
                                <td>
                                    <div class="progress-bar">
                                        <div class="progress-fill" style="width: {coverage}%"></div>
                                    </div>
                                </td>
                            </tr>
            """
            
        html += """
                        </tbody>
                    </table>
                </div>
                
                <div class="section">
                    <h3>💡 改进建议</h3>
        """
        
        # 添加建议
        for recommendation in results['recommendations']:
            html += f"""
                    <div class="recommendation">{recommendation}</div>
            """
            
        html += """
                </div>
            </div>
        </body>
        </html>
        """
        
        return html


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Pi Sorter 测试覆盖率分析器')
    parser.add_argument('--source-dir', type=str, default='src/external', help='源代码目录')
    parser.add_argument('--test-dir', type=str, default='tests', help='测试目录')
    parser.add_argument('--output-json', type=str, default='coverage_report.json', help='JSON输出文件')
    parser.add_argument('--output-html', type=str, default='coverage_analysis_report.html', help='HTML输出文件')
    parser.add_argument('--no-html', action='store_true', help='不生成HTML报告')
    
    args = parser.parse_args()
    
    # 创建分析器
    analyzer = CoverageAnalyzer(args.source_dir, args.test_dir)
    
    # 运行覆盖率分析
    if analyzer.run_coverage_analysis(args.output_json):
        # 分析结果
        results = analyzer.analyze_coverage_results()
        
        if results:
            # 打印摘要
            analyzer.print_coverage_summary()
            
            # 生成HTML报告
            if not args.no_html:
                analyzer.generate_html_report(args.output_html)
                
            print("\n✅ 覆盖率分析完成!")
        else:
            print("\n❌ 覆盖率结果分析失败")
    else:
        print("\n❌ 覆盖率分析失败")


if __name__ == '__main__':
    main()