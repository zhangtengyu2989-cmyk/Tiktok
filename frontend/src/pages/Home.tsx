import { useState, useEffect, useCallback, useMemo, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import axios from "axios";
import {
  Box, Typography, TextField, Button, Chip,
  CircularProgress, useTheme,
  useMediaQuery, Alert,
} from "@mui/material";
import HistoryOutlined from "@mui/icons-material/HistoryOutlined";
import EmailOutlinedIcon from "@mui/icons-material/EmailOutlined";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import CategoryPicker from "../components/CategoryPicker";
import UploadZone from "../components/UploadZone";
import { quickRecognize, quickRecognizeVideo, getApiHealth } from "../utils/api";
import type { QuickRecognizeResult } from "../utils/api";

/** @returns A stable key for a File object */
function fkey(f: File) {
  return `${f.name}_${f.size}_${f.lastModified}`;
}

/** 中文垂类 -> 英文 key 映射 */
const CAT_MAP: Record<string, string> = {
  "美食": "food", "食谱": "food", "做饭": "food", "烘焙": "food",
  "穿搭": "fashion", "时尚": "fashion", "服装": "fashion", "outfit": "fashion",
  "科技": "tech", "数码": "tech", "手机": "tech", "电脑": "tech",
  "旅行": "travel", "旅游": "travel", "景点": "travel",
  "美妆": "beauty", "护肤": "beauty", "化妆": "beauty",
  "健身": "fitness", "运动": "fitness", "减肥": "fitness",
  "生活": "lifestyle", "日常": "lifestyle", "vlog": "lifestyle",
  "家居": "home", "装修": "home", "家装": "home",
  // English keys pass through
  "food": "food", "fashion": "fashion", "tech": "tech", "travel": "travel",
  "beauty": "beauty", "fitness": "fitness", "lifestyle": "lifestyle", "home": "home",
};

/** 快识并行路数 */
const QUICK_RECOGNIZE_CONCURRENCY = 10;

/** 分析中轮播文案 */
const ANALYSIS_MESSAGES = [
  "正在全面分析视频内容...",
  "正在调用流量预测模型...",
  "正在识别封面视觉元素...",
  "正在提取标题和描述...",
  "正在比对同类内容数据...",
  "正在评估互动潜力...",
];

/** 平滑进度条：匀速前进到90%，每完成一张跳到真实进度，全部完成到100% */
function SmoothProgressBar({ done, total }: { done: number; total: number }) {
  const [smooth, setSmooth] = useState(0);
  const realPct = total === 0 ? 0 : (done / total) * 100;
  const targetRef = useRef(realPct);
  targetRef.current = realPct;

  useEffect(() => {
    // Tick every 200ms, creep toward 90% slowly, jump to real when real > smooth
    const timer = setInterval(() => {
      setSmooth((prev) => {
        const target = targetRef.current;
        if (target >= 100) return 100;
        if (target > prev) return target; // real progress jumped ahead, snap to it
        if (prev >= 90) return prev; // cap fake progress at 90%
        return prev + 0.8; // creep ~4%/sec
      });
    }, 200);
    return () => clearInterval(timer);
  }, []);

  // Snap to 100 when all done
  useEffect(() => {
    if (realPct >= 100) setSmooth(100);
  }, [realPct]);

  return (
    <Box sx={{ height: 4, bgcolor: "#f0f0f0", borderRadius: 2, overflow: "hidden" }}>
      <Box sx={{
        height: "100%", borderRadius: 2,
        background: "linear-gradient(90deg, #25f4ee, #fe2c55)",
        width: `${Math.min(smooth, 100)}%`,
        transition: "width 0.4s cubic-bezier(0.4,0,0.2,1)",
        position: "relative",
        "&::after": {
          content: '""', position: "absolute", inset: 0,
          background: "linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent)",
          animation: "shimmer 1.5s infinite",
        },
      }} />
    </Box>
  );
}

function AnalysisStatusText() {
  const [idx, setIdx] = useState(0);
  useEffect(() => {
    const t = setInterval(() => setIdx((i) => (i + 1) % ANALYSIS_MESSAGES.length), 3000);
    return () => clearInterval(t);
  }, []);
  return (
    <AnimatePresence mode="wait">
      <motion.div key={idx} initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -4 }} transition={{ duration: 0.2 }}>
        <Typography sx={{ fontSize: 11, color: "#999", fontWeight: 500 }}>
          {ANALYSIS_MESSAGES[idx]}
        </Typography>
      </motion.div>
    </AnimatePresence>
  );
}

