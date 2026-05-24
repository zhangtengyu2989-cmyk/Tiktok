"""
Pydantic 请求 / 响应模型 - TiktokRx
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum


class InputType(str, Enum):
    """内容类型枚举"""
    VIDEO = "video"           # 短视频
    IMAGE_TEXT = "image"      # 图文作品
    PURE_TEXT = "pure_text"  # 纯文字文章
    BGM = "bgm"             # BGM分析


class DiagnoseRequest(BaseModel):
    """诊断请求体"""
    title: str = ""
    content: str = ""
    category: str
    tags: list[str] = []
    input_type: InputType = InputType.VIDEO
    cover_image_url: Optional[str] = None


class BGMInfo(BaseModel):
    """BGM信息"""
    name: str
    artist: Optional[str] = None
    heat_index: int = 0
    heat_level: str = "C"  # S+, S, A, B, C
    style: Optional[str] = None
    mood: Optional[str] = None
    traffic_impact: str = "0%"


class BGMSuggestion(BaseModel):
    """BGM替换建议"""
    name: str
    artist: Optional[str] = None
    heat_level: str
    heat_index: int
    reason: str
    traffic_change: str  # e.g., "+15%"


class BGMAnalysisResult(BaseModel):
    """BGM分析结果"""
    score: int  # 0-100
    current_bgm: BGMInfo
    issues: list[str]
    suggestions: list[str]
    traffic_impact: str
    alternatives: list[BGMSuggestion] = []


class TextAnalysisResult(BaseModel):
    """纯文字分析结果"""
    score: int  # 0-100
    sub_scores: dict  # 各维度得分
    issues: list[str]
    suggestions: list[str]
    emotion_tendency: str  # 正面/负面/中性
    emotion_intensity: int  # 1-10
    interaction_trigger_count: int
    recommended_tags: list[str]


class AgentOpinion(BaseModel):
    """单个 Agent 的诊断意见"""
    agent_name: str
    dimension: str
    score: float
    issues: list[str]
    suggestions: list[str]
    reasoning: str
    debate_comments: list[str] = []


class SimulatedComment(BaseModel):
    """AI模拟评论"""
    username: str
    avatar_emoji: str
    comment: str
    sentiment: str


class DebateEntry(BaseModel):
    """辩论时间线中的单条记录"""
    round: int
    agent_name: str
    kind: str
    text: str


class CoverDirection(BaseModel):
    """封面方向建议"""
    layout: str = ""
    color_scheme: str = ""
    text_style: str = ""
    tips: list[str] = []


class DiagnoseResponse(BaseModel):
    """诊断报告响应体"""
    overall_score: float
    grade: str
    input_type: InputType = InputType.VIDEO
    radar_data: dict
    agent_opinions: list[AgentOpinion]
    issues: list[dict]
    suggestions: list[dict]
    debate_summary: str
    debate_timeline: list[DebateEntry] = []
    simulated_comments: list[SimulatedComment]
    optimized_title: Optional[str] = None
    optimized_content: Optional[str] = None
    cover_direction: Optional[CoverDirection] = None
    # BGM分析结果（如果有）
    bgm_analysis: Optional[BGMAnalysisResult] = None
    # 文字分析结果（如果有）
    text_analysis: Optional[TextAnalysisResult] = None


# --------------- 历史记录 ---------------

class HistoryCreateRequest(BaseModel):
    """保存诊断历史"""
    title: str
    category: str
    input_type: InputType = InputType.VIDEO
    report: dict


class HistoryListItem(BaseModel):
    """历史列表项（不含完整报告）"""
    id: str
    title: str
    category: str
    input_type: InputType
    overall_score: float
    grade: str
    created_at: str


class HistoryDetail(BaseModel):
    """历史详情（含完整报告）"""
    id: str
    title: str
    category: str
    input_type: InputType
    overall_score: float
    grade: str
    created_at: str
    report: dict


# --------------- BGM相关 ---------------

class BGMHotItem(BaseModel):
    """热门BGM项"""
    id: int
    song_name: str
    artist: Optional[str] = None
    heat_index: int
    heat_level: str
    style: Optional[str] = None
    categories: list[str] = []


class BGMHotResponse(BaseModel):
    """热门BGM列表响应"""
    items: list[BGMHotItem]
    total: int


class BGMIdentifyRequest(BaseModel):
    """BGM识别请求"""
    bgm_name: Optional[str] = None
    category: Optional[str] = None
