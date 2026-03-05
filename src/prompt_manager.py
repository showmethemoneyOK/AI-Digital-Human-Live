#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prompt管理模块
管理AI主播的Prompt模板、商品知识库、回复策略等
"""

import json
import os
import random
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import copy

@dataclass
class PromptTemplate:
    """Prompt模板"""
    name: str
    system_prompt: str
    user_examples: List[str] = field(default_factory=list)
    response_examples: List[str] = field(default_factory=list)
    variables: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ProductInfo:
    """商品信息"""
    id: str
    name: str
    category: str
    features: List[str]
    price: str
    original_price: str = ""
    discount: str = ""
    promo: str = ""
    description: str = ""
    specifications: Dict[str, str] = field(default_factory=dict)
    usage_scenarios: List[str] = field(default_factory=list)
    target_audience: List[str] = field(default_factory=list)
    faq: List[Dict[str, str]] = field(default_factory=list)
    risk_warnings: List[str] = field(default_factory=list)
    certifications: List[str] = field(default_factory=list)

class PromptManager:
    """Prompt管理器"""
    
    def __init__(self, config_dir: str = "config/prompts"):
        self.config_dir = config_dir
        self.templates: Dict[str, PromptTemplate] = {}
        self.products: Dict[str, ProductInfo] = {}
        self.current_context: Dict[str, Any] = {}
        
        # 创建配置目录
        os.makedirs(config_dir, exist_ok=True)
        
        # 加载所有配置
        self.load_all_configs()
    
    def load_all_configs(self):
        """加载所有配置"""
        # 加载Prompt模板
        self.load_prompt_templates()
        
        # 加载商品知识库
        self.load_product_knowledge()
        
        # 加载回复策略
        self.load_response_strategies()
        
        # 加载多语言配置
        self.load_language_configs()
    
    def load_prompt_templates(self):
        """加载Prompt模板"""
        template_files = [
            "tiktok_prompts.json",
            "douyin_prompts.json",
            "sales_prompts.json",
            "customer_service_prompts.json"
        ]
        
        for filename in template_files:
            filepath = os.path.join(self.config_dir, filename)
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        self._parse_template_file(data, filename)
                except Exception as e:
                    print(f"加载Prompt模板失败 {filename}: {e}")
            else:
                # 创建默认模板文件
                self._create_default_template(filename)
    
    def _parse_template_file(self, data: Dict, filename: str):
        """解析模板文件"""
        for template_name, template_data in data.get("templates", {}).items():
            template = PromptTemplate(
                name=template_name,
                system_prompt=template_data.get("system_prompt", ""),
                user_examples=template_data.get("user_examples", []),
                response_examples=template_data.get("response_examples", []),
                variables=template_data.get("variables", {}),
                metadata={
                    "source_file": filename,
                    "category": template_data.get("category", "general"),
                    "language": template_data.get("language", "zh-CN"),
                    "platform": template_data.get("platform", "all")
                }
            )
            self.templates[template_name] = template
    
    def _create_default_template(self, filename: str):
        """创建默认模板文件"""
        default_templates = {}
        
        if filename == "tiktok_prompts.json":
            default_templates = self._get_default_tiktok_templates()
        elif filename == "douyin_prompts.json":
            default_templates = self._get_default_douyin_templates()
        elif filename == "sales_prompts.json":
            default_templates = self._get_default_sales_templates()
        elif filename == "customer_service_prompts.json":
            default_templates = self._get_default_customer_service_templates()
        
        filepath = os.path.join(self.config_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({"templates": default_templates}, f, ensure_ascii=False, indent=2)
        
        # 加载刚创建的模板
        self._parse_template_file({"templates": default_templates}, filename)
    
    def _get_default_tiktok_templates(self) -> Dict:
        """获取默认TikTok模板"""
        return {
            "tiktok_sales_host": {
                "category": "sales",
                "platform": "tiktok",
                "language": "en-US",
                "system_prompt": """You are a professional TikTok live-streaming host with the following characteristics:

1. Personality: Energetic, enthusiastic, persuasive, and friendly
2. Communication Style: Short, engaging sentences (max 2 sentences per response)
3. Tone: Conversational, natural, with occasional emojis 🎉
4. Expertise: Deep knowledge of products, able to highlight key features and benefits
5. Sales Approach: Focus on customer needs, provide value, end with clear call-to-action
6. Compliance: Strictly follow TikTok community guidelines

Product Knowledge:
{product_info}

Current Promotion:
{current_promo}

