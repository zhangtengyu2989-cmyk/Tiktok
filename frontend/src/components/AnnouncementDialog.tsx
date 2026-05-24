import { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  Box,
  Typography,
  Button,
  IconButton,
  useMediaQuery,
  useTheme,
} from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";
import FavoriteIcon from "@mui/icons-material/Favorite";
import GitHubIcon from "@mui/icons-material/GitHub";
import LanguageIcon from "@mui/icons-material/Language";
import EmailOutlinedIcon from "@mui/icons-material/EmailOutlined";
import HandshakeOutlinedIcon from "@mui/icons-material/HandshakeOutlined";
import OpenInNewIcon from "@mui/icons-material/OpenInNew";
import WhatshotIcon from "@mui/icons-material/Whatshot";
import TrendingUpIcon from "@mui/icons-material/TrendingUp";
import CodeIcon from "@mui/icons-material/Code";

const STORAGE_KEY = "tiktokrx_announcement_seen_v1";

const WaveSvg = () => (
  <svg
    viewBox="0 0 600 80"
    preserveAspectRatio="none"
    style={{ position: "absolute", bottom: -1, left: 0, width: "100%", height: 48 }}
  >
    <path d="M0 40 C150 80 350 0 600 40 L600 80 L0 80Z" fill="#fafafa" />
  </svg>
);

function LinkCard({
  icon,
  label,
  sublabel,
  href,
  iconBg,
}: {
  icon: React.ReactNode;
  label: string;
  sublabel: string;
  href: string;
  iconBg: string;
}) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      style={{ textDecoration: "none", flex: 1, minWidth: 0 }}
    >
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          gap: 1.5,
          px: 2,
          py: 1.5,
          borderRadius: "14px",
          border: "1px solid rgba(254, 44, 85, 0.12)",
          background: "rgba(254, 44, 85, 0.04)",
          transition: "all 0.22s ease",
          cursor: "pointer",
          "&:hover": {
            borderColor: "rgba(254, 44, 85, 0.35)",
            background: "rgba(254, 44, 85, 0.08)",
            transform: "translateY(-2px)",
            boxShadow: "0 4px 20px rgba(254, 44, 85, 0.12)",
          },
        }}
      >
        <Box
          sx={{
            width: 38,
            height: 38,
            borderRadius: "10px",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            background: iconBg,
            flexShrink: 0,
          }}
        >
          {icon}
        </Box>
        <Box sx={{ minWidth: 0, flex: 1 }}>
          <Typography
            sx={{ fontWeight: 700, fontSize: "0.82rem", color: "#262626", lineHeight: 1.3 }}
          >
            {label}
          </Typography>
          <Typography
            sx={{
              fontSize: "0.7rem",
              color: "rgba(0,0,0,0.5)",
              fontWeight: 500,
              overflow: "hidden",
              textOverflow: "ellipsis",
              whiteSpace: "nowrap",
            }}
          >
            {sublabel}
          </Typography>
        </Box>
        <OpenInNewIcon sx={{ fontSize: 14, color: "rgba(0,0,0,0.3)", flexShrink: 0 }} />
      </Box>
    </a>
  );
}

const STATS = [
  {
    icon: <WhatshotIcon sx={{ fontSize: 20, color: "#fe2c55" }} />,
    val: "100万+",
    label: "全网曝光",
    bg: "rgba(254, 44, 85, 0.1)",
  },
  {
    icon: <TrendingUpIcon sx={{ fontSize: 20, color: "#25f4ee" }} />,
    val: "10万+",
    label: "日均流量",
    bg: "rgba(37, 244, 238, 0.1)",
  },
  {
    icon: <CodeIcon sx={{ fontSize: 20, color: "#fe2c55" }} />,
    val: "全开源",
    label: "MIT License",
    bg: "rgba(254, 44, 85, 0.1)",
  },
];

