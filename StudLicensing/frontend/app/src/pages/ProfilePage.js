"use client"

import { useState, useEffect } from "react"
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
} from "@mui/material"
import { ArrowBack, PhotoCamera, Person } from "@mui/icons-material"
import { useAuth } from "../contexts/AuthContext"
import { useApi } from "../contexts/ApiContext"
import UserAvatar from "../components/UserAvatar"

const ProfilePage = () => {
  const [profileInfo, setProfileInfo] = useState({ name: "", surname: "", email: "" })
  const [profilePicture, setProfilePicture] = useState(null)
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
  const { user } = useAuth()
  const { apiCall } = useApi()
  const navigate = useNavigate()

  useEffect(() => {
    fetchProfileInfo()
    fetchProfilePicture()
  }, [])

  const fetchProfileInfo = async () => {
    try {
      const response = await apiCall("/profile/info")
      if (response.ok) {
        const data = await response.json()
        setProfileInfo({
          name: data.name || "",
          surname: data.surname || "",
          email: user?.email || "",
        })
      }
    } catch (error) {
      console.error("Error fetching profile info:", error)
    }
  }

  const fetchProfilePicture = async () => {
    try {
      const response = await apiCall("/profile/picture")
      if (response.ok) {
        const blob = await response.blob()
        const imageUrl = URL.createObjectURL(blob)
        setProfilePicture(imageUrl)
      }
    } catch (error) {
      console.error("Error fetching profile picture:", error)
    }
  }

  const handleProfileUpdate = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError("")
    setSuccess("")

    try {
      const response = await apiCall("/profile/info", {
        method: "PUT",
        body: JSON.stringify({
          name: profileInfo.name,
          surname: profileInfo.surname,
        }),
        headers: {
          "Content-Type": "application/json",
        },
      })

      if (response.ok) {
        setSuccess("Profile updated successfully")
      } else {
        const errorData = await response.json()
        setError(errorData.detail || "Failed to update profile")
      }
    } catch (err) {
      setError("Network error. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  const handlePictureUpload = async (event) => {
    const file = event.target.files?.[0]
    if (!file) return

    setLoading(true)
    setError("")
    setSuccess("")

    try {
      const formData = new FormData()
      formData.append("new_picture", file)

      const response = await apiCall("/profile/picture", {
        method: "PUT",
        body: formData,
      })

      if (response.ok) {
        setSuccess("Profile picture updated successfully")
        fetchProfilePicture()
      } else {
        const errorData = await response.json()
        setError(errorData.detail || "Failed to update profile picture")
      }
    } catch (err) {
      setError("Network error. Please try again.")
    } finally {
      setLoading(false)
    }
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
        setPasswordError(errorData.detail || "Failed to change password")
      }
    } catch (err) {
      setPasswordError("Network error. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <Box sx={{ flexGrow: 1, minHeight: "100vh" }}>
      <AppBar position="static" elevation={0} sx={{ background: "linear-gradient(45deg, #1976d2 30%, #42a5f5 90%)" }}>
        <Toolbar>
          <IconButton
            size="large"
            edge="start"
            color="inherit"
            aria-label="back"
            onClick={() => navigate("/dashboard")}
            sx={{ mr: 2 }}
          >
            <ArrowBack />
          </IconButton>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1, fontWeight: 600 }}>
            Profile Settings
          </Typography>
          <UserAvatar />
        </Toolbar>
      </AppBar>

      <Container maxWidth="md" sx={{ mt: 4, mb: 4 }}>
        <Card elevation={3} sx={{ borderRadius: 3 }}>
          <CardContent sx={{ p: 4 }}>
            <Typography variant="h4" gutterBottom fontWeight="bold" color="primary">
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
                      width: 150,
                      height: 150,
                      mb: 3,
                      border: "4px solid",
                      borderColor: "primary.main",
                      boxShadow: 3,
                    }}
                  >
                    {!profilePicture && <Person sx={{ fontSize: 80 }} />}
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
                      sx={{ borderRadius: 2 }}
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
                    value={profileInfo.name}
                    onChange={(e) => setProfileInfo({ ...profileInfo, name: e.target.value })}
                    variant="outlined"
                    sx={{ mb: 2 }}
                  />
                  <TextField
                    margin="normal"
                    fullWidth
                    label="Last Name"
                    value={profileInfo.surname}
                    onChange={(e) => setProfileInfo({ ...profileInfo, surname: e.target.value })}
                    variant="outlined"
                    sx={{ mb: 2 }}
                  />
                  <TextField
                    margin="normal"
                    fullWidth
                    label="Email"
                    value={profileInfo.email}
                    disabled
                    variant="outlined"
                    sx={{ mb: 3 }}
                  />
                  <Box sx={{ display: "flex", gap: 2, flexWrap: "wrap" }}>
                    <Button
                      type="submit"
                      variant="contained"
                      disabled={loading}
                      sx={{ borderRadius: 2, minWidth: 140 }}
                    >
                      {loading ? <CircularProgress size={24} /> : "Update Profile"}
                    </Button>
                    <Button
                      variant="outlined"
                      onClick={() => setPasswordDialog(true)}
                      sx={{ borderRadius: 2, minWidth: 140 }}
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