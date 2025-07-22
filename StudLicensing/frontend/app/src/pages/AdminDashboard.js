"use client"

import { useState } from "react"
import {
  Container,
  Paper,
  Typography,
  Box,
  Tabs,
  Tab,
  AppBar,
  Toolbar,
  IconButton,
  useTheme,
  useMediaQuery,
} from "@mui/material"
import { ArrowBack, AdminPanelSettings } from "@mui/icons-material"
import { useNavigate } from "react-router-dom"
import { useAuth } from "../contexts/AuthContext"
import UserManagement from "../components/admin/UserManagement"
import CompanyManagement from "../components/admin/CompanyManagement"
import UserAvatar from "../components/UserAvatar"

function TabPanel(props) {
  const { children, value, index, ...other } = props

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`admin-tabpanel-${index}`}
      aria-labelledby={`admin-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: { xs: 2, sm: 3 } }}>{children}</Box>}
    </div>
  )
}

const AdminDashboard = () => {
  const [tabValue, setTabValue] = useState(0)
  const navigate = useNavigate()
  const { hasRole } = useAuth()
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down("md"))

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue)
  }

  const isAdmin = hasRole(["admin"])

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
              <AdminPanelSettings sx={{ fontSize: 20, color: "white" }} />
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
              StudLicensing Admin
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
            borderRadius: 3,
            overflow: "hidden",
            background:
              theme.palette.mode === "dark"
                ? "linear-gradient(135deg, rgba(25, 118, 210, 0.02) 0%, rgba(66, 165, 245, 0.02) 100%)"
                : "linear-gradient(135deg, rgba(25, 118, 210, 0.01) 0%, rgba(66, 165, 245, 0.01) 100%)",
          }}
        >
          <Box sx={{ borderBottom: 1, borderColor: "divider" }}>
            <Tabs
              value={tabValue}
              onChange={handleTabChange}
              aria-label="admin tabs"
              sx={{
                px: 2,
                "& .MuiTab-root": {
                  fontWeight: 500,
                  fontSize: { xs: "0.875rem", sm: "1rem" },
                  minWidth: { xs: "auto", sm: 160 },
                },
              }}
              variant={isMobile ? "fullWidth" : "standard"}
            >
              <Tab label="User Management" />
              {isAdmin && <Tab label="Company Management" />}
            </Tabs>
          </Box>
          <TabPanel value={tabValue} index={0}>
            <UserManagement />
          </TabPanel>
          {isAdmin && (
            <TabPanel value={tabValue} index={1}>
              <CompanyManagement />
            </TabPanel>
          )}
        </Paper>
      </Container>
    </Box>
  )
}

export default AdminDashboard