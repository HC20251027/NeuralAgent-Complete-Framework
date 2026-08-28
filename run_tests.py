#!/usr/bin/env python3
"""
NeuralAgent × Agno-BMAD 融合框架 - 测试运行器
============================================

完整的测试套件运行器，支持：
- 单元测试
- 集成测试  
- 演示测试
- 性能基准测试

Author: HC20251027
Date: 2025-11-06
"""

import sys
import os
import asyncio
import argparse
import json
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入测试模块
from tests import setup_test_environment, cleanup_test_environment, quick_test
from tests.unit import run_unit_tests
from tests.benchmarks import run_all_benchmarks, save_benchmark_results

class TestRunner:
    """测试运行器"""
    
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'test_suite': 'NeuralAgent Framework Tests',
            'results': {}
        }
    
    def run_unit_tests(self) -> bool:
        """运行单元测试"""
        print("=" * 60)
        print("运行单元测试...")
        print("=" * 60)
        
        try:
            success = run_unit_tests()
            self.results['results']['unit_tests'] = {
                'status': 'PASSED' if success else 'FAILED',
                'success': success
            }
            
            if success:
                print("✅ 单元测试全部通过")
            else:
                print("❌ 单元测试存在失败")
            
            return success
            
        except Exception as e:
            print(f"❌ 单元测试执行失败: {e}")
            self.results['results']['unit_tests'] = {
                'status': 'ERROR',
                'success': False,
                'error': str(e)
            }
            return False
    
    async def run_integration_tests(self) -> bool:
        """运行集成测试"""
        print("\n" + "=" * 60)
        print("运行集成测试...")
        print("=" * 60)
        
        try:
            # 设置测试环境
            setup_test_environment()
            
            # 运行快速测试
            test_result = await quick_test()
            
            self.results['results']['integration_tests'] = {
                'status': 'PASSED' if test_result['success'] else 'FAILED',
                'success': test_result['success'],
                'details': test_result
            }
            
            if test_result['success']:
                print("✅ 集成测试通过")
                print(f"   - 多模态处理: {'✅' if 'multimodal_result' in test_result else '❌'}")
                print(f"   - 智能体工作流: {'✅' if 'agent_results' in test_result else '❌'}")
            else:
                print("❌ 集成测试失败")
                print(f"   错误: {test_result.get('error', '未知错误')}")
            
            return test_result['success']
            
        except Exception as e:
            print(f"❌ 集成测试执行失败: {e}")
            self.results['results']['integration_tests'] = {
                'status': 'ERROR',
                'success': False,
                'error': str(e)
            }
            return False
        
        finally:
            # 清理测试环境
            cleanup_test_environment()
    
    async def run_demo_tests(self) -> bool:
        """运行演示测试"""
        print("\n" + "=" * 60)
        print("运行演示测试...")
        print("=" * 60)
        
        try:
            # 导入演示模块
            from tests.demo import VideoToPRDDemo, CollaborationModeDemo, UserInterfaceDemo, DocumentationExamples
            
            # 运行演示
            demo_results = {}
            
            # 视频到PRD演示
            try:
                video_demo = VideoToPRDDemo()
                await video_demo.run_demo()
                demo_results['video_to_prd'] = {'status': 'PASSED', 'success': True}
                print("✅ 视频到PRD演示完成")
            except Exception as e:
                demo_results['video_to_prd'] = {'status': 'FAILED', 'success': False, 'error': str(e)}
                print(f"❌ 视频到PRD演示失败: {e}")
            
            # 协作模式演示
            try:
                collab_demo = CollaborationModeDemo()
                await collab_demo.run_demo()
                demo_results['collaboration_modes'] = {'status': 'PASSED', 'success': True}
                print("✅ 协作模式演示完成")
            except Exception as e:
                demo_results['collaboration_modes'] = {'status': 'FAILED', 'success': False, 'error': str(e)}
                print(f"❌ 协作模式演示失败: {e}")
            
            # 用户界面演示
            try:
                ui_demo = UserInterfaceDemo()
                await ui_demo.run_demo()
                demo_results['user_interface'] = {'status': 'PASSED', 'success': True}
                print("✅ 用户界面演示完成")
            except Exception as e:
                demo_results['user_interface'] = {'status': 'FAILED', 'success': False, 'error': str(e)}
                print(f"❌ 用户界面演示失败: {e}")
            
            # 文档示例演示
            try:
                doc_demo = DocumentationExamples()
                await doc_demo.run_demo()
                demo_results['documentation'] = {'status': 'PASSED', 'success': True}
                print("✅ 文档示例演示完成")
            except Exception as e:
                demo_results['documentation'] = {'status': 'FAILED', 'success': False, 'error': str(e)}
                print(f"❌ 文档示例演示失败: {e}")
            
            # 统计演示结果
            successful_demos = sum(1 for r in demo_results.values() if r['success'])
            total_demos = len(demo_results)
            
            self.results['results']['demo_tests'] = {
                'status': 'PASSED' if successful_demos == total_demos else 'PARTIAL',
                'success': successful_demos == total_demos,
                'details': demo_results,
                'summary': {
                    'total_demos': total_demos,
                    'successful_demos': successful_demos,
                    'success_rate': successful_demos / total_demos if total_demos > 0 else 0
                }
            }
            
            print(f"\n演示测试完成: {successful_demos}/{total_demos} 成功")
            return successful_demos == total_demos
            
        except Exception as e:
            print(f"❌ 演示测试执行失败: {e}")
            self.results['results']['demo_tests'] = {
                'status': 'ERROR',
                'success': False,
                'error': str(e)
            }
            return False
    
    async def run_benchmark_tests(self) -> bool:
        """运行基准测试"""
        print("\n" + "=" * 60)
        print("运行性能基准测试...")
        print("=" * 60)
        
        try:
            benchmark_results = await run_all_benchmarks()
            
            # 保存基准测试结果
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            benchmark_file = f"benchmark_results_{timestamp}.json"
            save_benchmark_results(benchmark_results, benchmark_file)
            
            self.results['results']['benchmark_tests'] = {
                'status': 'COMPLETED',
                'success': True,
                'details': benchmark_results,
                'results_file': benchmark_file
            }
            
            print("✅ 基准测试完成")
            print(f"   结果已保存到: {benchmark_file}")
            
            # 打印关键指标
            print("\n关键性能指标:")
            if 'vision' in benchmark_results:
                print(f"   视觉处理平均时间: {benchmark_results['vision'].get('avg_processing_time', 'N/A'):.4f}s")
            if 'asr' in benchmark_results:
                print(f"   ASR处理平均时间: {benchmark_results['asr'].get('avg_processing_time', 'N/A'):.4f}s")
            if 'agent_workflow' in benchmark_results:
                print(f"   智能体工作流吞吐量: {benchmark_results['agent_workflow'].get('tasks_per_second', 'N/A'):.2f} 任务/秒")
            if 'system_integration' in benchmark_results:
                print(f"   系统集成总时间: {benchmark_results['system_integration'].get('total_system_time', 'N/A'):.4f}s")
            
            return True
            
        except Exception as e:
            print(f"❌ 基准测试执行失败: {e}")
            self.results['results']['benchmark_tests'] = {
                'status': 'ERROR',
                'success': False,
                'error': str(e)
            }
            return False
    
    def generate_report(self) -> str:
        """生成测试报告"""
        report = []
        report.append("=" * 80)
        report.append("NeuralAgent × Agno-BMAD 融合框架 - 测试报告")
        report.append("=" * 80)
        report.append(f"测试时间: {self.results['timestamp']}")
        report.append("")
        
        # 统计总体结果
        total_tests = len(self.results['results'])
        passed_tests = sum(1 for r in self.results['results'].values() if r.get('success', False))
        
        report.append(f"总体结果: {passed_tests}/{total_tests} 测试套件通过")
        report.append("")
        
        # 详细结果
        for test_name, test_result in self.results['results'].items():
            status_icon = "✅" if test_result.get('success', False) else "❌"
            report.append(f"{status_icon} {test_name.replace('_', ' ').title()}: {test_result['status']}")
            
            if 'summary' in test_result:
                summary = test_result['summary']
                report.append(f"   成功率: {summary.get('success_rate', 0):.1%}")
            
            if 'error' in test_result:
                report.append(f"   错误: {test_result['error']}")
            
            report.append("")
        
        # 建议
        report.append("建议:")
        if passed_tests == total_tests:
            report.append("🎉 所有测试通过！系统可以投入生产使用。")
        elif passed_tests >= total_tests * 0.8:
            report.append("⚠️  大部分测试通过，建议修复失败的测试后投入使用。")
        else:
            report.append("🚨 多个测试失败，建议修复所有问题后再投入生产。")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)
    
    async def run_all_tests(self) -> bool:
        """运行所有测试"""
        print("NeuralAgent × Agno-BMAD 融合框架 - 测试套件")
        print("=" * 80)
        
        overall_success = True
        
        # 运行各种测试
        overall_success &= self.run_unit_tests()
        overall_success &= await self.run_integration_tests()
        overall_success &= await self.run_demo_tests()
        overall_success &= await self.run_benchmark_tests()
        
        # 生成报告
        report = self.generate_report()
        print("\n" + report)
        
        # 保存详细报告
        report_file = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n详细测试报告已保存到: {report_file}")
        
        return overall_success

async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="NeuralAgent框架测试运行器")
    parser.add_argument('--test-type', choices=['unit', 'integration', 'demo', 'benchmark', 'all'], 
                       default='all', help='测试类型')
    parser.add_argument('--output', help='输出报告文件路径')
    parser.add_argument('--verbose', action='store_true', help='详细输出')
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    try:
        if args.test_type == 'unit':
            success = runner.run_unit_tests()
        elif args.test_type == 'integration':
            success = await runner.run_integration_tests()
        elif args.test_type == 'demo':
            success = await runner.run_demo_tests()
        elif args.test_type == 'benchmark':
            success = await runner.run_benchmark_tests()
        else:  # all
            success = await runner.run_all_tests()
        
        # 保存报告
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(runner.results, f, indent=2, ensure_ascii=False, default=str)
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n测试执行失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    asyncio.run(main())