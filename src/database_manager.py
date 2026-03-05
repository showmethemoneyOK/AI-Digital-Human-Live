#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库管理模块
使用SQLite存储用户交互、商品信息、系统日志等
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)

@dataclass
class InteractionRecord:
    """交互记录"""
    id: int = 0
    timestamp: str = ""
    user_id: str = ""
    platform: str = ""
    original_content: str = ""
    filtered_content: str = ""
    ai_response: str = ""
    risk_level: str = ""
    blocked_reasons: str = ""
    warning_reasons: str = ""
    response_time_ms: float = 0.0
    product_id: str = ""
    session_id: str = ""

@dataclass
class ProductRecord:
    """商品记录"""
    id: str = ""
    name: str = ""
    category: str = ""
    price: str = ""
    original_price: str = ""
    discount: str = ""
    promo: str = ""
    features: str = ""  # JSON字符串
    description: str = ""
    specifications: str = ""  # JSON字符串
    usage_scenarios: str = ""  # JSON字符串
    target_audience: str = ""  # JSON字符串
    faq: str = ""  # JSON字符串
    risk_warnings: str = ""  # JSON字符串
    certifications: str = ""  # JSON字符串
    created_at: str = ""
    updated_at: str = ""
    is_active: bool = True

@dataclass
class SystemLog:
    """系统日志"""
    id: int = 0
    timestamp: str = ""
    level: str = ""
    module: str = ""
    message: str = ""
    details: str = ""
    user_id: str = ""
    session_id: str = ""

