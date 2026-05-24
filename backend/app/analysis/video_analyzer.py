"""
Video analysis module.
Uses MiMo omni model video understanding API to extract visual cues from a video.

请求体对齐小米文档「视频理解」：
https://platform.xiaomimimo.com/#/docs/usage-guide/multimodal-understanding/video-understanding
"""
from __future__ import annotations

import json
import logging
import os
from typing import Optional

from app.agents.base_agent import (
    _get_anthropic_client,
    _get_client,
    _is_anthropic_provider,
    _is_mimo_openai_compat,
    _parse_json_from_llm_text,
)
from app.analysis.mimo_video import build_mimo_video_url_content_part

logger = logging.getLogger("tiktokrx.video_analyzer")


class VideoAnalyzer:
    """Analyze video semantics through MiMo video understanding."""

    async def analyze(
        self,
        video_data_url: str,
        *,
        prompt_hint: str = "",
        fps: Optional[float] = None,
        media_resolution: Optional[str] = None,
    ) -> dict:
        """
        Analyze one video and return structured summary for downstream diagnosis.
        @param fps - 若提供则临时覆盖环境变量 MIMO_VIDEO_FPS（写入 video_url.fps）
        @param media_resolution - 若提供则临时覆盖 MIMO_VIDEO_MEDIA_RESOLUTION
        """
        if _is_anthropic_provider():
            return await self._analyze_anthropic(video_data_url, prompt_hint=prompt_hint)
        client = _get_client()
        model = os.getenv("LLM_MODEL_OMNI", "mimo-v2-omni")
        sys_prompt = (
            "You are a strict JSON video analysis engine. "
            "Return ONLY valid JSON without markdown fences."
        )
        user_prompt = (
            "Analyze the uploaded video for Xiaohongshu note diagnosis and return JSON with fields: "
            "summary (string), "
            "scene_keywords (array of <=8 strings), "
            "cover_suggestion (string), "
            "has_face (boolean), "
            "shot_style (string), "
            "risk_or_limitations (array of strings). "
            "If confidence is low, still return best-effort values."
        )
        if prompt_hint.strip():
            user_prompt += f" Additional context: {prompt_hint.strip()}"

        video_part = build_mimo_video_url_content_part(video_data_url)
        if fps is not None:
            video_part["video_url"]["fps"] = max(0.1, min(float(fps), 10.0))
        if media_resolution is not None and media_resolution in ("default", "max"):
            video_part["media_resolution"] = media_resolution

        kwargs = {
            "model": model,
            "messages": [
                {"role": "system", "content": sys_prompt},
                {
                    "role": "user",
                    "content": [
                        video_part,
                        {"type": "text", "text": user_prompt},
                    ],
                },
            ],
            "temperature": float(os.getenv("LLM_TEMPERATURE", "0.3")),
        }
        max_out = int(os.getenv("LLM_MAX_COMPLETION_TOKENS", "1024"))
        if _is_mimo_openai_compat():
            kwargs["max_completion_tokens"] = max_out
        else:
            kwargs["max_tokens"] = max_out

        resp = await client.chat.completions.create(**kwargs)
        raw = (resp.choices[0].message.content or "").strip()
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = _parse_json_from_llm_text(raw)

        usage = getattr(resp, "usage", None)
        if usage:
            parsed["_meta"] = {
                "prompt_tokens": usage.prompt_tokens,
                "completion_tokens": usage.completion_tokens,
                "total_tokens": usage.total_tokens,
                "model": resp.model,
            }

        parsed.setdefault("summary", "")
        parsed.setdefault("scene_keywords", [])
        parsed.setdefault("cover_suggestion", "")
        parsed.setdefault("has_face", False)
        parsed.setdefault("shot_style", "")
        parsed.setdefault("risk_or_limitations", [])
        return parsed

    async def _analyze_anthropic(self, video_data_url: str, *, prompt_hint: str = "") -> dict:
        """Anthropic 视频分析（降级为文本描述，因为 Anthropic 不支持 video_url 内容块）。"""
        client = _get_anthropic_client()
        model = os.getenv("LLM_MODEL_OMNI", "mimo-v2-omni")
        sys_prompt = (
            "You are a strict JSON video analysis engine. "
            "Return ONLY valid JSON without markdown fences."
        )
        user_prompt = (
            "Analyze the uploaded video for Xiaohongshu note diagnosis and return JSON with fields: "
            "summary (string), "
            "scene_keywords (array of <=8 strings), "
            "cover_suggestion (string), "
            "has_face (boolean), "
            "shot_style (string), "
            "risk_or_limitations (array of strings). "
            "If confidence is low, still return best-effort values."
        )
        if prompt_hint.strip():
            user_prompt += f" Additional context: {prompt_hint.strip()}"

        try:
            resp = await client.messages.create(
                model=model,
                system=sys_prompt,
                messages=[{"role": "user", "content": user_prompt}],
                max_tokens=int(os.getenv("LLM_MAX_COMPLETION_TOKENS", "1024")),
                temperature=float(os.getenv("LLM_TEMPERATURE", "0.3")),
                thinking={"type": "disabled"},
            )
            raw = (next((b.text for b in resp.content if b.type == "text"), "") if resp.content else "").strip()
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                parsed = _parse_json_from_llm_text(raw)

            parsed["_meta"] = {
                "prompt_tokens": resp.usage.input_tokens,
                "completion_tokens": resp.usage.output_tokens,
                "total_tokens": resp.usage.input_tokens + resp.usage.output_tokens,
                "model": resp.model,
            }
        except Exception as e:
            logger.warning("Anthropic 视频分析失败: %s", e)
            parsed = {"summary": "", "scene_keywords": [], "cover_suggestion": "",
                      "has_face": False, "shot_style": "", "risk_or_limitations": [],
                      "error": str(e)}

        parsed.setdefault("summary", "")
        parsed.setdefault("scene_keywords", [])
        parsed.setdefault("cover_suggestion", "")
        parsed.setdefault("has_face", False)
        parsed.setdefault("shot_style", "")
        parsed.setdefault("risk_or_limitations", [])
        return parsed

