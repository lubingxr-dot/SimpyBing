#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
侦察-火力打击仿真程序 (完整修复版 - 增强Activity名称输出)
支持Activity状态追踪、日志推送和时间线记录
Generated at: 2025-01-17
"""

import simpy
import random
import json
import asyncio
import websockets
import logging
import time
import queue
import os
import sys
import functools
from typing import Dict, List, Any, Optional, Set, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np
from collections import deque
import threading
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor

# ============================================================================
# Activity时间线记录器模块
# ============================================================================

class ActivityTimelineLogger:
    """Activity执行时间线记录器"""
    
    def __init__(self, log_dir="activity_logs"):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        
        # 时间线日志文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file_path = os.path.join(log_dir, f"activity_timeline_{timestamp}.json")
        
        # 活动执行记录
        self.timeline_records = []
        self.activity_stats = {}
        
        # 初始化日志文件
        self._init_log_file()
    
    def _init_log_file(self):
        """初始化日志文件"""
        initial_data = {
            "simulation_info": {
                "start_time": datetime.now().isoformat(),
                "log_version": "1.0"
            },
            "timeline": []
        }
        
        with open(self.log_file_path, 'w', encoding='utf-8') as f:
            json.dump(initial_data, f, ensure_ascii=False, indent=2)
    
    def log_activity_start(self, activity_name: str, entity_name: str, entity_id: str, sim_time: float):
        """记录Activity开始"""
        record = {
            "event_type": "activity_start",
            "activity_name": activity_name,
            "entity_name": entity_name,
            "entity_id": entity_id,
            "sim_time": sim_time,
            "real_time": datetime.now().isoformat(),
            "timestamp": time.time()
        }
        
        self.timeline_records.append(record)
        self._append_to_file(record)
        
        # 更新统计信息
        if activity_name not in self.activity_stats:
            self.activity_stats[activity_name] = {
                "count": 0,
                "total_duration": 0,
                "executions": []
            }
    
    def log_activity_end(self, activity_name: str, entity_name: str, entity_id: str, 
                        sim_time: float, start_sim_time: float, result: Any = None):
        """记录Activity结束"""
        duration = sim_time - start_sim_time
        
        record = {
            "event_type": "activity_end",
            "activity_name": activity_name,
            "entity_name": entity_name,
            "entity_id": entity_id,
            "sim_time": sim_time,
            "start_sim_time": start_sim_time,
            "duration": duration,
            "real_time": datetime.now().isoformat(),
            "timestamp": time.time(),
            "result": str(result) if result else None
        }
        
        self.timeline_records.append(record)
        self._append_to_file(record)
        
        # 更新统计信息
        if activity_name in self.activity_stats:
            stats = self.activity_stats[activity_name]
            stats["count"] += 1
            stats["total_duration"] += duration
            stats["executions"].append({
                "entity": entity_name,
                "duration": duration,
                "sim_time": sim_time
            })
    
    def _append_to_file(self, record: Dict):
        """追加记录到文件"""
        try:
            # 读取现有数据
            with open(self.log_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 追加新记录
            data["timeline"].append(record)
            
            # 写回文件
            with open(self.log_file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logging.error(f"写入Activity日志失败: {e}")
    
    def generate_summary_report(self, output_file: str):
        """生成执行摘要报告"""
        summary = {
            "total_activities": len(self.activity_stats),
            "total_executions": sum(stats["count"] for stats in self.activity_stats.values()),
            "activity_details": {}
        }
        
        for activity_name, stats in self.activity_stats.items():
            avg_duration = stats["total_duration"] / stats["count"] if stats["count"] > 0 else 0
            summary["activity_details"][activity_name] = {
                "execution_count": stats["count"],
                "total_duration": stats["total_duration"],
                "average_duration": avg_duration,
                "executions": stats["executions"][:10]  # 只保留前10次执行记录
            }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        logging.info(f"Activity执行摘要已保存到: {output_file}")

# 全局Activity记录器实例
activity_logger = ActivityTimelineLogger()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 仿真常量
SIMULATION_END_TIME = 1800  # 30分钟
SIMULATION_START_TIME = 0
TIME_UNIT = 'second'
RUN_MODE = 'step'  # 默认单步模式
STEP_SIZE = 1  # 单步模式下每步1秒
REAL_TIME_RATIO = 5.0  # 5倍速
RANDOM_SEED = 123
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

# WebSocket配置
WS_HOST = '0.0.0.0'
WS_PORT = int(os.environ.get('WS_PORT', 8765))
WS_HEARTBEAT = 5
DEFAULT_LOG_PUSH_INTERVAL = 1.0  # 默认日志推送间隔（秒）

# 消息类型枚举
class MessageType(Enum):
    # 所有消息类型
    STATUS_UPDATE = "status_update"
    LOG_MESSAGE = "log_message"
    LOG_BATCH = "log_batch"  # 批量日志推送
    ENTITY_UPDATE = "entity_update"
    RESOURCE_UPDATE = "resource_update"
    GLOBAL_VAR_UPDATE = "global_var_update"
    EVENT_TRIGGERED = "event_triggered"
    ACTION_STARTED = "action_started"
    ACTION_COMPLETED = "action_completed"
    ACTIVITY_STARTED = "activity_started"
    ACTIVITY_COMPLETED = "activity_completed"
    ALERT = "alert"
    METRIC_UPDATE = "metric_update"
    SIMULATION_STATE_CHANGED = "simulation_state_changed"
    STEP_COMPLETED = "step_completed"

# 运行状态枚举
class RunState(Enum):
    RUNNING = "running"
    PAUSED = "paused"
    STEPPING = "stepping"
    STOPPED = "stopped"

# 消息包装器
@dataclass
class SimulationMessage:
    """仿真消息"""
    type: MessageType
    data: Any
    timestamp: datetime = None
    entity_id: Optional[str] = None
    log_id: int = 0  # 新增：日志唯一ID
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def to_dict(self):
        result = {
            'type': self.type.value,
            'timestamp': self.timestamp.isoformat(),
            'entity_id': self.entity_id,
            'data': self.data
        }
        if self.log_id > 0:
            result['log_id'] = self.log_id
        return result

# 消息收集器（增强版，支持推送和增量）
class MessageCollector:
    """消息收集器 - 存储消息供查询和推送"""
    def __init__(self, max_messages=1000):
        self.messages = deque(maxlen=max_messages)  # 限制消息数量
        self.messages_by_type = {}  # 按类型分组的消息
        self.lock = threading.Lock()
        self.log_id_counter = 0  # 日志ID计数器
        
        # 日志级别优先级
        self.log_levels = {
            'DEBUG': 0,
            'INFO': 1,
            'WARNING': 2,
            'ERROR': 3,
            'CRITICAL': 4
        }
        
        # 初始化各类型的消息队列
        for msg_type in MessageType:
            self.messages_by_type[msg_type] = deque(maxlen=100)
        
        # 日志消息缓存（用于推送）
        self.log_messages_buffer = deque(maxlen=500)
        self.last_push_time = {}  # 记录每个客户端的最后推送时间
    
    def add_message(self, message: SimulationMessage):
        """添加消息到收集器"""
        with self.lock:
            self.messages.append(message)
            self.messages_by_type[message.type].append(message)
            
            # 如果是日志消息，加入日志缓存并分配ID
            if message.type == MessageType.LOG_MESSAGE:
                self.log_id_counter += 1
                message.log_id = self.log_id_counter
                self.log_messages_buffer.append(message)
    
    def get_messages(self, msg_type: MessageType = None, count: int = 50) -> List[Dict]:
        """获取消息"""
        with self.lock:
            if msg_type:
                messages = list(self.messages_by_type.get(msg_type, []))[-count:]
            else:
                messages = list(self.messages)[-count:]
            
            return [msg.to_dict() for msg in messages]
    
    def get_messages_since(self, timestamp: datetime, msg_type: MessageType = None) -> List[Dict]:
        """获取指定时间后的消息"""
        with self.lock:
            if msg_type:
                source = self.messages_by_type.get(msg_type, [])
            else:
                source = self.messages
            
            result = []
            for msg in source:
                if msg.timestamp > timestamp:
                    result.append(msg.to_dict())
            return result
    
    def get_incremental_logs(self, last_id: int, level_filter: str = "INFO", 
                           max_count: int = 50) -> tuple:
        """获取增量日志（从指定ID之后，只返回指定级别及以上）"""
        with self.lock:
            result = []
            new_last_id = last_id
            filter_level = self.log_levels.get(level_filter, 1)
            
            for msg in self.log_messages_buffer:
                if msg.log_id > last_id:
                    log_level = self.log_levels.get(msg.data.get('level', 'INFO'), 1)
                    
                    # 级别过滤：只返回filter_level及以上的日志
                    if log_level >= filter_level:
                        result.append(msg.to_dict())
                        new_last_id = max(new_last_id, msg.log_id)
                        
                        if len(result) >= max_count:
                            break
            
            return result, new_last_id
    
    def clear_old_messages(self, before_timestamp: datetime):
        """清理旧消息"""
        with self.lock:
            # 清理总消息队列
            while self.messages and self.messages[0].timestamp < before_timestamp:
                self.messages.popleft()
            
            # 清理分类消息队列
            for msg_list in self.messages_by_type.values():
                while msg_list and msg_list[0].timestamp < before_timestamp:
                    msg_list.popleft()
            
            # 清理日志缓存
            while self.log_messages_buffer and self.log_messages_buffer[0].timestamp < before_timestamp:
                self.log_messages_buffer.popleft()

# 全局消息收集器
message_collector = MessageCollector()

# WebSocket客户端信息
@dataclass
class ClientInfo:
    """客户端信息"""
    websocket: websockets.WebSocketServerProtocol
    log_push_interval: float = DEFAULT_LOG_PUSH_INTERVAL
    last_log_push_time: datetime = None
    last_log_id: int = 0  # 新增：记录最后推送的日志ID
    log_level_filter: str = "INFO"  # 新增：日志级别过滤，默认INFO及以上
    max_logs_per_push: int = 30  # 新增：每次推送的最大日志数
    push_task: asyncio.Task = None
    
    def __post_init__(self):
        if self.last_log_push_time is None:
            self.last_log_push_time = datetime.now()

# WebSocket连接管理器（增强版）
class WebSocketManager:
    """WebSocket连接管理器"""
    def __init__(self):
        self.clients: Dict[websockets.WebSocketServerProtocol, ClientInfo] = {}
        self.loop = None
        self.lock = threading.Lock()
    
    def set_event_loop(self, loop):
        """设置事件循环"""
        self.loop = loop
    
    def add_client(self, websocket, log_push_interval: float = DEFAULT_LOG_PUSH_INTERVAL):
        """添加客户端"""
        with self.lock:
            client_info = ClientInfo(websocket=websocket, log_push_interval=log_push_interval)
            self.clients[websocket] = client_info
            logging.info(f'客户端连接: {websocket.remote_address}, 日志推送间隔: {log_push_interval}秒, 当前连接数: {len(self.clients)}')
            return client_info
    
    def remove_client(self, websocket):
        """移除客户端"""
        with self.lock:
            if websocket in self.clients:
                client_info = self.clients[websocket]
                # 取消推送任务
                if client_info.push_task and not client_info.push_task.done():
                    client_info.push_task.cancel()
                del self.clients[websocket]
            logging.info(f'客户端断开: {websocket.remote_address}, 当前连接数: {len(self.clients)}')
    
    def get_client(self, websocket) -> Optional[ClientInfo]:
        """获取客户端信息"""
        with self.lock:
            return self.clients.get(websocket)
    
    def update_push_interval(self, websocket, interval: float):
        """更新客户端的推送间隔"""
        with self.lock:
            if websocket in self.clients:
                self.clients[websocket].log_push_interval = interval
                logging.info(f'更新客户端 {websocket.remote_address} 的日志推送间隔为: {interval}秒')

# 全局WebSocket管理器
ws_manager = WebSocketManager()

# 日志和消息收集
def log_and_collect(level: str, message: str, entity: str = None, msg_type: MessageType = MessageType.LOG_MESSAGE, **kwargs):
    """记录日志并收集消息"""
    # 标准日志
    if level == 'INFO':
        logging.info(message)
    elif level == 'DEBUG':
        logging.debug(message)
    elif level == 'WARNING':
        logging.warning(message)
    elif level == 'ERROR':
        logging.error(message)
    
    # 收集消息供查询和推送
    msg_data = {
        'level': level,
        'message': message,
        'entity': entity
    }
    msg_data.update(kwargs)
    
    message_collector.add_message(SimulationMessage(
        type=msg_type,
        data=msg_data,
        entity_id=entity
    ))

# 日志推送任务（优化版）
async def log_push_task(client_info: ClientInfo):
    """定期推送日志的任务 - 增量推送，只推送INFO及以上级别"""
    try:
        empty_push_count = 0
        
        while True:
            await asyncio.sleep(client_info.log_push_interval)
            
            # 获取增量日志（只获取INFO及以上级别）
            logs, new_last_id = message_collector.get_incremental_logs(
                last_id=client_info.last_log_id,
                level_filter=client_info.log_level_filter,
                max_count=client_info.max_logs_per_push
            )
            
            if logs:
                # 推送日志
                await client_info.websocket.send(json.dumps({
                    'type': MessageType.LOG_BATCH.value,
                    'data': {
                        'logs': logs,
                        'count': len(logs),
                        'last_id': new_last_id,
                        'push_interval': client_info.log_push_interval,
                        'has_more': len(logs) >= client_info.max_logs_per_push,
                        'level_filter': client_info.log_level_filter
                    }
                }))
                
                # 更新最后推送的日志ID
                client_info.last_log_id = new_last_id
                empty_push_count = 0
                
            else:
                empty_push_count += 1
                
                # 如果连续5次没有新日志，自动增加推送间隔（最多5秒）
                if empty_push_count >= 5 and client_info.log_push_interval < 5.0:
                    client_info.log_push_interval = min(client_info.log_push_interval * 1.5, 5.0)
                
    except asyncio.CancelledError:
        logging.info(f"日志推送任务被取消: {client_info.websocket.remote_address}")
    except websockets.exceptions.ConnectionClosed:
        logging.info(f"连接已关闭，停止日志推送: {client_info.websocket.remote_address}")
    except Exception as e:
        logging.error(f"日志推送任务错误: {e}")

# 增强的Activity装饰器（增加了activity_name输出）
def enhanced_activity_wrapper(activity_func: Callable) -> Callable:
    """增强的Activity装饰器 - 自动记录执行时间线并发送完成消息"""
    
    @functools.wraps(activity_func)
    def wrapper(env, entity, context):
        # 获取Activity名称（从函数名提取）
        activity_id = activity_func.__name__  # 例如: activity_move_patrol
        activity_name = activity_func.__name__.replace('activity_', '')  # 例如: move_patrol
        
        # 获取Activity的中文名称（从函数文档字符串提取）
        activity_chinese_name = "未知活动"
        if activity_func.__doc__:
            # 从文档字符串中提取中文名称，格式为"活动：XXX"
            doc_lines = activity_func.__doc__.strip().split('\n')
            if doc_lines and doc_lines[0].startswith('活动：'):
                activity_chinese_name = doc_lines[0].replace('活动：', '').strip()
        
        entity_name = getattr(entity, 'name', 'Unknown')
        entity_id = getattr(entity, 'id', 'unknown')
        
        # 记录开始时间
        start_sim_time = env.now
        
        # 记录Activity开始到时间线
        activity_logger.log_activity_start(activity_name, entity_name, entity_id, start_sim_time)
        
        # 记录到运行日志
        log_and_collect('INFO', f'[Activity开始] {entity_name} - {activity_chinese_name} (仿真时间: {start_sim_time:.1f}s)', 
                       entity=entity_name)
        
        # 发送Activity开始消息（增加activity_name和activity_chinese_name字段）
        message_collector.add_message(SimulationMessage(
            type=MessageType.ACTIVITY_STARTED,
            entity_id=entity_id,
            data={
                'activity': activity_id,  # 完整的函数名
                'activity_name': activity_name,  # 不带activity_前缀的名称
                'activity_chinese_name': activity_chinese_name,  # 中文名称
                'entity_name': entity_name,
                'start_time': start_sim_time
            }
        ))
        
        # 更新实体状态（同时存储ID和名称）
        if hasattr(entity, 'update_status'):
            entity.update_status(activity=activity_id)
            # 添加额外的属性来存储名称信息
            entity.current_activity_name = activity_name
            entity.current_activity_chinese_name = activity_chinese_name
        
        try:
            # 执行原始Activity函数
            result = yield from activity_func(env, entity, context)
            
            # 记录结束时间
            end_sim_time = env.now
            duration = end_sim_time - start_sim_time
            
            # 记录Activity结束到时间线
            activity_logger.log_activity_end(activity_name, entity_name, entity_id, 
                                           end_sim_time, start_sim_time, result)
            
            # 记录到运行日志
            log_and_collect('INFO', 
                          f'[Activity完成] {entity_name} - {activity_chinese_name} '
                          f'(仿真时间: {end_sim_time:.1f}s, 耗时: {duration:.1f}s)', 
                          entity=entity_name)
            
            # 发送Activity完成消息（增加activity_name和activity_chinese_name字段）
            message_collector.add_message(SimulationMessage(
                type=MessageType.ACTIVITY_COMPLETED,
                entity_id=entity_id,
                data={
                    'activity': activity_id,  # 完整的函数名
                    'activity_name': activity_name,  # 不带activity_前缀的名称
                    'activity_chinese_name': activity_chinese_name,  # 中文名称
                    'entity_name': entity_name,
                    'start_time': start_sim_time,
                    'end_time': end_sim_time,
                    'duration': duration,
                    'result': str(result) if result else None
                }
            ))
            
            return result
            
        except Exception as e:
            # 记录异常
            end_sim_time = env.now
            activity_logger.log_activity_end(activity_name, entity_name, entity_id, 
                                           end_sim_time, start_sim_time, f"Error: {str(e)}")
            
            log_and_collect('ERROR', 
                          f'[Activity异常] {entity_name} - {activity_chinese_name} - 错误: {str(e)}', 
                          entity=entity_name)
            
            # 发送Activity异常消息（增加activity_name和activity_chinese_name字段）
            message_collector.add_message(SimulationMessage(
                type=MessageType.ACTIVITY_COMPLETED,
                entity_id=entity_id,
                data={
                    'activity': activity_id,  # 完整的函数名
                    'activity_name': activity_name,  # 不带activity_前缀的名称
                    'activity_chinese_name': activity_chinese_name,  # 中文名称
                    'entity_name': entity_name,
                    'start_time': start_sim_time,
                    'end_time': end_sim_time,
                    'error': str(e),
                    'status': 'failed'
                }
            ))
            
            raise
    
    return wrapper

# Helper Classes
class ExpressionEvaluator:
    """安全地计算数学表达式"""
    def __init__(self, context: Dict[str, Any]):
        self.context = context

    def evaluate(self, expression: str) -> Any:
        safe_dict = {
            'abs': abs, 'min': min, 'max': max,
            'pow': pow, 'round': round, 'sum': sum,
            'np': np, 'random': random.random,
            'calculate_patrol_route': self._calculate_patrol_route,
            'analyze_enemy_info': self._analyze_enemy_info
        }
        safe_dict.update(self.context)
        
        try:
            return eval(expression, {'__builtins__': {}}, safe_dict)
        except Exception as e:
            logging.error(f'表达式计算错误: {e}, 表达式: {expression}')
            return None
    
    def _calculate_patrol_route(self, current_position, time):
        """计算巡逻路线"""
        radius = 200
        angle = (time / 100) % (2 * np.pi)
        new_x = 100 + radius * np.cos(angle)
        new_y = 100 + radius * np.sin(angle)
        return {'x': new_x, 'y': new_y, 'z': 0}
    
    def _analyze_enemy_info(self, enemy_info):
        """分析敌情信息"""
        if isinstance(enemy_info, dict):
            strength = enemy_info.get('strength', 'unknown')
            if strength == 'company':
                return 0.8
            elif strength == 'platoon':
                return 0.5
            else:
                return 0.3
        return 0.5

class TimeDistribution:
    """基于概率分布生成时间值"""
    @staticmethod
    def generate(dist_type: str, params: Dict[str, float]) -> float:
        if dist_type == 'constant':
            return params.get('value', 1.0)
        elif dist_type == 'exponential':
            return random.expovariate(1.0 / params.get('rate', 1.0))
        elif dist_type == 'normal':
            return max(0, random.normalvariate(params.get('mean', 1.0), params.get('std', 0.1)))
        elif dist_type == 'uniform':
            return random.uniform(params.get('min', 0.0), params.get('max', 1.0))
        else:
            return 1.0

# 改进的单步暂停检查（增加了activity名称记录）
def check_pause(env: simpy.Environment, entity: Any):
    """检查是否需要暂停 - 改进版"""
    simulation = env.simulation
    
    # 单步模式处理
    if simulation.run_state == RunState.STEPPING:
        # 标记步骤点（增加activity名称信息）
        simulation.step_points.append({
            'time': env.now,
            'entity': entity.name if hasattr(entity, 'name') else str(entity),
            'action': getattr(entity, 'current_action', None),
            'activity': getattr(entity, 'current_activity', None),
            'activity_name': getattr(entity, 'current_activity_name', None),  # 新增
            'activity_chinese_name': getattr(entity, 'current_activity_chinese_name', None)  # 新增
        })
        
        # 等待下一步指令
        while simulation.run_state == RunState.STEPPING and not simulation.step_continue:
            yield env.timeout(0.01)  # 更短的检查间隔
        
        # 重置继续标志
        simulation.step_continue = False
    
    # 暂停模式处理
    while simulation.run_state == RunState.PAUSED:
        yield env.timeout(0.1)

# 基础实体类（增加了activity名称属性）
class BaseEntity:
    """基础实体类"""
    def __init__(self, env: simpy.Environment, entity_id: str, simulation):
        self.env = env
        self.id = entity_id
        self.simulation = simulation
        self.current_action = None
        self.current_activity = None
        self.current_activity_name = None  # 新增：存储activity名称
        self.current_activity_chinese_name = None  # 新增：存储activity中文名称
        self.message_queue = simpy.Store(env)
        
    def update_status(self, action: str = None, activity: str = None):
        """更新当前状态"""
        old_action = self.current_action
        old_activity = self.current_activity
        
        if action:
            self.current_action = action
        if activity:
            self.current_activity = activity
        
        # 收集状态更新消息（增加activity名称信息）
        if action != old_action or activity != old_activity:
            message_collector.add_message(SimulationMessage(
                type=MessageType.ENTITY_UPDATE,
                entity_id=self.id,
                data={
                    'entity_name': self.name,
                    'current_action': self.current_action,
                    'current_activity': self.current_activity,
                    'current_activity_name': self.current_activity_name,  # 新增
                    'current_activity_chinese_name': self.current_activity_chinese_name,  # 新增
                    'position': getattr(self, 'position', None)
                }
            ))
    
    def get_context(self) -> Dict:
        """获取当前上下文"""
        context = {
            'self': self,
            'env': self.env,
            'time': self.env.now,
            'global': self.simulation.global_vars
        }
        
        for attr in dir(self):
            if not attr.startswith('_') and hasattr(self, attr):
                value = getattr(self, attr)
                if isinstance(value, (int, float, str, bool)):
                    context[attr] = value
        
        return context

# 实体类定义（继承改进的基类）

class CommandPost(BaseEntity):
    """指挥所实体"""
    def __init__(self, env: simpy.Environment, entity_id: str, simulation):
        super().__init__(env, entity_id, simulation)
        self.name = '指挥所'
        self.type = 'passive'
        self.position = {'x': 0.0, 'y': 0.0, 'z': 0.0}
        self.attributes = {
            'unit_type': 'command',
            'call_sign': 'Eagle'
        }
        self.alert_level = 1
        self.actions = []

    def start(self):
        """启动实体进程"""
        log_and_collect('INFO', f'{self.name} ({self.attributes["call_sign"]}) 开始运行', entity=self.name)
        self.env.process(self.message_handler())

    def message_handler(self):
        """处理消息"""
        while True:
            try:
                msg = yield self.message_queue.get()
                log_and_collect('INFO', f'{self.name} 收到消息: {msg.get("type", "unknown")}', 
                               entity=self.name)
                
                if msg.get('type') == 'enemy_report':
                    self.env.process(self.run_action('act_process_intel', msg))
                    
            except simpy.Interrupt:
                break

    def run_action(self, action_id: str, context_data: Dict = None):
        """执行动作"""
        self.update_status(action=action_id)
        if action_id in actions:
            context = self.get_context()
            if context_data:
                context.update(context_data)
            yield self.env.process(actions[action_id].execute(self, context))

class ArtilleryBattalion(BaseEntity):
    """炮兵营实体"""
    def __init__(self, env: simpy.Environment, entity_id: str, simulation):
        super().__init__(env, entity_id, simulation)
        self.name = '炮兵营'
        self.type = 'agent'
        self.position = {'x': -500.0, 'y': -200.0, 'z': 0.0}
        self.attributes = {
            'unit_type': 'artillery',
            'call_sign': 'Thunder',
            'guns_count': '18'
        }
        self.fire_status = 'ready'
        self.rounds_fired = 0
        self.actions = []

    def start(self):
        """启动实体进程"""
        log_and_collect('INFO', 
                       f'{self.name} ({self.attributes["call_sign"]}) 准备就绪，火炮数量: {self.attributes["guns_count"]}', 
                       entity=self.name)
        self.env.process(self.message_handler())

    def message_handler(self):
        """处理消息"""
        while True:
            try:
                msg = yield self.message_queue.get()
                log_and_collect('INFO', f'{self.name} 收到命令: {msg.get("type", "unknown")}', 
                               entity=self.name)
                
                if msg.get('type') == 'fire_order':
                    self.env.process(self.run_action('act_execute_fire_mission', msg))
                elif msg.get('type') == 'cease_fire':
                    self.env.process(self.run_action('act_cease_fire', msg))
                    
            except simpy.Interrupt:
                break

    def run_action(self, action_id: str, context_data: Dict = None):
        """执行动作"""
        self.update_status(action=action_id)
        if action_id in actions:
            context = self.get_context()
            if context_data:
                context.update(context_data)
            yield self.env.process(actions[action_id].execute(self, context))

class ReconSquad(BaseEntity):
    """步兵侦察班实体"""
    def __init__(self, env: simpy.Environment, entity_id: str, simulation):
        super().__init__(env, entity_id, simulation)
        self.name = '步兵侦察班'
        self.type = 'agent'
        self.position = {'x': 100.0, 'y': 100.0, 'z': 0.0}
        self.attributes = {
            'unit_type': 'recon',
            'call_sign': 'Scout',
            'squad_size': '8'
        }
        self.patrol_status = 'patrolling'
        self.enemy_contact = False
        self.actions = []

    def start(self):
        """启动实体进程"""
        log_and_collect('INFO', 
                       f'{self.name} ({self.attributes["call_sign"]}) 开始执行侦察任务，人员: {self.attributes["squad_size"]}人', 
                       entity=self.name)
        self.env.process(self.run_action('act_patrol'))
        self.env.process(self.monitor_conditions())
        self.env.process(self.message_handler())

    def monitor_conditions(self):
        """监控触发条件"""
        while True:
            yield self.env.timeout(1)
            
            if self.enemy_contact and self.current_action != 'act_report_enemy':
                self.env.process(self.run_action('act_report_enemy'))
            
            if self.simulation.global_vars.get('StrikeCompleted', False) and self.current_action != 'act_assess_damage':
                self.env.process(self.run_action('act_assess_damage'))

    def run_action(self, action_id: str):
        """执行动作"""
        self.update_status(action=action_id)
        if action_id in actions:
            yield self.env.process(actions[action_id].execute(self, self.get_context()))

    def message_handler(self):
        """处理消息"""
        while True:
            try:
                msg = yield self.message_queue.get()
                log_and_collect('INFO', f'{self.name} 收到消息: {msg}', entity=self.name)
            except simpy.Interrupt:
                break

# 活动函数定义（全部使用装饰器）

@enhanced_activity_wrapper
def activity_move_patrol(env: simpy.Environment, entity: Any, context: Dict) -> simpy.Event:
    """活动：巡逻移动"""
    yield env.process(check_pause(env, entity))
    
    evaluator = ExpressionEvaluator(context)
    current_position = entity.position
    new_position = evaluator.evaluate('calculate_patrol_route(current_position, time)')
    
    if new_position:
        old_pos = entity.position.copy()
        entity.position = new_position
        log_and_collect('INFO', 
                       f'{entity.name} 移动到新位置: ({new_position["x"]:.1f}, {new_position["y"]:.1f})', 
                       entity=entity.name)
    
    delay_time = TimeDistribution.generate('constant', {'value': 30})
    yield env.timeout(delay_time)

@enhanced_activity_wrapper
def activity_scan_area(env: simpy.Environment, entity: Any, context: Dict) -> simpy.Event:
    """活动：扫描区域"""
    yield env.process(check_pause(env, entity))
    
    evaluator = ExpressionEvaluator(context)
    enemy_detected = evaluator.evaluate('random() < 0.3')
    
    entity.enemy_contact = enemy_detected
    
    if enemy_detected:
        log_and_collect('WARNING', f'{entity.name} 发现敌情！', entity=entity.name,
                       msg_type=MessageType.ALERT)
        entity.simulation.global_vars['EnemyDetected'] = True
    else:
        logging.info(f'{entity.name} 区域安全，未发现敌情')
    
    delay_time = TimeDistribution.generate('constant', {'value': 10})
    yield env.timeout(delay_time)
    
    return {'enemy_detected': enemy_detected}

@enhanced_activity_wrapper
def activity_gather_intel(env: simpy.Environment, entity: Any, context: Dict) -> simpy.Event:
    """活动：收集情报"""
    log_and_collect('INFO', f'{entity.name} 开始收集敌情详细信息', entity=entity.name)
    
    yield env.process(check_pause(env, entity))
    
    enemy_info = {
        'position': {'x': 800, 'y': 600},
        'strength': 'company',
        'type': 'mechanized'
    }
    
    context['enemy_info'] = enemy_info
    
    log_and_collect('INFO', f'{entity.name} 收集到敌情: 位置({enemy_info["position"]["x"]}, {enemy_info["position"]["y"]}), '
                          f'规模: {enemy_info["strength"]}, 类型: {enemy_info["type"]}', 
                   entity=entity.name)
    
    delay_time = TimeDistribution.generate('uniform', {'min': 20, 'max': 40})
    yield env.timeout(delay_time)
    
    return enemy_info

@enhanced_activity_wrapper
def activity_send_enemy_report(env: simpy.Environment, entity: Any, context: Dict) -> simpy.Event:
    """活动：发送敌情报告"""
    log_and_collect('INFO', f'{entity.name} 发送敌情报告到指挥所', entity=entity.name)
    
    yield env.process(check_pause(env, entity))
    
    if 'ent_command_post' in entity.simulation.entities:
        command_post = entity.simulation.entities['ent_command_post']
        enemy_info = context.get('enemy_info', {})
        
        message = {
            'type': 'enemy_report',
            'source': entity.id,
            'enemy_position': str(enemy_info.get('position', 'unknown')),
            'enemy_strength': enemy_info.get('strength', 'unknown'),
            'report_time': env.now,
            'enemy_info': enemy_info
        }
        
        yield command_post.message_queue.put(message)
        log_and_collect('INFO', f'{entity.name} 敌情报告已发送', entity=entity.name)
    
    entity.simulation.global_vars['EnemyDetected'] = True
    
    delay_time = TimeDistribution.generate('constant', {'value': 5})
    yield env.timeout(delay_time)

@enhanced_activity_wrapper
def activity_analyze_report(env: simpy.Environment, entity: Any, context: Dict) -> simpy.Event:
    """活动：分析报告"""
    log_and_collect('INFO', f'{entity.name} 开始分析敌情报告', entity=entity.name)
    
    yield env.process(check_pause(env, entity))
    
    evaluator = ExpressionEvaluator(context)
    enemy_info = context.get('enemy_info', {})
    threat_level = evaluator.evaluate('analyze_enemy_info(enemy_info)')
    
    context['threat_level'] = threat_level
    
    threat_desc = '高' if threat_level > 0.7 else ('中' if threat_level > 0.4 else '低')
    log_and_collect('INFO', f'{entity.name} 威胁评估完成: 威胁等级 - {threat_desc} ({threat_level:.2f})', 
                   entity=entity.name)
    
    delay_time = TimeDistribution.generate('constant', {'value': 30})
    yield env.timeout(delay_time)
    
    return {'threat_level': threat_level, 'threat_desc': threat_desc}

@enhanced_activity_wrapper
def activity_make_decision(env: simpy.Environment, entity: Any, context: Dict) -> simpy.Event:
    """活动：做出决策"""
    log_and_collect('INFO', f'{entity.name} 开始决策是否开火', entity=entity.name)
    
    yield env.process(check_pause(env, entity))
    
    threat_level = context.get('threat_level', 0.5)
    fire_decision = threat_level > 0.6
    
    context['fire_decision'] = fire_decision
    
    if fire_decision:
        log_and_collect('WARNING', f'{entity.name} 决定实施火力打击！', entity=entity.name,
                       msg_type=MessageType.ALERT)
        entity.env.process(entity.run_action('act_issue_fire_order', context))
    else:
        log_and_collect('INFO', f'{entity.name} 决定继续观察，暂不开火', entity=entity.name)
    
    delay_time = TimeDistribution.generate('constant', {'value': 20})
    yield env.timeout(delay_time)
    
    return {'fire_decision': fire_decision}

@enhanced_activity_wrapper
def activity_prepare_fire_order(env: simpy.Environment, entity: Any, context: Dict) -> simpy.Event:
    """活动：准备火力命令"""
    log_and_collect('INFO', f'{entity.name} 准备火力打击命令', entity=entity.name)
    
    yield env.process(check_pause(env, entity))
    
    enemy_info = context.get('enemy_info', {})
    fire_order = {
        'target': enemy_info.get('position', {'x': 800, 'y': 600}),
        'type': 'suppression',
        'rounds': 36
    }
    
    context['fire_order'] = fire_order
    
    log_and_collect('INFO', f'{entity.name} 火力命令准备完成: 目标位置({fire_order["target"]["x"]}, {fire_order["target"]["y"]}), '
                          f'弹药数量: {fire_order["rounds"]}发', 
                   entity=entity.name)
    
    delay_time = TimeDistribution.generate('constant', {'value': 15})
    yield env.timeout(delay_time)
    
    return fire_order

@enhanced_activity_wrapper
def activity_transmit_order(env: simpy.Environment, entity: Any, context: Dict) -> simpy.Event:
    """活动：传送命令"""
    log_and_collect('INFO', f'{entity.name} 传送火力命令到炮兵营', entity=entity.name)
    
    yield env.process(check_pause(env, entity))
    
    if 'ent_artillery_battalion' in entity.simulation.entities:
        artillery = entity.simulation.entities['ent_artillery_battalion']
        fire_order = context.get('fire_order', {})
        
        message = {
            'type': 'fire_order',
            'source': entity.id,
            'target_position': str(fire_order.get('target', 'unknown')),
            'fire_type': fire_order.get('type', 'suppression'),
            'rounds_count': fire_order.get('rounds', 36),
            'fire_order': fire_order
        }
        
        yield artillery.message_queue.put(message)
        log_and_collect('INFO', f'{entity.name} 火力命令已发送', entity=entity.name)
    
    delay_time = TimeDistribution.generate('constant', {'value': 5})
    yield env.timeout(delay_time)

@enhanced_activity_wrapper
def activity_prepare_guns(env: simpy.Environment, entity: Any, context: Dict) -> simpy.Event:
    """活动：准备火炮"""
    log_and_collect('INFO', f'{entity.name} 开始准备火炮', entity=entity.name)
    
    yield env.process(check_pause(env, entity))
    
    entity.fire_status = 'preparing'
    
    log_and_collect('INFO', f'{entity.name} 火炮装填中，{entity.attributes["guns_count"]}门火炮准备就绪', 
                   entity=entity.name)
    
    delay_time = TimeDistribution.generate('constant', {'value': 60})
    
    for i in range(6):
        yield env.timeout(delay_time / 6)
        progress = (i + 1) * 100 / 6
        if i % 2 == 0:
            log_and_collect('INFO', f'{entity.name} 准备进度: {progress:.0f}%', entity=entity.name)

@enhanced_activity_wrapper
def activity_fire_barrage(env: simpy.Environment, entity: Any, context: Dict) -> simpy.Event:
    """活动：火力齐射"""
    log_and_collect('WARNING', f'{entity.name} 开始火力齐射！', entity=entity.name,
                   msg_type=MessageType.ALERT)
    
    yield env.process(check_pause(env, entity))
    
    entity.fire_status = 'firing'
    rounds_fired = 36
    entity.rounds_fired += rounds_fired
    
    if 'res_artillery_rounds' in resources:
        ammo = resources['res_artillery_rounds']
        if ammo.level >= rounds_fired:
            yield ammo.get(rounds_fired)
            logging.info(f'{entity.name} 消耗弹药 {rounds_fired} 发，剩余: {ammo.level}')
            
            message_collector.add_message(SimulationMessage(
                type=MessageType.RESOURCE_UPDATE,
                data={
                    'resource_id': 'res_artillery_rounds',
                    'level': ammo.level,
                    'capacity': ammo.capacity,
                    'utilization': ((ammo.capacity - ammo.level) / ammo.capacity) * 100
                }
            ))
    
    delay_time = TimeDistribution.generate('constant', {'value': 120})
    
    for i in range(4):
        yield env.timeout(delay_time / 4)
        if i == 3:
            logging.info(f'{entity.name} 齐射完成')
    
    entity.simulation.global_vars['StrikeCompleted'] = True
    
    log_and_collect('INFO', f'{entity.name} 火力齐射完成，共发射 {rounds_fired} 发炮弹', entity=entity.name)
    
    return {'rounds_fired': rounds_fired, 'result': '齐射完成'}

@enhanced_activity_wrapper
def activity_observe_impact(env: simpy.Environment, entity: Any, context: Dict) -> simpy.Event:
    """活动：观察打击效果"""
    log_and_collect('INFO', f'{entity.name} 开始观察火力打击效果', entity=entity.name)
    
    yield env.process(check_pause(env, entity))
    
    damage_level = 0.7 + random.random() * 0.3
    context['damage_level'] = damage_level
    
    damage_desc = '严重' if damage_level > 0.85 else ('中等' if damage_level > 0.7 else '轻微')
    log_and_collect('INFO', f'{entity.name} 初步评估: 目标受损程度 - {damage_desc} ({damage_level:.2f})', 
                   entity=entity.name)
    
    delay_time = TimeDistribution.generate('constant', {'value': 60})
    yield env.timeout(delay_time)
    
    return {'damage_level': damage_level, 'damage_desc': damage_desc}

@enhanced_activity_wrapper
def activity_report_bda(env: simpy.Environment, entity: Any, context: Dict) -> simpy.Event:
    """活动：报告毁伤评估"""
    log_and_collect('INFO', f'{entity.name} 发送毁伤评估报告', entity=entity.name)
    
    yield env.process(check_pause(env, entity))
    
    damage_level = context.get('damage_level', 0.0)
    entity.simulation.global_vars['DamageAssessment'] = damage_level
    
    message_collector.add_message(SimulationMessage(
        type=MessageType.GLOBAL_VAR_UPDATE,
        data={'DamageAssessment': damage_level}
    ))
    
    if 'ent_command_post' in entity.simulation.entities:
        command_post = entity.simulation.entities['ent_command_post']
        
        message = {
            'type': 'bda_report',
            'source': entity.id,
            'damage_assessment': damage_level,
            'target_status': '摧毁' if damage_level > 0.8 else '重创'
        }
        
        yield command_post.message_queue.put(message)
    
    log_and_collect('INFO', f'{entity.name} 毁伤评估报告已发送: 毁伤程度 {damage_level:.2%}', entity=entity.name)
    
    delay_time = TimeDistribution.generate('constant', {'value': 10})
    yield env.timeout(delay_time)

@enhanced_activity_wrapper
def activity_evaluate_results(env: simpy.Environment, entity: Any, context: Dict) -> simpy.Event:
    """活动：评估结果"""
    log_and_collect('INFO', f'{entity.name} 评估任务执行结果', entity=entity.name)
    
    yield env.process(check_pause(env, entity))
    
    damage_assessment = entity.simulation.global_vars.get('DamageAssessment', 0.0)
    mission_success = damage_assessment >= 0.8
    
    context['mission_success'] = mission_success
    
    if mission_success:
        log_and_collect('INFO', f'{entity.name} 任务成功！目标已被有效打击', entity=entity.name)
    else:
        log_and_collect('WARNING', f'{entity.name} 任务未完全达成，可能需要补充打击', entity=entity.name)
    
    delay_time = TimeDistribution.generate('constant', {'value': 20})
    yield env.timeout(delay_time)
    
    return {'mission_success': mission_success}

@enhanced_activity_wrapper
def activity_send_cease_fire(env: simpy.Environment, entity: Any, context: Dict) -> simpy.Event:
    """活动：发送停火命令"""
    log_and_collect('INFO', f'{entity.name} 发送停火命令', entity=entity.name)
    
    yield env.process(check_pause(env, entity))
    
    if 'ent_artillery_battalion' in entity.simulation.entities:
        artillery = entity.simulation.entities['ent_artillery_battalion']
        
        message = {
            'type': 'cease_fire',
            'source': entity.id
        }
        
        yield artillery.message_queue.put(message)
        log_and_collect('INFO', f'{entity.name} 停火命令已发送', entity=entity.name)
    
    delay_time = TimeDistribution.generate('constant', {'value': 5})
    yield env.timeout(delay_time)

@enhanced_activity_wrapper
def activity_stop_firing(env: simpy.Environment, entity: Any, context: Dict) -> simpy.Event:
    """活动：停止射击"""
    log_and_collect('INFO', f'{entity.name} 执行停火命令', entity=entity.name)
    
    yield env.process(check_pause(env, entity))
    
    entity.fire_status = 'ceased'
    
    log_and_collect('INFO', f'{entity.name} 已停止射击，共发射 {entity.rounds_fired} 发炮弹', entity=entity.name)
    
    delay_time = TimeDistribution.generate('constant', {'value': 10})
    yield env.timeout(delay_time)

@enhanced_activity_wrapper
def activity_report_status(env: simpy.Environment, entity: Any, context: Dict) -> simpy.Event:
    """活动：报告状态"""
    log_and_collect('INFO', f'{entity.name} 报告当前状态', entity=entity.name)
    
    yield env.process(check_pause(env, entity))
    
    entity.fire_status = 'ready'
    
    remaining_ammo = 0
    if 'res_artillery_rounds' in resources:
        remaining_ammo = resources['res_artillery_rounds'].level
    
    log_and_collect('INFO', f'{entity.name} 状态: 就绪，剩余弹药: {remaining_ammo} 发', entity=entity.name)
    
    delay_time = TimeDistribution.generate('constant', {'value': 5})
    yield env.timeout(delay_time)
    
    return {'status': 'ready', 'remaining_ammo': remaining_ammo}

# 动作类定义
class ActionBase:
    """动作基类"""
    def __init__(self, env: simpy.Environment, action_id: str, name: str, chinese_name: str):
        self.env = env
        self.id = action_id
        self.name = name
        self.chinese_name = chinese_name
        self.interrupted = False

    def execute(self, entity: Any, context: Dict):
        """执行动作"""
        entity.update_status(action=self.id)
        
        # 收集动作开始消息
        message_collector.add_message(SimulationMessage(
            type=MessageType.ACTION_STARTED,
            entity_id=entity.id,
            data={
                'entity_name': entity.name,
                'action': self.id,
                'action_name': self.chinese_name
            }
        ))
        
        try:
            yield self.env.process(self.do_execute(entity, context))
            
            # 收集动作完成消息
            message_collector.add_message(SimulationMessage(
                type=MessageType.ACTION_COMPLETED,
                entity_id=entity.id,
                data={
                    'entity_name': entity.name,
                    'action': self.id,
                    'action_name': self.chinese_name
                }
            ))
        except simpy.Interrupt:
            self.interrupted = True
            logging.info(f'动作 {self.chinese_name} 被中断')

    def do_execute(self, entity: Any, context: Dict):
        """具体执行逻辑 - 子类实现"""
        yield self.env.timeout(0)

class ActionPatrol(ActionBase):
    """动作：巡逻"""
    def __init__(self, env: simpy.Environment, action_id: str):
        super().__init__(env, action_id, 'Patrol', '巡逻')

    def do_execute(self, entity: Any, context: Dict):
        """循环执行巡逻"""
        while entity.patrol_status == 'patrolling' and not entity.enemy_contact:
            yield self.env.process(activity_move_patrol(self.env, entity, context))
            yield self.env.process(activity_scan_area(self.env, entity, context))
            yield self.env.process(check_pause(self.env, entity))

class ActionReportEnemy(ActionBase):
    """动作：报告敌情"""
    def __init__(self, env: simpy.Environment, action_id: str):
        super().__init__(env, action_id, 'ReportEnemy', '报告敌情')

    def do_execute(self, entity: Any, context: Dict):
        yield self.env.process(activity_gather_intel(self.env, entity, context))
        yield self.env.process(activity_send_enemy_report(self.env, entity, context))

class ActionAssessDamage(ActionBase):
    """动作：评估毁伤"""
    def __init__(self, env: simpy.Environment, action_id: str):
        super().__init__(env, action_id, 'AssessDamage', '评估毁伤')

    def do_execute(self, entity: Any, context: Dict):
        yield self.env.process(activity_observe_impact(self.env, entity, context))
        yield self.env.process(activity_report_bda(self.env, entity, context))

class ActionProcessIntel(ActionBase):
    """动作：处理情报"""
    def __init__(self, env: simpy.Environment, action_id: str):
        super().__init__(env, action_id, 'ProcessIntel', '处理情报')

    def do_execute(self, entity: Any, context: Dict):
        yield self.env.process(activity_analyze_report(self.env, entity, context))
        yield self.env.process(activity_make_decision(self.env, entity, context))

class ActionIssueFireOrder(ActionBase):
    """动作：下达开火命令"""
    def __init__(self, env: simpy.Environment, action_id: str):
        super().__init__(env, action_id, 'IssueFireOrder', '下达开火命令')

    def do_execute(self, entity: Any, context: Dict):
        yield self.env.process(activity_prepare_fire_order(self.env, entity, context))
        yield self.env.process(activity_transmit_order(self.env, entity, context))

class ActionCeaseFireOrder(ActionBase):
    """动作：下达停火命令"""
    def __init__(self, env: simpy.Environment, action_id: str):
        super().__init__(env, action_id, 'CeaseFireOrder', '下达停火命令')

    def do_execute(self, entity: Any, context: Dict):
        yield self.env.process(activity_evaluate_results(self.env, entity, context))
        yield self.env.process(activity_send_cease_fire(self.env, entity, context))

class ActionExecuteFireMission(ActionBase):
    """动作：执行火力任务"""
    def __init__(self, env: simpy.Environment, action_id: str):
        super().__init__(env, action_id, 'ExecuteFireMission', '执行火力任务')

    def do_execute(self, entity: Any, context: Dict):
        rounds_needed = context.get('fire_order', {}).get('rounds', 36)
        if 'res_artillery_rounds' in resources:
            if resources['res_artillery_rounds'].level < rounds_needed:
                log_and_collect('ERROR', f'{entity.name} 弹药不足，需要 {rounds_needed} 发，剩余 {resources["res_artillery_rounds"].level} 发', 
                               entity=entity.name)
                return
        
        yield self.env.process(activity_prepare_guns(self.env, entity, context))
        yield self.env.process(activity_fire_barrage(self.env, entity, context))

class ActionCeaseFire(ActionBase):
    """动作：停止射击"""
    def __init__(self, env: simpy.Environment, action_id: str):
        super().__init__(env, action_id, 'CeaseFire', '停止射击')

    def do_execute(self, entity: Any, context: Dict):
        yield self.env.process(activity_stop_firing(self.env, entity, context))
        yield self.env.process(activity_report_status(self.env, entity, context))

# 事件处理器
class EventScheduler:
    """事件调度器"""
    def __init__(self, env: simpy.Environment, simulation):
        self.env = env
        self.simulation = simulation
        self.events = {}

    def start(self):
        """启动事件监控"""
        self.env.process(self.monitor_conditions())

    def monitor_conditions(self):
        """监控条件事件"""
        while True:
            yield self.env.timeout(1)
            
            # 监控发现敌情事件
            if self.simulation.global_vars.get('EnemyDetected', False):
                if 'evt_enemy_detected' not in self.events:
                    self.events['evt_enemy_detected'] = True
                    log_and_collect('WARNING', '触发事件: 发现敌情', msg_type=MessageType.EVENT_TRIGGERED)
            
            # 监控任务完成事件
            damage = self.simulation.global_vars.get('DamageAssessment', 0.0)
            if damage >= 0.8:
                if 'evt_mission_complete' not in self.events:
                    self.events['evt_mission_complete'] = True
                    log_and_collect('INFO', '触发事件: 任务完成', msg_type=MessageType.EVENT_TRIGGERED)
                    
                    # 触发停火命令
                    if 'ent_command_post' in self.simulation.entities:
                        command_post = self.simulation.entities['ent_command_post']
                        self.env.process(command_post.run_action('act_cease_fire_order'))

# 主仿真类（支持日志推送版）
class EATISimulation:
    """主仿真控制器 - 支持日志推送版"""
    def __init__(self):
        self.env = simpy.Environment()
        self.env.simulation = self
        self.entities = {}
        self.resources = {}
        self.actions = {}
        self.global_vars = {}
        
        # 运行控制
        self.run_state = RunState.STEPPING if RUN_MODE == 'step' else RunState.RUNNING
        self.step_continue = False
        self.step_points = []
        self.time_ratio = REAL_TIME_RATIO
        
        # WebSocket管理
        self.ws_server = None
        self.ws_thread = None
        self.ws_loop = None
        
        # 状态跟踪
        self.start_time = None
        self.last_message_check = datetime.now()
        
        # 初始化全局变量
        self.global_vars = {
            'EnemyDetected': False,
            'StrikeCompleted': False,
            'DamageAssessment': 0.0
        }
        
        # 命令队列
        self.command_queue = queue.Queue()
        
        # 事件调度器
        self.event_scheduler = EventScheduler(self.env, self)

    def setup(self):
        """设置仿真组件"""
        log_and_collect('INFO', '开始初始化侦察-火力打击仿真环境...')
        
        # 创建资源
        global resources
        resources = {}
        resources['res_artillery_rounds'] = simpy.Container(self.env, capacity=200, init=180)
        self.resources = resources
        
        # 创建实体
        self.entities['ent_command_post'] = CommandPost(self.env, 'ent_command_post', self)
        self.entities['ent_artillery_battalion'] = ArtilleryBattalion(self.env, 'ent_artillery_battalion', self)
        self.entities['ent_recon_squad'] = ReconSquad(self.env, 'ent_recon_squad', self)
        
        # 创建动作
        global actions
        actions = {}
        actions['act_patrol'] = ActionPatrol(self.env, 'act_patrol')
        actions['act_report_enemy'] = ActionReportEnemy(self.env, 'act_report_enemy')
        actions['act_assess_damage'] = ActionAssessDamage(self.env, 'act_assess_damage')
        actions['act_process_intel'] = ActionProcessIntel(self.env, 'act_process_intel')
        actions['act_issue_fire_order'] = ActionIssueFireOrder(self.env, 'act_issue_fire_order')
        actions['act_cease_fire_order'] = ActionCeaseFireOrder(self.env, 'act_cease_fire_order')
        actions['act_execute_fire_mission'] = ActionExecuteFireMission(self.env, 'act_execute_fire_mission')
        actions['act_cease_fire'] = ActionCeaseFire(self.env, 'act_cease_fire')
        self.actions = actions
        
        # 启动实体进程
        for entity in self.entities.values():
            if hasattr(entity, 'start'):
                entity.start()
        
        # 启动事件调度器
        self.event_scheduler.start()
        
        # 启动WebSocket服务器
        self.setup_websocket()
        
        log_and_collect('INFO', '仿真环境初始化完成')
        
        # 记录初始状态变化
        message_collector.add_message(SimulationMessage(
            type=MessageType.SIMULATION_STATE_CHANGED,
            data={'state': self.run_state.value, 'mode': RUN_MODE}
        ))

    def setup_websocket(self):
        """设置WebSocket服务器"""
        async def handle_client(websocket, path):
            """处理WebSocket客户端连接"""
            # 获取连接参数
            try:
                # 尝试从路径获取参数
                query_params = {}
                if '?' in path:
                    query_string = path.split('?')[1]
                    for param in query_string.split('&'):
                        if '=' in param:
                            key, value = param.split('=', 1)
                            query_params[key] = value
                
                # 获取日志推送间隔
                log_push_interval = float(query_params.get('log_interval', DEFAULT_LOG_PUSH_INTERVAL))
                log_push_interval = max(0.1, min(60.0, log_push_interval))  # 限制在0.1-60秒之间
                
                # 获取日志级别过滤（新增）
                log_level = query_params.get('log_level', 'INFO')
                if log_level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
                    log_level = 'INFO'
                
            except:
                log_push_interval = DEFAULT_LOG_PUSH_INTERVAL
                log_level = 'INFO'
            
            # 添加客户端
            client_info = ws_manager.add_client(websocket, log_push_interval)
            client_info.log_level_filter = log_level
            
            # 发送欢迎消息
            await websocket.send(json.dumps({
                'type': 'welcome',
                'data': {
                    'simulation_name': '侦察-火力打击仿真',
                    'total_time': SIMULATION_END_TIME,
                    'current_state': self.run_state.value,
                    'log_push_interval': log_push_interval,
                    'log_level_filter': log_level,
                    'message': f'欢迎连接到仿真系统，日志将每{log_push_interval}秒推送一次（{log_level}级别及以上）'
                }
            }))
            
            # 启动日志推送任务
            client_info.push_task = asyncio.create_task(log_push_task(client_info))
            
            try:
                async for message in websocket:
                    data = json.loads(message)
                    await self.handle_ws_message(websocket, data)
            except websockets.exceptions.ConnectionClosed:
                pass
            finally:
                ws_manager.remove_client(websocket)

        async def start_server():
            """启动WebSocket服务器"""
            self.ws_server = await websockets.serve(handle_client, WS_HOST, WS_PORT)
            log_and_collect('INFO', f'WebSocket服务器启动: {WS_HOST}:{WS_PORT}')

        def run_ws_server():
            """在独立线程中运行WebSocket服务器"""
            self.ws_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.ws_loop)
            ws_manager.set_event_loop(self.ws_loop)
            self.ws_loop.run_until_complete(start_server())
            self.ws_loop.run_forever()

        self.ws_thread = threading.Thread(target=run_ws_server, daemon=True)
        self.ws_thread.start()
        time.sleep(0.5)

    async def handle_ws_message(self, websocket, data: Dict):
        """处理WebSocket消息 - 支持日志配置"""
        msg_type = data.get('type')
        
        if msg_type == 'command':
            # 处理控制命令
            command = data.get('command')
            self.command_queue.put(command)
            await websocket.send(json.dumps({
                'type': 'ack',
                'command': command
            }))
        
        elif msg_type == 'set_log_config':
            # 设置日志配置（新增）
            config = data.get('config', {})
            client_info = ws_manager.get_client(websocket)
            
            if client_info:
                # 更新日志推送间隔
                if 'interval' in config:
                    interval = float(config['interval'])
                    client_info.log_push_interval = max(0.1, min(60.0, interval))
                
                # 更新日志级别过滤
                if 'level' in config:
                    level = config['level']
                    if level in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
                        client_info.log_level_filter = level
                
                # 更新每次推送的最大日志数
                if 'max_logs' in config:
                    max_logs = int(config['max_logs'])
                    client_info.max_logs_per_push = max(10, min(100, max_logs))
                
                # 重启推送任务
                if client_info.push_task:
                    client_info.push_task.cancel()
                    client_info.push_task = asyncio.create_task(log_push_task(client_info))
                
                await websocket.send(json.dumps({
                    'type': 'log_config_updated',
                    'config': {
                        'interval': client_info.log_push_interval,
                        'level': client_info.log_level_filter,
                        'max_logs': client_info.max_logs_per_push
                    }
                }))
        
        elif msg_type == 'get_log_history':
            # 获取历史日志（用于初始加载）
            options = data.get('options', {})
            count = min(options.get('count', 50), 200)
            level = options.get('level', 'INFO')
            
            # 获取最近的日志
            logs, last_id = message_collector.get_incremental_logs(
                last_id=0,  # 从头获取
                level_filter=level,
                max_count=count
            )
            
            # 更新客户端的最后日志ID
            client_info = ws_manager.get_client(websocket)
            if client_info and logs:
                client_info.last_log_id = last_id
            
            await websocket.send(json.dumps({
                'type': 'log_history',
                'data': {
                    'logs': logs,
                    'count': len(logs),
                    'last_id': last_id
                }
            }))
        
        elif msg_type == 'get_status':
            # 查询当前状态
            status = self.get_simulation_status()
            await websocket.send(json.dumps({
                'type': MessageType.STATUS_UPDATE.value,
                'data': status
            }))
        
        elif msg_type == 'get_resources':
            # 查询资源状态
            resources_data = {}
            for res_id, resource in self.resources.items():
                if hasattr(resource, 'level'):
                    resources_data[res_id] = {
                        'name': '炮弹储备',
                        'level': resource.level,
                        'capacity': resource.capacity,
                        'utilization': ((resource.capacity - resource.level) / resource.capacity) * 100
                    }
            await websocket.send(json.dumps({
                'type': MessageType.RESOURCE_UPDATE.value,
                'data': resources_data
            }))
        
        elif msg_type == 'get_global_vars':
            # 查询全局变量
            await websocket.send(json.dumps({
                'type': MessageType.GLOBAL_VAR_UPDATE.value,
                'data': self.global_vars.copy()
            }))
        
        elif msg_type == 'get_step_info':
            # 查询单步信息
            if self.run_state == RunState.STEPPING:
                await websocket.send(json.dumps({
                    'type': MessageType.STEP_COMPLETED.value,
                    'data': {
                        'current_time': self.env.now,
                        'step_points': self.step_points,
                        'next_available': self.env.now < SIMULATION_END_TIME,
                        'waiting_for_step': not self.step_continue
                    }
                }))
        
        elif msg_type == 'get_messages':
            # 查询消息（不包括日志，日志通过推送获取）
            options = data.get('options', {})
            message_type = options.get('message_type')
            count = options.get('count', 50)
            since = options.get('since')
            
            # 排除日志消息类型
            if message_type and message_type != 'LOG_MESSAGE':
                msg_type_enum = MessageType[message_type] if message_type in MessageType.__members__ else None
            else:
                msg_type_enum = None
            
            if since:
                since_time = datetime.fromisoformat(since)
                messages = message_collector.get_messages_since(since_time, msg_type_enum)
            else:
                messages = message_collector.get_messages(msg_type_enum, count)
            
            # 过滤掉日志消息
            messages = [m for m in messages if m['type'] != MessageType.LOG_MESSAGE.value]
            
            await websocket.send(json.dumps({
                'type': 'messages',
                'data': messages
            }))

    def run(self):
        """运行仿真"""
        log_and_collect('INFO', f'仿真开始运行 - 模式: {RUN_MODE}, 总时长: {SIMULATION_END_TIME}秒')
        self.start_time = time.time()
        
        try:
            if self.run_state == RunState.STEPPING:
                self.run_step_mode()
            else:
                self.run_continuous()
        except Exception as e:
            log_and_collect('ERROR', f'仿真运行错误: {e}')
            raise
        finally:
            log_and_collect('INFO', '仿真运行完成')
            self.record_completion()

    def run_step_mode(self):
        """单步运行模式"""
        log_and_collect('INFO', '进入单步运行模式，等待步进指令...')
        
        while self.env.now < SIMULATION_END_TIME and self.run_state != RunState.STOPPED:
            self.process_commands()
            
            if self.run_state == RunState.RUNNING:
                self.run_continuous()
                break
            
            elif self.run_state == RunState.STEPPING:
                if self.step_continue:
                    step_start_time = self.env.now
                    self.step_points.clear()
                    next_time = min(self.env.now + STEP_SIZE, SIMULATION_END_TIME)
                    
                    try:
                        self.env.run(until=next_time)
                    except simpy.Interrupt:
                        pass
                    
                    # 记录步骤完成
                    message_collector.add_message(SimulationMessage(
                        type=MessageType.STEP_COMPLETED,
                        data={
                            'step_start': step_start_time,
                            'step_end': self.env.now,
                            'step_points': self.step_points,
                            'next_available': self.env.now < SIMULATION_END_TIME
                        }
                    ))
                    
                    self.step_continue = False
                    logging.info(f'单步执行完成: {step_start_time:.1f}s -> {self.env.now:.1f}s')
                else:
                    time.sleep(0.05)
            
            elif self.run_state == RunState.PAUSED:
                time.sleep(0.1)

    def run_continuous(self):
        """连续运行模式"""
        start_real_time = time.time() - (self.env.now / self.time_ratio if self.time_ratio > 0 else 0)
        
        while self.env.now < SIMULATION_END_TIME and self.run_state != RunState.STOPPED:
            self.process_commands()
            
            if self.run_state == RunState.PAUSED:
                time.sleep(0.1)
                continue
            
            elif self.run_state == RunState.STEPPING:
                logging.info('切换到单步模式')
                self.run_step_mode()
                break
            
            step_time = min(0.1, SIMULATION_END_TIME - self.env.now)
            self.env.run(until=self.env.now + step_time)
            
            if self.time_ratio > 0:
                real_elapsed = time.time() - start_real_time
                sim_elapsed = self.env.now
                expected_real_time = sim_elapsed / self.time_ratio
                if expected_real_time > real_elapsed:
                    time.sleep(expected_real_time - real_elapsed)

    def process_commands(self):
        """处理所有待处理的命令"""
        while not self.command_queue.empty():
            try:
                command = self.command_queue.get_nowait()
                self.process_command(command)
            except queue.Empty:
                break

    def process_command(self, command: Dict):
        """处理外部命令"""
        cmd_type = command.get('type')
        old_state = self.run_state
        
        if cmd_type == 'pause':
            self.run_state = RunState.PAUSED
            log_and_collect('INFO', '仿真已暂停')
            
        elif cmd_type == 'resume':
            if self.run_state == RunState.PAUSED:
                self.run_state = RunState.RUNNING
                log_and_collect('INFO', '仿真已恢复')
            
        elif cmd_type == 'step':
            if self.run_state != RunState.STEPPING:
                self.run_state = RunState.STEPPING
                log_and_collect('INFO', '切换到单步模式')
            self.step_continue = True
            
        elif cmd_type == 'run':
            self.run_state = RunState.RUNNING
            log_and_collect('INFO', '切换到连续运行模式')
            
        elif cmd_type == 'change_speed':
            self.time_ratio = command.get('speed_ratio', 1.0)
            log_and_collect('INFO', f'仿真速度调整为: {self.time_ratio}x')
            
        elif cmd_type == 'stop':
            self.run_state = RunState.STOPPED
            log_and_collect('INFO', '仿真已停止')
        
        # 记录状态变化
        if old_state != self.run_state:
            message_collector.add_message(SimulationMessage(
                type=MessageType.SIMULATION_STATE_CHANGED,
                data={'old_state': old_state.value, 'new_state': self.run_state.value}
            ))

    def record_completion(self):
        """记录仿真完成"""
        status = self.get_simulation_status()
        status['completed'] = True
        status['completion_time'] = datetime.now().isoformat()
        
        message_collector.add_message(SimulationMessage(
            type=MessageType.SIMULATION_STATE_CHANGED,
            data={
                'state': 'completed',
                'final_status': status
            }
        ))

    def get_simulation_status(self) -> Dict:
        """获取仿真状态（增加了activity名称字段）"""
        progress = (self.env.now / SIMULATION_END_TIME) * 100
        real_elapsed = time.time() - self.start_time if self.start_time else 0
        
        entities_status = {}
        for entity_id, entity in self.entities.items():
            entity_status = {
                'name': entity.name,
                'type': entity.type,
                'position': getattr(entity, 'position', None),
                'current_action': getattr(entity, 'current_action', None),
                'current_activity': getattr(entity, 'current_activity', None),
                'current_activity_name': getattr(entity, 'current_activity_name', None),  # 新增
                'current_activity_chinese_name': getattr(entity, 'current_activity_chinese_name', None),  # 新增
            }
            
            if entity_id == 'ent_command_post':
                entity_status['alert_level'] = entity.alert_level
            elif entity_id == 'ent_artillery_battalion':
                entity_status['fire_status'] = entity.fire_status
                entity_status['rounds_fired'] = entity.rounds_fired
            elif entity_id == 'ent_recon_squad':
                entity_status['patrol_status'] = entity.patrol_status
                entity_status['enemy_contact'] = entity.enemy_contact
            
            entities_status[entity_id] = entity_status
        
        resources_status = {}
        for res_id, resource in self.resources.items():
            if hasattr(resource, 'level'):
                resources_status[res_id] = {
                    'name': '炮弹储备',
                    'level': resource.level,
                    'capacity': resource.capacity,
                    'utilization': ((resource.capacity - resource.level) / resource.capacity) * 100
                }
        
        return {
            'simulation_time': self.env.now,
            'real_elapsed_time': real_elapsed,
            'total_time': SIMULATION_END_TIME,
            'progress': progress,
            'run_state': self.run_state.value,
            'simulation_speed': self.time_ratio,
            'entities': entities_status,
            'resources': resources_status,
            'global_vars': self.global_vars.copy(),
            'step_mode': self.run_state == RunState.STEPPING
        }

# Main Entry Point
def main():
    """主入口点"""
    try:
        logging.info(f"侦察-火力打击仿真程序启动 (增强Activity名称输出版) - PID: {os.getpid()}")
        logging.info(f"WebSocket端口: {WS_PORT}")
        logging.info(f"运行模式: {RUN_MODE}")
        logging.info(f"仿真时长: {SIMULATION_END_TIME}秒")
        logging.info(f"仿真速度: {REAL_TIME_RATIO}x")
        logging.info(f"默认日志推送间隔: {DEFAULT_LOG_PUSH_INTERVAL}秒")
        logging.info("增量日志推送，默认只推送INFO及以上级别")
        logging.info("所有Activity都将记录开始和完成状态，包含activity_name和activity_chinese_name字段")
        
        global env
        simulation = EATISimulation()
        env = simulation.env
        
        simulation.setup()
        time.sleep(1)
        simulation.run()
        
    except KeyboardInterrupt:
        log_and_collect('INFO', '仿真被用户中断')
    except Exception as e:
        log_and_collect('ERROR', f'仿真错误: {e}')
        logging.exception("仿真程序异常退出")
        raise
    finally:
        try:
            if 'simulation' in locals():
                results = {
                    'simulation_info': {
                        'name': '侦察-火力打击仿真',
                        'total_time': SIMULATION_END_TIME,
                        'end_time': simulation.env.now,
                        'completion_rate': (simulation.env.now / SIMULATION_END_TIME) * 100
                    },
                    'final_status': simulation.get_simulation_status(),
                    'global_vars': simulation.global_vars,
                    'events_triggered': list(simulation.event_scheduler.events.keys())
                }
                
                with open('detect_fire_simulation_results.json', 'w', encoding='utf-8') as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
                
                log_and_collect('INFO', '仿真结果已保存到 detect_fire_simulation_results.json')
                
                # 生成Activity时间线报告
                activity_logger.generate_summary_report('activity_execution_summary.json')
                log_and_collect('INFO', f'Activity时间线已保存到: {activity_logger.log_file_path}')
                log_and_collect('INFO', 'Activity执行摘要已保存到: activity_execution_summary.json')
                
                if simulation.global_vars.get('DamageAssessment', 0) >= 0.8:
                    log_and_collect('INFO', '任务成功完成！目标已被有效摧毁')
                else:
                    log_and_collect('WARNING', '任务未完全达成')
        except Exception as e:
            logging.error(f"保存结果失败: {e}")
        
        try:
            if 'simulation' in locals() and simulation.ws_loop:
                simulation.ws_loop.call_soon_threadsafe(simulation.ws_loop.stop)
        except:
            pass

if __name__ == '__main__':
    main()