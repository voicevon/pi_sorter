#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理器 - 重构版本
提供统一的配置加载、验证和管理功能

重构改进：
1. 统一API命名规范：所有方法使用动词开头，如load_configuration()、validate_settings()等
2. 增强配置验证和错误处理
3. 完善文档字符串和类型注解
4. 支持多种配置格式和热重载
"""

import json
import yaml
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional, List, Union, Type, TypeVar
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

T = TypeVar('T')


class ConfigFormat(Enum):
    """配置文件格式枚举"""
    JSON = "json"
    YAML = "yaml"
    YAML_ALT = "yml"


@dataclass
class ValidationResult:
    """配置验证结果"""
    is_valid: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    config_path: Optional[str] = None
    validation_time: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ConfigMetadata:
    """配置元数据"""
    file_path: str
    file_format: ConfigFormat
    file_size: int
    last_modified: datetime
    load_time: datetime
    reload_count: int = 0


class ConfigManager:
    """
    配置管理器类
    提供统一的配置加载、验证、管理和热重载功能
    
    主要功能：
    - 多种配置文件格式支持（JSON、YAML）
    - 配置验证和错误处理
    - 配置热重载和缓存
    - 配置模板和默认值
    - 配置变更通知
    """
    
    def __init__(self, config_path: Optional[str] = None, 
                 auto_reload: bool = False, 
                 validation_enabled: bool = True):
        """
        初始化配置管理器
        
        Args:
            config_path: 配置文件路径
            auto_reload: 是否启用自动重载
            validation_enabled: 是否启用配置验证
        """
        # 配置参数
        self.config_path = config_path
        self.auto_reload = auto_reload
        self.validation_enabled = validation_enabled
        
        # 配置数据
        self.config_data: Dict[str, Any] = {}
        self.config_metadata: Optional[ConfigMetadata] = None
        self.config_cache: Dict[str, Any] = {}
        
        # 配置模板
        self.config_templates: Dict[str, Dict[str, Any]] = {}
        self.default_values: Dict[str, Any] = {}
        
        # 验证规则
        self.validation_rules: Dict[str, callable] = {}
        self.custom_validators: List[callable] = []
        
        # 热重载
        self.reload_thread: Optional[threading.Thread] = None
        self.reload_interval = 5.0  # 秒
        self.last_check_time = datetime.now()
        
        # 变更通知
        self.change_callbacks: List[callable] = []
        self.change_notification_enabled = True
        
        # 统计信息
        self.stats = {
            'load_count': 0,
            'reload_count': 0,
            'validation_count': 0,
            'error_count': 0,
            'start_time': datetime.now().isoformat()
        }
        
        # 日志
        self.logger = logging.getLogger(f"{__name__}.ConfigManager")
        
        # 注册默认验证器
        self._register_default_validators()
        
        self.logger.info("配置管理器初始化完成")
    
    def load_configuration(self, config_path: Optional[str] = None, 
                          force_reload: bool = False) -> bool:
        """
        加载配置文件
        
        Args:
            config_path: 配置文件路径，为None时使用默认路径
            force_reload: 是否强制重载
            
        Returns:
            bool: 加载成功返回True
        """
        try:
            # 确定配置文件路径
            if config_path:
                self.config_path = config_path
            elif not self.config_path:
                self.logger.error("未指定配置文件路径")
                return False
                
            config_file = Path(self.config_path)
            
            # 检查文件是否存在
            if not config_file.exists():
                self.logger.error(f"配置文件不存在: {self.config_path}")
                return False
                
            # 检查是否需要重载
            if not force_reload and self.config_metadata:
                current_modified = datetime.fromtimestamp(config_file.stat().st_mtime)
                if current_modified <= self.config_metadata.last_modified:
                    self.logger.debug(f"配置文件未修改，跳过加载: {self.config_path}")
                    return True
                    
            self.logger.info(f"开始加载配置文件: {self.config_path}")
            
            # 读取配置文件
            file_format = self._detect_file_format(config_file)
            
            with open(config_file, 'r', encoding='utf-8') as f:
                if file_format == ConfigFormat.JSON:
                    new_config = json.load(f)
                elif file_format in [ConfigFormat.YAML, ConfigFormat.YAML_ALT]:
                    new_config = yaml.safe_load(f)
                else:
                    self.logger.error(f"不支持的文件格式: {file_format}")
                    return False
                    
            # 更新配置数据
            old_config = self.config_data.copy()
            self.config_data = new_config
            
            # 更新元数据
            file_stat = config_file.stat()
            self.config_metadata = ConfigMetadata(
                file_path=str(config_file.absolute()),
                file_format=file_format,
                file_size=file_stat.st_size,
                last_modified=datetime.fromtimestamp(file_stat.st_mtime),
                load_time=datetime.now(),
                reload_count=self.config_metadata.reload_count + 1 if self.config_metadata else 0
            )
            
            # 验证配置
            if self.validation_enabled:
                validation_result = self.validate_configuration()
                if not validation_result.is_valid:
                    self.logger.error(f"配置验证失败: {validation_result.errors}")
                    # 恢复旧配置
                    self.config_data = old_config
                    return False
                    
            # 更新统计
            self.stats['load_count'] += 1
            if self.config_metadata.reload_count > 0:
                self.stats['reload_count'] += 1
                
            # 触发变更通知
            if self.change_notification_enabled and old_config != self.config_data:
                self._notify_config_change(old_config, self.config_data)
                
            self.logger.info(f"配置文件加载成功: {self.config_path}")
            return True
            
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON解析失败: {str(e)}")
            self.stats['error_count'] += 1
            return False
        except yaml.YAMLError as e:
            self.logger.error(f"YAML解析失败: {str(e)}")
            self.stats['error_count'] += 1
            return False
        except Exception as e:
            self.logger.error(f"配置文件加载失败: {str(e)}")
            self.stats['error_count'] += 1
            return False
    
    def save_configuration(self, config_path: Optional[str] = None, 
                          backup: bool = True) -> bool:
        """
        保存配置文件
        
        Args:
            config_path: 保存路径，为None时使用当前配置路径
            backup: 是否创建备份
            
        Returns:
            bool: 保存成功返回True
        """
        try:
            # 确定保存路径
            if config_path:
                save_path = Path(config_path)
            elif self.config_path:
                save_path = Path(self.config_path)
            else:
                self.logger.error("未指定保存路径")
                return False
                
            # 创建备份
            if backup and save_path.exists():
                backup_path = save_path.with_suffix(f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
                backup_path.write_text(save_path.read_text(), encoding='utf-8')
                self.logger.info(f"配置备份已创建: {backup_path}")
                
            # 检测文件格式
            file_format = self._detect_file_format(save_path)
            
            # 保存配置
            with open(save_path, 'w', encoding='utf-8') as f:
                if file_format == ConfigFormat.JSON:
                    json.dump(self.config_data, f, indent=2, ensure_ascii=False, default=str)
                elif file_format in [ConfigFormat.YAML, ConfigFormat.YAML_ALT]:
                    yaml.dump(self.config_data, f, default_flow_style=False, allow_unicode=True)
                else:
                    self.logger.error(f"不支持的文件格式: {file_format}")
                    return False
                    
            self.logger.info(f"配置文件已保存: {save_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"配置文件保存失败: {str(e)}")
            return False
    
    def validate_configuration(self, config_data: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """
        验证配置数据
        
        Args:
            config_data: 要验证的配置数据，为None时使用当前配置
            
        Returns:
            ValidationResult: 验证结果
        """
        try:
            self.stats['validation_count'] += 1
            
            # 使用指定的配置数据或当前配置
            if config_data is None:
                config_data = self.config_data
                
            result = ValidationResult(
                config_path=self.config_path,
                validation_time=datetime.now().isoformat()
            )
            
            # 基础验证
            if not isinstance(config_data, dict):
                result.is_valid = False
                result.errors.append("配置数据必须是字典类型")
                return result
                
            # 执行默认验证
            for validator_name, validator_func in self.validation_rules.items():
                try:
                    validator_result = validator_func(config_data)
                    if validator_result:
                        if isinstance(validator_result, list):
                            result.errors.extend(validator_result)
                        elif isinstance(validator_result, str):
                            result.errors.append(validator_result)
                except Exception as e:
                    result.warnings.append(f"验证器'{validator_name}'执行失败: {str(e)}")
                    
            # 执行自定义验证器
            for validator_func in self.custom_validators:
                try:
                    validator_result = validator_func(config_data)
                    if validator_result:
                        if isinstance(validator_result, list):
                            result.errors.extend(validator_result)
                        elif isinstance(validator_result, str):
                            result.errors.append(validator_result)
                except Exception as e:
                    result.warnings.append(f"自定义验证器执行失败: {str(e)}")
                    
            # 设置最终验证结果
            result.is_valid = len(result.errors) == 0
            
            if result.is_valid:
                self.logger.debug("配置验证通过")
            else:
                self.logger.error(f"配置验证失败: {result.errors}")
                
            return result
            
        except Exception as e:
            self.logger.error(f"配置验证失败: {str(e)}")
            return ValidationResult(
                is_valid=False,
                errors=[f"配置验证异常: {str(e)}"],
                config_path=self.config_path,
                validation_time=datetime.now().isoformat()
            )
    
    def get_configuration_value(self, key_path: str, default_value: Any = None) -> Any:
        """
        获取配置值（支持点号路径）
        
        Args:
            key_path: 配置键路径（如 'system.name'）
            default_value: 默认值
            
        Returns:
            Any: 配置值，不存在返回默认值
        """
        try:
            keys = key_path.split('.')
            value = self.config_data
            
            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return default_value
                    
            return value
            
        except Exception as e:
            self.logger.error(f"获取配置值失败: {key_path}, {str(e)}")
            return default_value
    
    def set_configuration_value(self, key_path: str, value: Any) -> bool:
        """
        设置配置值（支持点号路径）
        
        Args:
            key_path: 配置键路径（如 'system.name'）
            value: 配置值
            
        Returns:
            bool: 设置成功返回True
        """
        try:
            keys = key_path.split('.')
            config = self.config_data
            
            # 导航到父级
            for key in keys[:-1]:
                if key not in config:
                    config[key] = {}
                config = config[key]
                
            # 设置值
            config[keys[-1]] = value
            
            self.logger.debug(f"配置值已设置: {key_path} = {value}")
            return True
            
        except Exception as e:
            self.logger.error(f"设置配置值失败: {key_path}, {str(e)}")
            return False
    
    def get_camera_configuration(self) -> Dict[str, Any]:
        """
        获取摄像头配置
        
        Returns:
            Dict[str, Any]: 摄像头配置
        """
        return self.get_configuration_value('camera', {})
    
    def get_mqtt_configuration(self) -> Dict[str, Any]:
        """
        获取MQTT配置
        
        Returns:
            Dict[str, Any]: MQTT配置
        """
        # 优先级：broker > mqtt > 顶层配置
        broker_config = self.get_configuration_value('broker', {})
        if broker_config:
            return broker_config
            
        mqtt_config = self.get_configuration_value('mqtt', {})
        if mqtt_config:
            return mqtt_config
            
        return {}
    
    def get_system_configuration(self) -> Dict[str, Any]:
        """
        获取系统配置
        
        Returns:
            Dict[str, Any]: 系统配置
        """
        return self.get_configuration_value('system', {})
    
    def get_topics_configuration(self) -> Dict[str, str]:
        """
        获取主题配置
        
        Returns:
            Dict[str, str]: 主题配置
        """
        # 优先级：topics > mqtt.topics
        topics_config = self.get_configuration_value('topics', {})
        if topics_config:
            return topics_config
            
        mqtt_config = self.get_mqtt_configuration()
        if 'topics' in mqtt_config:
            return mqtt_config['topics']
            
        return {}
    
    def register_validation_rule(self, rule_name: str, validator_func: callable):
        """
        注册验证规则
        
        Args:
            rule_name: 规则名称
            validator_func: 验证函数
        """
        self.validation_rules[rule_name] = validator_func
        self.logger.debug(f"验证规则已注册: {rule_name}")
    
    def add_custom_validator(self, validator_func: callable):
        """
        添加自定义验证器
        
        Args:
            validator_func: 验证函数
        """
        self.custom_validators.append(validator_func)
        self.logger.debug("自定义验证器已添加")
    
    def add_change_callback(self, callback: callable):
        """
        添加配置变更回调
        
        Args:
            callback: 回调函数
        """
        self.change_callbacks.append(callback)
        self.logger.debug("配置变更回调已添加")
    
    def start_auto_reload(self) -> bool:
        """
        启动自动重载
        
        Returns:
            bool: 启动成功返回True
        """
        try:
            if self.reload_thread and self.reload_thread.is_alive():
                self.logger.debug("自动重载已在运行")
                return True
                
            if not self.config_path:
                self.logger.error("未指定配置文件路径，无法启动自动重载")
                return False
                
            self.logger.info("启动配置自动重载")
            
            self.reload_thread = threading.Thread(
                target=self._auto_reload_loop, 
                name="ConfigAutoReload"
            )
            self.reload_thread.daemon = True
            self.reload_thread.start()
            
            return True
            
        except Exception as e:
            self.logger.error(f"启动自动重载失败: {str(e)}")
            return False
    
    def stop_auto_reload(self) -> bool:
        """
        停止自动重载
        
        Returns:
            bool: 停止成功返回True
        """
        try:
            if not self.reload_thread or not self.reload_thread.is_alive():
                self.logger.debug("自动重载未在运行")
                return True
                
            self.logger.info("停止配置自动重载")
            
            # 等待线程结束
            self.reload_thread.join(timeout=5)
            
            return True
            
        except Exception as e:
            self.logger.error(f"停止自动重载失败: {str(e)}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        try:
            uptime = 0
            if self.stats['start_time']:
                start_time = datetime.fromisoformat(self.stats['start_time'])
                uptime = (datetime.now() - start_time).total_seconds()
                
            return {
                'load_count': self.stats['load_count'],
                'reload_count': self.stats['reload_count'],
                'validation_count': self.stats['validation_count'],
                'error_count': self.stats['error_count'],
                'uptime_seconds': uptime,
                'config_path': self.config_path,
                'auto_reload': self.auto_reload,
                'validation_enabled': self.validation_enabled,
                'has_metadata': self.config_metadata is not None
            }
            
        except Exception as e:
            self.logger.error(f"获取统计信息失败: {str(e)}")
            return {'error': str(e)}
    
    def _detect_file_format(self, file_path: Path) -> ConfigFormat:
        """
        检测文件格式（内部方法）
        
        Args:
            file_path: 文件路径
            
        Returns:
            ConfigFormat: 文件格式
        """
        suffix = file_path.suffix.lower()
        
        if suffix == '.json':
            return ConfigFormat.JSON
        elif suffix in ['.yaml', '.yml']:
            return ConfigFormat.YAML if suffix == '.yaml' else ConfigFormat.YAML_ALT
        else:
            # 默认使用YAML格式
            return ConfigFormat.YAML
    
    def _register_default_validators(self):
        """
        注册默认验证器（内部方法）
        """
        def validate_camera_config(config: Dict[str, Any]) -> List[str]:
            """验证摄像头配置"""
            errors = []
            
            camera_config = config.get('camera', {})
            if not camera_config:
                return errors
                
            if camera_config.get('enabled', True):
                resolution = camera_config.get('resolution', [1280, 1024])
                if not isinstance(resolution, list) or len(resolution) != 2:
                    errors.append("摄像头分辨率配置无效，必须是包含两个整数的列表")
                else:
                    width, height = resolution
                    if not (isinstance(width, int) and isinstance(height, int)):
                        errors.append("摄像头分辨率必须是整数")
                    elif width <= 0 or height <= 0:
                        errors.append("摄像头分辨率必须为正数")
                        
                fps = camera_config.get('fps', 30)
                if not isinstance(fps, (int, float)) or fps <= 0:
                    errors.append("摄像头帧率必须是正数")
                    
            return errors
        
        def validate_mqtt_config(config: Dict[str, Any]) -> List[str]:
            """验证MQTT配置"""
            errors = []
            
            # 检查broker配置
            broker_config = config.get('broker', {})
            if broker_config:
                if not broker_config.get('host'):
                    errors.append("MQTT代理地址不能为空")
                if not isinstance(broker_config.get('port', 1883), int):
                    errors.append("MQTT代理端口必须是整数")
                    
            # 检查mqtt配置
            mqtt_config = config.get('mqtt', {})
            if mqtt_config:
                if not mqtt_config.get('host'):
                    errors.append("MQTT主机地址不能为空")
                if 'port' in mqtt_config and not isinstance(mqtt_config['port'], int):
                    errors.append("MQTT端口必须是整数")
                    
            return errors
        
        def validate_system_config(config: Dict[str, Any]) -> List[str]:
            """验证系统配置"""
            errors = []
            
            system_config = config.get('system', {})
            if not system_config:
                return errors
                
            log_level = system_config.get('log_level', 'INFO')
            valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
            if log_level not in valid_levels:
                errors.append(f"日志级别无效，必须是: {valid_levels}")
                
            return errors
        
        # 注册验证器
        self.register_validation_rule('camera', validate_camera_config)
        self.register_validation_rule('mqtt', validate_mqtt_config)
        self.register_validation_rule('system', validate_system_config)
    
    def _auto_reload_loop(self):
        """
        自动重载循环（内部线程方法）
        """
        self.logger.info("配置自动重载循环已启动")
        
        while self.auto_reload:
            try:
                current_time = datetime.now()
                
                # 检查是否需要重载
                if (current_time - self.last_check_time).total_seconds() >= self.reload_interval:
                    self.last_check_time = current_time
                    
                    # 尝试重载配置
                    if self.load_configuration():
                        self.logger.debug("配置自动重载完成")
                    else:
                        self.logger.warning("配置自动重载失败")
                        
                time.sleep(1.0)
                
            except Exception as e:
                self.logger.error(f"自动重载循环错误: {str(e)}")
                time.sleep(5.0)
                
        self.logger.info("配置自动重载循环已停止")
    
    def _notify_config_change(self, old_config: Dict[str, Any], new_config: Dict[str, Any]):
        """
        通知配置变更（内部方法）
        
        Args:
            old_config: 旧配置
            new_config: 新配置
        """
        try:
            self.logger.info("配置已变更，触发回调通知")
            
            for callback in self.change_callbacks:
                try:
                    callback(old_config, new_config)
                except Exception as e:
                    self.logger.error(f"配置变更回调执行失败: {str(e)}")
                    
        except Exception as e:
            self.logger.error(f"配置变更通知失败: {str(e)}")
    
    # 上下文管理器支持
    def __enter__(self):
        """
        上下文管理器入口
        
        Returns:
            ConfigManager: 配置管理器实例
        """
        if self.config_path and not self.load_configuration():
            raise RuntimeError("配置加载失败")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        上下文管理器出口
        """
        self.stop_auto_reload()


