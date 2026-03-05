#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
内容安全过滤模块
包含敏感词检测、合规检查、内容审核等功能
"""

import re
import json
import os
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum

class ContentRiskLevel(Enum):
    """内容风险等级"""
    SAFE = "safe"           # 安全
    LOW_RISK = "low_risk"   # 低风险
    MEDIUM_RISK = "medium_risk"  # 中风险
    HIGH_RISK = "high_risk" # 高风险
    BLOCKED = "blocked"     # 必须拦截

@dataclass
class FilterResult:
    """过滤结果"""
    passed: bool = False
    risk_level: ContentRiskLevel = ContentRiskLevel.SAFE
    filtered_text: str = ""
    blocked_reasons: List[str] = field(default_factory=list)
    warning_reasons: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)

class ContentFilter:
    """内容安全过滤器"""
    
    def __init__(self, config_path: str = "config/filter_config.json"):
        self.config_path = config_path
        self.sensitive_words = set()
        self.political_keywords = set()
        self.advertising_keywords = set()
        self.violence_keywords = set()
        self.sexual_keywords = set()
        self.scam_keywords = set()
        self.compliance_rules = {}
        
        # 加载配置
        self.load_config()
        
        # 编译正则表达式
        self.compile_patterns()
    
    def load_config(self):
        """加载过滤配置"""
        default_config = self.get_default_config()
        
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            else:
                config = default_config
                # 保存默认配置
                os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"加载过滤配置失败，使用默认配置: {e}")
            config = default_config
        
        # 加载敏感词库
        self.sensitive_words = set(config.get("sensitive_words", []))
        self.political_keywords = set(config.get("political_keywords", []))
        self.advertising_keywords = set(config.get("advertising_keywords", []))
        self.violence_keywords = set(config.get("violence_keywords", []))
        self.sexual_keywords = set(config.get("sexual_keywords", []))
        self.scam_keywords = set(config.get("scam_keywords", []))
        self.compliance_rules = config.get("compliance_rules", {})
        
        # 加载外部敏感词文件（如果有）
        self.load_external_wordlists()
    
    def get_default_config(self) -> Dict:
        """获取默认配置"""
        return {
            "sensitive_words": [
                # 政治敏感词
                "政治敏感词1", "政治敏感词2", "政治敏感词3",
                # 违法内容
                "毒品", "枪支", "爆炸物",
                # 欺诈
                "传销", "诈骗", "赌博",
                # 其他
                "自杀", "暴力", "恐怖"
            ],
            "political_keywords": [
                "国家领导人", "政府", "政党", "政治", "敏感事件"
            ],
            "advertising_keywords": [
                "最低价", "全网最低", "绝对便宜", "亏本卖",
                "假一赔十", "无效退款", "保证有效"
            ],
            "violence_keywords": [
                "打死", "杀死", "暴力", "血腥", "恐怖"
            ],
            "sexual_keywords": [
                "色情", "淫秽", "性爱", "裸体", "成人"
            ],
            "scam_keywords": [
                "免费领取", "中奖", "转账", "银行卡", "密码"
            ],
            "compliance_rules": {
                "max_length": 200,  # 最大长度
                "min_length": 2,    # 最小长度
                "allow_emoji": True,  # 允许表情
                "max_emoji_count": 5,  # 最大表情数量
                "allow_urls": False,  # 允许URL
                "allow_phone": False,  # 允许电话号码
                "allow_email": False,  # 允许邮箱
                "require_ai_disclosure": True,  # 需要AI身份声明
                "ai_disclosure_text": "本直播间由AI数字人主播为您服务"
            },
            "risk_thresholds": {
                "high_risk_score": 80,
                "medium_risk_score": 50,
                "low_risk_score": 20
            }
        }
    
    def load_external_wordlists(self):
        """加载外部敏感词文件"""
        wordlist_dirs = [
            "config/wordlists/",
            "assets/wordlists/",
            "data/wordlists/"
        ]
        
        for dir_path in wordlist_dirs:
            if os.path.exists(dir_path):
                for filename in os.listdir(dir_path):
                    if filename.endswith('.txt'):
                        filepath = os.path.join(dir_path, filename)
                        try:
                            with open(filepath, 'r', encoding='utf-8') as f:
                                words = [line.strip() for line in f if line.strip()]
                                self.sensitive_words.update(words)
                            print(f"已加载敏感词文件: {filename}, 词数: {len(words)}")
                        except Exception as e:
                            print(f"加载敏感词文件失败 {filename}: {e}")
    
    def compile_patterns(self):
        """编译正则表达式模式"""
        # URL模式
        self.url_pattern = re.compile(
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        )
        
        # 电话号码模式
        self.phone_pattern = re.compile(
            r'1[3-9]\d{9}|0\d{2,3}-\d{7,8}|400-\d{3}-\d{4}'
        )
        
        # 邮箱模式
        self.email_pattern = re.compile(
            r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        )
        
        # 微信/QQ模式
        self.social_pattern = re.compile(
            r'微信[:：]?\s*[a-zA-Z0-9_-]{6,20}|'
            r'QQ[:：]?\s*\d{5,12}|'
            r'加[我你]?[微Vv信qQ]{1,3}'
        )
    
    def filter_text(self, text: str, context: Dict = None) -> FilterResult:
        """过滤文本内容"""
        if not text or not isinstance(text, str):
            return FilterResult(passed=False, risk_level=ContentRiskLevel.HIGH_RISK)
        
        result = FilterResult()
        result.filtered_text = text
        risk_score = 0
        
        # 1. 基础检查
        basic_checks = self._check_basic_rules(text)
        if not basic_checks["passed"]:
            result.blocked_reasons.extend(basic_checks["reasons"])
            risk_score += 30
        
        # 2. 敏感词检查
        sensitive_result = self._check_sensitive_words(text)
        if sensitive_result["found"]:
            result.blocked_reasons.extend(sensitive_result["reasons"])
            risk_score += sensitive_result["score"]
            # 替换敏感词
            result.filtered_text = sensitive_result["filtered_text"]
        
        # 3. 合规检查（针对抖音）
        if context and context.get("platform") == "douyin":
            compliance_result = self._check_compliance(text, context)
            if not compliance_result["passed"]:
                result.blocked_reasons.extend(compliance_result["reasons"])
                risk_score += 40
        
        # 4. 广告检测
        ad_result = self._check_advertising(text)
        if ad_result["found"]:
            result.warning_reasons.extend(ad_result["reasons"])
            risk_score += ad_result["score"]
        
        # 5. 风险内容检测
        risk_result = self._check_risk_content(text)
        if risk_result["found"]:
            result.blocked_reasons.extend(risk_result["reasons"])
            risk_score += risk_result["score"]
        
        # 6. 联系方式检测
        contact_result = self._check_contact_info(text)
        if contact_result["found"]:
            result.blocked_reasons.extend(contact_result["reasons"])
            risk_score += 50
        
        # 确定风险等级
        result.risk_level = self._calculate_risk_level(risk_score)
        
        # 判断是否通过
        if (result.risk_level == ContentRiskLevel.BLOCKED or 
            result.risk_level == ContentRiskLevel.HIGH_RISK):
            result.passed = False
        else:
            result.passed = True
        
        # 添加建议
        if not result.passed and result.risk_level == ContentRiskLevel.MEDIUM_RISK:
            result.suggestions.append("内容存在风险，建议修改后重试")
        elif result.risk_level == ContentRiskLevel.LOW_RISK:
            result.suggestions.append("内容基本安全，但建议优化表达")
        
        return result
    
    def _check_basic_rules(self, text: str) -> Dict:
        """基础规则检查"""
        rules = self.compliance_rules
        reasons = []
        
        # 长度检查
        if len(text) > rules.get("max_length", 200):
            reasons.append(f"内容过长（{len(text)}字符），最大允许{rules['max_length']}字符")
        
        if len(text) < rules.get("min_length", 2):
            reasons.append(f"内容过短（{len(text)}字符），至少需要{rules['min_length']}字符")
        
        # 表情检查
        if not rules.get("allow_emoji", True):
            # 简单的表情检测
            emoji_count = sum(1 for char in text if ord(char) > 0x2000)
            if emoji_count > 0:
                reasons.append("不允许使用表情符号")
        
        elif rules.get("allow_emoji", True):
            emoji_count = sum(1 for char in text if ord(char) > 0x2000)
            max_emoji = rules.get("max_emoji_count", 5)
            if emoji_count > max_emoji:
                reasons.append(f"表情符号过多（{emoji_count}个），最多允许{max_emoji}个")
        
        return {
            "passed": len(reasons) == 0,
            "reasons": reasons
        }
    
    def _check_sensitive_words(self, text: str) -> Dict:
        """敏感词检查"""
        found_words = []
        filtered_text = text
        score = 0
        
        # 检查所有敏感词类别
        word_categories = [
            (self.sensitive_words, 50, "敏感词"),
            (self.political_keywords, 80, "政治敏感词"),
            (self.violence_keywords, 70, "暴力内容"),
            (self.sexual_keywords, 70, "色情内容"),
            (self.scam_keywords, 60, "欺诈内容")
        ]
        
        for word_set, word_score, category in word_categories:
            for word in word_set:
                if word in text:
                    found_words.append(f"{category}: {word}")
                    score += word_score
                    # 替换为***
                    filtered_text = filtered_text.replace(word, "***")
        
        return {
            "found": len(found_words) > 0,
            "reasons": found_words,
            "score": score,
            "filtered_text": filtered_text
        }
    
    def _check_compliance(self, text: str, context: Dict) -> Dict:
        """合规检查（针对抖音）"""
        reasons = []
        
        # 检查AI身份声明
        if self.compliance_rules.get("require_ai_disclosure", True):
            disclosure_text = self.compliance_rules.get("ai_disclosure_text", "")
            if disclosure_text and disclosure_text not in text:
                reasons.append("缺少AI身份声明")
        
        # 检查虚假宣传
        for keyword in self.advertising_keywords:
            if keyword in text:
                reasons.append(f"可能涉及虚假宣传: {keyword}")
                break
        
        # 检查价格说明
        price_patterns = [
            r"原价\s*[¥$]?\s*\d+",
            r"现价\s*[¥$]?\s*\d+",
            r"仅售\s*[¥$]?\s*\d+"
        ]
        
        for pattern in price_patterns:
            if re.search(pattern, text):
                # 检查是否有明确的价格说明
                if "价格" not in text and "售价" not in text:
                    reasons.append("价格信息不明确")
                break
        
        return {
            "passed": len(reasons) == 0,
            "reasons": reasons
        }
    
    def _check_advertising(self, text: str) -> Dict:
        """广告内容检测"""
        found = False
        reasons = []
        score = 0
        
        for keyword in self.advertising_keywords:
            if keyword in text:
                found = True
                reasons.append(f"广告内容: {keyword}")
                score += 30
                break
        
        # 检查过度促销用语
        promotion_words = ["限时", "抢购", "秒杀", "仅限", "最后"]
        promotion_count = sum(1 for word in promotion_words if word in text)
        if promotion_count >= 3:
            found = True
            reasons.append("过度促销用语")
            score += 20
        
        return {
            "found": found,
            "reasons": reasons,
            "score": score
        }
    
    def _check_risk_content(self, text: str) -> Dict:
        """风险内容检测"""
        found = False
        reasons = []
        score = 0
        
        # 检查医疗相关（高风险）
        medical_keywords = ["治疗", "治愈", "疗效", "药效", "保健品"]
        medical_count = sum(1 for word in medical_keywords if word in text)
        if medical_count > 0:
            found = True
            reasons.append("涉及医疗内容，需要风险提示")
            score += 40
        
        # 检查金融相关（高风险）
        financial_keywords = ["投资", "理财", "收益", "回报率", "金融"]
        financial_count = sum(1 for word in financial_keywords if word in text)
        if financial_count > 0:
            found = True
            reasons.append("涉及金融内容，需要风险提示")
            score += 50
        
        return {
            "found": found,
            "reasons": reasons,
            "score": score
        }
    
    def _check_contact_info(self, text: str) -> Dict:
        """联系方式检测"""
        found = False
        reasons = []
        
        # 检查URL
        if self.url_pattern.search(text):
            found = True
            reasons.append("包含URL链接")
        
        # 检查电话号码
        if self.phone_pattern.search(text):
            found = True
            reasons.append("包含电话号码")
        
        # 检查邮箱
        if self.email_pattern.search(text):
            found = True
            reasons.append("包含邮箱地址")
        
        # 检查微信/QQ
        if self.social_pattern.search(text):
            found = True
            reasons.append("包含社交媒体联系方式")
        
        return {
            "found": found,
            "reasons": reasons,
            "score": 50 if found else 0
        }
    
    def _calculate_risk_level(self, score: int) -> ContentRiskLevel:
        """计算风险等级"""
        thresholds = self.compliance_rules.get("risk_thresholds", {})
        
        high_threshold = thresholds.get("high_risk_score", 80)
        medium_threshold = thresholds.get("medium_risk_score", 50)
        low_threshold = thresholds.get("low_risk_score", 20)
        
        if score >= high_threshold:
            return ContentRiskLevel.BLOCKED
        elif score >= medium_threshold:
            return ContentRiskLevel.HIGH_RISK
        elif score >= low_threshold:
            return ContentRiskLevel.MEDIUM_RISK
        elif score > 0:
            return ContentRiskLevel.LOW_RISK
        else:
            return ContentRiskLevel.SAFE
    
    def add_sensitive_word(self, word: str, category: str = "general"):
        """添加敏感词"""
        if category == "political":
            self.political_keywords.add(word)
        elif category == "advertising":
            self.advertising_keywords.add(word)
        elif category == "violence":
            self.violence_keywords.add(word)
        elif category == "sexual":
            self.sexual_keywords.add(word)
        elif category == "scam":
            self.scam_keywords.add(word)
        else:
            self.sensitive_words.add(word)
    
    def save_config(self):
        """保存配置到文件"""
        config = {
            "sensitive_words": list(self.sensitive_words),
            "political_keywords": list(self.political_keywords),
            "advertising_keywords": list(self.advertising_keywords),
            "violence_keywords": list(self.violence_keywords),
            "sexual_keywords": list(self.sexual_keywords),
            "scam_keywords": list(self