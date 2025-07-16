"use client"

import { useState, useEffect } from "react"
import {
  Avatar,
  IconButton,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
  Divider,
  Switch,
  FormControlLabel,
  Box,
} from "@mui/material"
import { Person, AdminPanelSettings, ExitToApp, Brightness4, Brightness7 } from "@mui/icons-material"
import { useAuth } from "../contexts/AuthContext"
import { useApi } from "../contexts/ApiContext"
import { useThemeMode } from "../contexts/ThemeContext"
import { useNavigate } from "react-router-dom"

const UserAvatar = () => {
  const [anchorEl, setAnchorEl] = useState(null)
  const [profilePicture, setProfilePicture] = useState(null)
  const { user, logout, hasRole } = useAuth()
  const { apiCall } = useApi()
  const { darkMode, toggleDarkMode } = useThemeMode()
  const navigate = useNavigate()

  useEffect(() => {
    fetchProfilePicture()
  }, [])

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

  const handleMenu = (event) => {
    setAnchorEl(event.currentTarget)
  }

  const handleClose = () => {
    setAnchorEl(null)
  }

  const handleProfile = () => {
    navigate("/profile")
    handleClose()
  }

  const handleAdmin = () => {
    navigate("/admin")
    handleClose()
  }

  const handleLogout = async () => {
    try {
      await apiCall("/auth/logout", { method: "POST" })
    } catch (error) {
      console.error("Logout error:", error)
    } finally {
      logout()
      navigate("/login")
    }
    handleClose()
  }

  return (
    <>
      <IconButton
        size="large"
        aria-label="account of current user"
        aria-controls="menu-appbar"
        aria-haspopup="true"
        onClick={handleMenu}
        color="inherit"
        sx={{ p: 0.5 }}
      >
        <Avatar
          src={profilePicture || undefined}
          sx={{
            width: 40,
            height: 40,
            border: "2px solid rgba(255,255,255,0.2)",
          }}
        >
          {!profilePicture && <Person />}
        </Avatar>
      </IconButton>
      <Menu
        id="menu-appbar"
        anchorEl={anchorEl}
        anchorOrigin={{
          vertical: "bottom",
          horizontal: "right",
        }}
        keepMounted
        transformOrigin={{
          vertical: "top",
          horizontal: "right",
        }}
        open={Boolean(anchorEl)}
        onClose={handleClose}
        PaperProps={{
          sx: {
            mt: 1,
            minWidth: 200,
          },
        }}
      >
        <Box sx={{ px: 2, py: 1 }}>
          <FormControlLabel
            control={<Switch checked={darkMode} onChange={toggleDarkMode} size="small" />}
            label={
              <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                {darkMode ? <Brightness7 fontSize="small" /> : <Brightness4 fontSize="small" />}
                {darkMode ? "Light Mode" : "Dark Mode"}
              </Box>
            }
          />
        </Box>
        <Divider />
        {hasRole(["admin", "company_admin", "company_developper", "company_commercial"]) && (
          <MenuItem onClick={handleAdmin}>
            <ListItemIcon>
              <AdminPanelSettings fontSize="small" />
            </ListItemIcon>
            <ListItemText>Admin</ListItemText>
          </MenuItem>
        )}
        <MenuItem onClick={handleProfile}>
          <ListItemIcon>
            <Person fontSize="small" />
          </ListItemIcon>
          <ListItemText>Profile</ListItemText>
        </MenuItem>
        <MenuItem onClick={handleLogout}>
          <ListItemIcon>
            <ExitToApp fontSize="small" />
          </ListItemIcon>
          <ListItemText>Logout</ListItemText>
        </MenuItem>
      </Menu>
    </>
  )
}

export default UserAvatar