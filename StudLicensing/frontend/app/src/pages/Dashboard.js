"use client"
import { useEffect, useState } from "react"
import { useNavigate } from "react-router-dom"
import {
  Container,
  Paper,
  Typography,
  Box,
  Button,
  Grid,
  Card,
  CardContent,
  CardActions,
  AppBar,
  Toolbar,
  Chip,
  Avatar,
} from "@mui/material"
import { AdminPanelSettings, Person, TrendingUp, Business } from "@mui/icons-material"
import { useAuth } from "../contexts/AuthContext"
import { useApi } from "../contexts/ApiContext"
import UserAvatar from "../components/UserAvatar"

const Dashboard = () => {
  const { user, hasRole } = useAuth()
  const { apiCall } = useApi()
  const navigate = useNavigate()
  const [profileInfo, setProfileInfo] = useState({ name: "", surname: "" })

  useEffect(() => {
    fetchProfileInfo()
  }, [])

  const fetchProfileInfo = async () => {
    try {
      const response = await apiCall("/profile/info")
      if (response.ok) {
        const data = await response.json()
        setProfileInfo({
          name: data.name || "",
          surname: data.surname || "",
        })
      }
    } catch (error) {
      console.error("Error fetching profile info:", error)
    }
  }

  return (
    <Box sx={{ flexGrow: 1, minHeight: "100vh" }}>
      <AppBar position="static" elevation={0} sx={{ background: "linear-gradient(45deg, #1976d2 30%, #42a5f5 90%)" }}>
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1, fontWeight: 600 }}>
            StudLicensing Dashboard
          </Typography>
          <UserAvatar />
        </Toolbar>
      </AppBar>

      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Paper
          elevation={3}
          sx={{
            p: 4,
            mb: 4,
            background: "linear-gradient(135deg, rgba(25, 118, 210, 0.1) 0%, rgba(66, 165, 245, 0.1) 100%)",
            borderRadius: 3,
          }}
        >
          <Box display="flex" alignItems="center" gap={3}>
            <Avatar sx={{ width: 80, height: 80, bgcolor: "primary.main" }}>
              <Person sx={{ fontSize: 40 }} />
            </Avatar>
            <Box>
              <Typography variant="h4" gutterBottom fontWeight="bold">
                Welcome back, {profileInfo.name} {profileInfo.surname}!
              </Typography>
              <Box display="flex" gap={2} alignItems="center" flexWrap="wrap">
                <Chip label={user?.roleDisplayName} color="primary" variant="filled" sx={{ fontWeight: 500 }} />
                <Typography variant="body1" color="text.secondary">
                  {user?.email}
                </Typography>
              </Box>
            </Box>
          </Box>
        </Paper>

        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card
              elevation={2}
              sx={{
                height: "100%",
                transition: "transform 0.2s, box-shadow 0.2s",
                "&:hover": {
                  transform: "translateY(-4px)",
                  boxShadow: 6,
                },
              }}
            >
              <CardContent sx={{ p: 3 }}>
                <Box display="flex" alignItems="center" gap={2} mb={2}>
                  <Avatar sx={{ bgcolor: "secondary.main" }}>
                    <Person />
                  </Avatar>
                  <Typography variant="h5" component="div" fontWeight="600">
                    Profile Management
                  </Typography>
                </Box>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Update your personal information, profile picture, and account settings.
                </Typography>
              </CardContent>
              <CardActions sx={{ p: 3, pt: 0 }}>
                <Button variant="contained" onClick={() => navigate("/profile")} sx={{ borderRadius: 2 }}>
                  Manage Profile
                </Button>
              </CardActions>
            </Card>
          </Grid>

          {hasRole(["admin", "company_admin", "company_developper", "company_commercial"]) && (
            <Grid item xs={12} md={6}>
              <Card
                elevation={2}
                sx={{
                  height: "100%",
                  transition: "transform 0.2s, box-shadow 0.2s",
                  "&:hover": {
                    transform: "translateY(-4px)",
                    boxShadow: 6,
                  },
                }}
              >
                <CardContent sx={{ p: 3 }}>
                  <Box display="flex" alignItems="center" gap={2} mb={2}>
                    <Avatar sx={{ bgcolor: "warning.main" }}>
                      <AdminPanelSettings />
                    </Avatar>
                    <Typography variant="h5" component="div" fontWeight="600">
                      Admin Panel
                    </Typography>
                  </Box>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    Manage users, companies, and administrative tasks with advanced controls.
                  </Typography>
                </CardContent>
                <CardActions sx={{ p: 3, pt: 0 }}>
                  <Button
                    variant="contained"
                    color="warning"
                    onClick={() => navigate("/admin")}
                    sx={{ borderRadius: 2 }}
                  >
                    Open Admin
                  </Button>
                </CardActions>
              </Card>
            </Grid>
          )}

          <Grid item xs={12} md={6}>
            <Card
              elevation={2}
              sx={{
                height: "100%",
                transition: "transform 0.2s, box-shadow 0.2s",
                "&:hover": {
                  transform: "translateY(-4px)",
                  boxShadow: 6,
                },
              }}
            >
              <CardContent sx={{ p: 3 }}>
                <Box display="flex" alignItems="center" gap={2} mb={2}>
                  <Avatar sx={{ bgcolor: "success.main" }}>
                    <TrendingUp />
                  </Avatar>
                  <Typography variant="h5" component="div" fontWeight="600">
                    Analytics
                  </Typography>
                </Box>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  View your licensing statistics, usage reports, and performance metrics.
                </Typography>
              </CardContent>
              <CardActions sx={{ p: 3, pt: 0 }}>
                <Button variant="outlined" color="success" sx={{ borderRadius: 2 }} disabled>
                  Coming Soon
                </Button>
              </CardActions>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card
              elevation={2}
              sx={{
                height: "100%",
                transition: "transform 0.2s, box-shadow 0.2s",
                "&:hover": {
                  transform: "translateY(-4px)",
                  boxShadow: 6,
                },
              }}
            >
              <CardContent sx={{ p: 3 }}>
                <Box display="flex" alignItems="center" gap={2} mb={2}>
                  <Avatar sx={{ bgcolor: "info.main" }}>
                    <Business />
                  </Avatar>
                  <Typography variant="h5" component="div" fontWeight="600">
                    License Management
                  </Typography>
                </Box>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Manage your software licenses, renewals, and compliance tracking.
                </Typography>
              </CardContent>
              <CardActions sx={{ p: 3, pt: 0 }}>
                <Button variant="outlined" color="info" sx={{ borderRadius: 2 }} disabled>
                  Coming Soon
                </Button>
              </CardActions>
            </Card>
          </Grid>
        </Grid>
      </Container>
    </Box>
  )
}

export default Dashboard