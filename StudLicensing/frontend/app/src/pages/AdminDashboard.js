"use client"

import { useState } from "react"
import { Container, Paper, Typography, Box, Tabs, Tab, AppBar, Toolbar, IconButton } from "@mui/material"
import { ArrowBack } from "@mui/icons-material"
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
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  )
}

const AdminDashboard = () => {
  const [tabValue, setTabValue] = useState(0)
  const navigate = useNavigate()
  const { hasRole } = useAuth()

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue)
  }

  const isAdmin = hasRole(["admin"])

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
            StudLicensing Admin
          </Typography>
          <UserAvatar />
        </Toolbar>
      </AppBar>

      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Paper elevation={3} sx={{ borderRadius: 3 }}>
          <Box sx={{ borderBottom: 1, borderColor: "divider" }}>
            <Tabs value={tabValue} onChange={handleTabChange} aria-label="admin tabs" sx={{ px: 2 }}>
              <Tab label="User Management" sx={{ fontWeight: 500 }} />
              {isAdmin && <Tab label="Company Management" sx={{ fontWeight: 500 }} />}
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