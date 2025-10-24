#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MQTT管理器 - 重构版本
提供统一的MQTT通信接口，支持连接管理、消息发布订阅和错误处理

重构改进：
1. 统一API命名规范：所有方法使用动词开头，如connect_broker()、publish_message()等
2. 增强错误处理和重连机制
3. 完善文档字符串和类型注解
4. 统一消息格式和主题管理
"""

import json
import time
import threading
import logging
from typing import Optional, Callable, Dict, Any, List, Union
from datetime import datetime

try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False
    logging.warning("paho-mqtt库不可用，MQTT功能将受限")


class MQTTManager:
    """
    MQTT管理器类
    提供统一的MQTT连接、发布、订阅和错误处理功能
    
    主要功能：
    - MQTT代理连接管理
    - 消息发布和订阅
    - 自动重连机制
    - 消息队列和缓存
    - 连接状态监控
    """
    
    def __init__(self, broker_config: Dict[str, Any]):
        """
        初始化MQTT管理器
        
        Args:
            broker_config: MQTT代理配置字典，包含：
                - host: 代理地址
                - port: 代理端口
                - username: 用户名（可选）
                - password: 密码（可选）
                - client_id: 客户端ID
                - keepalive: 心跳间隔（秒）
                - reconnect_delay: 重连延迟（秒）
                - max_reconnect_attempts: 最大重连次数
        """
        # 配置参数
        self.broker_host = broker_config.get('host', 'localhost')
        self.broker_port = broker_config.get('port', 1883)
        self.username = broker_config.get('username')
        self.password = broker_config.get('password')
        self.client_id = broker_config.get('client_id', 'mqtt_client')
        self.keepalive = broker_config.get('keepalive', 60)
        self.reconnect_delay = broker_config.get('reconnect_delay', 5)
        self.max_reconnect_attempts = broker_config.get('max_reconnect_attempts', 10)
        
        # 连接状态
        self.is_connected = False
        self.is_connecting = False
        self.connection_start_time = None
        self.reconnect_attempts = 0
        
        # MQTT客户端
        self.client: Optional[mqtt.Client] = None
        
        # 线程相关
        self.connection_thread: Optional[threading.Thread] = None
        self.reconnect_thread: Optional[threading.Thread] = None
        self.message_queue_lock = threading.Lock()
        
        # 回调函数
        self.message_callbacks: Dict[str, Callable] = {}
        self.connection_callback: Optional[Callable[[bool], None]] = None
        
        # 消息队列（用于离线时缓存消息）
        self.message_queue: List[Dict[str, Any]] = []
        self.max_queue_size = 1000
        
        # 统计信息
        self.stats = {
            'messages_sent': 0,
            'messages_received': 0,
            'connection_attempts': 0,
            'disconnections': 0,
            'start_time': datetime.now().isoformat()
        }
        
        # 日志
        self.logger = logging.getLogger(f"{__name__}.MQTTManager")
        self.logger.info(f"MQTT管理器初始化完成: {self.client_id}")
    
    def connect_to_broker(self) -> bool:
        """
        连接到MQTT代理
        
        Returns:
            bool: 连接成功返回True
        """
        try:
            if self.is_connected:
                self.logger.warning("已连接到MQTT代理")
                return True
                
            if self.is_connecting:
                self.logger.warning("正在连接中...")
                return False
                
            if not MQTT_AVAILABLE:
                self.logger.error("paho-mqtt库不可用，无法连接")
                return False
                
            self.logger.info(f"开始连接MQTT代理: {self.broker_host}:{self.broker_port}")
            self.is_connecting = True
            self.stats['connection_attempts'] += 1
            self.connection_start_time = datetime.now()
            
            # 创建MQTT客户端
            self.client = mqtt.Client(client_id=self.client_id, clean_session=True)
            
            # 设置认证信息
            if self.username and self.password:
                self.client.username_pw_set(self.username, self.password)
                
            # 设置回调函数
            self.client.on_connect = self._on_connect_handler
            self.client.on_disconnect = self._on_disconnect_handler
            self.client.on_message = self._on_message_handler
            self.client.on_publish = self._on_publish_handler
            self.client.on_subscribe = self._on_subscribe_handler
            
            # 设置连接参数
            self.client.reconnect_delay_set(min_delay=1, max_delay=60)
            
            # 开始连接
            result = self.client.connect(self.broker_host, self.broker_port, self.keepalive)
            
            if result == 0:
                # 启动网络循环
                self.client.loop_start()
                
                # 等待连接完成（最多等待30秒）
                timeout = 30
                start_time = time.time()
                while not self.is_connected and (time.time() - start_time) < timeout:
                    time.sleep(0.1)
                    
                if self.is_connected:
                    self.logger.info("MQTT代理连接成功")
                    return True
                else:
                    self.logger.error("MQTT代理连接超时")
                    self.client.loop_stop()
                    return False
            else:
                self.logger.error(f"MQTT代理连接失败: 错误码 {result}")
                return False
                
        except Exception as e:
            self.logger.error(f"连接MQTT代理失败: {str(e)}")
            return False
        finally:
            self.is_connecting = False
    
    def disconnect_from_broker(self) -> bool:
        """
        断开与MQTT代理的连接
        
        Returns:
            bool: 断开成功返回True
        """
        try:
            if not self.is_connected or not self.client:
                self.logger.debug("未连接到MQTT代理")
                return True
                
            self.logger.info("断开MQTT代理连接")
            
            # 停止重连线程
            if self.reconnect_thread and self.reconnect_thread.is_alive():
                self.reconnect_thread.join(timeout=5)
                
            # 断开连接
            result = self.client.disconnect()
            
            # 停止网络循环
            self.client.loop_stop()
            
            # 清理状态
            self.is_connected = False
            self.client = None
            
            self.logger.info("MQTT代理连接已断开")
            return True
            
        except Exception as e:
            self.logger.error(f"断开MQTT代理连接失败: {str(e)}")
            return False
    
    def publish_message(self, topic: str, payload: Union[str, dict, bytes], 
                       qos: int = 1, retain: bool = False) -> bool:
        """
        发布消息到指定主题
        
        Args:
            topic: 消息主题
            payload: 消息内容（字符串、字典或字节）
            qos: 服务质量等级（0, 1, 2）
            retain: 是否保留消息
            
        Returns:
            bool: 发布成功返回True
        """
        try:
            # 转换消息格式
            if isinstance(payload, dict):
                message = json.dumps(payload, ensure_ascii=False, default=str)
            elif isinstance(payload, str):
                message = payload
            elif isinstance(payload, bytes):
                message = payload
            else:
                message = str(payload)
                
            self.logger.debug(f"发布消息: topic={topic}, qos={qos}, retain={retain}")
            
            # 如果未连接，尝试缓存消息
            if not self.is_connected:
                self.logger.warning(f"未连接到代理，缓存消息: {topic}")
                self._cache_message(topic, message, qos, retain)
                return False
                
            # 发布消息
            result = self.client.publish(topic, message, qos, retain)
            
            if result.is_published():
                self.stats['messages_sent'] += 1
                self.logger.debug(f"消息发布成功: {topic}")
                return True
            else:
                self.logger.warning(f"消息发布失败: {topic}")
                return False
                
        except Exception as e:
            self.logger.error(f"发布消息失败: {str(e)}")
            return False
    
    def subscribe_to_topic(self, topic: str, callback: Optional[Callable] = None, 
                          qos: int = 1) -> bool:
        """
        订阅指定主题
        
        Args:
            topic: 订阅主题（支持通配符）
            callback: 消息回调函数
            qos: 服务质量等级
            
        Returns:
            bool: 订阅成功返回True
        """
        try:
            if not self.is_connected:
                self.logger.error("未连接到MQTT代理，无法订阅")
                return False
                
            self.logger.info(f"订阅主题: {topic}")
            
            # 注册回调函数
            if callback:
                self.message_callbacks[topic] = callback
                
            # 发送订阅请求
            result, mid = self.client.subscribe(topic, qos)
            
            if result == 0:
                self.logger.info(f"主题订阅成功: {topic}")
                return True
            else:
                self.logger.error(f"主题订阅失败: {topic}, 错误码: {result}")
                return False
                
        except Exception as e:
            self.logger.error(f"订阅主题失败: {str(e)}")
            return False
    
    def unsubscribe_from_topic(self, topic: str) -> bool:
        """
        取消订阅指定主题
        
        Args:
            topic: 要取消订阅的主题
            
        Returns:
            bool: 取消订阅成功返回True
        """
        try:
            if not self.is_connected:
                self.logger.debug("未连接到MQTT代理")
                return True
                
            self.logger.info(f"取消订阅主题: {topic}")
            
            # 移除回调函数
            if topic in self.message_callbacks:
                del self.message_callbacks[topic]
                
            # 发送取消订阅请求
            result, mid = self.client.unsubscribe(topic)
            
            if result == 0:
                self.logger.info(f"取消订阅成功: {topic}")
                return True
            else:
                self.logger.error(f"取消订阅失败: {topic}, 错误码: {result}")
                return False
                
        except Exception as e:
            self.logger.error(f"取消订阅失败: {str(e)}")
            return False
    
    def get_connection_status(self) -> Dict[str, Any]:
        """
        获取连接状态信息
        
        Returns:
            Dict[str, Any]: 连接状态信息
        """
        return {
            'is_connected': self.is_connected,
            'is_connecting': self.is_connecting,
            'broker_host': self.broker_host,
            'broker_port': self.broker_port,
            'client_id': self.client_id,
            'reconnect_attempts': self.reconnect_attempts,
            'connection_start_time': self.connection_start_time.isoformat() if self.connection_start_time else None,
            'uptime': (datetime.now() - datetime.fromisoformat(self.stats['start_time'])).total_seconds() if self.stats['start_time'] else 0
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        return self.stats.copy()
    
    def set_connection_callback(self, callback: Optional[Callable[[bool], None]]):
        """
        设置连接状态变化回调
        
        Args:
            callback: 回调函数，参数为连接状态(bool)
        """
        self.connection_callback = callback
    
    def start_auto_reconnect(self) -> bool:
        """
        启动自动重连机制
        
        Returns:
            bool: 启动成功返回True
        """
        try:
            if self.reconnect_thread and self.reconnect_thread.is_alive():
                self.logger.debug("自动重连已在运行")
                return True
                
            self.logger.info("启动自动重连机制")
            
            self.reconnect_thread = threading.Thread(
                target=self._reconnect_loop, 
                name="MQTTReconnect"
            )
            self.reconnect_thread.daemon = True
            self.reconnect_thread.start()
            
            return True
            
        except Exception as e:
            self.logger.error(f"启动自动重连失败: {str(e)}")
            return False
    
    def stop_auto_reconnect(self) -> bool:
        """
        停止自动重连机制
        
        Returns:
            bool: 停止成功返回True
        """
        try:
            self.logger.info("停止自动重连机制")
            
            # 停止重连线程
            if self.reconnect_thread and self.reconnect_thread.is_alive():
                self.reconnect_thread.join(timeout=5)
                
            return True
            
        except Exception as e:
            self.logger.error(f"停止自动重连失败: {str(e)}")
            return False
    
    def flush_message_queue(self) -> int:
        """
        清空并发送消息队列中的所有消息
        
        Returns:
            int: 成功发送的消息数量
        """
        try:
            if not self.is_connected:
                self.logger.debug("未连接到代理，无法清空消息队列")
                return 0
                
            with self.message_queue_lock:
                if not self.message_queue:
                    return 0
                    
                self.logger.info(f"开始发送消息队列中的 {len(self.message_queue)} 条消息")
                
                sent_count = 0
                failed_messages = []
                
                for message_data in self.message_queue:
                    try:
                        result = self.client.publish(
                            message_data['topic'],
                            message_data['message'],
                            message_data['qos'],
                            message_data['retain']
                        )
                        
                        if result.is_published():
                            sent_count += 1
                            self.stats['messages_sent'] += 1
                        else:
                            failed_messages.append(message_data)
                            
                    except Exception as e:
                        self.logger.error(f"发送队列消息失败: {str(e)}")
                        failed_messages.append(message_data)
                        
                # 更新消息队列
                self.message_queue = failed_messages
                
                self.logger.info(f"消息队列处理完成: 成功 {sent_count}, 失败 {len(failed_messages)}")
                return sent_count
                
        except Exception as e:
            self.logger.error(f"清空消息队列失败: {str(e)}")
            return 0
    
    def _cache_message(self, topic: str, message: Union[str, bytes], 
                      qos: int, retain: bool) -> bool:
        """
        缓存消息到队列（内部方法）
        
        Args:
            topic: 消息主题
            message: 消息内容
            qos: 服务质量等级
            retain: 是否保留
            
        Returns:
            bool: 缓存成功返回True
        """
        try:
            with self.message_queue_lock:
                if len(self.message_queue) >= self.max_queue_size:
                    # 队列已满，移除最旧的消息
                    self.message_queue.pop(0)
                    self.logger.warning("消息队列已满，移除最旧消息")
                    
                message_data = {
                    'topic': topic,
                    'message': message,
                    'qos': qos,
                    'retain': retain,
                    'timestamp': datetime.now().isoformat()
                }
                
                self.message_queue.append(message_data)
                self.logger.debug(f"消息已缓存: {topic}")
                return True
                
        except Exception as e:
            self.logger.error(f"缓存消息失败: {str(e)}")
            return False
    
    def _on_connect_handler(self, client, userdata, flags, rc):
        """
        连接回调处理（内部方法）
        """
        try:
            if rc == 0:
                self.is_connected = True
                self.reconnect_attempts = 0
                self.logger.info("MQTT代理连接已建立")
                
                # 清空消息队列
                self.flush_message_queue()
                
                # 调用连接回调
                if self.connection_callback:
                    try:
                        self.connection_callback(True)
                    except Exception as e:
                        self.logger.error(f"连接回调错误: {str(e)}")
                        
            else:
                self.is_connected = False
                error_messages = {
                    1: "连接被拒绝 - 协议版本错误",
                    2: "连接被拒绝 - 客户端标识符错误",
                    3: "连接被拒绝 - 服务器不可用",
                    4: "连接被拒绝 - 用户名或密码错误",
                    5: "连接被拒绝 - 未授权"
                }
                error_msg = error_messages.get(rc, f"连接失败 - 错误码: {rc}")
                self.logger.error(f"MQTT代理连接失败: {error_msg}")
                
        except Exception as e:
            self.logger.error(f"连接回调处理失败: {str(e)}")
    
    def _on_disconnect_handler(self, client, userdata, rc):
        """
        断开连接回调处理（内部方法）
        """
        try:
            self.is_connected = False
            self.stats['disconnections'] += 1
            
            if rc == 0:
                self.logger.info("MQTT代理连接已正常断开")
            else:
                self.logger.warning(f"MQTT代理连接异常断开: 错误码 {rc}")
                
            # 调用连接回调
            if self.connection_callback:
                try:
                    self.connection_callback(False)
                except Exception as e:
                    self.logger.error(f"断开连接回调错误: {str(e)}")
                    
        except Exception as e:
            self.logger.error(f"断开连接回调处理失败: {str(e)}")
    
    def _on_message_handler(self, client, userdata, msg):
        """
        消息接收回调处理（内部方法）
        """
        try:
            self.stats['messages_received'] += 1
            
            # 解码消息
            try:
                if isinstance(msg.payload, bytes):
                    payload_str = msg.payload.decode('utf-8')
                else:
                    payload_str = str(msg.payload)
                    
                # 尝试解析JSON
                try:
                    payload_data = json.loads(payload_str)
                except json.JSONDecodeError:
                    payload_data = payload_str
                    
            except Exception as e:
                self.logger.error(f"消息解码失败: {str(e)}")
                payload_data = str(msg.payload)
                
            self.logger.debug(f"收到消息: topic={msg.topic}, qos={msg.qos}")
            
            # 查找匹配的回调函数
            matched = False
            for subscribed_topic, callback in self.message_callbacks.items():
                if self._topic_matches(subscribed_topic, msg.topic):
                    try:
                        callback(msg.topic, payload_data)
                        matched = True
                    except Exception as e:
                        self.logger.error(f"消息回调处理失败: {str(e)}")
                        
            if not matched:
                self.logger.debug(f"没有匹配的消息回调: {msg.topic}")
                
        except Exception as e:
            self.logger.error(f"消息处理失败: {str(e)}")
    
    def _on_publish_handler(self, client, userdata, mid):
        """
        消息发布回调处理（内部方法）
        """
        # 发布成功回调，可用于跟踪消息状态
        pass
    
    def _on_subscribe_handler(self, client, userdata, mid, granted_qos):
        """
        订阅回调处理（内部方法）
        """
        self.logger.debug(f"订阅确认: mid={mid}, granted_qos={granted_qos}")
    
    def _reconnect_loop(self):
        """
        自动重连循环（内部线程方法）
        """
        self.logger.info("自动重连循环已启动")
        
        while True:
            try:
                if self.is_connected:
                    time.sleep(1)
                    continue
                    
                # 检查是否需要重连
                if self.reconnect_attempts >= self.max_reconnect_attempts:
                    self.logger.error(f"重连次数已达上限 ({self.max_reconnect_attempts})，停止重连")
                    break
                    
                # 等待重连延迟
                delay = min(self.reconnect_delay * (2 ** self.reconnect_attempts), 60)
                self.logger.info(f"等待 {delay} 秒后重连 (第 {self.reconnect_attempts + 1} 次)")
                time.sleep(delay)
                
                # 尝试重连
                if self.connect_to_broker():
                    self.logger.info("重连成功")
                else:
                    self.reconnect_attempts += 1
                    self.logger.warning(f"重连失败 (第 {self.reconnect_attempts} 次)")
                    
            except Exception as e:
                self.logger.error(f"重连循环错误: {str(e)}")
                time.sleep(5)
                
        self.logger.info("自动重连循环已停止")
    
    def _topic_matches(self, subscribed_topic: str, received_topic: str) -> bool:
        """
        检查主题是否匹配（支持通配符）
        
        Args:
            subscribed_topic: 订阅的主题
            received_topic: 收到的主题
            
        Returns:
            bool: 匹配返回True
        """
        try:
            # 简单的通配符匹配
            if subscribed_topic == received_topic:
                return True
                
            # 支持单级通配符 +
            if '+' in subscribed_topic:
                sub_parts = subscribed_topic.split('/')
                rec_parts = received_topic.split('/')
                
                if len(sub_parts) != len(rec_parts):
                    return False
                    
                for sub_part, rec_part in zip(sub_parts, rec_parts):
                    if sub_part != '+' and sub_part != rec_part:
                        return False
                        
                return True
                
            # 支持多级通配符 #
            if '#' in subscribed_topic:
                sub_parts = subscribed_topic.split('/')
                rec_parts = received_topic.split('/')
                
                # # 必须是最后一个字符
                if sub_parts[-1] != '#':
                    return False
                    
                # 检查前面的部分是否匹配
                for i in range(len(sub_parts) - 1):
                    if i >= len(rec_parts):
                        return False
                    if sub_parts[i] != rec_parts[i] and sub_parts[i] != '+':
                        return False
                        
                return True
                
            return False
            
        except Exception as e:
            self.logger.error(f"主题匹配错误: {str(e)}")
            return False


# 向后兼容的别名（用于过渡期）
class SorterMQTTManager:
    """
    分拣系统专用MQTT管理器（向后兼容）
    提供旧版本的方法名映射和专用主题管理
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化分拣系统MQTT管理器
        
        Args:
            config: 配置字典，支持多种格式
        """
        self.logger = logging.getLogger(f"{__name__}.SorterMQTTManager")
        
        # 解析配置
        broker_config = self._parse_config(config)
        
        # 创建基础MQTT管理器
        self.manager = MQTTManager(broker_config)
        
        # 主题配置
        self.topics = broker_config.get('topics', {})
        
        self.logger.info("分拣系统MQTT管理器初始化完成")
    
    def connect(self) -> bool:
        """
        连接到MQTT代理（兼容旧版本）
        
        Returns:
            bool: 连接成功返回True
        """
        self.logger.warning("connect() 已弃用，请使用 connect_to_broker()")
        return self.manager.connect_to_broker()
    
    def disconnect(self) -> bool:
        """
        断开MQTT代理连接（兼容旧版本）
        
        Returns:
            bool: 断开成功返回True
        """
        return self.manager.disconnect_from_broker()
    
    def publish_message(self, topic: str, payload: Union[str, dict, bytes], 
                       qos: int = 1, retain: bool = False) -> bool:
        """
        发布消息（兼容旧版本）
        
        Args:
            topic: 消息主题
            payload: 消息内容
            qos: 服务质量等级
            retain: 是否保留消息
            
        Returns:
            bool: 发布成功返回True
        """
        return self.manager.publish_message(topic, payload, qos, retain)
    
    def publish_status(self, status: str, client_id: str = None) -> bool:
        """
        发布状态消息（专用方法）
        
        Args:
            status: 状态信息
            client_id: 客户端ID（可选）
            
        Returns:
            bool: 发布成功返回True
        """
        topic = self.topics.get('status', 'pi_sorter/status')
        payload = {
            'timestamp': datetime.now().isoformat(),
            'client_id': client_id or self.manager.client_id,
            'status': status
        }
        return self.publish_message(topic, payload)
    
    def publish_result(self, item_id: str, grade: str, **kwargs) -> bool:
        """
        发布分拣结果（专用方法）
        
        Args:
            item_id: 物品ID
            grade: 分拣等级
            **kwargs: 其他结果参数
            
        Returns:
            bool: 发布成功返回True
        """
        topic = self.topics.get('results', 'pi_sorter/results')
        payload = {
            'item_id': item_id,
            'grade': grade,
            'timestamp': datetime.now().isoformat(),
            **kwargs
        }
        return self.publish_message(topic, payload)
    
    def publish_image(self, filename: str, image_data: bytes, 
                     size_bytes: int = None, use_base64: bool = True) -> bool:
        """
        发布图像消息（专用方法）
        
        Args:
            filename: 图像文件名
            image_data: 图像数据
            size_bytes: 图像大小（字节）
            use_base64: 是否使用Base64编码
            
        Returns:
            bool: 发布成功返回True
        """
        import base64
        
        topic = self.topics.get('images', 'pi_sorter/images')
        
        if use_base64:
            # Base64编码版本
            payload = {
                'type': 'image',
                'filename': filename,
                'size_bytes': size_bytes or len(image_data),
                'encoding': 'base64',
                'content': base64.b64encode(image_data).decode('utf-8'),
                'timestamp': datetime.now().isoformat()
            }
        else:
            # 元数据引用版本
            payload = {
                'type': 'image_ref',
                'filename': filename,
                'path': f"/data/images/{filename}",
                'size_bytes': size_bytes or len(image_data),
                'timestamp': datetime.now().isoformat(),
                'note': 'image too large to inline; sending path only'
            }
            
        return self.publish_message(topic, payload)
    
    def publish_alert(self, alert_type: str, level: str, message: str) -> bool:
        """
        发布告警消息（专用方法）
        
        Args:
            alert_type: 告警类型
            level: 告警级别
            message: 告警消息
            
        Returns:
            bool: 发布成功返回True
        """
        topic = self.topics.get('alerts', 'pi_sorter/alerts')
        payload = {
            'type': alert_type,
            'level': level,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        return self.publish_message(topic, payload)
    
    def subscribe_to_status(self, callback: Callable) -> bool:
        """
        订阅状态主题（专用方法）
        
        Args:
            callback: 消息回调函数
            
        Returns:
            bool: 订阅成功返回True
        """
        topic = self.topics.get('status', 'pi_sorter/status')
        return self.manager.subscribe_to_topic(topic, callback)
    
    def subscribe_to_results(self, callback: Callable) -> bool:
        """
        订阅结果主题（专用方法）
        
        Args:
            callback: 消息回调函数
            
        Returns:
            bool: 订阅成功返回True
        """
        topic = self.topics.get('results', 'pi_sorter/results')
        return self.manager.subscribe_to_topic(topic, callback)
    
    def subscribe_to_images(self, callback: Callable) -> bool:
        """
        订阅图像主题（专用方法）
        
        Args:
            callback: 消息回调函数
            
        Returns:
            bool: 订阅成功返回True
        """
        topic = self.topics.get('images', 'pi_sorter/images')
        return self.manager.subscribe_to_topic(topic, callback)
    
    def get_connection_status(self) -> Dict[str, Any]:
        """
        获取连接状态（兼容旧版本）
        
        Returns:
            Dict[str, Any]: 连接状态信息
        """
        return self.manager.get_connection_status()
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息（兼容旧版本）
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        return self.manager.get_statistics()
    
    def _parse_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析配置（内部方法）
        
        Args:
            config: 原始配置字典
            
        Returns:
            Dict[str, Any]: 解析后的配置
        """
        broker_config = {}
        
        # 优先级1: broker节点
        if 'broker' in config:
            broker_config.update(config['broker'])
        # 优先级2: mqtt节点
        elif 'mqtt' in config:
            broker_config.update(config['mqtt'])
        else:
            # 直接提取配置
            broker_config.update(config)
            
        # 主题配置
        if 'topics' in config:
            broker_config['topics'] = config['topics']
        elif 'mqtt' in config and 'topics' in config['mqtt']:
            broker_config['topics'] = config['mqtt']['topics']
            
        return broker_config


# 模块测试
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🧪 MQTT管理器测试")
    
    # 测试配置
    test_config = {
        'broker': {
            'host': 'test.mosquitto.org',
            'port': 1883,
            'client_id': 'test_client',
            'keepalive': 60
        },
        'topics': {
            'status': 'test/status',
            'results': 'test/results',
            'images': 'test/images',
            'alerts': 'test/alerts'
        }
    }
    
    try:
        # 创建管理器
        manager = SorterMQTTManager(test_config)
        
        # 测试连接
        if manager.connect():
            print("✅ MQTT代理连接成功")
            
            # 测试发布消息
            if manager.publish_status("测试状态"):
                print("✅ 状态消息发布成功")
            else:
                print("❌ 状态消息发布失败")
                
            # 测试发布结果
            if manager.publish_result("test001", "A", length=150.5, diameter=12.3):
                print("✅ 结果消息发布成功")
            else:
                print("❌ 结果消息发布失败")
                
            # 断开连接
            manager.disconnect()
            print("✅ MQTT代理连接已断开")
            
        else:
            print("❌ MQTT代理连接失败")
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        
    print("🧪 测试完成")