# 向后兼容的别名（用于过渡期）
class ConfigManagerLegacy:
    """
    配置管理器（向后兼容）
    提供旧版本的方法名映射
    """
    
    def __init__(self, config_path: str = None):
        """
        初始化配置管理器（兼容旧版本）
        
        Args:
            config_path: 配置文件路径
        """
        self.manager = ConfigManager(config_path)
        self.logger = logging.getLogger(f"{__name__}.ConfigManagerLegacy")
    
    def load_config(self, config_path: str = None) -> bool:
        """
        加载配置（兼容旧版本）
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            bool: 加载成功返回True
        """
        self.logger.warning("load_config() 已弃用，请使用 load_configuration()")
        return self.manager.load_configuration(config_path)
    
    def get_config(self, key_path: str, default_value: Any = None) -> Any:
        """
        获取配置值（兼容旧版本）
        
        Args:
            key_path: 配置键路径
            default_value: 默认值
            
        Returns:
            Any: 配置值
        """
        self.logger.warning("get_config() 已弃用，请使用 get_configuration_value()")
        return self.manager.get_configuration_value(key_path, default_value)
    
    def get_camera_config(self) -> Dict[str, Any]:
        """
        获取摄像头配置（兼容旧版本）
        
        Returns:
            Dict[str, Any]: 摄像头配置
        """
        return self.manager.get_camera_configuration()
    
    def get_mqtt_config(self) -> Dict[str, Any]:
        """
        获取MQTT配置（兼容旧版本）
        
        Returns:
            Dict[str, Any]: MQTT配置
        """
        return self.manager.get_mqtt_configuration()