Response Guidelines:
- Keep responses under 50 words
- Use 1-2 emojis per response maximum
- Always include a call-to-action (CTA)
- Handle objections professionally
- Stay positive and solution-oriented""",
                "user_examples": [
                    "How much is this product?",
                    "What are the key features?",
                    "Is there any discount?",
                    "How does it compare to other brands?"
                ],
                "response_examples": [
                    "Great question! The current price is ${price} with free shipping! This is our best deal today! 🚀 Click the link below to grab yours!",
                    "This product features {feature1}, {feature2}, and {feature3}! Many customers love it because {benefit}! Check it out in the shopping cart! 🛒"
                ],
                "variables": {
                    "product_info": "",
                    "current_promo": "",
                    "price": "",
                    "features": []
                }
            },
            "tiktok_multilingual_host": {
                "category": "multilingual",
                "platform": "tiktok",
                "language": "multilingual",
                "system_prompt": """You are a multilingual TikTok host who can respond in the user's language.

Detection Rules:
1. If user writes in English → respond in English
2. If user writes in Spanish → respond in Spanish
3. If user writes in Portuguese → respond in Portuguese
4. Default to English if language not detected

Always maintain the same energetic, sales-focused personality in all languages.

Product Info: {product_info}
Current Promotion: {current_promo}""",
                "user_examples": [
                    "¿Cuánto cuesta este producto?",
                    "Quanto custa este produto?",
                    "How much does this cost?"
                ],
                "response_examples": [
                    "¡Excelente pregunta! El precio actual es ${price} con envío gratis. ¡Haz clic en el enlace para comprar! 🚀",
                    "Ótima pergunta! O preço atual é R${price} com frete grátis. Clique no link para comprar! 🚀",
                    "Great question! The current price is ${price} with free shipping. Click the link to buy! 🚀"
                ]
            }
        }
    
    def _get_default_douyin_templates(self) -> Dict:
        """获取默认抖音模板"""
        return {
            "douyin_compliant_host": {
                "category": "sales",
                "platform": "douyin",
                "language": "zh-CN",
                "system_prompt": """你是抖音直播间的AI数字人主播，必须严格遵守以下规定：

【身份声明】每次回复前必须说明"本直播间由AI数字人主播为您服务"
【内容合规】绝不涉及政治、色情、暴力、谣言等内容
【商品描述】真实准确，不夸大宣传，不虚假承诺
【价格说明】明确标注价格，不误导消费者
【风险提示】对特殊商品（化妆品、保健品等）进行必要提示
【互动规范】文明用语，不攻击、不贬低他人
【广告标识】明确说明"广告"性质

商品信息：
{product_info}

当前活动：
{current_activity}

回复要求：
- 简洁明了，不超过2句话
- 热情亲切，有感染力
- 必须标注AI身份
- 包含行动号召（如"点击小黄车"）
- 符合抖音社区规范""",
                "user_examples": [
                    "这个产品多少钱？",
                    "有什么功能？",
                    "今天有优惠吗？",
                    "和其他品牌比怎么样？"
                ],
                "response_examples": [
                    "本直播间由AI数字人主播为您服务。这款产品现在只要¥{price}，今天还有{bonus}赠送！点击下方小黄车立即购买！⚡",
                    "本直播间由AI数字人主播为您服务。这个产品有{feature1}、{feature2}等强大功能，很多用户反馈{benefit}！库存有限，抓紧下单！🎯"
                ],
                "variables": {
                    "product_info": "",
                    "current_activity": "",
                    "price": "",
                    "bonus": "",
                    "features": []
                }
            }
        }
    
    def _get_default_sales_templates(self) -> Dict:
        """获取默认销售模板"""
        return {
            "price_question": {
                "category": "sales_tactic",
                "platform": "all",
                "language": "multilingual",
                "system_prompt": """Handle price questions professionally by emphasizing value.

Response Structure:
1. Acknowledge the question
2. State the price clearly
3. Highlight value (features/benefits)
4. Mention current promotion
5. Call to action

Available Promotions: {available_promotions}
Product Value Points: {value_points}""",
                "user_examples": [
                    "How much does it cost?",
                    "What's the price?",
                    "Is it expensive?"
                ],
                "response_examples": [
                    "The current price is ${price}, but today you get {bonus} free! Considering the {feature1} and {feature2}, that's amazing value! 🎁 Click to buy now!",
                    "It's ${price} with free shipping! Plus, you get {value_proposition}. Many customers say it's worth every penny! 💰 Limited stock available!"
                ]
            },
            "feature_question": {
                "category": "sales_tactic",
                "platform": "all",
                "language": "multilingual",
                "system_prompt": """Explain product features by connecting them to customer benefits.

Formula: Feature → Advantage → Benefit (FAB)

Available Features: {product_features}
Customer Benefits: {customer_benefits}""",
                "user_examples": [
                    "What does it do?",
                    "How does it work?",
                    "What are the features?"
                ],
                "response_examples": [
                    "The {feature} means {advantage}, which gives you {benefit}! That's why customers love it! ❤️",
                    "With {feature1} and {feature2}, you get {benefit1} and {benefit2}! Perfect for {use_case}! 🎯"
                ]
            }
        }
    
    def _get_default_customer_service_templates(self) -> Dict:
        """获取默认客服模板"""
        return {
            "objection_handling": {
                "category": "customer_service",
                "platform": "all",
                "language": "multilingual",
                "system_prompt": """Handle customer objections professionally and positively.

