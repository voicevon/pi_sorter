#!/usr/bin/env python3
"""
从 ssh pi test 项目引用的MQTT模块
MQTT module referenced from ssh pi test project
"""

import json
import logging
import threading
import time
from datetime import datetime
from typing import Dict, Any, Callable, Optional

try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False
    print("警告: paho-mqtt 库未安装，MQTT功能不可用")


class MQTTClient:
    """
    MQTT客户端类 (从 ssh pi test 项目引用)
    MQTT client class (referenced from ssh pi test project)
    """
    
    def __init__(self, broker_host: str = "localhost", broker_port: int = 1883,
                 client_id: str = None, username: str = None, password: str = None):
        """
        初始化MQTT客户端
        
        Args:
            broker_host: MQTT代理服务器地址
            broker_port: MQTT代理服务器端口
            client_id: 客户端ID
            username: 用户名
            password: 密码
        """
        if not MQTT_AVAILABLE:
            raise ImportError("paho-mqtt 库未安装，无法使用MQTT功能")
        
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.client_id = client_id or f"pi_sorter_{int(time.time())}"
        self.username = username
        self.password = password
        
        # 创建MQTT客户端，兼容 paho-mqtt 2.x 的 callback_api_version
        try:
            self.client = mqtt.Client(
                client_id=self.client_id,
                protocol=mqtt.MQTTv311,
                transport="tcp",
                callback_api_version=getattr(mqtt, 'CallbackAPIVersion', None).VERSION1
                if hasattr(getattr(mqtt, 'CallbackAPIVersion', None), 'VERSION1') else None
            )
        except TypeError:
            # 旧版本不支持 callback_api_version 关键字
            self.client = mqtt.Client(self.client_id)
        
        # 设置认证
        if self.username and self.password:
            self.client.username_pw_set(self.username, self.password)
        
        # 连接状态
        self.is_connected = False
        self.connection_lock = threading.Lock()
        
        # 消息回调
        self.message_callbacks = {}
        self.default_callback = None
        
        # 日志
        self.logger = logging.getLogger(__name__)
        
        # 设置MQTT回调
        # 绑定回调（兼容 v1 API）
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        self.client.on_publish = self._on_publish
        self.client.on_subscribe = self._on_subscribe
        
        # 重连设置
        self.auto_reconnect = True
        self.reconnect_delay = 5
        self.max_reconnect_attempts = 10
        self.reconnect_thread = None
    
    def _on_connect(self, client, userdata, flags, rc, properties=None):
        """连接回调"""
        # 记录最近一次 rc
        try:
            self._last_connect_rc = rc
        except Exception:
            pass
        if rc == 0:
            with self.connection_lock:
                self.is_connected = True
            self.logger.info(f"MQTT连接成功: {self.broker_host}:{self.broker_port}")
        else:
            self.logger.error(f"MQTT连接失败，错误码: {rc}")

    def _on_disconnect(self, client, userdata, rc, properties=None):
        """断开连接回调"""
        with self.connection_lock:
            self.is_connected = False
        
        if rc != 0:
            self.logger.warning(f"MQTT意外断开连接，错误码: {rc}")
            if self.auto_reconnect:
                self._start_reconnect()
        else:
            self.logger.info("MQTT正常断开连接")
    
    def _on_message(self, client, userdata, msg):
        """消息接收回调"""
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')
            
            self.logger.debug(f"收到MQTT消息: {topic} -> {payload}")
            
            # 尝试解析JSON
            try:
                data = json.loads(payload)
            except json.JSONDecodeError:
                data = payload
            
            # 调用对应的回调函数
            if topic in self.message_callbacks:
                self.message_callbacks[topic](topic, data)
            elif self.default_callback:
                self.default_callback(topic, data)
            
        except Exception as e:
            self.logger.error(f"处理MQTT消息时发生错误: {str(e)}")
    
    def _on_publish(self, client, userdata, mid):
        """发布消息回调"""
        self.logger.debug(f"MQTT消息发布成功，消息ID: {mid}")
    
    def _on_subscribe(self, client, userdata, mid, granted_qos):
        """订阅回调"""
        self.logger.debug(f"MQTT订阅成功，消息ID: {mid}, QoS: {granted_qos}")
    
    def _start_reconnect(self):
        """开始重连"""
        if self.reconnect_thread and self.reconnect_thread.is_alive():
            return
        
        self.reconnect_thread = threading.Thread(target=self._reconnect_loop)
        self.reconnect_thread.daemon = True
        self.reconnect_thread.start()
    
    def _reconnect_loop(self):
        """重连循环"""
        attempts = 0
        
        while not self.is_connected and attempts < self.max_reconnect_attempts:
            try:
                attempts += 1
                self.logger.info(f"尝试重连MQTT ({attempts}/{self.max_reconnect_attempts})...")
                
                self.client.reconnect()
                time.sleep(self.reconnect_delay)
                
            except Exception as e:
                self.logger.error(f"MQTT重连失败: {str(e)}")
                time.sleep(self.reconnect_delay)
        
        if not self.is_connected:
            self.logger.error("MQTT重连失败，已达到最大尝试次数")
    
    def connect(self, keepalive: int = 60) -> bool:
        """
        连接到MQTT代理
        
        Args:
            keepalive: 保活时间(秒)
            
        Returns:
            bool: 连接是否成功
        """
        try:
            self.logger.info(
                f"连接MQTT代理: host={self.broker_host}:{self.broker_port}, "
                f"client_id={self.client_id}, username={'SET' if self.username else 'NONE'}"
            )
            
            # 兼容 paho-mqtt 1.x 与 2.x：不依赖 connect 的返回值，统一通过 on_connect 设置连接状态
            # 在 2.x 中，connect 返回值语义发生变化，因此直接启动网络循环并等待回调标记
            self.client.connect(self.broker_host, self.broker_port, keepalive)
            
            # 启动网络循环
            self.client.loop_start()

            # 等待连接完成（由 on_connect 回调置位）
            timeout = 10
            start_time = time.time()
            self._last_connect_rc = None
            self.logger.debug("等待 on_connect 回调以确认连接...")
            while not self.is_connected and (time.time() - start_time) < timeout:
                time.sleep(0.1)

            if self.is_connected:
                return True
            else:
                self.logger.error(f"MQTT连接超时或失败，last_rc={self._last_connect_rc}")
                return False
                
        except Exception as e:
            self.logger.error(f"MQTT连接时发生错误: {str(e)}")
            return False
    
    def disconnect(self):
        """断开MQTT连接"""
        try:
            self.auto_reconnect = False
            self.client.loop_stop()
            self.client.disconnect()
            
            with self.connection_lock:
                self.is_connected = False
            
            self.logger.info("MQTT连接已断开")
            
        except Exception as e:
            self.logger.error(f"断开MQTT连接时发生错误: {str(e)}")
    
    def publish(self, topic: str, payload: Any, qos: int = 0, retain: bool = False) -> bool:
        """
        发布消息
        
        Args:
            topic: 主题
            payload: 消息内容
            qos: 服务质量等级
            retain: 是否保留消息
            
        Returns:
            bool: 发布是否成功
        """
        if not self.is_connected:
            self.logger.error("MQTT未连接，无法发布消息")
            return False
        
        try:
            # 转换为JSON字符串
            if isinstance(payload, (dict, list)):
                payload = json.dumps(payload, ensure_ascii=False)
            elif not isinstance(payload, str):
                payload = str(payload)
            
            result = self.client.publish(topic, payload, qos, retain)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                self.logger.debug(f"MQTT消息发布: {topic} -> {payload}")
                return True
            else:
                self.logger.error(f"MQTT消息发布失败，错误码: {result.rc}")
                return False
                
        except Exception as e:
            self.logger.error(f"发布MQTT消息时发生错误: {str(e)}")
            return False
    
    def subscribe(self, topic: str, callback: Callable[[str, Any], None] = None, qos: int = 0) -> bool:
        """
        订阅主题
        
        Args:
            topic: 主题
            callback: 消息回调函数
            qos: 服务质量等级
            
        Returns:
            bool: 订阅是否成功
        """
        if not self.is_connected:
            self.logger.error("MQTT未连接，无法订阅主题")
            return False
        
        try:
            result = self.client.subscribe(topic, qos)
            
            if result[0] == mqtt.MQTT_ERR_SUCCESS:
                if callback:
                    self.message_callbacks[topic] = callback
                
                self.logger.info(f"MQTT主题订阅成功: {topic}")
                return True
            else:
                self.logger.error(f"MQTT主题订阅失败，错误码: {result[0]}")
                return False
                
        except Exception as e:
            self.logger.error(f"订阅MQTT主题时发生错误: {str(e)}")
            return False
    
    def unsubscribe(self, topic: str) -> bool:
        """
        取消订阅主题
        
        Args:
            topic: 主题
            
        Returns:
            bool: 取消订阅是否成功
        """
        if not self.is_connected:
            self.logger.error("MQTT未连接，无法取消订阅")
            return False
        
        try:
            result = self.client.unsubscribe(topic)
            
            if result[0] == mqtt.MQTT_ERR_SUCCESS:
                # 移除回调
                if topic in self.message_callbacks:
                    del self.message_callbacks[topic]
                
                self.logger.info(f"MQTT主题取消订阅成功: {topic}")
                return True
            else:
                self.logger.error(f"MQTT主题取消订阅失败，错误码: {result[0]}")
                return False
                
        except Exception as e:
            self.logger.error(f"取消订阅MQTT主题时发生错误: {str(e)}")
            return False
    
    def set_default_callback(self, callback: Callable[[str, Any], None]):
        """
        设置默认消息回调函数
        
        Args:
            callback: 回调函数
        """
        self.default_callback = callback
    
    def is_alive(self) -> bool:
        """
        检查连接是否活跃
        
        Returns:
            bool: 连接是否活跃
        """
        return self.is_connected


