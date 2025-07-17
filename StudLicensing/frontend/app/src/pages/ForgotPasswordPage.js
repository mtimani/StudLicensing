"use client"

import { useState } from "react"
import { Link } from "react-router-dom"
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
import { useApi } from "../contexts/ApiContext"

const ForgotPasswordPage = () => {
  const [email, setEmail] = useState("")
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)
  const [error, setError] = useState("")
  const { apiCall } = useApi()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError("")

    try {
      const formData = new FormData()
      formData.append("email", email)

      const response = await apiCall("/auth/forgot_password", {
        method: "POST",
        body: formData,
      })

      if (response.ok) {
        setSuccess(true)
      } else {
        const errorData = await response.json()
        setError(errorData.detail || "Failed to send reset email")
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
                {success ? "Check Your Email" : "Forgot Password"}
              </Typography>
            </Box>

            {success ? (
              <>
                <Alert severity="success" sx={{ mb: 3, borderRadius: 2 }}>
                  If an account with that email exists, we've sent you a password reset link.
                </Alert>
                <Box textAlign="center">
                  <Link to="/login" style={{ textDecoration: "none" }}>
                    <Typography variant="body2" color="primary">
                      Back to Sign In
                    </Typography>
                  </Link>
                </Box>
              </>
            ) : (
              <Box component="form" onSubmit={handleSubmit}>
                {error && (
                  <Alert severity="error" sx={{ mb: 3, borderRadius: 2 }}>
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
                  variant="outlined"
                  sx={{ mb: 2 }}
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
                  {loading ? <CircularProgress size={24} color="inherit" /> : "Send Reset Link"}
                </Button>

                <Box textAlign="center">
                  <Link to="/login" style={{ textDecoration: "none" }}>
                    <Typography variant="body2" color="primary" sx={{ "&:hover": { textDecoration: "underline" } }}>
                      Back to Sign In
                    </Typography>
                  </Link>
                </Box>
              </Box>
            )}
          </CardContent>
        </Card>
      </Container>
    </Box>
  )
}

export default ForgotPasswordPage