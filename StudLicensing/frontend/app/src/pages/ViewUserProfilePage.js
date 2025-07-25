"use client"

import { useState, useEffect, useCallback } from "react"
import { useParams, useNavigate } from "react-router-dom"
import {
  Container,
  Typography,
  Box,
  Avatar,
  Grid,
  Alert,
  CircularProgress,
  AppBar,
  Toolbar,
  IconButton,
  Card,
  CardContent,
  useTheme,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
} from "@mui/material"
import { ArrowBack, Person, Email, Phone, Badge, Business, AccountCircle } from "@mui/icons-material"
import { useApi } from "../contexts/ApiContext"
import UserAvatar from "../components/UserAvatar"

// Helper function to get display name for roles
const getRoleDisplayName = (role) => {
  const roleMap = {
    admin: "Global Administrator",
    company_admin: "Company Administrator",
    company_developper: "Company Developer",
    company_commercial: "Company Commercial",
    company_client: "Client",
    basic: "Basic User",
  }
  return roleMap[role] || role
}

const ViewUserProfilePage = () => {
  const { username } = useParams()
  const [profileData, setProfileData] = useState(null)
  const [profilePicture, setProfilePicture] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const { apiCall } = useApi()
  const navigate = useNavigate()
  const theme = useTheme()

  const fetchUserProfile = useCallback(async () => {
    setLoading(true)
    setError("")
    try {
      // Fetch user info
      const userInfoResponse = await apiCall("/admin/search_user", {
        method: "POST",
        body: new URLSearchParams({ username }).toString(),
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
      })

      if (userInfoResponse.ok) {
        const data = await userInfoResponse.json()
        const user = data.users?.find((u) => u.username === username)
        if (user) {
          setProfileData({
            name: user.name || "",
            surname: user.surname || "",
            email: user.email || "", // Corrected from user.username to user.email
            phoneNumber: user.phoneNumber || "",
            user_type: user.user_type || "",
            // Ensure company_title is always an array for consistent rendering
            company_title: Array.isArray(user.company_title)
              ? user.company_title
              : user.company_title
                ? [user.company_title]
                : [],
          })
        } else {
          setError("User not found.")
        }
      } else {
        const errorData = await userInfoResponse.json()
        setError(errorData.detail || "Failed to fetch user profile.")
      }

      // Fetch profile picture (if available for this user)
      const profilePictureResponse = await apiCall("/admin/get_user_profile_picture", {
        method: "POST",
        body: new URLSearchParams({ username }).toString(),
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
      })
      if (profilePictureResponse.ok) {
        const blob = await profilePictureResponse.blob()
        const imageUrl = URL.createObjectURL(blob)
        setProfilePicture(imageUrl)
      } else {
        // It's okay if there's no picture, just don't set an error for it
        setProfilePicture(null)
      }
    } catch (err) {
      setError("Network error. Please try again.")
    } finally {
      setLoading(false)
    }
  }, [username, apiCall])

  useEffect(() => {
    fetchUserProfile()
  }, [fetchUserProfile])

  if (loading) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", alignItems: "center", minHeight: "100vh" }}>
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Box sx={{ flexGrow: 1, minHeight: "100vh", bgcolor: "background.default" }}>
      <AppBar
        position="fixed"
        elevation={0}
        sx={{
          zIndex: (theme) => theme.zIndex.drawer + 1,
          background: "linear-gradient(135deg, #1976d2 0%, #42a5f5 50%, #64b5f6 100%)",
          boxShadow: "0 8px 32px rgba(25, 118, 210, 0.4)",
          borderBottom: "1px solid rgba(255, 255, 255, 0.1)",
          borderRadius: 0,
        }}
      >
        <Toolbar sx={{ py: 1 }}>
          <IconButton
            size="large"
            edge="start"
            color="inherit"
            aria-label="back"
            onClick={() => navigate("/admin")}
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
              User Profile View
            </Typography>
          </Box>
          <UserAvatar />
        </Toolbar>
      </AppBar>
      <Toolbar />

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
              Profile Details for {profileData?.name} {profileData?.surname}
            </Typography>

            {error && (
              <Alert severity="error" sx={{ mb: 3, borderRadius: 2 }}>
                {error}
              </Alert>
            )}

            {profileData && (
              <Grid container spacing={4} alignItems="center">
                <Grid item xs={12} md={4}>
                  <Box display="flex" flexDirection="column" alignItems="center" sx={{ pt: 2 }}>
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
                    <Typography variant="h6" fontWeight="bold" sx={{ mb: 0.5 }}>
                      {profileData.name} {profileData.surname}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {getRoleDisplayName(profileData.user_type)}
                    </Typography>
                  </Box>
                </Grid>

                <Grid item xs={12} md={8}>
                  <List
                    sx={{
                      width: "100%",
                      borderRadius: 2,
                      p: 2,
                      background:
                        theme.palette.mode === "dark"
                          ? "linear-gradient(135deg, rgba(50, 50, 50, 0.8) 0%, rgba(70, 70, 70, 0.8) 100%)"
                          : "linear-gradient(135deg, rgba(240, 240, 240, 0.8) 0%, rgba(250, 250, 250, 0.8) 100%)",
                      boxShadow: "0 4px 12px rgba(0,0,0,0.1)",
                      backdropFilter: "blur(5px)",
                    }}
                  >
                    <ListItem>
                      <ListItemIcon>
                        <Badge color="action" />
                      </ListItemIcon>
                      <ListItemText
                        primary="First Name"
                        secondary={profileData.name || "-"}
                        primaryTypographyProps={{ variant: "subtitle2", color: "text.secondary" }}
                        secondaryTypographyProps={{ variant: "body1", fontWeight: "medium" }}
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemIcon>
                        <Badge color="action" />
                      </ListItemIcon>
                      <ListItemText
                        primary="Last Name"
                        secondary={profileData.surname || "-"}
                        primaryTypographyProps={{ variant: "subtitle2", color: "text.secondary" }}
                        secondaryTypographyProps={{ variant: "body1", fontWeight: "medium" }}
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemIcon>
                        <Phone color="action" />
                      </ListItemIcon>
                      <ListItemText
                        primary="Phone Number"
                        secondary={profileData.phoneNumber || "-"}
                        primaryTypographyProps={{ variant: "subtitle2", color: "text.secondary" }}
                        secondaryTypographyProps={{ variant: "body1", fontWeight: "medium" }}
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemIcon>
                        <Email color="action" />
                      </ListItemIcon>
                      <ListItemText
                        primary="Email"
                        secondary={profileData.email || "-"}
                        primaryTypographyProps={{ variant: "subtitle2", color: "text.secondary" }}
                        secondaryTypographyProps={{ variant: "body1", fontWeight: "medium" }}
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemIcon>
                        <AccountCircle color="action" />
                      </ListItemIcon>
                      <ListItemText
                        primary="User Type"
                        secondary={getRoleDisplayName(profileData.user_type)}
                        primaryTypographyProps={{ variant: "subtitle2", color: "text.secondary" }}
                        secondaryTypographyProps={{ variant: "body1", fontWeight: "medium" }}
                      />
                    </ListItem>
                    {profileData.user_type !== "admin" && (
                      <ListItem>
                        <ListItemIcon>
                          <Business color="action" />
                        </ListItemIcon>
                        <ListItemText
                          primary={profileData.company_title.length > 1 ? "Companies" : "Company"}
                          secondary={profileData.company_title.length > 0 ? profileData.company_title.join(", ") : "-"}
                          primaryTypographyProps={{ variant: "subtitle2", color: "text.secondary" }}
                          secondaryTypographyProps={{ variant: "body1", fontWeight: "medium" }}
                        />
                      </ListItem>
                    )}
                  </List>
                </Grid>
              </Grid>
            )}
          </CardContent>
        </Card>
      </Container>
    </Box>
  )
}

export default ViewUserProfilePage