/** 首页：桌面端双栏布局，移动端单页布局 */
export default function Home() {
  const navigate = useNavigate();
  const theme = useTheme();
  const isDesktop = useMediaQuery(theme.breakpoints.up("md"));

  const [files, setFiles] = useState<File[]>([]);
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [category, setCategory] = useState("food");

  const [aiRecogs, setAiRecogs] = useState<Record<string, QuickRecognizeResult>>({});
  const [aiLoading, setAiLoading] = useState<Record<string, boolean>>({});
  const [uploadingPulse, setUploadingPulse] = useState(false);
  const [analyzingPulse, setAnalyzingPulse] = useState(false);

  const [userEdited, setUserEdited] = useState({ title: false, content: false, category: false });
  /** null=探测中；false=连不上本机 API（多为未启动或 Vite 代理端口不对） */
  const [apiReachable, setApiReachable] = useState<boolean | null>(null);

  const uploadPulseTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const analyzePulseTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const recognizeInFlightRef = useRef<Set<string>>(new Set());
  const prevPendingRecognitionRef = useRef(false);

  useEffect(() => { document.title = "抖医 - AI 驱动的抖音内容诊断平台"; }, []);

  useEffect(() => {
    void getApiHealth().then(setApiReachable);
  }, []);

  useEffect(() => {
    return () => {
      if (uploadPulseTimerRef.current) clearTimeout(uploadPulseTimerRef.current);
      if (analyzePulseTimerRef.current) clearTimeout(analyzePulseTimerRef.current);
    };
  }, []);

  const triggerUploadPulse = useCallback(() => {
    if (uploadPulseTimerRef.current) clearTimeout(uploadPulseTimerRef.current);
    setUploadingPulse(true);
    uploadPulseTimerRef.current = setTimeout(() => {
      setUploadingPulse(false);
      uploadPulseTimerRef.current = null;
    }, 500);
  }, []);

  const handleFilesChange = useCallback(
    (newFiles: File[]) => {
      setFiles(newFiles.slice(0, 9));
      if (newFiles.length > 0) triggerUploadPulse();
    },
    [triggerUploadPulse],
  );

  const appendFiles = useCallback(
    (incoming: File[]) => {
      if (incoming.length === 0) return;
      setFiles((prev) => [...prev, ...incoming].slice(0, 9));
      triggerUploadPulse();
    },
    [triggerUploadPulse],
  );

  /** Ctrl+V paste images */
  useEffect(() => {
    const handlePaste = (e: ClipboardEvent) => {
      const items = e.clipboardData?.items;
      if (!items) return;
      const pasted: File[] = [];
      for (const item of items) {
        if (item.type.startsWith("image/") || item.type.startsWith("video/")) {
          const file = item.getAsFile();
          if (file) pasted.push(file);
        }
      }
      appendFiles(pasted);
    };
    window.addEventListener("paste", handlePaste);
    return () => window.removeEventListener("paste", handlePaste);
  }, [appendFiles]);

  const anyLoading = useMemo(() => Object.values(aiLoading).some(Boolean), [aiLoading]);
  const allResults = useMemo(() => Object.values(aiRecogs), [aiRecogs]);
  const successRecogEntries = useMemo(
    () => Object.entries(aiRecogs).filter(([, r]) => r.success),
    [aiRecogs],
  );
  const successResults = useMemo(
    () => successRecogEntries.map(([, r]) => r),
    [successRecogEntries],
  );

  const aggregated = useMemo(() => {
    let bestTitle = "";
    const contentParts: string[] = [];  // 合并多张图的正文
    let bestCategory = "";
    let bestSummary = "";
    let engLikes = 0, engCollects = 0, engComments = 0;

    // Pass 1: content 类型 — 标题取第一个, 正文全部合并
    for (const [, r] of successRecogEntries) {
      if ((r.slot_type || "").toLowerCase() === "content") {
        if (!bestTitle && r.title?.trim()) bestTitle = r.title.trim();
        if (r.content_text?.trim()) contentParts.push(r.content_text.trim());
      }
      if (!bestCategory && r.category?.trim()) bestCategory = r.category.trim();
      if (!bestSummary && r.summary?.trim()) bestSummary = r.summary.trim();
      // 提取互动数据（取最大值）
      const eng = r.engagement_signal;
      if (eng) {
        engLikes = Math.max(engLikes, eng.likes_visible || 0);
        engCollects = Math.max(engCollects, eng.collects_visible || 0);
        engComments = Math.max(engComments, eng.comments_visible || 0);
      }
    }

    // Pass 2: fallback — 非 content 类型补充
    if (!bestTitle) {
      for (const [, r] of successRecogEntries) {
        if (!bestTitle && r.title?.trim()) bestTitle = r.title.trim();
      }
    }
    if (contentParts.length === 0) {
      for (const [, r] of successRecogEntries) {
        if (r.content_text?.trim()) contentParts.push(r.content_text.trim());
      }
    }

    // 合并正文（去重：如果两段内容有50%以上重叠就跳过）
    const mergedParts: string[] = [];
    for (const part of contentParts) {
      const isDuplicate = mergedParts.some((existing) => {
        const shorter = part.length < existing.length ? part : existing;
        return existing.includes(shorter.slice(0, 30)) || part.includes(existing.slice(0, 30));
      });
      if (!isDuplicate) mergedParts.push(part);
    }
    let bestContent = mergedParts.join("\n");

    /**
     * 封面图 slot 模型常按要求不返 title/content_text，只返 summary。
     * 若不回填，会出现「垂类已识别、分析完成」但标题正文全空。
     */
    /** 仅视频时 summary 多为画面概括，不能冒充笔记标题（标题需另传封面/标题截图） */
    const videoOnlySuccess =
      successRecogEntries.length > 0 &&
      successRecogEntries.every(([, r]) => r.success && r.media_source === "video");

    if (!bestTitle && bestSummary && !videoOnlySuccess) {
      const s = bestSummary.replace(/\s+/g, " ").trim();
      if (s) {
        const firstPhrase = (s.split(/[。！？\n]/)[0] || s).trim();
        bestTitle = (firstPhrase || s).slice(0, 100);
      }
    }
    if (!bestContent.trim() && bestSummary.trim()) {
      bestContent = bestSummary.trim();
    }

    return {
      bestTitle, bestContent, bestCategory, bestSummary,
      engagementData: { likes: engLikes, collects: engCollects, comments: engComments },
    };
  }, [successRecogEntries]);

  const imageFileKeys = useMemo(
    () => new Set(files.filter((f) => f.type.startsWith("image/")).map(fkey)),
    [files],
  );

  /** 待快识的视频（与 UploadZone 一致，至多一个视频位） */
  const videoFileKeys = useMemo(
    () => new Set(files.filter((f) => f.type.startsWith("video/")).map(fkey)),
    [files],
  );

  /** 图片 + 视频均需完成快识后解锁表单 */
  const recognizeFileKeys = useMemo(() => {
    const s = new Set<string>();
    imageFileKeys.forEach((k) => s.add(k));
    videoFileKeys.forEach((k) => s.add(k));
    return s;
  }, [imageFileKeys, videoFileKeys]);

  const pendingRecognition = useMemo(() => {
    if (recognizeFileKeys.size === 0) return false;
    for (const key of recognizeFileKeys) {
      if (aiLoading[key] || !aiRecogs[key]) return true;
    }
    return false;
  }, [recognizeFileKeys, aiLoading, aiRecogs]);

  const allRecognitionDone = useMemo(() => {
    if (recognizeFileKeys.size === 0) return true;
    for (const k of recognizeFileKeys) {
      if (!aiRecogs[k] && !aiLoading[k]) return false;
      if (aiLoading[k]) return false;
    }
    return true;
  }, [recognizeFileKeys, aiRecogs, aiLoading]);

  useEffect(() => {
    const { bestTitle, bestContent, bestCategory } = aggregated;

    if (!userEdited.title && bestTitle) {
      setTitle(bestTitle.slice(0, 100));
    }
    if (!userEdited.content && bestContent) {
      setContent(bestContent);
    }
    if (!userEdited.category && bestCategory) {
      const mapped = CAT_MAP[bestCategory];
      if (mapped) setCategory(mapped);
    }
  }, [aggregated, userEdited]);

  const allFailed = allRecognitionDone && successResults.length === 0 && allResults.length > 0;

  /** 全部失败时展示后端/模型返回的首条原因，便于区分「连不上 API」与「Key/模型报错」 */
  const firstRecognizeError = useMemo(() => {
    for (const r of Object.values(aiRecogs)) {
      if (!r.success && r.error?.trim()) return r.error.trim();
    }
    return null;
  }, [aiRecogs]);

  const showWarnings = allRecognitionDone && files.length > 0 && !allFailed;
  const warnings = useMemo(() => {
    if (!showWarnings) return { title: false, content: false, category: false };
    const { bestTitle, bestContent, bestCategory, bestSummary } = aggregated;
    return {
      title: !bestTitle && !bestSummary,
      content: !bestContent,
      category: !bestCategory,
    };
  }, [showWarnings, aggregated]);

  const autoFilled = useMemo(() => {
    const { bestTitle, bestContent, bestCategory } = aggregated;
    return {
      /** 仅当有可写入标题的识别字段时标「已填」；仅有 summary 不会写入标题，避免空框却显示已填 */
      title: !userEdited.title && !!bestTitle,
      content: !userEdited.content && !!bestContent,
      category: !userEdited.category && !!bestCategory && !!CAT_MAP[bestCategory],
    };
  }, [aggregated, userEdited]);

  /** 仅有视频、无截图：笔记标题通常不在视频画面里 */
  const videoWithoutImage = videoFileKeys.size > 0 && imageFileKeys.size === 0;

  const runRecognition = useCallback(async (file: File, slotHint?: "cover" | "content" | "profile" | "comments") => {
    const key = fkey(file);
    if (recognizeInFlightRef.current.has(key)) return;
    recognizeInFlightRef.current.add(key);
    setAiLoading((p) => {
      if (p[key]) return p;
      return { ...p, [key]: true };
    });
    try {
      const res = file.type.startsWith("video/")
        ? await quickRecognizeVideo(file)
        : await quickRecognize(file, slotHint);
      const merged =
        !res.success && !res.error?.trim()
          ? {
              ...res,
              error: "识别未返回有效内容，请检查 OPENAI_API_KEY、OPENAI_BASE_URL 与 LLM_MODEL_OMNI",
            }
          : res;
      setAiRecogs((p) => ({ ...p, [key]: merged }));
    } catch (e: unknown) {
      let errMsg = "识别失败";
      if (axios.isAxiosError(e)) {
        const d = e.response?.data;
        if (d && typeof d === "object" && "detail" in d) {
          const det = (d as { detail: unknown }).detail;
          errMsg = typeof det === "string" ? det : JSON.stringify(det);
        } else if (e.code === "ERR_NETWORK" || e.message === "Network Error") {
          errMsg = "无法连接后端：请确认已启动 API，且端口与 Vite 代理一致（默认 8000，可用 VITE_API_PROXY_TARGET 覆盖）";
        } else if (e.message) {
          errMsg = e.message;
        }
      } else if (e instanceof Error && e.message) {
        errMsg = e.message;
      }
      setAiRecogs((p) => ({
        ...p,
        [key]: {
          success: false,
          slot_type: "unknown",
          extra_slots: [],
          category: "",
          summary: "",
          error: errMsg,
        },
      }));
    } finally {
      recognizeInFlightRef.current.delete(key);
      setAiLoading((p) => ({ ...p, [key]: false }));
    }
  }, []);

  useEffect(() => {
    const validKeys = new Set(files.map(fkey));
    setAiRecogs((prev) => {
      let changed = false;
      const next: Record<string, QuickRecognizeResult> = {};
      Object.entries(prev).forEach(([key, value]) => {
        if (validKeys.has(key)) next[key] = value;
        else changed = true;
      });
      return changed ? next : prev;
    });
    setAiLoading((prev) => {
      let changed = false;
      const next: Record<string, boolean> = {};
      Object.entries(prev).forEach(([key, value]) => {
        if (validKeys.has(key)) next[key] = value;
        else changed = true;
      });
      return changed ? next : prev;
    });
    recognizeInFlightRef.current.forEach((key) => {
      if (!validKeys.has(key)) recognizeInFlightRef.current.delete(key);
    });
  }, [files]);

  useEffect(() => {
    const mediaFiles = files.filter(
      (f) => f.type.startsWith("image/") || f.type.startsWith("video/"),
    );
    const inFlight = mediaFiles.filter((f) => aiLoading[fkey(f)]).length;
    const freeSlots = Math.max(0, QUICK_RECOGNIZE_CONCURRENCY - inFlight);
    const need = mediaFiles.filter((f) => {
      const k = fkey(f);
      return !aiRecogs[k] && !aiLoading[k];
    });
    need.slice(0, freeSlots).forEach((file) => {
      void runRecognition(file);
    });
  }, [files, aiRecogs, aiLoading, runRecognition]);

  useEffect(() => {
    if (!prevPendingRecognitionRef.current && pendingRecognition && analyzePulseTimerRef.current) {
      clearTimeout(analyzePulseTimerRef.current);
      analyzePulseTimerRef.current = null;
      setAnalyzingPulse(false);
    }
    if (prevPendingRecognitionRef.current && !pendingRecognition && recognizeFileKeys.size > 0) {
      if (analyzePulseTimerRef.current) clearTimeout(analyzePulseTimerRef.current);
      setAnalyzingPulse(true);
      analyzePulseTimerRef.current = setTimeout(() => {
        setAnalyzingPulse(false);
        analyzePulseTimerRef.current = null;
      }, 700);
    }
    prevPendingRecognitionRef.current = pendingRecognition;
  }, [pendingRecognition, recognizeFileKeys.size]);

  useEffect(() => {
    if (files.length === 0) {
      setAiRecogs({});
      setAiLoading({});
      recognizeInFlightRef.current.clear();
      setUserEdited({ title: false, content: false, category: false });
      setTitle("");
      setContent("");
      setCategory("food");
      setUploadingPulse(false);
      setAnalyzingPulse(false);
      if (uploadPulseTimerRef.current) {
        clearTimeout(uploadPulseTimerRef.current);
        uploadPulseTimerRef.current = null;
      }
      if (analyzePulseTimerRef.current) {
        clearTimeout(analyzePulseTimerRef.current);
        analyzePulseTimerRef.current = null;
      }
    }
  }, [files.length]);

  const processingStatus = useMemo(() => {
    if (files.length === 0) return null;
    if (uploadingPulse) {
      return { label: "上传中", tone: "info" as const, text: "素材已接收，正在准备识别..." };
    }
    if (pendingRecognition) {
      const videoPending = [...videoFileKeys].some((k) => aiLoading[k] || !aiRecogs[k]);
      const imagePending = [...imageFileKeys].some((k) => aiLoading[k] || !aiRecogs[k]);
      if (videoPending && !imagePending && imageFileKeys.size === 0) {
        return { label: "识别中", tone: "info" as const, text: "AI 正在识别视频内容（含画面与字幕），请稍候..." };
      }
      return { label: "识别中", tone: "info" as const, text: "AI 正在自动识别图片与视频..." };
    }
    if (analyzingPulse) {
      return { label: "分析中", tone: "info" as const, text: "正在汇总识别结果并回填表单..." };
    }
    if (allRecognitionDone) {
      return { label: "已就绪", tone: "success" as const, text: "识别完成，可以继续发起诊断。" };
    }
    return null;
  }, [
    files.length,
    uploadingPulse,
    pendingRecognition,
    analyzingPulse,
    allRecognitionDone,
    videoFileKeys,
    imageFileKeys,
    aiLoading,
    aiRecogs,
  ]);

  const lockInputs = !!processingStatus && processingStatus.label !== "已就绪";
  const isFormBlocked = files.length > 0 && !allRecognitionDone;

  const [submitError, setSubmitError] = useState("");
  // Auto-clear error when user fixes the condition
  useEffect(() => { if (submitError) setSubmitError(""); }, [files.length, title]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleSubmit = () => {
    if (files.length === 0) { setSubmitError("请先上传笔记截图"); return; }
    if (!title.trim()) { setSubmitError("请输入笔记标题"); return; }
    if (lockInputs || isFormBlocked) { setSubmitError("AI 识别中，请稍等"); return; }
    setSubmitError("");
    // Check if any recognition result shows high engagement
    const hasHighEngagement = successResults.some(r => r.engagement_signal?.is_high_engagement);
    navigate("/diagnosing", {
      state: {
        title, content, tags: "", category,
        coverFile: files.find((f) => f.type.startsWith("image/")) ?? null,
        coverImages: files.filter((f) => f.type.startsWith("image/")),
        videoFile: files.find((f) => f.type.startsWith("video/")) ?? null,
        hasHighEngagement,
      },
    });
  };

  const recognizedSlots = useMemo(
    () => new Set(
      successRecogEntries
        .map(([, r]) => (typeof r.slot_type === "string" ? r.slot_type.toLowerCase() : ""))
        .filter(Boolean),
    ),
    [successRecogEntries],
  );
  const hasDetailScreenshot = recognizedSlots.has("content");
  const canSubmit = files.length > 0 && title.trim().length > 0 && !lockInputs && !isFormBlocked;
  /* aiSuggestion removed — detail screenshot warning shown inline below CTA */
  const slotLabelMap: Record<string, string> = {
    content: "详情",
    cover: "封面",
    profile: "主页",
    comments: "评论区",
  };

  /** 所有素材的快识请求已结束（含全部失败） */
  const isReady = files.length > 0 && allRecognitionDone;
  /** 至少有一条快识成功，才显示「分析完成」绿条，避免与「全部失败」红条同时出现 */
  const hasRecogSuccess = successResults.length > 0;
  const [, setLeaving] = useState(false);

  // Reset leaving on mount (browser back button fix)
  useEffect(() => { setLeaving(false); }, []);

  return (
    <Box sx={{
      height: { md: "100dvh" },
      minHeight: { xs: "100dvh" },
      display: "flex",
      flexDirection: "column",
      bgcolor: "#fafafa",
      position: "relative",
      overflow: "hidden",
      "&::before": {
        content: '""',
        position: "absolute",
        top: 0, left: 0, right: 0, bottom: 0,
        background: `
          radial-gradient(ellipse 100% 80% at 10% 0%, #f0f0f0 0%, transparent 50%),
          radial-gradient(ellipse 80% 60% at 90% 100%, rgba(37, 244, 238, 0.06) 0%, transparent 45%),
          radial-gradient(ellipse 60% 50% at 50% 0%, rgba(254, 44, 85, 0.04) 0%, transparent 40%),
          linear-gradient(180deg, rgba(250, 250, 250, 0.6) 0%, rgba(255, 255, 255, 0.4) 100%)
        `,
        pointerEvents: "none",
      },
      "&::after": {
        content: '""',
        position: "absolute",
        top: 0, left: 0, right: 0, bottom: 0,
        backgroundImage: `
          radial-gradient(circle at 15% 25%, rgba(254, 44, 85, 0.12) 0%, transparent 2%),
          radial-gradient(circle at 85% 15%, #f0f0f0 0%, transparent 1.5%),
          radial-gradient(circle at 75% 75%, rgba(37, 244, 238, 0.1) 0%, transparent 2%),
          radial-gradient(circle at 25% 85%, rgba(37, 244, 238, 0.06) 0%, transparent 1%),
          radial-gradient(circle at 50% 50%, rgba(255, 255, 255, 0.02) 0%, transparent 1%)
        `,
        backgroundSize: "100% 100%",
        pointerEvents: "none",
        animation: "ambientMove 25s ease-in-out infinite",
        "@keyframes ambientMove": {
          "0%, 100%": { transform: "scale(1) translateY(0)" },
          "50%": { transform: "scale(1.05) translateY(-10px)" },
        },
      },
    }}>

      {/* ═══ Header ═══ */}
      <Box component="header" sx={{
        flexShrink: 0,
        display: "flex", alignItems: "center", justifyContent: "space-between",
        px: { xs: 1.5, md: 3 }, height: 56,
        bgcolor: "rgba(255, 255, 255, 0.9)",
        backdropFilter: "blur(20px)",
        borderBottom: "1px solid rgba(254, 44, 85, 0.1)",
        position: "relative",
        zIndex: 10,
      }}>
        <Box sx={{ display: "flex", alignItems: "center", gap: { xs: 0.75, md: 1.5 } }}>
          <Box sx={{ display: "flex", alignItems: "center", gap: 0.75, flexShrink: 0 }}>
            <Box component="img" src="/app/favicon.svg" sx={{
              width: 32, height: 32, borderRadius: "8px",
              boxShadow: "0 0 20px rgba(254, 44, 85, 0.25)",
            }}/>
            <Typography sx={{ fontSize: 16, fontWeight: 700, color: "#262626", letterSpacing: "-0.02em" }}>
              抖医
            </Typography>
          </Box>
          <Typography sx={{
            display: { xs: "none", md: "block" },
            fontSize: 12, color: "rgba(160, 160, 160, 0.7)", fontWeight: 400,
          }}>
            AI 驱动的抖音内容诊断平台
          </Typography>
        </Box>
        <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
          <Button
            onClick={() => { setLeaving(true); setTimeout(() => { window.location.href = "/"; }, 350); }}
            size="small"
            sx={{ color: "rgba(160, 160, 160, 0.75)", fontSize: 12, fontWeight: 500, minWidth: "auto", px: 1.5, borderRadius: "8px",
              "&:hover": { color: "#fe2c55", bgcolor: "rgba(254, 44, 85, 0.06)" } }}
          >
            白皮书
          </Button>
          <Button startIcon={<HistoryOutlined sx={{ fontSize: 15 }} />}
            onClick={() => navigate("/history")} size="small"
            sx={{ color: "rgba(160, 160, 160, 0.75)", fontSize: 12, fontWeight: 500, minWidth: "auto", px: 1.5, borderRadius: "8px",
              "&:hover": { color: "#25f4ee", bgcolor: "rgba(37, 244, 238, 0.06)" } }}
          >
            <Box component="span" sx={{ display: { xs: "none", sm: "inline" } }}>历史</Box>
          </Button>
          <Button startIcon={<EmailOutlinedIcon sx={{ fontSize: 15 }} />}
            component="a" href="mailto:jmr@jiangmuran.com" size="small"
            sx={{ color: "rgba(160, 160, 160, 0.75)", fontSize: 12, fontWeight: 500, minWidth: "auto", px: 1.5, borderRadius: "8px",
              textDecoration: "none",
              "&:hover": { color: "#fe2c55", bgcolor: "rgba(254, 44, 85, 0.06)" } }}
          >
            <Box component="span" sx={{ display: { xs: "none", sm: "inline" } }}>联系</Box>
          </Button>
        </Box>
      </Box>

      {/* ═══ Work area — 填满剩余空间，桌面不滚动 ═══ */}
      <Box sx={{
        flex: 1,
        display: "flex", justifyContent: "center", alignItems: "stretch",
        px: { xs: 0, md: 3 },
        py: { xs: 0, md: 2 },
        pb: { xs: "100px", md: 2 },
        overflow: { xs: "auto", md: "hidden" },
        minHeight: 0,
      }}>
        <Box sx={{
          width: "100%", maxWidth: 1000,
          display: "grid",
          gridTemplateColumns: { xs: "1fr", md: "1.2fr 1fr" },
          gap: { xs: 0, md: 2 },
          alignItems: "stretch",
          minHeight: 0,
        }}>

          {/* ═══ Left: Upload ═══ */}
          <Box sx={{
            bgcolor: "rgba(255, 255, 255, 0.85)",
            backdropFilter: "blur(20px)",
            border: { md: "1px solid #f0f0f0" },
            borderBottom: { xs: "1px solid #f0f0f0", md: "1px solid #f0f0f0" },
            borderRadius: { xs: 0, md: "16px" },
            p: { xs: 2, md: 2.5 },
            display: "flex", flexDirection: "column",
            gap: 1.5,
            minHeight: 0,
            overflow: "hidden",
            boxShadow: "0 2px 12px rgba(0, 0, 0, 0.04)",
          }}>
            <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexShrink: 0 }}>
              <Box>
                <Typography sx={{ fontSize: 14, fontWeight: 600, color: "#262626" }}>
                  上传内容素材
                </Typography>
                <Typography sx={{ fontSize: 12, color: "#999", mt: 0.25 }}>
                  拖入抖音视频/图文截图，AI 自动识别
                </Typography>
              </Box>
              {files.length > 0 && (
                <Chip size="small" label={`${files.length}/9`} sx={{
                  height: 22, fontSize: 10, fontWeight: 600,
                  bgcolor: "rgba(37, 244, 238, 0.08)",
                  color: "#25f4ee",
                  border: "1px solid rgba(37, 244, 238, 0.15)",
                }} />
              )}
            </Box>

            {apiReachable === false && (
              <Alert severity="warning" sx={{ fontSize: 12, py: 0.5, borderRadius: "10px" }}>
                无法连接本机诊断 API，请启动后端服务
              </Alert>
            )}

            <Box sx={{ flex: 1, minHeight: 0, overflow: "hidden" }}>
              <UploadZone files={files} onFilesChange={handleFilesChange} maxFiles={9} compact={isDesktop} />
            </Box>

            {/* Slot chips */}
            <AnimatePresence>
              {files.length > 0 && (
                <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }}
                  exit={{ opacity: 0, height: 0 }} transition={{ duration: 0.2 }}
                  style={{ flexShrink: 0 }}>
                  <Box sx={{ display: "flex", gap: 0.5, flexWrap: "wrap", alignItems: "center" }}>
                    {Object.entries(slotLabelMap).map(([slot, label]) => (
                      <Chip key={slot} size="small" label={label}
                        color={recognizedSlots.has(slot) ? "primary" : "default"}
                        variant={recognizedSlots.has(slot) ? "filled" : "outlined"}
                        sx={{ fontSize: 10, height: 20 }} />
                    ))}
                  </Box>
                </motion.div>
              )}
            </AnimatePresence>

            {/* AI analysis progress bar — smooth */}
            <AnimatePresence>
              {(anyLoading || pendingRecognition) && files.length > 0 && (
                <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }}
                  exit={{ opacity: 0, height: 0 }} transition={{ duration: 0.25 }}
                  style={{ flexShrink: 0 }}>
                  <Box sx={{ px: 0.5 }}>
                    <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", mb: 0.5 }}>
                      <AnalysisStatusText />
                      <Typography sx={{ fontSize: 10, color: "#666", fontVariantNumeric: "tabular-nums" }}>
                        {Object.keys(aiRecogs).length}/{Math.max(recognizeFileKeys.size, 1)}
                      </Typography>
                    </Box>
                    <SmoothProgressBar
                      done={Object.keys(aiRecogs).length}
                      total={Math.max(recognizeFileKeys.size, 1)}
                    />
                  </Box>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Ready state */}
            {isReady && files.length > 0 && hasRecogSuccess && (
              <Box sx={{ display: "flex", alignItems: "center", gap: 0.5, px: 0.5 }}>
                <CheckCircleIcon sx={{ fontSize: 13, color: "#52c41a" }} />
                <Typography sx={{ fontSize: 11, color: "#52c41a", fontWeight: 500 }}>分析完成，可以开始诊断</Typography>
              </Box>
            )}
            {allFailed && (
              <Typography sx={{ fontSize: 11, color: "#ff4d4f", px: 0.5, lineHeight: 1.5 }}>
                {firstRecognizeError
                  ? `识别失败：${firstRecognizeError}`
                  : "识别失败，请检查网络或手动输入"}
              </Typography>
            )}

          </Box>

          {/* ═══ Right: Form ═══ */}
          <Box sx={{
            bgcolor: "rgba(255, 255, 255, 0.85)",
            backdropFilter: "blur(20px)",
            border: { md: "1px solid rgba(37, 244, 238, 0.06)" },
            borderRadius: { xs: 0, md: "16px" },
            p: { xs: 2, md: 2.5 },
            display: "flex", flexDirection: "column",
            gap: 1.75,
            minHeight: 0,
            overflow: { xs: "visible", md: "auto" },
            boxShadow: "0 2px 12px rgba(0, 0, 0, 0.04)",
          }}>
            <Typography sx={{ fontSize: 14, fontWeight: 600, color: "#262626", flexShrink: 0 }}>
              内容信息
            </Typography>

            {videoWithoutImage && allRecognitionDone && !allFailed && (
              <Alert severity="info" sx={{ fontSize: 12, py: 0.75, borderRadius: "10px", flexShrink: 0 }}>
                仅上传视频时，笔记标题一般在发布页或信息流封面，很少出现在画面里。请再传一张含标题或封面大字的截图。
              </Alert>
            )}

            {isFormBlocked && (
              <Box sx={{ display: "flex", alignItems: "center", gap: 0.75, px: 1, py: 0.5, borderRadius: "8px", bgcolor: "#f5f5f5", border: "1px solid #e8e8e8", flexShrink: 0 }}>
                <CircularProgress size={12} thickness={5} sx={{ color: "#fe2c55" }} />
                <Typography sx={{ fontSize: 12, color: "#666", fontWeight: 500 }}>AI 识别中，完成后自动填入</Typography>
              </Box>
            )}

            <Box sx={{
              flex: 1, minHeight: 0,
              opacity: isFormBlocked ? 0.4 : 1,
              pointerEvents: isFormBlocked ? "none" : "auto",
              transition: "opacity 0.3s",
              display: "flex", flexDirection: "column", gap: 1.75,
            }}>
              <Box>
                <Box sx={{ display: "flex", alignItems: "center", gap: 0.5, mb: 0.5 }}>
                  <Typography sx={{ fontSize: 13, fontWeight: 500, color: "#a3a3a3" }}>标题</Typography>
                  {autoFilled.title && <Typography sx={{ fontSize: 10, color: "#52c41a", fontWeight: 500 }}>AI 已填</Typography>}
                </Box>
                <TextField required fullWidth size="small" disabled={lockInputs} value={title}
                  onChange={(e) => { setTitle(e.target.value); setUserEdited((p) => ({ ...p, title: true })); }}
                  placeholder="笔记标题" slotProps={{ htmlInput: { maxLength: 100 } }} />
                {showWarnings && warnings.title && !title.trim() && !userEdited.title && (
                  <Typography sx={{ fontSize: 11, color: "#faad14", mt: 0.5 }}>请手动输入标题</Typography>
                )}
              </Box>

              <Box>
                <Box sx={{ display: "flex", alignItems: "center", gap: 0.5, mb: 0.5 }}>
                  <Typography sx={{ fontSize: 13, fontWeight: 500, color: "#a3a3a3" }}>正文</Typography>
                  {autoFilled.content && <Typography sx={{ fontSize: 10, color: "#52c41a", fontWeight: 500 }}>AI 已填</Typography>}
                </Box>
                <TextField fullWidth multiline rows={isDesktop ? 3 : 3} size="small" disabled={lockInputs} value={content}
                  onChange={(e) => { setContent(e.target.value); setUserEdited((p) => ({ ...p, content: true })); }}
                  placeholder="笔记正文（可选）" />
              </Box>

              <Box>
                <Box sx={{ display: "flex", alignItems: "center", gap: 0.5, mb: 0.75 }}>
                  <Typography sx={{ fontSize: 13, fontWeight: 500, color: "#a3a3a3" }}>垂类</Typography>
                  {autoFilled.category && <Typography sx={{ fontSize: 10, color: "#52c41a", fontWeight: 500 }}>AI 已识别</Typography>}
                </Box>
                <CategoryPicker value={category} onChange={(v) => { setCategory(v); setUserEdited((p) => ({ ...p, category: true })); }} />
              </Box>
            </Box>

            {/* Desktop CTA */}
            <Box sx={{ display: { xs: "none", md: "flex" }, flexDirection: "column", gap: 1, flexShrink: 0, pt: 0.5 }}>
              <Button variant="contained" fullWidth disabled={!canSubmit} onClick={handleSubmit}
                sx={{
                  py: 1.1, fontSize: 14, fontWeight: 700, borderRadius: "10px", minHeight: 44,
                  background: canSubmit ? "linear-gradient(135deg, #25f4ee, #fe2c55)" : "#e0e0e0",
                  color: canSubmit ? "#fff" : "#aaa",
                  boxShadow: canSubmit ? "0 4px 20px rgba(254, 44, 85, 0.25)" : "none",
                  "&:hover": {
                    background: canSubmit ? "linear-gradient(135deg, #25f4ee, #fe2c55)" : "#e0e0e0",
                    boxShadow: canSubmit ? "0 8px 28px rgba(254, 44, 85, 0.35)" : "none",
                    transform: canSubmit ? "translateY(-1px)" : "none",
                  },
                  "&:active": { transform: "translateY(0)" },
                }}
              >
                开始诊断
              </Button>
              {files.length > 0 && allRecognitionDone && !hasDetailScreenshot && (
                <Typography sx={{ fontSize: 10, color: "#666", textAlign: "center" }}>建议补充详情页截图</Typography>
              )}
            </Box>
          </Box>
        </Box>
      </Box>

      {/* ═══ Mobile fixed CTA ═══ */}
      <Box sx={{
        display: { xs: "block", md: "none" },
        position: "fixed", bottom: 0, left: 0, right: 0, zIndex: 30,
        px: 1.5, pt: 1,
        pb: "max(8px, env(safe-area-inset-bottom))",
        bgcolor: "rgba(12, 12, 14, 0.95)",
        backdropFilter: "blur(24px)",
        borderTop: "1px solid #f0f0f0",
      }}>
        <Button variant="contained" fullWidth onClick={handleSubmit}
          sx={{
            py: 1.1, fontSize: 15, fontWeight: 700, borderRadius: "10px", minHeight: 48,
            background: canSubmit ? "linear-gradient(135deg, #25f4ee, #fe2c55)" : "#e0e0e0",
            color: canSubmit ? "#fff" : "#aaa",
            boxShadow: canSubmit ? "0 4px 20px rgba(254, 44, 85, 0.25)" : "none",
            "&:hover": { background: canSubmit ? "linear-gradient(135deg, #25f4ee, #fe2c55)" : "#e0e0e0" },
          }}
        >
          开始诊断
        </Button>
        {submitError && (
          <Typography sx={{ fontSize: 11, color: "#ff4d4f", textAlign: "center", mt: 0.5 }}>
            {submitError}
          </Typography>
        )}
      </Box>

      {/* ═══ Footer ═══ */}
      <Box sx={{
        display: { xs: "none", md: "flex" },
        justifyContent: "center", alignItems: "center", gap: 1.5,
        py: 0.8, flexShrink: 0,
        borderTop: "1px solid rgba(254, 44, 85, 0.05)",
        bgcolor: "rgba(12, 12, 14, 0.8)",
        backdropFilter: "blur(12px)",
        position: "relative", zIndex: 1,
      }}>
        <Typography component="a" href="/terms"
          sx={{ fontSize: 11, color: "rgba(100, 100, 100, 0.5)", textDecoration: "none", "&:hover": { color: "#fe2c55" } }}>
          服务条款
        </Typography>
        <Typography sx={{ fontSize: 11, color: "rgba(50, 50, 50, 0.4)" }}>|</Typography>
        <Typography component="a" href="/privacy"
          sx={{ fontSize: 11, color: "rgba(100, 100, 100, 0.5)", textDecoration: "none", "&:hover": { color: "#fe2c55" } }}>
          隐私政策
        </Typography>
        <Typography sx={{ fontSize: 11, color: "rgba(50, 50, 50, 0.4)" }}>|</Typography>
        <Typography component="a" href="https://github.com/jiangmuran/tiktokrx" target="_blank"
          sx={{ fontSize: 11, color: "rgba(100, 100, 100, 0.5)", textDecoration: "none", "&:hover": { color: "#25f4ee" } }}>
          GitHub
        </Typography>
        <Typography sx={{ fontSize: 11, color: "rgba(50, 50, 50, 0.4)" }}>|</Typography>
        <Typography component="a" href="mailto:jmr@jiangmuran.com"
          sx={{ fontSize: 11, color: "rgba(100, 100, 100, 0.5)", textDecoration: "none", "&:hover": { color: "#fe2c55" } }}>
          合作联系
        </Typography>
      </Box>

    </Box>
  );
}