export default function AnnouncementDialog() {
  const [open, setOpen] = useState(false);
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("sm"));

  useEffect(() => {
    try {
      if (!localStorage.getItem(STORAGE_KEY)) {
        const timer = setTimeout(() => setOpen(true), 800);
        return () => clearTimeout(timer);
      }
    } catch {
      /* localStorage unavailable */
    }
  }, []);

  const handleClose = () => {
    setOpen(false);
    try {
      localStorage.setItem(STORAGE_KEY, Date.now().toString());
    } catch {
      /* ignore */
    }
  };

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth="sm"
      fullWidth
      fullScreen={isMobile}
      slotProps={{
        paper: {
          sx: {
            borderRadius: isMobile ? 0 : "24px",
            overflow: "hidden",
            maxHeight: isMobile ? "100%" : "92vh",
            boxShadow: "0 24px 80px rgba(0,0,0,0.6)",
            background: "#ffffff",
            border: "1px solid #f0f0f0",
          },
        },
      }}
    >
      {/* ───── Hero ───── */}
      <Box
        sx={{
          background: "linear-gradient(145deg, #fafafa 0%, #fff 50%, #f5f5f5 100%)",
          px: { xs: 3, sm: 4 },
          pt: { xs: 4, sm: 5 },
          pb: { xs: 5, sm: 6 },
          position: "relative",
          textAlign: "center",
          overflow: "hidden",
          borderBottom: "1px solid #f0f0f0",
        }}
      >
        {/* Decorative gold orbs */}
        <Box
          sx={{
            position: "absolute", width: 260, height: 260, borderRadius: "50%",
            background: "radial-gradient(circle, rgba(254,44,85,0.08) 0%, transparent 70%)",
            top: -100, right: -60,
          }}
        />
        <Box
          sx={{
            position: "absolute", width: 160, height: 160, borderRadius: "50%",
            background: "radial-gradient(circle, rgba(254,44,85,0.06) 0%, transparent 70%)",
            bottom: 10, left: -50,
          }}
        />
        <Box
          sx={{
            position: "absolute", width: 80, height: 80, borderRadius: "50%",
            background: "radial-gradient(circle, rgba(37,244,238,0.05) 0%, transparent 70%)",
            top: "30%", left: "20%",
          }}
        />
        {/* Gold accent line */}
        <Box
          sx={{
            position: "absolute",
            top: 0, left: "50%", transform: "translateX(-50%)",
            width: "60%", height: 1,
            background: "linear-gradient(90deg, transparent, rgba(254,44,85,0.4), transparent)",
          }}
        />
        <WaveSvg />

        <IconButton
          onClick={handleClose}
          size="small"
          sx={{
            position: "absolute", top: 12, right: 12,
            color: "rgba(0,0,0,0.5)",
            backdropFilter: "blur(8px)",
            background: "rgba(0,0,0,0.03)",
            border: "1px solid rgba(0,0,0,0.06)",
            "&:hover": { color: "#fe2c55", background: "rgba(254,44,85,0.1)" },
          }}
        >
          <CloseIcon fontSize="small" />
        </IconButton>

        <Box sx={{ position: "relative", zIndex: 1 }}>
          <Box
            sx={{
              width: 56, height: 56, borderRadius: "16px",
              background: "linear-gradient(135deg, rgba(254,44,85,0.2), rgba(254,44,85,0.08))",
              backdropFilter: "blur(12px)",
              border: "1px solid rgba(254,44,85,0.3)",
              display: "flex", alignItems: "center", justifyContent: "center",
              mx: "auto", mb: 2,
            }}
          >
            <FavoriteIcon sx={{ color: "#fe2c55", fontSize: 28 }} />
          </Box>
          <Typography
            sx={{
              color: "#262626", fontWeight: 800,
              fontSize: { xs: "1.35rem", sm: "1.5rem" },
              letterSpacing: "-0.5px", mb: 1,
            }}
          >
            抖医 是公益项目
          </Typography>
          <Typography
            sx={{
              color: "rgba(0,0,0,0.6)",
              fontSize: { xs: "0.85rem", sm: "0.9rem" },
              lineHeight: 1.7, maxWidth: 380, mx: "auto",
            }}
          >
            完全免费 · 完全开源 · 由团队自费运营
          </Typography>
        </Box>
      </Box>

      {/* ───── Content ───── */}
      <DialogContent
        sx={{
          px: { xs: 2.5, sm: 3.5 },
          py: { xs: 2.5, sm: 3 },
          background: "#fafafa",
          "&::-webkit-scrollbar": { width: 4 },
          "&::-webkit-scrollbar-thumb": { background: "rgba(254,44,85,0.2)", borderRadius: 2 },
        }}
      >
        {/* Stats row */}
        <Box sx={{ display: "flex", gap: { xs: 1, sm: 1.5 }, mb: 2.5 }}>
          {STATS.map((s) => (
            <Box
              key={s.label}
              sx={{
                flex: 1, textAlign: "center",
                py: { xs: 1.2, sm: 1.5 }, px: 0.5,
                borderRadius: "14px",
                background: "rgba(0,0,0,0.02)",
                border: "1px solid rgba(254,44,85,0.1)",
                boxShadow: "0 2px 12px rgba(0,0,0,0.3)",
              }}
            >
              <Box sx={{ display: "flex", justifyContent: "center", mb: 0.5 }}>
                {s.icon}
              </Box>
              <Typography
                sx={{
                  fontWeight: 800,
                  fontSize: { xs: "0.95rem", sm: "1.1rem" },
                  color: "#fe2c55", lineHeight: 1.3,
                }}
              >
                {s.val}
              </Typography>
              <Typography
                sx={{
                  fontSize: "0.65rem", color: "rgba(0,0,0,0.4)", mt: 0.2,
                  fontWeight: 600, letterSpacing: "0.3px",
                }}
              >
                {s.label}
              </Typography>
            </Box>
          ))}
        </Box>

        {/* Links: GitHub + Homepage */}
        <Box
          sx={{
            display: "flex", gap: 1.5, mb: 2.5,
            flexDirection: { xs: "column", sm: "row" },
          }}
        >
          <LinkCard
            icon={<GitHubIcon sx={{ fontSize: 20, color: "#fe2c55" }} />}
            label="开源仓库"
            sublabel="github.com/jiangmuran/tiktokrx"
            href="https://github.com/jiangmuran/tiktokrx"
            iconBg="linear-gradient(135deg, rgba(254,44,85,0.15), rgba(254,44,85,0.05))"
          />
          <LinkCard
            icon={<LanguageIcon sx={{ fontSize: 20, color: "#25f4ee" }} />}
            label="开发者主页"
            sublabel="jiangmuran.com"
            href="https://jiangmuran.com"
            iconBg="linear-gradient(135deg, rgba(37,244,238,0.15), rgba(37,244,238,0.05))"
          />
        </Box>

        {/* Sustainability note */}
        <Box
          sx={{
            background: "linear-gradient(135deg, rgba(254,44,85,0.08), rgba(254,44,85,0.03))",
            border: "1px solid rgba(254,44,85,0.15)",
            borderRadius: "14px", px: 2.5, py: 2, mb: 2.5,
          }}
        >
          <Typography
            sx={{ fontSize: "0.85rem", color: "rgba(0,0,0,0.7)", lineHeight: 1.75, fontWeight: 500 }}
          >
            由于服务器与 AI Token 成本持续增长，项目可能会在赞助资源耗尽后暂停服务。如果您觉得 抖医 有价值，欢迎通过赞助或合作帮助我们走得更远。
          </Typography>
        </Box>

        {/* Collaboration */}
        <Box
          sx={{
            display: "flex", alignItems: "flex-start", gap: 1.5,
            px: 2.5, py: 2, borderRadius: "14px",
            border: "1px solid rgba(254,44,85,0.08)",
            background: "rgba(0,0,0,0.02)", mb: 2.5,
          }}
        >
          <HandshakeOutlinedIcon
            sx={{ color: "#fe2c55", mt: 0.2, fontSize: 22, flexShrink: 0 }}
          />
          <Box>
            <Typography sx={{ fontWeight: 700, fontSize: "0.92rem", mb: 0.5, color: "#262626" }}>
              广告位招租 · 有偿合作
            </Typography>
            <Typography sx={{ fontSize: "0.82rem", color: "rgba(0,0,0,0.5)", lineHeight: 1.7 }}>
              我们开放广告位与商业合作。如有赞助、推广、技术合作意向，欢迎来信并附上联系方式、合作事由与意向报价。
            </Typography>
          </Box>
        </Box>

        {/* Contact email */}
        <Box
          sx={{
            display: "flex", alignItems: "center", justifyContent: "center",
            gap: 1, py: 1.2, borderRadius: "12px",
            background: "rgba(254,44,85,0.04)",
            border: "1px solid rgba(254,44,85,0.1)", mb: 3,
          }}
        >
          <EmailOutlinedIcon sx={{ fontSize: 16, color: "#fe2c55" }} />
          <Typography sx={{ fontSize: "0.82rem", color: "rgba(0,0,0,0.6)" }}>
            合作联系{" "}
            <a
              href="mailto:516984044@qq.com"
              style={{ color: "#fe2c55", fontWeight: 700, textDecoration: "none" }}
            >
              516984044@qq.com
            </a>
          </Typography>
        </Box>

        {/* CTA */}
        <Button
          variant="contained"
          color="primary"
          fullWidth
          size="large"
          onClick={handleClose}
          sx={{
            py: 1.6, fontSize: "0.95rem", fontWeight: 700,
            borderRadius: "14px", textTransform: "none",
          }}
        >
          好的，开始使用 抖医
        </Button>

        <Typography
          sx={{
            textAlign: "center", fontSize: "0.68rem",
            color: "rgba(0,0,0,0.3)", mt: 1.5, letterSpacing: "0.3px",
          }}
        >
          此弹窗仅在首次访问时展示
        </Typography>
      </DialogContent>
    </Dialog>
  );
}
