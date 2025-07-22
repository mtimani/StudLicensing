"use client"
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
  useTheme,
} from "@mui/material"
import { AdminPanelSettings, Person, TrendingUp, Business } from "@mui/icons-material"
import { useAuth } from "../contexts/AuthContext"
import UserAvatar from "../components/UserAvatar"
import { useProfile } from "../contexts/ProfileContext"

const Dashboard = () => {
  const { user, hasRole } = useAuth()
  const { profileInfo } = useProfile() // Use ProfileContext instead of local state
  const navigate = useNavigate()
  const theme = useTheme()
  // Remove unused variable: const isMobile = useMediaQuery(theme.breakpoints.down("md"))

  return (
    <Box sx={{ flexGrow: 1, minHeight: "100vh", bgcolor: "background.default" }}>
      <AppBar
        position="fixed"
        elevation={0}
        sx={{
          background: "linear-gradient(135deg, #1976d2 0%, #42a5f5 50%, #64b5f6 100%)",
          boxShadow: "0 8px 32px rgba(25, 118, 210, 0.4)",
          borderBottom: "1px solid rgba(255, 255, 255, 0.1)",
          borderRadius: 0, // Remove rounded edges
          zIndex: (theme) => theme.zIndex.drawer + 1,
        }}
      >
        <Toolbar sx={{ py: 1 }}>
          <Box sx={{ display: "flex", alignItems: "center", gap: 2, flexGrow: 1 }}>
            <Box
              sx={{
                width: 40,
                height: 40,
                borderRadius: "50%",
                background: "linear-gradient(45deg, #ffffff20, #ffffff40)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                backdropFilter: "blur(10px)",
              }}
            >
              <Typography variant="h6" fontWeight="bold" color="white">
                S
              </Typography>
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
              StudLicensing Dashboard
            </Typography>
          </Box>
          <UserAvatar />
        </Toolbar>
      </AppBar>
      <Toolbar />

      <Container maxWidth="lg" sx={{ mt: 4, mb: 4, px: { xs: 2, sm: 3 } }}>
        <Paper
          elevation={3}
          sx={{
            p: { xs: 3, sm: 4 },
            mb: 4,
            background:
              theme.palette.mode === "dark"
                ? "linear-gradient(135deg, rgba(25, 118, 210, 0.1) 0%, rgba(66, 165, 245, 0.1) 100%)"
                : "linear-gradient(135deg, rgba(25, 118, 210, 0.05) 0%, rgba(66, 165, 245, 0.05) 100%)",
            borderRadius: 3,
            border: `1px solid ${theme.palette.divider}`,
          }}
        >
          <Box
            display="flex"
            alignItems="center"
            gap={3}
            flexDirection={{ xs: "column", sm: "row" }}
            textAlign={{ xs: "center", sm: "left" }}
          >
            <Avatar sx={{ width: { xs: 60, sm: 80 }, height: { xs: 60, sm: 80 }, bgcolor: "primary.main" }}>
              <Person sx={{ fontSize: { xs: 30, sm: 40 } }} />
            </Avatar>
            <Box>
              <Typography
                variant="h4"
                gutterBottom
                fontWeight="bold"
                sx={{ fontSize: { xs: "1.75rem", sm: "2.125rem" } }}
              >
                Welcome back, {profileInfo.name} {profileInfo.surname}!
              </Typography>
              <Box
                display="flex"
                gap={2}
                alignItems="center"
                flexWrap="wrap"
                justifyContent={{ xs: "center", sm: "flex-start" }}
              >
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
                borderRadius: 3,
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
                <Button
                  variant="contained"
                  onClick={() => navigate("/profile")}
                  sx={{
                    borderRadius: 2,
                    background: "linear-gradient(45deg, #1976d2 30%, #42a5f5 90%)",
                    boxShadow: "0 3px 5px 2px rgba(25, 118, 210, .3)",
                  }}
                >
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
                  borderRadius: 3,
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
                borderRadius: 3,
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
                borderRadius: 3,
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