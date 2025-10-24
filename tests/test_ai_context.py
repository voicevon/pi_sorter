#!/usr/bin/env python3
"""
AI上下文文档验证脚本
用于验证.ai-context.yaml文件的完整性和可用性
"""

import os
import yaml
import sys
from pathlib import Path

def test_ai_context_file():
    """测试AI上下文文件是否存在且格式正确"""
    
    # 查找项目根目录
    current_dir = Path(__file__).parent.parent
    context_file = current_dir / ".ai-context.yaml"
    
    print(f"🔍 检查AI上下文文件: {context_file}")
    
    # 检查文件是否存在
    if not context_file.exists():
        print("❌ 错误: .ai-context.yaml 文件不存在")
        return False
    
    print("✅ AI上下文文件存在")
    
    # 尝试解析YAML文件
    try:
        with open(context_file, 'r', encoding='utf-8') as f:
            context_data = yaml.safe_load(f)
        print("✅ YAML格式正确")
    except yaml.YAMLError as e:
        print(f"❌ YAML格式错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 文件读取错误: {e}")
        return False
    
    # 验证必要的字段
    required_sections = [
        'project_info',
        'technology_stack', 
        'development_environment',
        'project_structure',
        'ai_assistant_guidelines'
    ]
    
    print("\n📋 验证必要字段:")
    for section in required_sections:
        if section in context_data:
            print(f"✅ {section}")
        else:
            print(f"❌ 缺少字段: {section}")
            return False
    
    # 验证项目信息
    project_info = context_data.get('project_info', {})
    if project_info.get('name') and project_info.get('type'):
        print("✅ 项目基本信息完整")
    else:
        print("❌ 项目基本信息不完整")
        return False
    
    # 验证开发环境信息
    dev_env = context_data.get('development_environment', {})
    if dev_env.get('type') == 'SSH远程开发':
        ssh_config = dev_env.get('ssh_config', {})
        if ssh_config.get('host') and ssh_config.get('username'):
            print("✅ SSH配置信息完整")
        else:
            print("❌ SSH配置信息不完整")
            return False
    
    print("\n🎯 上下文文档验证通过!")
    return True

def test_environment_detection():
    """测试环境检测功能"""
    
    print("\n🔍 环境检测测试:")
    
    # 检查当前工作目录
    current_dir = os.getcwd()
    print(f"📁 当前工作目录: {current_dir}")
    
    # 检查项目标识文件
    project_files = [
        ".ai-context.yaml",
        "config/integrated_config.yaml", 
        "src/external/integrated_system.py",
        "docs/AI智能体启动指南.md"
    ]
    
    print("\n📄 项目文件检查:")
    for file_path in project_files:
        full_path = Path(current_dir) / file_path
        if full_path.exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} (不存在)")
    
    # 检查SSH配置
    ssh_config_path = Path(current_dir) / "config" / "ssh_config.txt"
    if ssh_config_path.exists():
        print("✅ SSH配置文件存在")
        try:
            with open(ssh_config_path, 'r', encoding='utf-8') as f:
                ssh_content = f.read()
                if "192.168.2.192" in ssh_content:
                    print("✅ SSH配置包含正确的主机信息")
                else:
                    print("❌ SSH配置信息不完整")
        except Exception as e:
            print(f"❌ SSH配置读取错误: {e}")
    else:
        print("❌ SSH配置文件不存在")

def generate_context_summary():
    """生成上下文摘要"""
    
    context_file = Path(__file__).parent.parent / ".ai-context.yaml"
    
    if not context_file.exists():
        print("❌ 无法生成摘要: 上下文文件不存在")
        return
    
    try:
        with open(context_file, 'r', encoding='utf-8') as f:
            context_data = yaml.safe_load(f)
        
        print("\n📊 项目上下文摘要:")
        print("=" * 50)
        
        # 项目信息
        project_info = context_data.get('project_info', {})
        print(f"项目名称: {project_info.get('display_name', 'N/A')}")
        print(f"项目类型: {project_info.get('type', 'N/A')}")
        print(f"主要语言: {context_data.get('technology_stack', {}).get('primary_language', 'N/A')}")
        
        # 开发环境
        dev_env = context_data.get('development_environment', {})
        print(f"开发模式: {dev_env.get('type', 'N/A')}")
        
        if dev_env.get('type') == 'SSH远程开发':
            ssh_config = dev_env.get('ssh_config', {})
            print(f"远程主机: {ssh_config.get('host', 'N/A')}")
            print(f"用户名: {ssh_config.get('username', 'N/A')}")
        
        # 当前状态
        current_status = context_data.get('current_development_status', {})
        completed = current_status.get('completed', [])
        in_progress = current_status.get('in_progress', [])
        
        print(f"\n已完成任务: {len(completed)} 项")
        print(f"进行中任务: {len(in_progress)} 项")
        
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ 生成摘要失败: {e}")

def main():
    """主函数"""
    
    print("🤖 AI智能体上下文文档验证工具")
    print("=" * 60)
    
    # 测试上下文文件
    if not test_ai_context_file():
        sys.exit(1)
    
    # 测试环境检测
    test_environment_detection()
    
    # 生成上下文摘要
    generate_context_summary()
    
    print("\n🎉 所有验证测试完成!")

if __name__ == "__main__":
    main()