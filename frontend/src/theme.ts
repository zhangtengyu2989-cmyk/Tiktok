import { createTheme, type ThemeOptions } from "@mui/material/styles";

/**
 * 抖医 TiktokRx 主题：浅色模式 + 抖音粉/青点缀
 * 与着陆页风格统一：年轻、潮流、清爽
 */

const PINK = "#fe2c55";
const CYAN = "#25f4ee";

const themeOptions: ThemeOptions = {
  palette: {
    mode: "light",
    primary: {
      main: PINK,
      light: "#ff6b81",
      dark: "#d4264a",
      contrastText: "#ffffff",
    },
    secondary: {
      main: CYAN,
      light: "#5ff5ee",
      dark: "#1cc9c3",
      contrastText: "#000000",
    },
    error: {
      main: "#ff6b6b",
      light: "#ff9999",
      dark: "#e64545",
    },
    warning: {
      main: "#f59e0b",
      light: "#fbbf24",
      dark: "#d97706",
    },
    info: {
      main: CYAN,
      light: "#5ff5ee",
      dark: "#1cc9c3",
    },
    success: {
      main: "#00c853",
      light: "#69f0ae",
      dark: "#00a844",
    },
    background: {
      default: "#fafafa",
      paper: "#ffffff",
    },
    text: {
      primary: "#262626",
      secondary: "#666666",
    },
    divider: "#f0f0f0",
  },

  typography: {
    fontFamily: [
      "Inter",
      "Noto Sans SC",
      "PingFang SC",
      "-apple-system",
      "BlinkMacSystemFont",
      "sans-serif",
    ].join(","),
    fontWeightRegular: 400,
    fontWeightMedium: 500,
    fontWeightBold: 700,
    h1: { fontWeight: 800, fontSize: "2rem", lineHeight: 1.3, letterSpacing: "-0.02em" },
    h2: { fontWeight: 700, fontSize: "1.75rem", lineHeight: 1.35, letterSpacing: "-0.02em" },
    h3: { fontWeight: 600, fontSize: "1.5rem", lineHeight: 1.4 },
    h4: { fontWeight: 600, fontSize: "1.25rem", lineHeight: 1.4 },
    h5: { fontWeight: 600, fontSize: "1.1rem", lineHeight: 1.5 },
    h6: { fontWeight: 600, fontSize: "1rem", lineHeight: 1.5 },
    subtitle1: { fontWeight: 500, fontSize: "1rem", lineHeight: 1.6 },
    subtitle2: { fontWeight: 500, fontSize: "0.875rem", lineHeight: 1.6 },
    body1: { fontWeight: 400, fontSize: "1rem", lineHeight: 1.7 },
    body2: { fontWeight: 400, fontSize: "0.875rem", lineHeight: 1.7 },
    button: { fontWeight: 600, fontSize: "0.875rem", letterSpacing: "0.02em" },
    caption: { fontWeight: 400, fontSize: "0.75rem", lineHeight: 1.5, color: "#999999" },
  },

  shape: {
    borderRadius: 12,
  },

  shadows: [
    "none",
    "0 1px 3px rgba(0, 0, 0, 0.04)",
    "0 2px 8px rgba(0, 0, 0, 0.06)",
    "0 4px 16px rgba(0, 0, 0, 0.08)",
    "0 8px 24px rgba(0, 0, 0, 0.08)",
    "0 12px 32px rgba(0, 0, 0, 0.10)",
    "0 16px 40px rgba(0, 0, 0, 0.12)",
    "0 4px 16px rgba(0,0,0,0.06)",
    "0 4px 16px rgba(0,0,0,0.06)",
    "0 4px 16px rgba(0,0,0,0.06)",
    "0 4px 16px rgba(0,0,0,0.06)",
    "0 4px 16px rgba(0,0,0,0.06)",
    "0 4px 16px rgba(0,0,0,0.06)",
    "0 4px 16px rgba(0,0,0,0.06)",
    "0 4px 16px rgba(0,0,0,0.06)",
    "0 4px 16px rgba(0,0,0,0.06)",
    "0 4px 16px rgba(0,0,0,0.06)",
    "0 4px 16px rgba(0,0,0,0.06)",
    "0 4px 16px rgba(0,0,0,0.06)",
    "0 4px 16px rgba(0,0,0,0.06)",
    "0 4px 16px rgba(0,0,0,0.06)",
    "0 4px 16px rgba(0,0,0,0.06)",
    "0 4px 16px rgba(0,0,0,0.06)",
    "0 4px 16px rgba(0,0,0,0.06)",
    "0 4px 16px rgba(0,0,0,0.06)",
  ],

  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          backgroundColor: "#fafafa",
          backgroundImage: "none",
        },
      },
    },

    MuiButton: {
      defaultProps: {
        disableElevation: true,
      },
      styleOverrides: {
        root: {
          textTransform: "none" as const,
          fontWeight: 600,
          borderRadius: 8,
          padding: "8px 20px",
          transition: "all 0.2s ease",
        },
        sizeLarge: {
          padding: "12px 28px",
          fontSize: "1rem",
          borderRadius: 10,
        },
        sizeSmall: {
          padding: "4px 14px",
          fontSize: "0.8rem",
          borderRadius: 6,
        },
      },
      variants: [
        {
          props: { variant: "contained" as const, color: "primary" as const },
          style: {
            background: `linear-gradient(135deg, ${CYAN}, ${PINK})`,
            color: "#ffffff",
            boxShadow: "0 4px 20px rgba(254, 44, 85, 0.25)",
            "&:hover": {
              background: `linear-gradient(135deg, ${CYAN}, ${PINK})`,
              boxShadow: "0 8px 28px rgba(254, 44, 85, 0.35)",
              transform: "translateY(-1px)",
            },
            "&:active": {
              transform: "translateY(0)",
            },
            "&.Mui-disabled": {
              background: "#e0e0e0",
              color: "#aaa",
              boxShadow: "none",
            },
          },
        },
        {
          props: { variant: "outlined" as const, color: "primary" as const },
          style: {
            borderWidth: 1,
            borderColor: "rgba(254, 44, 85, 0.3)",
            color: PINK,
            "&:hover": {
              borderWidth: 1,
              backgroundColor: "rgba(254, 44, 85, 0.06)",
              borderColor: PINK,
            },
          },
        },
      ],
    },

    MuiCard: {
      defaultProps: {
        elevation: 0,
      },
      styleOverrides: {
        root: {
          borderRadius: 12,
          border: "1px solid #f0f0f0",
          backgroundColor: "#ffffff",
          boxShadow: "0 2px 12px rgba(0, 0, 0, 0.04)",
          transition: "transform 0.25s, box-shadow 0.25s",
          "&:hover": {
            transform: "translateY(-2px)",
            boxShadow: "0 8px 30px rgba(0, 0, 0, 0.08)",
          },
        },
      },
    },

    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: "none",
          backgroundColor: "#ffffff",
        },
        rounded: {
          borderRadius: 12,
        },
      },
    },

    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: 6,
          fontWeight: 500,
          height: 26,
        },
        colorPrimary: {
          background: "rgba(254, 44, 85, 0.08)",
          color: PINK,
          border: "1px solid rgba(254, 44, 85, 0.15)",
        },
        colorSecondary: {
          background: "rgba(37, 244, 238, 0.08)",
          color: "#1cc9c3",
          border: "1px solid rgba(37, 244, 238, 0.2)",
        },
      },
    },

    MuiTextField: {
      styleOverrides: {
        root: {
          "& .MuiOutlinedInput-root": {
            borderRadius: 10,
            backgroundColor: "#ffffff",
            transition: "box-shadow 0.2s ease, border-color 0.2s ease",
            "& .MuiOutlinedInput-notchedOutline": {
              borderColor: "#e8e8e8",
              borderWidth: 1,
            },
            "&:hover .MuiOutlinedInput-notchedOutline": {
              borderColor: "#d0d0d0",
            },
            "&.Mui-focused": {
              boxShadow: "0 0 0 3px rgba(254, 44, 85, 0.08)",
            },
            "&.Mui-focused .MuiOutlinedInput-notchedOutline": {
              borderColor: PINK,
              borderWidth: 1,
            },
            "&.Mui-disabled": {
              backgroundColor: "#f5f5f5",
              "& .MuiOutlinedInput-notchedOutline": {
                borderColor: "#e0e0e0",
              },
            },
          },
          "& .MuiInputBase-input": {
            color: "#262626",
            "&::placeholder": {
              color: "#bbb",
              opacity: 1,
            },
          },
        },
      },
    },

    MuiStepper: {
      styleOverrides: {
        root: {
          paddingLeft: 0,
          paddingRight: 0,
        },
      },
    },

    MuiStepConnector: {
      styleOverrides: {
        line: {
          borderColor: "#e0e0e0",
        },
      },
    },

    MuiStepIcon: {
      styleOverrides: {
        root: {
          color: "#d0d0d0",
          "&.Mui-active": {
            color: PINK,
          },
          "&.Mui-completed": {
            color: CYAN,
          },
        },
      },
    },

    MuiAlert: {
      styleOverrides: {
        root: {
          borderRadius: 10,
          alignItems: "center",
        },
        colorWarning: {
          backgroundColor: "#fff8e1",
          color: "#262626",
          border: "1px solid rgba(245, 158, 11, 0.2)",
        },
        colorInfo: {
          backgroundColor: "#e6fffe",
          color: "#262626",
          border: "1px solid rgba(37, 244, 238, 0.2)",
        },
      },
    },

    MuiDialog: {
      styleOverrides: {
        paper: {
          borderRadius: 14,
          boxShadow: "0 16px 48px rgba(0, 0, 0, 0.12)",
          backgroundColor: "#ffffff",
          border: "1px solid #f0f0f0",
        },
      },
    },

    MuiTooltip: {
      styleOverrides: {
        tooltip: {
          borderRadius: 6,
          fontSize: "0.75rem",
          fontWeight: 500,
          backgroundColor: "#262626",
          padding: "6px 12px",
        },
      },
    },

    MuiLinearProgress: {
      styleOverrides: {
        root: {
          borderRadius: 4,
          height: 4,
          backgroundColor: "rgba(254, 44, 85, 0.1)",
        },
        bar: {
          borderRadius: 4,
          background: `linear-gradient(90deg, ${CYAN}, ${PINK})`,
        },
      },
    },

    MuiIconButton: {
      styleOverrides: {
        root: {
          transition: "background-color 0.18s ease",
          "&:hover": {
            backgroundColor: "rgba(0, 0, 0, 0.04)",
          },
        },
      },
    },

    MuiFab: {
      styleOverrides: {
        root: {
          boxShadow: "0 4px 16px rgba(254, 44, 85, 0.2)",
          "&:hover": {
            boxShadow: "0 8px 24px rgba(254, 44, 85, 0.3)",
          },
        },
      },
    },

    MuiTabs: {
      styleOverrides: {
        indicator: {
          background: `linear-gradient(90deg, ${CYAN}, ${PINK})`,
          height: 2,
          borderRadius: "2px 2px 0 0",
        },
      },
    },

    MuiTab: {
      styleOverrides: {
        root: {
          textTransform: "none",
          fontWeight: 500,
          "&.Mui-selected": {
            color: PINK,
          },
        },
      },
    },
  },
};

const theme = createTheme(themeOptions);

export default theme;