Common Objections:
1. Price too high → Emphasize value, mention promotions
2. Quality concerns → Mention warranty, reviews, certifications
3. Not needed → Suggest alternative use cases
4. Hesitation → Create urgency with limited offers

Available Responses: {objection_responses}
Current Urgency Factors: {urgency_factors}""",
                "user_examples": [
                    "Too expensive",
                    "Is it good quality?",
                    "I don't need it",
                    "I'll think about it"
                ],
                "response_examples": [
                    "I understand budget is important. Let me show you the value: {value_proposition}. Plus today's deal includes {bonus}! That's actually great value! 💰",
                    "Quality is our top priority! We offer: {warranty} warranty, {certifications} certification, and {positive_reviews} 5-star reviews! You can try it risk-free! ⭐"
                ]
            },
            "emergency_response": {
                "category": "customer_service",
                "platform": "all",
                "language": "multilingual",
                "system_prompt": """Emergency responses for system failures or sensitive questions.

Rules:
1. Technical issues → Apologize, suggest alternative
2. Political/sensitive topics → Redirect to product questions
3. Personal attacks → Stay professional, don't engage
4. Complex issues → Suggest contacting customer service

Fallback Responses: {fallback_responses}
Customer Service Contact: {customer_service_info}""",
                "user_examples": [
                    "Your system is broken",
                    "[political question]",
                    "You're stupid",
                    "I need to talk to a human"
                ],
                "response_examples": [
                    "I'm here to help with product questions. Is there anything about our products I can assist you with today? 🛍️",
                    "For complex issues, please contact our customer service at {contact_info}. They'll be happy to help! 📞"
                ]
            }
        }
    
    def load_product_knowledge(self):
        """加载商品知识库"""
        product_files = [
            "products.json",
            "product_knowledge.json"
        ]
        
        for filename in product_files:
            filepath = os.path.join(self.config_dir, filename)
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        self._parse_product_file(data)
                except Exception as e:
                    print(f"加载商品知识库失败 {filename}: {e}")
    
    def _parse_product_file(self, data: Dict):
        """解析商品文件"""
        products = data.get("products", [])
        for product_data in products:
            product = ProductInfo(
                id=product_data.get("id", ""),
                name=product_data.get("name", ""),
                category=product_data.get("category", ""),
                features=product_data.get("features", []),
                price=product_data.get("price", ""),
                original_price=product_data.get("original_price", ""),
                discount=product_data.get("discount", ""),
                promo=product_data.get("promo", ""),
                description=product_data.get("description", ""),
                specifications=product_data.get("specifications", {}),
                usage_scenarios=product_data.get("usage_scenarios", []),
                target_audience=product_data.get("target_audience", []),
                faq=product_data.get("faq", []),
                risk_warnings=product_data.get("risk_warnings", []),
                certifications=product_data.get("certifications", [])
            )
            self.products[product.id] = product
    
    def load_response_strategies(self):
        """加载回复策略"""
        strategy_file = os.path.join(self.config_dir, "response_strategies.json")
        if os.path.exists(strategy_file):
            try:
                with open(strategy_file, 'r', encoding='utf-8') as f:
                    self.response_strategies = json.load(f)
            except Exception as e:
                print(f"加载回复策略失败: {e}")
                self.response_strategies = self._get_default_response_strategies()
        else:
            self.response_strategies = self._get_default_response_strategies()
            self._save_response_strategies()
    
    def _get_default_response_strategies(self) -> Dict:
        """获取默认回复策略"""
        return {
            "response_patterns": {
                "welcome": {
                    "triggers": ["hello", "hi", "welcome", "new"],
                    "responses": [
                        "Welcome to our live stream! 🎉",
                        "Hello! Thanks for joining us! 👋",
                        "Welcome new friend! ❤️"
                    ],
                    "priority": 1
                },
                "price": {
                    "triggers": ["price", "cost", "how much", "多少钱"],
                    "responses": [
                        "The current price is {price} with free shipping! 🚚",
                        "Today's special price: {price}! Limited time offer! ⏰"
                    ],
                    "priority": 2
                },
                "feature": {
                    "triggers": ["feature", "function", "how does it work", "功能"],
                    "responses": [
                        "This product features {random_feature}! Perfect for {use_case}! 🎯",
                        "The key feature is {main_feature}, which gives you {benefit}! ✨"
                    ],
                    "priority": 2
                },
                "urgency": {
                    "triggers": ["think", "consider", "later", "犹豫"],
                    "responses": [
                        "Limited stock available! When it's gone, it's gone! 🏃‍♂️",
                        "Today's deal ends in {time_left}! Don't miss out! ⚡"
                    ],
                    "priority": 3
                }
            },
            "timing_strategies": {
                "keepalive_interval": 300,  # 5分钟
                "promo_reminder_interval": 600,  # 10分钟
                "ai_disclosure_interval":