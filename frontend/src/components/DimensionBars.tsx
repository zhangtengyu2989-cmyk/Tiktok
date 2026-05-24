import { useEffect, useRef, useState } from "react";
import { Box, Typography, Stack } from "@mui/material";

interface Props {
  data: Record<string, number>;
}

// 维度配置（支持5维和6维动态渲染）
const DIM_CONFIG: Record<string, { label: string; color: string }> = {
  content: { label: "内容质量", color: "#ff2442" },
  visual: { label: "视觉表现", color: "#8b5cf6" },
  growth: { label: "增长策略", color: "#f59e0b" },
  user_reaction: { label: "用户反应", color: "#3b82f6" },
  bgm_adaptation: { label: "BGM适配", color: "#10b981" },
  technical_performance: { label: "技术表现", color: "#06b6d4" },
  overall: { label: "综合评分", color: "#262626" },
};

// 维度显示顺序
const DIM_ORDER = [
  "content", "visual", "growth", "user_reaction",
  "bgm_adaptation", "technical_performance",
];

function scoreLabel(score: number): string {
  if (score >= 90) return "优秀";
  if (score >= 75) return "良好";
  if (score >= 60) return "一般";
  if (score >= 40) return "较差";
  return "很差";
}

export default function DimensionBars({ data }: Props) {
  const [animated, setAnimated] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const timer = setTimeout(() => setAnimated(true), 200);
    return () => clearTimeout(timer);
  }, []);

  // 自适应：只显示数据中存在的维度，按固定顺序排列
  const activeDims = DIM_ORDER.filter((k) => k in data);

  return (
    <Stack ref={ref} spacing={2}>
      {activeDims.map((key) => {
        const dim = DIM_CONFIG[key] ?? { label: key, color: "#888" };
        const score = Math.round(data[key] ?? 0);
        return (
          <Box key={key}>
            <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", mb: 0.5 }}>
              <Typography sx={{ fontSize: 13, fontWeight: 500, color: "#505050" }}>
                {dim.label}
              </Typography>
              <Box sx={{ display: "flex", alignItems: "baseline", gap: 0.5 }}>
                <Typography sx={{ fontSize: 15, fontWeight: 700, color: dim.color, fontVariantNumeric: "tabular-nums" }}>
                  {score}
                </Typography>
                <Typography sx={{ fontSize: 11, color: "#bbb" }}>
                  {scoreLabel(score)}
                </Typography>
              </Box>
            </Box>
            <Box sx={{ height: 7, bgcolor: "rgba(0,0,0,0.04)", borderRadius: 4, overflow: "hidden" }}>
              <Box
                sx={{
                  height: "100%",
                  bgcolor: dim.color,
                  borderRadius: 4,
                  width: animated ? `${score}%` : "0%",
                  transition: "width 1.2s cubic-bezier(0.2,0,0.2,1)",
                  boxShadow: animated ? `0 0 8px ${dim.color}30` : "none",
                }}
              />
            </Box>
          </Box>
        );
      })}
    </Stack>
  );
}