# 模块测试
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🧪 配置管理器测试")
    
    # 创建测试配置
    test_config = {
        'system': {
            'name': '测试系统',
            'version': '1.0.0',
            'log_level': 'INFO'
        },
        'camera': {
            'enabled': True,
            'resolution': [1280, 1024],
            'fps': 30
        },
        'mqtt': {
            'host': 'localhost',
            'port': 1883,
            'topics': {
                'status': 'test/status',
                'results': 'test/results'
            }
        }
    }
    
    try:
        # 保存测试配置到文件
        test_file = Path("test_config.yaml")
        with open(test_file, 'w') as f:
            yaml.dump(test_config, f)
            
        # 测试配置管理器
        with ConfigManager(str(test_file)) as manager:
            print(f"✅ 配置管理器初始化成功")
            
            # 验证配置
            validation_result = manager.validate_configuration()
            if validation_result.is_valid:
                print(f"✅ 配置验证通过")
            else:
                print(f"❌ 配置验证失败: {validation_result.errors}")
                
            # 获取配置值
            system_name = manager.get_configuration_value('system.name')
            print(f"📋 系统名称: {system_name}")
            
            # 获取统计信息
            stats = manager.get_statistics()
            print(f"📊 统计信息: {stats}")
            
        # 清理测试文件
        test_file.unlink()
        print(f"✅ 测试完成")
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        
    print("🧪 测试完成")