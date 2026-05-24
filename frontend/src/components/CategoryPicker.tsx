import { Box, Typography } from "@mui/material";

interface Props {
  value: string;
  onChange: (v: string) => void;
}

/* 只保留白皮书/论文中有真实回归数据的 5 个品类 */
const CATEGORIES = [
  { key: "food", label: "美食" },
  { key: "fashion", label: "穿搭" },
  { key: "tech", label: "科技" },
  { key: "travel", label: "旅行" },
  { key: "lifestyle", label: "生活" },
];

export default function CategoryPicker({ value, onChange }: Props) {
  return (
    <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1 }}>
      {CATEGORIES.map((cat) => {
        const selected = value === cat.key;
        return (
          <Box
            key={cat.key}
            onClick={() => onChange(cat.key)}
            sx={{
              px: 1.75,
              py: 0.7,
              borderRadius: "999px",
              cursor: "pointer",
              fontSize: "0.82rem",
              fontWeight: 600,
              transition: "all 0.25s cubic-bezier(0.2,0,0.2,1)",
              userSelect: "none",
              border: "1.5px solid transparent",
              ...(selected
                ? {
                    background: "linear-gradient(135deg, #25f4ee, #fe2c55)",
                    color: "#ffffff",
                    boxShadow: "0 4px 16px rgba(254, 44, 85, 0.25)",
                    borderColor: "transparent",
                    transform: "scale(1.02)",
                  }
                : {
                    bgcolor: "#f5f5f5",
                    color: "#666",
                    borderColor: "#e8e8e8",
                    "&:hover": {
                      bgcolor: "rgba(254, 44, 85, 0.06)",
                      color: "#fe2c55",
                      borderColor: "rgba(254, 44, 85, 0.2)",
                      transform: "translateY(-1px)",
                      boxShadow: "0 2px 8px rgba(254, 44, 85, 0.1)",
                    },
                    "&:active": {
                      transform: "scale(0.97)",
                    },
                  }),
            }}
          >
            <Typography sx={{ fontSize: "inherit", fontWeight: "inherit", lineHeight: 1.5 }}>
              {cat.label}
            </Typography>
          </Box>
        );
      })}
    </Box>
  );
}
