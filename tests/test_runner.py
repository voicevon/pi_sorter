#!/usr/bin/env python3
"""
Pi Sorter - 测试运行器
用于运行所有测试套件并生成测试报告
"""

import os
import sys
import time
import unittest
import json
from datetime import datetime
from typing import Dict, Any, List

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '../src/external'))

# 导入测试模块
from test_comprehensive import (
    TestConfigManager,
    TestCSICameraManager,
    TestSorterMQTTManager,
    TestEncoderManager,
    TestSystemMonitor,
    TestEnhancedSystemMonitor,
    TestIntegratedSortingSystem,
    TestSystemIntegration,
    TestPerformance,
    TestErrorHandling,
    TestConfigurationValidation
)


class TestReportGenerator:
    """测试报告生成器"""
    
    def __init__(self, output_dir: str = "test_reports"):
        """初始化报告生成器"""
        self.output_dir = output_dir
        self.test_results = []
        self.start_time = None
        self.end_time = None
        
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
    def start_test_run(self):
        """开始测试运行"""
        self.start_time = datetime.now()
        print(f"🚀 开始运行测试套件...")
        print(f"开始时间: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
    def end_test_run(self):
        """结束测试运行"""
        self.end_time = datetime.now()
        duration = self.end_time - self.start_time
        print(f"\n✅ 测试运行完成!")
        print(f"结束时间: {self.end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"总耗时: {duration.total_seconds():.2f}秒")
        
    def add_test_result(self, test_name: str, result: unittest.TestResult):
        """添加测试结果"""
        self.test_results.append({
            'test_name': test_name,
            'tests_run': result.testsRun,
            'failures': len(result.failures),
            'errors': len(result.errors),
            'skipped': len(result.skipped) if hasattr(result, 'skipped') else 0,
            'success': result.wasSuccessful(),
            'duration': getattr(result, 'duration', 0.0)
        })
        
    def generate_summary_report(self) -> Dict[str, Any]:
        """生成测试摘要报告"""
        total_tests = sum(r['tests_run'] for r in self.test_results)
        total_failures = sum(r['failures'] for r in self.test_results)
        total_errors = sum(r['errors'] for r in self.test_results)
        total_skipped = sum(r['skipped'] for r in self.test_results)
        total_success = total_tests - total_failures - total_errors - total_skipped
        
        success_rate = (total_success / total_tests * 100) if total_tests > 0 else 0
        
        summary = {
            'test_run_info': {
                'start_time': self.start_time.isoformat() if self.start_time else None,
                'end_time': self.end_time.isoformat() if self.end_time else None,
                'duration_seconds': (self.end_time - self.start_time).total_seconds() if self.start_time and self.end_time else 0
            },
            'overall_results': {
                'total_tests': total_tests,
                'passed': total_success,
                'failed': total_failures,
                'errors': total_errors,
                'skipped': total_skipped,
                'success_rate': success_rate
            },
            'detailed_results': self.test_results
        }
        
        return summary
        
    def save_report_to_file(self, filename: str = None):
        """保存报告到文件"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"test_report_{timestamp}.json"
            
        report_path = os.path.join(self.output_dir, filename)
        
        summary = self.generate_summary_report()
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
            
        print(f"📊 测试报告已保存到: {report_path}")
        return report_path
        
    def print_summary(self):
        """打印测试摘要"""
        summary = self.generate_summary_report()
        
        print("\n" + "="*60)
        print("📋 测试摘要报告")
        print("="*60)
        
        # 测试运行信息
        if summary['test_run_info']['start_time']:
            print(f"开始时间: {summary['test_run_info']['start_time']}")
        if summary['test_run_info']['end_time']:
            print(f"结束时间: {summary['test_run_info']['end_time']}")
        print(f"总耗时: {summary['test_run_info']['duration_seconds']:.2f}秒")
        
        print("\n" + "-"*40)
        print("📈 总体结果")
        print("-"*40)
        
        results = summary['overall_results']
        print(f"总测试数: {results['total_tests']}")
        print(f"通过: {results['passed']} ✅")
        print(f"失败: {results['failed']} ❌")
        print(f"错误: {results['errors']} ⚠️")
        print(f"跳过: {results['skipped']} ⏭️")
        print(f"成功率: {results['success_rate']:.1f}%")
        
        print("\n" + "-"*40)
        print("🔍 详细结果")
        print("-"*40)
        
        for result in summary['detailed_results']:
            status_icon = "✅" if result['success'] else "❌"
            print(f"{status_icon} {result['test_name']}")
            print(f"   运行: {result['tests_run']}, 失败: {result['failures']}, 错误: {result['errors']}")
            print(f"   耗时: {result['duration']:.2f}秒")
            print()


class CustomTestRunner(unittest.TextTestRunner):
    """自定义测试运行器"""
    
    def __init__(self, stream=None, descriptions=True, verbosity=2):
        super().__init__(stream, descriptions, verbosity)
        self.start_time = None
        self.end_time = None
        
    def run(self, test):
        """运行测试"""
        self.start_time = time.time()
        result = super().run(test)
        self.end_time = time.time()
        result.duration = self.end_time - self.start_time
        return result


def run_all_tests():
    """运行所有测试"""
    # 创建测试套件
    test_suite = unittest.TestSuite()
    
    # 添加所有测试类
    test_classes = [
        TestConfigManager,
        TestCSICameraManager,
        TestSorterMQTTManager,
        TestEncoderManager,
        TestSystemMonitor,
        TestEnhancedSystemMonitor,
        TestIntegratedSortingSystem,
        TestSystemIntegration,
        TestPerformance,
        TestErrorHandling,
        TestConfigurationValidation
    ]
    
    # 加载测试用例
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # 创建报告生成器
    report_generator = TestReportGenerator()
    report_generator.start_test_run()
    
    # 运行测试
    runner = CustomTestRunner()
    
    print("\n" + "="*60)
    print("🧪 Pi Sorter 综合测试套件")
    print("="*60)
    print(f"测试总数: {test_suite.countTestCases()}")
    print("="*60 + "\n")
    
    # 运行测试套件
    result = runner.run(test_suite)
    
    # 生成报告
    report_generator.add_test_result("综合测试套件", result)
    report_generator.end_test_run()
    report_generator.print_summary()
    
    # 保存详细报告
    report_path = report_generator.save_report_to_file()
    
    # 返回测试结果
    return {
        'success': result.wasSuccessful(),
        'tests_run': result.testsRun,
        'failures': len(result.failures),
        'errors': len(result.errors),
        'report_path': report_path
    }


def run_specific_test(test_class_name: str):
    """运行特定测试类"""
    # 获取测试类
    test_class = globals().get(test_class_name)
    if not test_class:
        print(f"❌ 测试类 {test_class_name} 不存在")
        return False
    
    # 创建测试套件
    test_suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
    
    # 运行测试
    runner = CustomTestRunner()
    result = runner.run(test_suite)
    
    print(f"\n📊 {test_class_name} 测试结果:")
    print(f"运行测试: {result.testsRun}")
    print(f"通过: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    print(f"成功率: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    return result.wasSuccessful()


def run_performance_tests():
    """运行性能测试"""
    print("\n" + "="*60)
    print("⚡ 运行性能测试")
    print("="*60)
    
    # 运行性能测试
    return run_specific_test('TestPerformance')


def run_error_handling_tests():
    """运行错误处理测试"""
    print("\n" + "="*60)
    print("🛡️ 运行错误处理测试")
    print("="*60)
    
    # 运行错误处理测试
    return run_specific_test('TestErrorHandling')


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Pi Sorter 测试运行器')
    parser.add_argument('--test-class', type=str, help='运行特定测试类')
    parser.add_argument('--performance', action='store_true', help='只运行性能测试')
    parser.add_argument('--error-handling', action='store_true', help='只运行错误处理测试')
    parser.add_argument('--output-dir', type=str, default='test_reports', help='测试报告输出目录')
    
    args = parser.parse_args()
    
    # 根据参数运行测试
    if args.test_class:
        success = run_specific_test(args.test_class)
    elif args.performance:
        success = run_performance_tests()
    elif args.error_handling:
        success = run_error_handling_tests()
    else:
        # 运行所有测试
        results = run_all_tests()
        success = results['success']
        
        print(f"\n🎯 测试运行总结:")
        print(f"总测试数: {results['tests_run']}")
        print(f"失败数: {results['failures']}")
        print(f"错误数: {results['errors']}")
        print(f"报告文件: {results['report_path']}")
    
    # 返回退出码
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()