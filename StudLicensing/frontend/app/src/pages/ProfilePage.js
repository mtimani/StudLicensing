"use client"

import { useEffect } from "react"

import { useState } from "react"
import { useNavigate } from "react-router-dom"
import {
  Container,
  Typography,
  Box,
  TextField,
  Button,
  Avatar,
  Grid,
  Alert,
  CircularProgress,
  AppBar,
  Toolbar,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Card,
  CardContent,
  useTheme,
} from "@mui/material"
import { ArrowBack, PhotoCamera, Person } from "@mui/icons-material"
import { useAuth } from "../contexts/AuthContext"
import { useApi } from "../contexts/ApiContext"
import { useProfile } from "../contexts/ProfileContext"
import UserAvatar from "../components/UserAvatar"

const ProfilePage = () => {
  const [localProfileInfo, setLocalProfileInfo] = useState({ name: "", surname: "" })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")
  const [passwordDialog, setPasswordDialog] = useState(false)
  const [passwordData, setPasswordData] = useState({
    oldPassword: "",
    newPassword: "",
    confirmPassword: "",
  })
  const [passwordError, setPasswordError] = useState("")
  const [initialized, setInitialized] = useState(false)
  const [profileErrorTimeout, setProfileErrorTimeout] = useState(null)
  const [passwordErrorTimeout, setPasswordErrorTimeout] = useState(null)
  const { user } = useAuth()
  const { apiCall } = useApi()
  const { profileInfo, profilePicture, updateProfileInfo, updateProfilePicture } = useProfile()
  const navigate = useNavigate()
  const theme = useTheme()

  const clearErrorAfterTimeout = (setErrorFn, timeoutRef, setTimeoutRef) => {
    if (timeoutRef) {
      clearTimeout(timeoutRef)
    }
    const timeout = setTimeout(() => {
      setErrorFn("")
      setTimeoutRef(null)
    }, 10000)
    setTimeoutRef(timeout)
  }

  // Initialize local state when profileInfo is loaded
  useEffect(() => {
    if (profileInfo.name || profileInfo.surname) {
      setLocalProfileInfo({
        name: profileInfo.name,
        surname: profileInfo.surname,
      })
      setInitialized(true)
    }
  }, [profileInfo.name, profileInfo.surname])

  const handleProfileUpdate = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError("")
    setSuccess("")

    const result = await updateProfileInfo(localProfileInfo)

    if (result.success) {
      setSuccess("Profile updated successfully")
    } else {
      setError(result.error)
      clearErrorAfterTimeout(setError, profileErrorTimeout, setProfileErrorTimeout)
    }
    setLoading(false)
  }

  const handlePictureUpload = async (event) => {
    const file = event.target.files?.[0]
    if (!file) return

    setLoading(true)
    setError("")
    setSuccess("")

    const result = await updateProfilePicture(file)

    if (result.success) {
      setSuccess("Profile picture updated successfully")
    } else {
      setError(result.error)
      clearErrorAfterTimeout(setError, profileErrorTimeout, setProfileErrorTimeout)
    }
    setLoading(false)
  }

  const handlePasswordChange = async (e) => {
    e.preventDefault()
    if (passwordData.newPassword !== passwordData.confirmPassword) {
      setPasswordError("New passwords do not match")
      return
    }

    setLoading(true)
    setPasswordError("")

    try {
      const response = await apiCall("/auth/change_password", {
        method: "POST",
        body: JSON.stringify({
          old_password: passwordData.oldPassword,
          new_password: passwordData.newPassword,
          confirm_password: passwordData.confirmPassword,
        }),
        headers: {
          "Content-Type": "application/json",
        },
      })

      if (response.ok) {
        setSuccess("Password changed successfully")
        setPasswordDialog(false)
        setPasswordData({ oldPassword: "", newPassword: "", confirmPassword: "" })
      } else {
        const errorData = await response.json()
        const errorMessage = errorData.detail || "Failed to change password"
        setPasswordError(errorMessage)
        clearErrorAfterTimeout(setPasswordError, passwordErrorTimeout, setPasswordErrorTimeout)
      }
    } catch (err) {
      const errorMessage = "Network error. Please try again."
      setPasswordError(errorMessage)
      clearErrorAfterTimeout(setPasswordError, passwordErrorTimeout, setPasswordErrorTimeout)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    return () => {
      if (profileErrorTimeout) clearTimeout(profileErrorTimeout)
      if (passwordErrorTimeout) clearTimeout(passwordErrorTimeout)
    }
  }, [profileErrorTimeout, passwordErrorTimeout])

  if (!initialized) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", alignItems: "center", minHeight: "100vh" }}>
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Box sx={{ flexGrow: 1, minHeight: "100vh", bgcolor: "background.default" }}>
      <AppBar
        position="static"
        elevation={0}
        sx={{
          background: "linear-gradient(135deg, #1976d2 0%, #42a5f5 50%, #64b5f6 100%)",
          boxShadow: "0 8px 32px rgba(25, 118, 210, 0.4)",
          borderBottom: "1px solid rgba(255, 255, 255, 0.1)",
          borderRadius: 0, // Remove rounded edges
        }}
      >
        <Toolbar sx={{ py: 1 }}>
          <IconButton
            size="large"
            edge="start"
            color="inherit"
            aria-label="back"
            onClick={() => navigate("/dashboard")}
            sx={{
              mr: 2,
              background: "rgba(255, 255, 255, 0.1)",
              "&:hover": { background: "rgba(255, 255, 255, 0.2)" },
            }}
          >
            <ArrowBack />
          </IconButton>
          <Box sx={{ display: "flex", alignItems: "center", gap: 2, flexGrow: 1 }}>
            <Box
              sx={{
                width: 32,
                height: 32,
                borderRadius: "50%",
                background: "linear-gradient(45deg, #ffffff20, #ffffff40)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                backdropFilter: "blur(10px)",
              }}
            >
              <Person sx={{ fontSize: 20, color: "white" }} />
            </Box>
            <Typography
              variant="h6"
              component="div"
              sx={{
                fontWeight: 700,
                fontSize: { xs: "1.1rem", sm: "1.25rem" },
                letterSpacing: "0.5px",
                textShadow: "0 2px 4px rgba(0,0,0,0.1)",
              }}
            >
              Profile Settings
            </Typography>
          </Box>
          <UserAvatar />
        </Toolbar>
      </AppBar>

      <Container maxWidth="md" sx={{ mt: 4, mb: 4, px: { xs: 2, sm: 3 } }}>
        <Card
          elevation={3}
          sx={{
            borderRadius: 3,
            background:
              theme.palette.mode === "dark"
                ? "linear-gradient(135deg, rgba(25, 118, 210, 0.05) 0%, rgba(66, 165, 245, 0.05) 100%)"
                : "linear-gradient(135deg, rgba(25, 118, 210, 0.02) 0%, rgba(66, 165, 245, 0.02) 100%)",
          }}
        >
          <CardContent sx={{ p: { xs: 3, sm: 4 } }}>
            <Typography
              variant="h4"
              gutterBottom
              fontWeight="bold"
              color="primary"
              sx={{ fontSize: { xs: "1.75rem", sm: "2.125rem" } }}
            >
              Profile Settings
            </Typography>

            {error && (
              <Alert severity="error" sx={{ mb: 3, borderRadius: 2 }}>
                {error}
              </Alert>
            )}
            {success && (
              <Alert severity="success" sx={{ mb: 3, borderRadius: 2 }}>
                {success}
              </Alert>
            )}

            <Grid container spacing={4}>
              <Grid item xs={12} md={4}>
                <Box display="flex" flexDirection="column" alignItems="center">
                  <Avatar
                    src={profilePicture || undefined}
                    sx={{
                      width: { xs: 120, sm: 150 },
                      height: { xs: 120, sm: 150 },
                      mb: 3,
                      border: "4px solid",
                      borderColor: "primary.main",
                      boxShadow: "0 8px 32px rgba(25, 118, 210, 0.3)",
                    }}
                  >
                    {!profilePicture && <Person sx={{ fontSize: { xs: 60, sm: 80 } }} />}
                  </Avatar>
                  <input
                    accept="image/*"
                    style={{ display: "none" }}
                    id="profile-picture-upload"
                    type="file"
                    onChange={handlePictureUpload}
                  />
                  <label htmlFor="profile-picture-upload">
                    <Button
                      variant="outlined"
                      component="span"
                      startIcon={<PhotoCamera />}
                      disabled={loading}
                      sx={{
                        borderRadius: 2,
                        px: 3,
                        py: 1,
                        fontSize: { xs: "0.875rem", sm: "1rem" },
                      }}
                    >
                      Upload Picture
                    </Button>
                  </label>
                </Box>
              </Grid>

              <Grid item xs={12} md={8}>
                <Box component="form" onSubmit={handleProfileUpdate}>
                  <TextField
                    margin="normal"
                    fullWidth
                    label="First Name"
                    value={localProfileInfo.name}
                    onChange={(e) => setLocalProfileInfo({ ...localProfileInfo, name: e.target.value })}
                    variant="outlined"
                    sx={{ mb: 2 }}
                  />
                  <TextField
                    margin="normal"
                    fullWidth
                    label="Last Name"
                    value={localProfileInfo.surname}
                    onChange={(e) => setLocalProfileInfo({ ...localProfileInfo, surname: e.target.value })}
                    variant="outlined"
                    sx={{ mb: 2 }}
                  />
                  <TextField
                    margin="normal"
                    fullWidth
                    label="Email"
                    value={user?.email || ""}
                    disabled
                    variant="outlined"
                    sx={{ mb: 3 }}
                  />
                  <Box
                    sx={{
                      display: "flex",
                      gap: 2,
                      flexDirection: { xs: "column", sm: "row" },
                      alignItems: { xs: "stretch", sm: "center" },
                    }}
                  >
                    <Button
                      type="submit"
                      variant="contained"
                      disabled={loading}
                      sx={{
                        borderRadius: 2,
                        minWidth: { xs: "auto", sm: 140 },
                        py: 1.5,
                        background: "linear-gradient(45deg, #1976d2 30%, #42a5f5 90%)",
                        boxShadow: "0 3px 5px 2px rgba(25, 118, 210, .3)",
                      }}
                    >
                      {loading ? <CircularProgress size={24} /> : "Update Profile"}
                    </Button>
                    <Button
                      variant="outlined"
                      onClick={() => setPasswordDialog(true)}
                      sx={{
                        borderRadius: 2,
                        minWidth: { xs: "auto", sm: 140 },
                        py: 1.5,
                      }}
                    >
                      Change Password
                    </Button>
                  </Box>
                </Box>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      </Container>

      <Dialog
        open={passwordDialog}
        onClose={() => {
          setPasswordDialog(false)
          setPasswordError("")
        }}
        maxWidth="sm"
        fullWidth
        PaperProps={{
          sx: { borderRadius: 3 },
        }}
      >
        <form onSubmit={handlePasswordChange}>
          <DialogTitle sx={{ pb: 1 }}>
            <Typography variant="h5" fontWeight="bold">
              Change Password
            </Typography>
          </DialogTitle>
          <DialogContent>
            {passwordError && (
              <Alert severity="error" sx={{ mb: 2, borderRadius: 2 }}>
                {passwordError}
              </Alert>
            )}
            <TextField
              margin="normal"
              fullWidth
              label="Current Password"
              type="password"
              value={passwordData.oldPassword}
              onChange={(e) => setPasswordData({ ...passwordData, oldPassword: e.target.value })}
              variant="outlined"
              required
            />
            <TextField
              margin="normal"
              fullWidth
              label="New Password"
              type="password"
              value={passwordData.newPassword}
              onChange={(e) => setPasswordData({ ...passwordData, newPassword: e.target.value })}
              variant="outlined"
              required
            />
            <TextField
              margin="normal"
              fullWidth
              label="Confirm New Password"
              type="password"
              value={passwordData.confirmPassword}
              onChange={(e) => setPasswordData({ ...passwordData, confirmPassword: e.target.value })}
              variant="outlined"
              required
            />
          </DialogContent>
          <DialogActions sx={{ p: 3 }}>
            <Button
              onClick={() => {
                setPasswordDialog(false)
                setPasswordError("")
              }}
              sx={{ borderRadius: 2 }}
            >
              Cancel
            </Button>
            <Button type="submit" variant="contained" disabled={loading} sx={{ borderRadius: 2 }}>
              {loading ? <CircularProgress size={24} /> : "Change Password"}
            </Button>
          </DialogActions>
        </form>
      </Dialog>
    </Box>
  )
}

export default ProfilePage