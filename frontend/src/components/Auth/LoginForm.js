// src/components/Auth/LoginForm.js
import React, { useState } from "react";
import {
  TextField,
  Button,
  Typography,
  Box,
  CircularProgress,
  Alert,
} from "@mui/material";
import AuthService from "../../services/AuthService";
import { useNavigate } from "react-router-dom";

const LoginForm = ({ onLoginSuccess }) => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const data = await AuthService.login(email, password);

      // Call the success callback (if provided)
      if (onLoginSuccess) {
        console.log("Login successful:", data);
        onLoginSuccess(data);
      }

      // Add explicit navigation here to ensure it happens
      navigate("/");
    } catch (err) {
      setError(err.message || "Login failed. Please check your credentials.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box 
      component="form" 
      onSubmit={handleSubmit} 
      sx={{ 
        width: "100%",
        position: "relative",
        "&::before": {
          content: '""',
          position: "absolute",
          top: -20,
          right: -20,
          width: 80,
          height: 80,
          background: "radial-gradient(circle, rgba(88, 167, 254, 0.15) 0%, rgba(127, 231, 134, 0) 70%)",
          borderRadius: "50%",
          zIndex: 0,
        }
      }}
    >
      {error && (
        <Alert 
          severity="error" 
          sx={{ 
            mb: 2,
            borderRadius: 1.5,
            animation: "shake 0.5s cubic-bezier(.36,.07,.19,.97) both",
            "@keyframes shake": {
              "10%, 90%": { transform: "translate3d(-1px, 0, 0)" },
              "20%, 80%": { transform: "translate3d(2px, 0, 0)" },
              "30%, 50%, 70%": { transform: "translate3d(-4px, 0, 0)" },
              "40%, 60%": { transform: "translate3d(4px, 0, 0)" }
            }
          }}
        >
          {error}
        </Alert>
      )}

      <TextField
        margin="normal"
        required
        fullWidth
        id="email"
        label="Email Address"
        name="email"
        autoComplete="email"
        autoFocus
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        disabled={loading}
        sx={{ 
          "& .MuiOutlinedInput-root": {
            borderRadius: 2,
            transition: "all 0.3s ease",
            "&:hover .MuiOutlinedInput-notchedOutline": {
              borderColor: "#58A7FE"
            },
            "&.Mui-focused .MuiOutlinedInput-notchedOutline": {
              borderColor: "#58A7FE",
              boxShadow: "0 0 0 3px rgba(88, 167, 254, 0.15)"
            }
          },
          "& .MuiFormLabel-root.Mui-focused": {
            color: "#58A7FE"
          }
        }}
      />

      <TextField
        margin="normal"
        required
        fullWidth
        name="password"
        label="Password"
        type="password"
        id="password"
        autoComplete="current-password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        disabled={loading}
        sx={{ 
          "& .MuiOutlinedInput-root": {
            borderRadius: 2,
            transition: "all 0.3s ease",
            "&:hover .MuiOutlinedInput-notchedOutline": {
              borderColor: "#7FE786"
            },
            "&.Mui-focused .MuiOutlinedInput-notchedOutline": {
              borderColor: "#7FE786",
              boxShadow: "0 0 0 3px rgba(127, 231, 134, 0.15)"
            }
          },
          "& .MuiFormLabel-root.Mui-focused": {
            color: "#7FE786"
          }
        }}
      />

      <Button
        type="submit"
        fullWidth
        variant="contained"
        sx={{
          mt: 3.5,
          mb: 2.5,
          background: "linear-gradient(90deg, #58A7FE, #7FE786)",
          boxShadow: "0 4px 15px rgba(88, 167, 254, 0.25)",
          borderRadius: 2.5,
          py: 1.5,
          textTransform: "none",
          fontSize: "1.05rem",
          fontWeight: 600,
          transition: "all 0.3s ease",
          "&:hover": { 
            boxShadow: "0 6px 20px rgba(88, 167, 254, 0.35)",
            transform: "translateY(-1px)"
          }
        }}
        disabled={loading}
      >
        {loading ? <CircularProgress size={24} color="inherit" /> : "Sign In"}
      </Button>

      <Typography 
        variant="body2" 
        align="center" 
        sx={{ 
          mt: 2,
          color: "text.secondary",
          fontWeight: 500,
          position: "relative",
          "&::before, &::after": {
            content: '""',
            position: "absolute",
            top: "50%",
            width: "15%",
            height: "1px",
            background: "rgba(0,0,0,0.1)",
          },
          "&::before": {
            left: "15%",
          },
          "&::after": {
            right: "15%",
          }
        }}
      >
        Don't have an account? Use the Sign Up tab above.
      </Typography>
    </Box>
  );
};

export default LoginForm;