class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, db_path: str = "data/live_system.db"):
        self.db_path = db_path
        self.connection = None
        
        # 确保数据目录存在
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # 初始化数据库
        self.initialize_database()
    
    @contextmanager
    def get_connection(self):
        """获取数据库连接（上下文管理器）"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def initialize_database(self):
        """初始化数据库表"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 交互记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    original_content TEXT,
                    filtered_content TEXT,
                    ai_response TEXT,
                    risk_level TEXT,
                    blocked_reasons TEXT,
                    warning_reasons TEXT,
                    response_time_ms REAL,
                    product_id TEXT,
                    session_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 商品信息表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS products (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    category TEXT,
                    price TEXT,
                    original_price TEXT,
                    discount TEXT,
                    promo TEXT,
                    features TEXT,
                    description TEXT,
                    specifications TEXT,
                    usage_scenarios TEXT,
                    target_audience TEXT,
                    faq TEXT,
                    risk_warnings TEXT,
                    certifications TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            ''')
            
            # 系统日志表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    level TEXT NOT NULL,
                    module TEXT NOT NULL,
                    message TEXT NOT NULL,
                    details TEXT,
                    user_id TEXT,
                    session_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 用户会话表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_sessions (
                    session_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    interaction_count INTEGER DEFAULT 0,
                    total_response_time_ms REAL DEFAULT 0,
                    risk_level_summary TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # API调用记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS api_calls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    api_type TEXT NOT NULL,
                    endpoint TEXT NOT NULL,
                    status_code INTEGER,
                    response_time_ms REAL,
                    success BOOLEAN,
                    error_message TEXT,
                    request_data TEXT,
                    response_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_interactions_user_id ON interactions(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_interactions_timestamp ON interactions(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON system_logs(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_logs_level ON system_logs(level)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_api_calls_timestamp ON api_calls(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_api_calls_api_type ON api_calls(api_type)')
            
            logger.info("数据库初始化完成")
    
    def save_interaction(self, interaction: InteractionRecord) -> int:
        """保存交互记录"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO interactions (
                        timestamp, user_id, platform, original_content,
                        filtered_content, ai_response, risk_level,
                        blocked_reasons, warning_reasons, response_time_ms,
                        product_id, session_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    interaction.timestamp,
                    interaction.user_id,
                    interaction.platform,
                    interaction.original_content,
                    interaction.filtered_content,
                    interaction.ai_response,
                    interaction.risk_level,
                    json.dumps(interaction.blocked_reasons) if isinstance(interaction.blocked_reasons, list) else interaction.blocked_reasons,
                    json.dumps(interaction.warning_reasons) if isinstance(interaction.warning_reasons, list) else interaction.warning_reasons,
                    interaction.response_time_ms,
                    interaction.product_id,
                    interaction.session_id
                ))
                
                return cursor.lastrowid
                
        except Exception as e:
            logger.error(f"保存交互记录失败: {e}")
            return 0
    
    def get_interactions(self, user_id: str = None, limit: int = 100, 
                        offset: int = 0) -> List[InteractionRecord]:
        """获取交互记录"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if user_id:
                    cursor.execute('''
                        SELECT * FROM interactions 
                        WHERE user_id = ? 
                        ORDER BY timestamp DESC 
                        LIMIT ? OFFSET ?
                    ''', (user_id, limit, offset))
                else:
                    cursor.execute('''
                        SELECT * FROM interactions 
                        ORDER BY timestamp DESC 
                        LIMIT ? OFFSET ?
                    ''', (limit, offset))
                
                rows = cursor.fetchall()
                interactions = []
                
                for row in rows:
                    interaction = InteractionRecord(
                        id=row['id'],
                        timestamp=row['timestamp'],
                        user_id=row['user_id'],
                        platform=row['platform'],
                        original_content=row['original_content'],
                        filtered_content=row['filtered_content'],
                        ai_response=row['ai_response'],
                        risk_level=row['risk_level'],
                        blocked_reasons=json.loads(row['blocked_reasons']) if row['blocked_reasons'] else [],
                        warning_reasons=json.loads(row['warning_reasons']) if row['warning_reasons'] else [],
                        response_time_ms=row['response_time_ms'],
                        product_id=row['product_id'],
                        session_id=row['session_id']
                    )
                    interactions.append(interaction)
                
                return interactions
                
        except Exception as e:
            logger.error(f"获取交互记录失败: {e}")
            return []
    
    def save_product(self, product: ProductRecord) -> bool:
        """保存商品信息"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # 检查是否已存在
                cursor.execute('SELECT id FROM products WHERE id = ?', (product.id,))
                exists = cursor.fetchone()
                
                current_time = datetime.now().isoformat()
                
                if exists:
                    # 更新
                    cursor.execute('''
                        UPDATE products SET
                            name = ?, category = ?, price = ?, original_price = ?,
                            discount = ?, promo = ?, features = ?, description = ?,
                            specifications = ?, usage_scenarios = ?, target_audience = ?,
                            faq = ?, risk_warnings = ?, certifications = ?,
                            updated_at = ?, is_active = ?
                        WHERE id = ?
                    ''', (
                        product.name,
                        product.category,
                        product.price,
                        product.original_price,
                        product.discount,
                        product.promo,
                        json.dumps(product.features) if isinstance(product.features, list) else product.features,
                        product.description,
                        json.dumps(product.specifications) if isinstance(product.specifications, dict) else product.specifications,
                        json.dumps(product.usage_scenarios) if isinstance(product.usage_scenarios, list) else product.usage_scenarios,
                        json.dumps(product.target_audience) if isinstance(product.target_audience, list) else product.target_audience,
                        json.dumps(product.faq) if isinstance(product.faq, list) else product.faq,
                        json.dumps(product.risk_warnings) if isinstance(product.risk_warnings, list) else product.risk_warnings,
                        json.dumps(product.certifications) if isinstance(product.certifications, list) else product.certifications,
                        current_time,
                        product.is_active,
                        product.id
                    ))
                else:
                    # 插入
                    cursor.execute('''
                        INSERT INTO products (
                            id, name, category, price, original_price,
                            discount, promo, features, description,
                            specifications, usage_scenarios, target_audience,
                            faq, risk_warnings, certifications,
                            created_at, updated_at, is_active
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        product.id,
                        product.name,
                        product.category,
                        product.price,
                        product.original_price,
                        product.discount,
                        product.promo,
                        json.dumps(product.features) if isinstance(product.features, list) else product.features,
                        product.description,
                        json.dumps(product.specifications) if isinstance(product.specifications, dict) else product.specifications,
                        json.dumps(product.usage_scenarios) if isinstance(product.usage_scenarios, list) else product.usage_scenarios,
                        json.dumps(product.target_audience) if isinstance(product.target_audience, list) else product.target_audience,
                        json.dumps(product.faq) if isinstance(product.faq, list) else product.faq,
                        json.dumps(product.risk_warnings) if isinstance(product.risk_warnings, list) else product.risk_warnings,
                        json.dumps(product.certifications) if isinstance(product.certifications, list) else product.certifications,
                        current_time,
                        current_time,
                        product.is_active
                    ))
                
                return True
                
        except Exception as e:
            logger.error(f"保存商品信息失败: {e}")
            return False
    
    def get_product(self, product_id: str) -> Optional[ProductRecord]:
        """获取商品信息"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM products WHERE id = ?', (product_id,))
                row = cursor.fetchone()
                
                if row:
                    return ProductRecord(
                        id=row['id'],
                        name=row['name'],
                        category=row['category'],
                        price=row['price'],
                        original_price=row['original_price'],
                        discount=row['discount'],
                        promo=row['promo'],
                        features=json.loads(row['features']) if row['features'] else [],
                        description=row['description'],
                        specifications=json.loads(row['specifications']) if row['specifications'] else {},
                        usage_scenarios=json.loads(row['usage_scenarios']) if row['usage_scenarios'] else [],
                        target_audience=json.loads(row['target_audience']) if row['target_audience'] else [],
                        faq=json.loads(row['faq']) if row['faq'] else [],
                        risk_warnings=json.loads(row['risk_warnings']) if row['risk_warnings'] else [],
                        certifications=json.loads(row['certifications']) if row['certifications'] else [],
                        created_at=row['created_at'],
                        updated_at=row['updated_at'],
                        is_active=bool(row['is_active'])
                    )
                return None
                
        except Exception as e:
            logger.error(f"获取商品信息失败: {e}")
            return None
    
    def get_active_products(self) -> List[ProductRecord]:
        """获取活跃商品"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM products WHERE is_active = 1')
                rows = cursor.fetchall()
                
                products = []
                for row in rows:
                    product = ProductRecord(
                        id=row['id'],
                        name=row['name'],
                        category=row['category'],
                        price=row['price'],
                        original_price=row['original_price'],
                        discount=row['discount'],
                        promo=row['promo'],
                        features=json.loads(row['features']) if row['features'] else [],
                        description=row['description'],
                        specifications=json.loads(row['specifications']) if row['specifications'] else {},
                        usage_scenarios=json.loads(row['usage_scenarios']) if row['usage_scenarios'] else [],
                        target_audience=json.loads(row['target_audience']) if row['target_audience'] else [],
                        faq=json.loads(row['faq']) if row['faq'] else [],
                        risk_warnings=json.loads(row['risk_warnings']) if row['risk_warnings'] else [],
                        certifications=json.loads(row['certifications']) if row['certifications'] else [],
                        created_at=row['created_at'],
                        updated_at=row['updated_at'],
                        is_active=bool(row['is_active'])
                    )
                    products.append(product)
                
                return products
                
        except Exception as e:
            logger.error(f"获取活跃商品失败: {e}")
            return []
    
    def log_system_event(self, level: str, module: str, message: str, 
                        details: str = "", user_id: str = "", 
                        session_id: str = "") -> bool:
        """记录系统日志"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO system_logs (
                        timestamp, level, module, message, details, user_id, session_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    datetime.now().isoformat(),
                    level,
                    module,
                    message,
                    details,
                    user_id,
                    session_id
                ))
                
                return True
                
        except Exception as e:
            logger.error(f"记录系统日志失败: {e}")
            return False
    
    def get_system_logs(self, level: str = None, module: str = None, 
                       limit: int = 100) -> List[SystemLog]:
        """获取系统日志"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                query = 'SELECT * FROM system_logs'
                params = []
                
                if level or module:
                    conditions = []
                    if level:
                        conditions.append('level = ?')
                        params.append(level)
                    if module:
                        conditions.append('module = ?')
                        params.append(module)
                    
                    query += ' WHERE ' + ' AND '.join(conditions)
                
                query += ' ORDER