"use client"

import { useState, useEffect } from "react"
import {
  Box,
  Typography,
  TextField,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  CircularProgress,
  IconButton,
  Chip,
  Card,
  CardContent,
} from "@mui/material"
import { Add, Edit, Delete, Search } from "@mui/icons-material"
import { useApi } from "../../contexts/ApiContext"

const UserManagement = () => {
  const [users, setUsers] = useState([])
  const [searchTerm, setSearchTerm] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")
  const [createDialog, setCreateDialog] = useState(false)
  const [editDialog, setEditDialog] = useState(false)
  const [deleteDialog, setDeleteDialog] = useState(false)
  const [selectedUser, setSelectedUser] = useState(null)
  const [newUser, setNewUser] = useState({
    username: "",
    name: "",
    surname: "",
    user_type: "company_client",
    company_id: "",
  })
  const { apiCall } = useApi()

  // Exclude 'basic' from user types
  const userTypes = ["admin", "company_admin", "company_client", "company_commercial", "company_developper"]

  const searchUsers = async () => {
    setLoading(true)
    setError("")

    try {
      const requestBody = searchTerm ? { searched_user: searchTerm } : {}

      const response = await apiCall("/admin/search_user", {
        method: "POST",
        body: JSON.stringify(requestBody),
        headers: {
          "Content-Type": "application/json",
        },
      })

      if (response.ok) {
        const data = await response.json()
        console.log("API Response:", data) // Debug log
        // Handle the correct API response format
        const users = data.users || []
        setUsers(users)
      } else {
        const errorData = await response.json()
        setError(errorData.detail || "Failed to search users")
      }
    } catch (err) {
      setError("Network error. Please try again.")
      console.error("Search error:", err)
    } finally {
      setLoading(false)
    }
  }

  const handleCreateUser = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError("")
    setSuccess("")

    try {
      const formData = new FormData()
      formData.append("username", newUser.username)
      formData.append("name", newUser.name)
      formData.append("surname", newUser.surname)
      formData.append("user_type", newUser.user_type)
      if (newUser.company_id) {
        formData.append("company_id", newUser.company_id)
      }

      const response = await apiCall("/admin/account_create", {
        method: "POST",
        body: formData,
      })

      if (response.ok) {
        setSuccess("User created successfully")
        setCreateDialog(false)
        setNewUser({
          username: "",
          name: "",
          surname: "",
          user_type: "company_client",
          company_id: "",
        })
        searchUsers()
      } else {
        const errorData = await response.json()
        setError(errorData.detail || "Failed to create user")
      }
    } catch (err) {
      setError("Network error. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  const handleDeleteUser = async () => {
    if (!selectedUser) return

    setLoading(true)
    setError("")
    setSuccess("")

    try {
      const formData = new FormData()
      formData.append("username", selectedUser.username)
      formData.append("confirm_username", selectedUser.username)

      const response = await apiCall("/admin/delete_user", {
        method: "POST",
        body: formData,
      })

      if (response.ok) {
        setSuccess("User deleted successfully")
        setDeleteDialog(false)
        setSelectedUser(null)
        searchUsers()
      } else {
        const errorData = await response.json()
        setError(errorData.detail || "Failed to delete user")
      }
    } catch (err) {
      setError("Network error. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  const handleUpdateUser = async (e) => {
    e.preventDefault()
    if (!selectedUser) return

    setLoading(true)
    setError("")
    setSuccess("")

    try {
      const formData = new FormData()
      formData.append("username", selectedUser.username)
      formData.append("confirm_username", selectedUser.username)
      formData.append("name", selectedUser.name)
      formData.append("surname", selectedUser.surname)

      const response = await apiCall("/admin/update_user_profile_info", {
        method: "POST",
        body: formData,
      })

      if (response.ok) {
        setSuccess("User updated successfully")
        setEditDialog(false)
        setSelectedUser(null)
        searchUsers()
      } else {
        const errorData = await response.json()
        setError(errorData.detail || "Failed to update user")
      }
    } catch (err) {
      setError("Network error. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    searchUsers()
  }, [])

  return (
    <Box>
      <Typography variant="h5" gutterBottom fontWeight="bold">
        User Management
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2, borderRadius: 2 }}>
          {error}
        </Alert>
      )}
      {success && (
        <Alert severity="success" sx={{ mb: 2, borderRadius: 2 }}>
          {success}
        </Alert>
      )}

      <Card sx={{ mb: 3, borderRadius: 2 }}>
        <CardContent>
          <Box sx={{ display: "flex", gap: 2, alignItems: "center", flexWrap: "wrap" }}>
            <TextField
              label="Search users"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Email, name, or surname"
              sx={{ flexGrow: 1, minWidth: 200 }}
              variant="outlined"
              size="small"
              onKeyPress={(e) => {
                if (e.key === "Enter") {
                  searchUsers()
                }
              }}
            />
            <Button
              variant="outlined"
              startIcon={<Search />}
              onClick={searchUsers}
              disabled={loading}
              sx={{ borderRadius: 2 }}
            >
              Search
            </Button>
            <Button
              variant="contained"
              startIcon={<Add />}
              onClick={() => setCreateDialog(true)}
              sx={{ borderRadius: 2 }}
            >
              Create User
            </Button>
          </Box>
        </CardContent>
      </Card>

      <TableContainer component={Paper} sx={{ borderRadius: 2 }}>
        <Table>
          <TableHead>
            <TableRow sx={{ bgcolor: "grey.50" }}>
              <TableCell sx={{ fontWeight: "bold" }}>Email</TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>Name</TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>Surname</TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>Type</TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {users.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} align="center" sx={{ py: 4 }}>
                  <Typography color="text.secondary">{loading ? "Loading..." : "No users found"}</Typography>
                </TableCell>
              </TableRow>
            ) : (
              users.map((user, index) => (
                <TableRow key={user.id || index} hover>
                  <TableCell>{user.username}</TableCell>
                  <TableCell>{user.name}</TableCell>
                  <TableCell>{user.surname}</TableCell>
                  <TableCell>
                    <Chip label={user.user_type} size="small" color="primary" variant="outlined" />
                  </TableCell>
                  <TableCell>
                    <IconButton
                      onClick={() => {
                        setSelectedUser(user)
                        setEditDialog(true)
                      }}
                      color="primary"
                    >
                      <Edit />
                    </IconButton>
                    <IconButton
                      onClick={() => {
                        setSelectedUser(user)
                        setDeleteDialog(true)
                      }}
                      color="error"
                    >
                      <Delete />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Create User Dialog */}
      <Dialog
        open={createDialog}
        onClose={() => setCreateDialog(false)}
        maxWidth="sm"
        fullWidth
        PaperProps={{ sx: { borderRadius: 3 } }}
      >
        <form onSubmit={handleCreateUser}>
          <DialogTitle>
            <Typography variant="h5" fontWeight="bold">
              Create New User
            </Typography>
          </DialogTitle>
          <DialogContent>
            <TextField
              margin="normal"
              fullWidth
              label="Email"
              type="email"
              value={newUser.username}
              onChange={(e) => setNewUser({ ...newUser, username: e.target.value })}
              variant="outlined"
              required
            />
            <TextField
              margin="normal"
              fullWidth
              label="First Name"
              value={newUser.name}
              onChange={(e) => setNewUser({ ...newUser, name: e.target.value })}
              variant="outlined"
              required
            />
            <TextField
              margin="normal"
              fullWidth
              label="Last Name"
              value={newUser.surname}
              onChange={(e) => setNewUser({ ...newUser, surname: e.target.value })}
              variant="outlined"
              required
            />
            <FormControl fullWidth margin="normal" variant="outlined">
              <InputLabel>User Type</InputLabel>
              <Select
                value={newUser.user_type}
                onChange={(e) => setNewUser({ ...newUser, user_type: e.target.value })}
                label="User Type"
              >
                {userTypes.map((type) => (
                  <MenuItem key={type} value={type}>
                    {type.replace("_", " ").replace(/\b\w/g, (l) => l.toUpperCase())}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <TextField
              margin="normal"
              fullWidth
              label="Company ID (optional)"
              type="number"
              value={newUser.company_id}
              onChange={(e) => setNewUser({ ...newUser, company_id: e.target.value })}
              variant="outlined"
            />
          </DialogContent>
          <DialogActions sx={{ p: 3 }}>
            <Button onClick={() => setCreateDialog(false)} sx={{ borderRadius: 2 }}>
              Cancel
            </Button>
            <Button type="submit" variant="contained" disabled={loading} sx={{ borderRadius: 2 }}>
              {loading ? <CircularProgress size={24} /> : "Create"}
            </Button>
          </DialogActions>
        </form>
      </Dialog>

      {/* Edit User Dialog */}
      <Dialog
        open={editDialog}
        onClose={() => setEditDialog(false)}
        maxWidth="sm"
        fullWidth
        PaperProps={{ sx: { borderRadius: 3 } }}
      >
        <form onSubmit={handleUpdateUser}>
          <DialogTitle>
            <Typography variant="h5" fontWeight="bold">
              Edit User
            </Typography>
          </DialogTitle>
          <DialogContent>
            {selectedUser && (
              <>
                <TextField
                  margin="normal"
                  fullWidth
                  label="Email"
                  value={selectedUser.username}
                  disabled
                  variant="outlined"
                />
                <TextField
                  margin="normal"
                  fullWidth
                  label="First Name"
                  value={selectedUser.name}
                  onChange={(e) => setSelectedUser({ ...selectedUser, name: e.target.value })}
                  variant="outlined"
                  required
                />
                <TextField
                  margin="normal"
                  fullWidth
                  label="Last Name"
                  value={selectedUser.surname}
                  onChange={(e) => setSelectedUser({ ...selectedUser, surname: e.target.value })}
                  variant="outlined"
                  required
                />
              </>
            )}
          </DialogContent>
          <DialogActions sx={{ p: 3 }}>
            <Button onClick={() => setEditDialog(false)} sx={{ borderRadius: 2 }}>
              Cancel
            </Button>
            <Button type="submit" variant="contained" disabled={loading} sx={{ borderRadius: 2 }}>
              {loading ? <CircularProgress size={24} /> : "Update"}
            </Button>
          </DialogActions>
        </form>
      </Dialog>

      {/* Delete User Dialog */}
      <Dialog open={deleteDialog} onClose={() => setDeleteDialog(false)} PaperProps={{ sx: { borderRadius: 3 } }}>
        <DialogTitle>
          <Typography variant="h5" fontWeight="bold">
            Delete User
          </Typography>
        </DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete user <strong>{selectedUser?.username}</strong>? This action cannot be
            undone.
          </Typography>
        </DialogContent>
        <DialogActions sx={{ p: 3 }}>
          <Button onClick={() => setDeleteDialog(false)} sx={{ borderRadius: 2 }}>
            Cancel
          </Button>
          <Button
            onClick={handleDeleteUser}
            color="error"
            variant="contained"
            disabled={loading}
            sx={{ borderRadius: 2 }}
          >
            {loading ? <CircularProgress size={24} /> : "Delete"}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

export default UserManagement