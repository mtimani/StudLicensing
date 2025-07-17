"use client"

import { useState, useEffect } from "react"
import { useNavigate, Link, useSearchParams } from "react-router-dom"
import {
  Container,
  TextField,
  Button,
  Typography,
  Box,
  Alert,
  CircularProgress,
  Card,
  CardContent,
} from "@mui/material"
import { useAuth } from "../contexts/AuthContext"
import { useApi } from "../contexts/ApiContext"

const LoginPage = () => {
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [searchParams] = useSearchParams()
  const { login, isAuthenticated } = useAuth()
  const { apiCall } = useApi()
  const navigate = useNavigate()

  useEffect(() => {
    if (isAuthenticated) {
      navigate("/dashboard")
    }
  }, [isAuthenticated, navigate])

  useEffect(() => {
    const message = searchParams.get("message")
    if (message === "session_expired") {
      setError("Your session has expired. Please login again.")
    }
  }, [searchParams])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError("")

    try {
      const formData = new FormData()
      formData.append("username", username)
      formData.append("password", password)

      const response = await apiCall("/auth/token", {
        method: "POST",
        body: formData,
      })

      if (response.ok) {
        const data = await response.json()
        login(data.access_token)
        navigate("/dashboard")
      } else {
        const errorData = await response.json()
        setError(errorData.detail || "Login failed")
      }
    } catch (err) {
      setError("Network error. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <Box
      sx={{
        minHeight: "100vh",
        background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        p: { xs: 1, sm: 2 },
      }}
    >
      <Container component="main" maxWidth="sm" sx={{ px: { xs: 1, sm: 2 } }}>
        <Card elevation={24} sx={{ borderRadius: 4, mx: { xs: 1, sm: 0 } }}>
          <CardContent sx={{ p: { xs: 3, sm: 4 } }}>
            <Box textAlign="center" mb={{ xs: 3, sm: 4 }}>
              <Typography
                component="h1"
                variant="h3"
                fontWeight="bold"
                color="primary"
                gutterBottom
                sx={{ fontSize: { xs: "2rem", sm: "3rem" } }}
              >
                StudLicensing
              </Typography>
              <Typography variant="h5" color="text.secondary" sx={{ fontSize: { xs: "1.25rem", sm: "1.5rem" } }}>
                Welcome back
              </Typography>
            </Box>

            {error && (
              <Alert severity="error" sx={{ mb: 3, borderRadius: 2 }}>
                {error}
              </Alert>
            )}

            <Box component="form" onSubmit={handleSubmit}>
              <TextField
                margin="normal"
                required
                fullWidth
                id="username"
                label="Email Address"
                name="username"
                autoComplete="email"
                autoFocus
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                variant="outlined"
                sx={{ mb: 2 }}
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
                variant="outlined"
                sx={{ mb: 3 }}
              />
              <Button
                type="submit"
                fullWidth
                variant="contained"
                size="large"
                disabled={loading}
                sx={{
                  py: 1.5,
                  mb: 2,
                  background: "linear-gradient(45deg, #1976d2 30%, #42a5f5 90%)",
                  boxShadow: "0 3px 5px 2px rgba(25, 118, 210, .3)",
                }}
              >
                {loading ? <CircularProgress size={24} color="inherit" /> : "Sign In"}
              </Button>
              <Box textAlign="center">
                <Link to="/forgot-password" style={{ textDecoration: "none" }}>
                  <Typography variant="body2" color="primary" sx={{ "&:hover": { textDecoration: "underline" } }}>
                    Forgot password?
                  </Typography>
                </Link>
              </Box>
            </Box>
          </CardContent>
        </Card>
      </Container>
    </Box>
  )
}

export default LoginPage