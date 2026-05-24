import { useEffect, useRef } from "react";
import * as echarts from "echarts/core";
import { RadarChart as EChartsRadar } from "echarts/charts";
import {
  TooltipComponent,
  RadarComponent,
} from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";

echarts.use([EChartsRadar, TooltipComponent, RadarComponent, CanvasRenderer]);

interface Props {
  data: Record<string, number>;
}

// 维度中文名映射（支持5维和6维）
const DIM_LABEL: Record<string, string> = {
  content: "内容质量",
  visual: "视觉表现",
  growth: "增长策略",
  user_reaction: "用户反应",
  bgm_adaptation: "BGM适配",
  technical_performance: "技术表现",
  overall: "综合评分",
};

// 雷达图显示的维度（排除 overall，它不是雷达的一个轴）
const RADAR_DIMS = [
  "content", "visual", "growth", "user_reaction",
  "bgm_adaptation", "technical_performance",
];

export default function RadarChart({ data }: Props) {
  const chartRef = useRef<HTMLDivElement>(null);
  const instanceRef = useRef<echarts.ECharts | null>(null);

  // 自适应：只显示数据中存在的维度
  const activeDims = RADAR_DIMS.filter((k) => k in (data || {}));
  const indicators = activeDims.map((key) => ({
    name: DIM_LABEL[key] ?? key,
    max: 100,
  }));
  const values = activeDims.map((key) => (data || {})[key] ?? 50);

  useEffect(() => {
    if (!chartRef.current) return;
    // 延迟初始化确保容器尺寸已计算
    const initChart = () => {
      if (!chartRef.current) return;
      if (!instanceRef.current) {
        instanceRef.current = echarts.init(chartRef.current);
      }
      instanceRef.current.setOption({
        animationDuration: 1200,
        radar: {
          indicator: indicators,
          shape: "polygon" as const,
          splitNumber: 4,
          center: ["50%", "50%"],
          radius: "55%",
          axisName: {
            color: "#262626",
            fontSize: 10,
            fontWeight: 600,
            padding: [0, 12],
            overflow: "truncate",
            width: 48,
          },
          splitLine: { lineStyle: { color: "#f0f0f0" } },
          splitArea: { show: false },
          axisLine: { lineStyle: { color: "#e8e8e8" } },
        },
        series: [
          {
            type: "radar",
            data: [
              {
                value: values,
                areaStyle: { color: "rgba(255,36,66,0.15)" },
                lineStyle: { color: "#ff2442", width: 2 },
                itemStyle: { color: "#ff2442", borderColor: "#fff", borderWidth: 2 },
                symbol: "circle",
                symbolSize: 6,
              },
            ],
          },
        ],
        tooltip: {
          trigger: "item",
          backgroundColor: "#fff",
          borderColor: "#f0f0f0",
          textStyle: { color: "#262626", fontSize: 13 },
        },
      });
      instanceRef.current.resize();
    };
    // 使用 requestAnimationFrame 确保 DOM 已布局
    const raf = requestAnimationFrame(initChart);
    return () => cancelAnimationFrame(raf);
  }, [data, indicators, values]);

  useEffect(() => {
    const handleResize = () => instanceRef.current?.resize();
    window.addEventListener("resize", handleResize);
    // 监听容器尺寸变化
    const ro = new ResizeObserver(() => instanceRef.current?.resize());
    if (chartRef.current) ro.observe(chartRef.current);
    return () => {
      window.removeEventListener("resize", handleResize);
      ro.disconnect();
      instanceRef.current?.dispose();
      instanceRef.current = null;
    };
  }, []);

  if (activeDims.length === 0) {
    return <div style={{ height: 280, display: "flex", alignItems: "center", justifyContent: "center", color: "#ccc", fontSize: 13 }}>暂无雷达数据</div>;
  }

  return <div ref={chartRef} style={{ height: 300, width: "100%", padding: "0 8px" }} />;
}
