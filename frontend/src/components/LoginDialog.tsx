/**
 * 登录/注册对话框
 */
import { useState } from "react";
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Tabs,
  Tab,
  Box,
  Typography,
  IconButton,
  CircularProgress,
} from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";
import { useAuth } from "../contexts/AuthContext";

interface LoginDialogProps {
  open: boolean;
  onClose: () => void;
  initialTab?: "login" | "register";
}

export default function LoginDialog({ open, onClose, initialTab = "login" }: LoginDialogProps) {
  const { login, register } = useAuth();
  const [tab, setTab] = useState<"login" | "register">(initialTab);
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    setError("");
    setLoading(true);
    try {
      if (tab === "login") {
        await login(username, password);
      } else {
        await register(username, email, password);
      }
      onClose();
      setUsername("");
      setEmail("");
      setPassword("");
    } catch (e: any) {
      setError(e.message || "操作失败");
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setError("");
    setUsername("");
    setEmail("");
    setPassword("");
    onClose();
  };

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth="xs"
      fullWidth
    >
      <DialogTitle sx={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
          <Box
            sx={{
              width: 28,
              height: 28,
              borderRadius: "6px",
              background: "linear-gradient(135deg, #25f4ee, #fe2c55)",
            }}
          />
          <Typography variant="h6" sx={{ fontWeight: 700 }}>
            抖医账号
          </Typography>
        </Box>
        <IconButton onClick={handleClose} size="small">
          <CloseIcon fontSize="small" />
        </IconButton>
      </DialogTitle>

      <Tabs
        value={tab}
        onChange={(_, v) => { setTab(v); setError(""); }}
        sx={{ borderBottom: 1, borderColor: "divider", mx: 2 }}
      >
        <Tab value="login" label="登录" />
        <Tab value="register" label="注册" />
      </Tabs>

      <DialogContent sx={{ pt: 3 }}>
        <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
          <TextField
            label="用户名"
            value={username}
            onChange={e => setUsername(e.target.value)}
            fullWidth
            size="small"
            autoFocus={tab === "login"}
          />
          {tab === "register" && (
            <TextField
              label="邮箱"
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              fullWidth
              size="small"
            />
          )}
          <TextField
            label="密码"
            type="password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            fullWidth
            size="small"
            autoFocus={tab === "register"}
          />
          {error && (
            <Typography color="error" variant="body2">
              {error}
            </Typography>
          )}
        </Box>
      </DialogContent>

      <DialogActions sx={{ px: 3, pb: 3 }}>
        <Button onClick={handleClose} color="inherit">
          取消
        </Button>
        <Button
          onClick={handleSubmit}
          variant="contained"
          disabled={loading || !username || !password || (tab === "register" && !email)}
          sx={{
            background: "linear-gradient(135deg, #25f4ee, #fe2c55)",
            "&:hover": { background: "linear-gradient(135deg, #25f4ee, #fe2c55)" },
          }}
        >
          {loading ? <CircularProgress size={20} /> : tab === "login" ? "登录" : "注册"}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