class SorterMQTTManager:
    """
    芦笋分拣机MQTT管理器 (从 ssh pi test 项目引用并适配)
    Asparagus sorter MQTT manager (referenced from ssh pi test project and adapted)
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化MQTT管理器
        
        Args:
            config: MQTT配置
        """
        self.config = config
        self.client = None
        self.logger = logging.getLogger(__name__)
        
        # 主题配置（优先读取 mqtt.topics，其次读取顶层 topics），统一为 pi_sorter/*
        mqtt_topics = config.get('mqtt', {}).get('topics', {})
        top_topics = config.get('topics', {})
        self.topics = {
            'status': mqtt_topics.get('status') or top_topics.get('status') or 'pi_sorter/status',
            'results': mqtt_topics.get('results') or top_topics.get('results') or 'pi_sorter/results',
            'commands': mqtt_topics.get('commands') or top_topics.get('commands') or 'pi_sorter/commands',
            'images': mqtt_topics.get('images') or top_topics.get('images') or 'pi_sorter/images',
            'alerts': mqtt_topics.get('alerts') or top_topics.get('alerts') or 'pi_sorter/alerts',
            'statistics': mqtt_topics.get('statistics') or top_topics.get('statistics') or 'pi_sorter/statistics',
            'heartbeat': mqtt_topics.get('heartbeat') or top_topics.get('heartbeat') or 'pi_sorter/heartbeat'
        }
        
        # 状态信息
        self.device_status = {
            'online': False,
            'processing': False,
            'camera_status': 'unknown',
            'last_update': None
        }
    
    def initialize(self) -> bool:
        """
        初始化MQTT连接
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            # 获取代理配置
            broker_config = self.config.get('broker', {})
            mqtt_config = self.config.get('mqtt', {})
            
            # 合并配置，优先使用 broker 配置
            client_config = {
                'host': broker_config.get('host') or mqtt_config.get('broker_host', 'localhost'),
                'port': broker_config.get('port') or mqtt_config.get('broker_port', 1883),
                'username': broker_config.get('username') or mqtt_config.get('username'),
                'password': broker_config.get('password') or mqtt_config.get('password'),
                'client_id': broker_config.get('client_id') or mqtt_config.get('client_id', 'pi_sorter')
            }
            
            self.client = MQTTClient(
                broker_host=client_config['host'],
                broker_port=client_config['port'],
                client_id=client_config['client_id'],
                username=client_config['username'],
                password=client_config['password']
            )
            
            # 设置命令回调
            self.client.set_default_callback(self._handle_command)
            
            # 连接MQTT
            # 传入 keepalive（默认 60）
            if self.client.connect(keepalive=mqtt_config.get('keepalive', 60)):
                # 订阅命令主题
                self.client.subscribe(self.topics['commands'], self._handle_command)
                
                # 发布上线状态
                self._publish_status('online', True)
                
                self.logger.info("MQTT管理器初始化成功")
                return True
            else:
                self.logger.error("MQTT连接失败")
                return False
                
        except Exception as e:
            self.logger.error(f"MQTT管理器初始化失败: {str(e)}")
            return False
    
    def _handle_command(self, topic: str, data: Any):
        """
        处理命令消息
        
        Args:
            topic: 主题
            data: 消息数据
        """
        try:
            if topic == self.topics['commands']:
                if isinstance(data, dict):
                    command = data.get('command')
                    params = data.get('params', {})
                    
                    self.logger.info(f"收到命令: {command}, 参数: {params}")
                    
                    # 处理不同命令
                    if command == 'start_sorting':
                        self._handle_start_sorting(params)
                    elif command == 'stop_sorting':
                        self._handle_stop_sorting(params)
                    elif command == 'get_status':
                        self._handle_get_status(params)
                    elif command == 'capture_image':
                        self._handle_capture_image(params)
                    else:
                        self.logger.warning(f"未知命令: {command}")
                
        except Exception as e:
            self.logger.error(f"处理命令时发生错误: {str(e)}")
    
    def _handle_start_sorting(self, params: Dict[str, Any]):
        """处理开始分拣命令"""
        self.device_status['processing'] = True
        self._publish_status('processing', True)
        self.logger.info("开始分拣作业")
    
    def _handle_stop_sorting(self, params: Dict[str, Any]):
        """处理停止分拣命令"""
        self.device_status['processing'] = False
        self._publish_status('processing', False)
        self.logger.info("停止分拣作业")
    
    def _handle_get_status(self, params: Dict[str, Any]):
        """处理获取状态命令"""
        self._publish_device_status()
    
    def _handle_capture_image(self, params: Dict[str, Any]):
        """处理拍照命令"""
        # 这里可以触发摄像头拍照
        self.logger.info("收到拍照命令")
        # TODO: 集成摄像头功能
    
    def publish_sorting_result(self, result: Dict[str, Any]) -> bool:
        """
        发布分拣结果
        
        Args:
            result: 分拣结果数据
            
        Returns:
            bool: 发布是否成功
        """
        if not self.client or not self.client.is_alive():
            return False
        
        try:
            # 添加时间戳
            result['timestamp'] = datetime.now().isoformat()
            
            return self.client.publish(self.topics['results'], result)
            
        except Exception as e:
            self.logger.error(f"发布分拣结果失败: {str(e)}")
            return False
    
    def publish_alert(self, alert_type: str, message: str, level: str = 'info') -> bool:
        """
        发布警报消息
        
        Args:
            alert_type: 警报类型
            message: 警报消息
            level: 警报级别 (info, warning, error)
            
        Returns:
            bool: 发布是否成功
        """
        if not self.client or not self.client.is_alive():
            return False
        
        try:
            alert_data = {
                'type': alert_type,
                'message': message,
                'level': level,
                'timestamp': datetime.now().isoformat()
            }
            
            return self.client.publish(self.topics['alerts'], alert_data)
            
        except Exception as e:
            self.logger.error(f"发布警报失败: {str(e)}")
            return False
    
    def _publish_status(self, key: str, value: Any) -> bool:
        """
        发布状态信息
        
        Args:
            key: 状态键
            value: 状态值
            
        Returns:
            bool: 发布是否成功
        """
        if not self.client or not self.client.is_alive():
            return False
        
        try:
            self.device_status[key] = value
            self.device_status['last_update'] = datetime.now().isoformat()
            
            status_data = {
                key: value,
                'timestamp': datetime.now().isoformat()
            }
            
            return self.client.publish(self.topics['status'], status_data)
            
        except Exception as e:
            self.logger.error(f"发布状态失败: {str(e)}")
            return False
    
    def _publish_device_status(self) -> bool:
        """发布完整设备状态"""
        if not self.client or not self.client.is_alive():
            return False
        
        try:
            self.device_status['last_update'] = datetime.now().isoformat()
            return self.client.publish(self.topics['status'], self.device_status)
            
        except Exception as e:
            self.logger.error(f"发布设备状态失败: {str(e)}")
            return False
    
    def publish_message(self, topic: str, message: Any, qos: int = 0, retain: bool = False) -> bool:
        """
        发布通用消息
        
        Args:
            topic: MQTT主题
            message: 消息内容
            qos: 服务质量等级
            retain: 是否保留消息
            
        Returns:
            bool: 发布是否成功
        """
        if not self.client or not self.client.is_alive():
            self.logger.error("MQTT客户端未连接")
            return False
        
        try:
            return self.client.publish(topic, message, qos, retain)
            
        except Exception as e:
            self.logger.error(f"发布消息失败: {str(e)}")
            return False
    
    def shutdown(self):
        """关闭MQTT管理器"""
        try:
            if self.client:
                # 发布离线状态
                self._publish_status('online', False)
                
                # 断开连接
                self.client.disconnect()
                
            self.logger.info("MQTT管理器已关闭")
            
        except Exception as e:
            self.logger.error(f"关闭MQTT管理器时发生错误: {str(e)}")


# 使用示例
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # MQTT配置
    config = {
        'mqtt': {
            'broker_host': 'localhost',
            'broker_port': 1883,
            'client_id': 'pi_sorter_test',
            'username': None,
            'password': None
        },
        'topics': {
            'status': 'pi_sorter/status',
            'results': 'pi_sorter/results',
            'commands': 'pi_sorter/commands',
            'images': 'pi_sorter/images',
            'alerts': 'pi_sorter/alerts'
        }
    }
    
    # 测试MQTT功能
    if MQTT_AVAILABLE:
        print("测试MQTT功能...")
        
        try:
            manager = SorterMQTTManager(config)
            
            if manager.initialize():
                print("MQTT管理器初始化成功")
                
                # 发布测试结果
                test_result = {
                    'item_id': 'test_001',
                    'grade': 'A',
                    'length': 180.5,
                    'diameter': 12.3,
                    'defects': []
                }
                
                manager.publish_sorting_result(test_result)
                
                # 发布测试警报
                manager.publish_alert('test', '这是一个测试警报', 'info')
                
                # 等待一段时间
                time.sleep(5)
                
                # 关闭管理器
                manager.shutdown()
                
            else:
                print("MQTT管理器初始化失败")
                
        except Exception as e:
            print(f"测试失败: {str(e)}")
    else:
        print("MQTT库不可用，跳过测试")