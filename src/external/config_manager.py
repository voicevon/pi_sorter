#!/usr/bin/env python3
"""
配置管理器 - 管理集成系统配置
Configuration manager for integrated system
"""

import os
import yaml
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path


class ConfigManager:
    """
    配置管理器类
    Configuration manager class
    """
    
    def __init__(self, config_path: str = None):
        """
        初始化配置管理器
        
        Args:
            config_path: 配置文件路径
        """
        self.logger = logging.getLogger(__name__)
        
        # 默认配置文件路径
        if config_path is None:
            current_dir = Path(__file__).parent.parent.parent
            config_path = current_dir / "config" / "integrated_config.yaml"
        
        self.config_path = Path(config_path)
        self.config = {}
        self.default_config = self._get_default_config()
        
        # 加载配置
        self.load_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """
        获取默认配置
        
        Returns:
            Dict: 默认配置
        """
        return {
            'system': {
                'name': '芦笋分拣系统',
                'version': '1.0.0',
                'debug': False,
                'log_level': 'INFO'
            },
            'camera': {
                'enabled': True,
                'device_id': 0,
                'resolution': [1280, 1024],
                'fps': 30,
                'brightness': 0.5,
                'contrast': 0.5,
                'saturation': 0.5,
                'exposure': -1,
                'auto_capture': True,
                'capture_interval': 5.0  # 五秒间隔拍照
            },
            'mqtt': {
                'enabled': False,
                'broker_host': 'localhost',
                'broker_port': 1883,
                'client_id': 'pi_sorter_integrated',
                'topics': {
                    'status': 'pi_sorter/status',
                    'results': 'pi_sorter/results',
                    'commands': 'pi_sorter/commands',
                    'alerts': 'pi_sorter/alerts',
                    'images': 'pi_sorter/images',
                    'statistics': 'pi_sorter/statistics',
                    'heartbeat': 'pi_sorter/heartbeat'
                }
            },
            'processing': {
                'interval': 5.0,  # 处理间隔（秒）
                'save_results': True,
                'save_images': True,
                'save_raw_images': True,
                'image_format': 'jpg',
                'image_quality': 95
            }
        }
    
    def load_config(self) -> bool:
        """
        加载配置文件
        
        Returns:
            bool: 加载是否成功
        """
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    if self.config_path.suffix.lower() == '.yaml' or self.config_path.suffix.lower() == '.yml':
                        self.config = yaml.safe_load(f)
                    elif self.config_path.suffix.lower() == '.json':
                        self.config = json.load(f)
                    else:
                        self.logger.error(f"不支持的配置文件格式: {self.config_path.suffix}")
                        return False
                
                # 合并默认配置
                self.config = self._merge_configs(self.default_config, self.config)
                
                self.logger.info(f"配置文件加载成功: {self.config_path}")
                return True
            else:
                self.logger.warning(f"配置文件不存在，使用默认配置: {self.config_path}")
                self.config = self.default_config.copy()
                
                # 创建默认配置文件
                self.save_config()
                return True
                
        except Exception as e:
            self.logger.error(f"加载配置文件失败: {str(e)}")
            self.config = self.default_config.copy()
            return False
    
    def save_config(self) -> bool:
        """
        保存配置文件
        
        Returns:
            bool: 保存是否成功
        """
        try:
            # 确保目录存在
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                if self.config_path.suffix.lower() == '.yaml' or self.config_path.suffix.lower() == '.yml':
                    yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True, indent=2)
                elif self.config_path.suffix.lower() == '.json':
                    json.dump(self.config, f, ensure_ascii=False, indent=2)
                else:
                    self.logger.error(f"不支持的配置文件格式: {self.config_path.suffix}")
                    return False
            
            self.logger.info(f"配置文件保存成功: {self.config_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"保存配置文件失败: {str(e)}")
            return False
    
    def _merge_configs(self, default: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
        """
        合并配置字典
        
        Args:
            default: 默认配置
            user: 用户配置
            
        Returns:
            Dict: 合并后的配置
        """
        result = default.copy()
        
        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            key_path: 配置键路径，用点分隔，如 'camera.resolution'
            default: 默认值
            
        Returns:
            Any: 配置值
        """
        try:
            keys = key_path.split('.')
            value = self.config
            
            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return default
            
            return value
            
        except Exception as e:
            self.logger.error(f"获取配置值失败: {key_path}, {str(e)}")
            return default
    
    def set(self, key_path: str, value: Any) -> bool:
        """
        设置配置值
        
        Args:
            key_path: 配置键路径，用点分隔
            value: 配置值
            
        Returns:
            bool: 设置是否成功
        """
        try:
            keys = key_path.split('.')
            config = self.config
            
            # 导航到目标位置
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
    
    def get_camera_config(self) -> Dict[str, Any]:
        """
        获取摄像头配置
        
        Returns:
            Dict: 摄像头配置
        """
        return self.get('camera', {})
    
    def get_mqtt_config(self) -> Dict[str, Any]:
        """
        获取MQTT配置
        
        Returns:
            Dict: MQTT配置
        """
        return self.get('mqtt', {})
    
    def get_processing_config(self) -> Dict[str, Any]:
        """
        获取处理配置
        
        Returns:
            Dict: 处理配置
        """
        return self.get('processing', {})
    
    def get_system_config(self) -> Dict[str, Any]:
        """
        获取系统配置
        
        Returns:
            Dict: 系统配置
        """
        return self.get('system', {})
    
    def is_camera_enabled(self) -> bool:
        """
        检查摄像头是否启用
        
        Returns:
            bool: 摄像头是否启用
        """
        return self.get('camera.enabled', True)
    
    def is_mqtt_enabled(self) -> bool:
        """
        检查MQTT是否启用
        
        Returns:
            bool: MQTT是否启用
        """
        return self.get('mqtt.enabled', False)
    
    def is_debug_mode(self) -> bool:
        """
        检查是否为调试模式
        
        Returns:
            bool: 是否为调试模式
        """
        return self.get('system.debug', False) or self.get('debug.enabled', False)
    
    def get_log_level(self) -> str:
        """
        获取日志级别
        
        Returns:
            str: 日志级别
        """
        return self.get('system.log_level', 'INFO')
    
    def validate_config(self) -> Dict[str, Any]:
        """
        验证配置
        
        Returns:
            Dict: 验证结果
        """
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        try:
            # 验证摄像头配置
            camera_config = self.get_camera_config()
            if camera_config.get('enabled', True):
                resolution = camera_config.get('resolution', [1280, 1024])
                if not isinstance(resolution, list) or len(resolution) != 2:
                    validation_result['errors'].append("摄像头分辨率配置无效")
                
                device_id = camera_config.get('device_id', 0)
                if not isinstance(device_id, int) or device_id < 0:
                    validation_result['errors'].append("摄像头设备ID无效")
            
            # 验证MQTT配置
            mqtt_config = self.get_mqtt_config()
            if mqtt_config.get('enabled', False):
                broker_host = mqtt_config.get('broker_host')
                if not broker_host:
                    validation_result['errors'].append("MQTT代理主机未配置")
                
                broker_port = mqtt_config.get('broker_port', 1883)
                if not isinstance(broker_port, int) or broker_port <= 0 or broker_port > 65535:
                    validation_result['errors'].append("MQTT代理端口无效")
            
            # 验证处理配置
            processing_config = self.get_processing_config()
            interval = processing_config.get('interval', 1.0)
            if not isinstance(interval, (int, float)) or interval <= 0:
                validation_result['errors'].append("处理间隔配置无效")
            
            # 设置验证结果
            if validation_result['errors']:
                validation_result['valid'] = False
            
            return validation_result
            
        except Exception as e:
            validation_result['valid'] = False
            validation_result['errors'].append(f"配置验证失败: {str(e)}")
            return validation_result
    
    def reload_config(self) -> bool:
        """
        重新加载配置
        
        Returns:
            bool: 重新加载是否成功
        """
        self.logger.info("重新加载配置文件...")
        return self.load_config()
    
    def backup_config(self, backup_path: str = None) -> bool:
        """
        备份配置文件
        
        Args:
            backup_path: 备份文件路径
            
        Returns:
            bool: 备份是否成功
        """
        try:
            if backup_path is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_path = self.config_path.parent / f"backup_{timestamp}_{self.config_path.name}"
            
            backup_path = Path(backup_path)
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 复制配置文件
            import shutil
            shutil.copy2(self.config_path, backup_path)
            
            self.logger.info(f"配置文件备份成功: {backup_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"配置文件备份失败: {str(e)}")
            return False
    
    def get_all_config(self) -> Dict[str, Any]:
        """
        获取完整配置
        
        Returns:
            Dict: 完整配置
        """
        return self.config.copy()
    
    def update_config(self, new_config: Dict[str, Any]) -> bool:
        """
        更新配置
        
        Args:
            new_config: 新配置
            
        Returns:
            bool: 更新是否成功
        """
        try:
            self.config = self._merge_configs(self.config, new_config)
            self.logger.info("配置已更新")
            return True
            
        except Exception as e:
            self.logger.error(f"更新配置失败: {str(e)}")
            return False


# 使用示例
if __name__ == "__main__":
    import logging
    from datetime import datetime
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("测试配置管理器...")
    
    try:
        # 创建配置管理器
        config_manager = ConfigManager()
        
        # 验证配置
        validation = config_manager.validate_config()
        print(f"配置验证结果: {validation}")
        
        # 获取配置值
        camera_enabled = config_manager.is_camera_enabled()
        mqtt_enabled = config_manager.is_mqtt_enabled()
        log_level = config_manager.get_log_level()
        
        print(f"摄像头启用: {camera_enabled}")
        print(f"MQTT启用: {mqtt_enabled}")
        print(f"日志级别: {log_level}")
        
        # 获取特定配置
        camera_resolution = config_manager.get('camera.resolution')
        mqtt_broker = config_manager.get('mqtt.broker_host')
        
        print(f"摄像头分辨率: {camera_resolution}")
        print(f"MQTT代理: {mqtt_broker}")
        
        # 设置配置值
        config_manager.set('system.debug', True)
        debug_mode = config_manager.is_debug_mode()
        print(f"调试模式: {debug_mode}")
        
        # 保存配置
        if config_manager.save_config():
            print("配置保存成功")
        
        print("配置管理器测试完成")
        
    except Exception as e:
        print(f"测试失败: {str(e)}")