"use client"

import { useState, useEffect, useRef } from "react"
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
  TableSortLabel,
  Tooltip,
  Menu
} from "@mui/material"
import { Add, Edit, Delete, Email, Search, Settings } from "@mui/icons-material"
import { useApi } from "../../contexts/ApiContext"
import { useAuth } from "../../contexts/AuthContext"

// ---------- Sort helpers ----------
const descendingComparator = (a, b, orderBy) => {
  let valA = ''
  let valB = ''
  if (orderBy === 'company') {
    const titlesA = Array.isArray(a.company_title) ? a.company_title.join(', ') : a.company_title || ''
    const titlesB = Array.isArray(b.company_title) ? b.company_title.join(', ') : b.company_title || ''
    valA = titlesA.toLowerCase()
    valB = titlesB.toLowerCase()
  } else {
    valA = (a[orderBy] || '').toString().toLowerCase()
    valB = (b[orderBy] || '').toString().toLowerCase()
  }
  if (valB < valA) return -1
  if (valB > valA) return 1
  return 0
}

const getComparator = (order, orderBy) => {
  return order === 'desc'
    ? (a, b) => descendingComparator(a, b, orderBy)
    : (a, b) => -descendingComparator(a, b, orderBy)
}

const stableSort = (array, comparator) => {
  const stabilized = array.map((el, index) => [el, index])
  stabilized.sort((a, b) => {
    const comp = comparator(a[0], b[0])
    if (comp !== 0) return comp
    return a[1] - b[1]
  })
  return stabilized.map((el) => el[0])
}

const UserManagement = () => {
  const { apiCall } = useApi()
  const { hasRole } = useAuth()
  const isAdmin = hasRole(["admin"])
  const canOnlyCreateClient = hasRole(["company_developper", "company_commercial"])
  const isLimitedRole = hasRole(["company_developper", "company_commercial"])
  const isCompanyAdmin = hasRole(["company_admin"])
  const isGlobalAdmin = hasRole(["admin"])

  // ---------- State ----------
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")
  const [searchTerm, setSearchTerm] = useState("")
  const [filterType, setFilterType] = useState('all_types')
  const [filterCompany, setFilterCompany] = useState('all')
  const [order, setOrder] = useState('asc')
  const [orderBy, setOrderBy] = useState('username')
  const [createDialog, setCreateDialog] = useState(false)
  const [editDialog, setEditDialog] = useState(false)
  const [deleteDialog, setDeleteDialog] = useState(false)
  const [selectedUser, setSelectedUser] = useState(null)
  const [newUser, setNewUser] = useState({ username: "", name: "", surname: "", user_type: "company_client", company_id: "" })

  // --- Admin-only dialog states ---
  const [updateEmailDialog, setUpdateEmailDialog] = useState(false)
  const [updateEmailData, setUpdateEmailData] = useState({ old_username: "", new_username: "", confirm_new_username: "" })
  const [emailError, setEmailError] = useState("")
  const [emailLoading, setEmailLoading] = useState(false)

  const [addToCompanyDialog, setAddToCompanyDialog] = useState(false)
  const [removeFromCompanyDialog, setRemoveFromCompanyDialog] = useState(false)
  const [companyActionData, setCompanyActionData] = useState({ username: "", company_id: "" })

  // --- Company search for Add/Remove Company dialogs ---
  const [companySearchTerm, setCompanySearchTerm] = useState("")
  const [companySearchLoading, setCompanySearchLoading] = useState(false)
  const [companySearchError, setCompanySearchError] = useState("")
  const [companyOptions, setCompanyOptions] = useState([])

  // For Remove dialog: keep the company IDs the user belongs to
  const removeDialogUserCompanyIds = useRef([])
  const removeDialogUserCompanyTitles = useRef([])

  // ---------- User Types ----------
  const userTypes = ["all_types", "global_admin", "company_admin", "company_client", "company_commercial", "company_developper"]
  const userTypeLabels = {
    all_types: "All Types",
    global_admin: "Global Administrator",
    admin: "Administrator",
    company_admin: "Company Administrator",
    company_client: "Client",
    company_commercial: "Company Commercial",
    company_developper: "Company Developper",
  }

  // ---------- Fetch/Search ----------
  const searchUsers = async () => {
    setLoading(true)
    setError("")
    try {
      const params = new URLSearchParams()
      if (searchTerm) params.append("searched_user", searchTerm)
      const res = await apiCall("/admin/search_user", {
        method: "POST",
        body: params.toString(),
        headers: { "Content-Type": "application/x-www-form-urlencoded" }
      })
      if (res.ok) {
        const data = await res.json()
        setUsers(data.users || [])
      } else {
        const err = await res.json()
        setError(err.detail || "Failed to search users")
      }
    } catch {
      setError("Network error. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  // ---------------- CRUD HANDLERS ----------------

  // CREATE USER (multipart/form-data)
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
      if (isGlobalAdmin && newUser.company_id) {
        formData.append("company_id", newUser.company_id)
      }

      const res = await apiCall("/admin/account_create", {
        method: "POST",
        body: formData,
      })
      if (res.ok || res.status === 201) {
        setSuccess("User created!")
        setCreateDialog(false)
        setNewUser({ username: "", name: "", surname: "", user_type: "company_client", company_id: "" })
        searchUsers()
      } else {
        const err = await res.json()
        setError(err.detail || "Failed to create user")
      }
    } catch {
      setError("Network error.")
    } finally {
      setLoading(false)
    }
  }

  // EDIT/UPDATE USER (application/x-www-form-urlencoded)
  const handleUpdateUser = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError("")
    setSuccess("")
    try {
      const params = new URLSearchParams()
      params.append("username", selectedUser.username)
      params.append("confirm_username", selectedUser.username)
      if (selectedUser.name) params.append("name", selectedUser.name)
      if (selectedUser.surname) params.append("surname", selectedUser.surname)

      const res = await apiCall("/admin/update_user_profile_info", {
        method: "POST",
        body: params.toString(),
        headers: { "Content-Type": "application/x-www-form-urlencoded" }
      })
      if (res.ok) {
        setSuccess("User updated!")
        setEditDialog(false)
        setSelectedUser(null)
        searchUsers()
      } else {
        const err = await res.json()
        setError(err.detail || "Failed to update user")
      }
    } catch {
      setError("Network error.")
    } finally {
      setLoading(false)
    }
  }

  // DELETE USER (application/x-www-form-urlencoded)
  const handleDeleteUser = async () => {
    if (!selectedUser) return
    setLoading(true)
    setError("")
    setSuccess("")
    try {
      const params = new URLSearchParams()
      params.append("username", selectedUser.username)
      params.append("confirm_username", selectedUser.username)

      const res = await apiCall("/admin/delete_user", {
        method: "POST",
        body: params.toString(),
        headers: { "Content-Type": "application/x-www-form-urlencoded" }
      })
      if (res.ok) {
        setSuccess("User deleted!")
        setDeleteDialog(false)
        setSelectedUser(null)
        searchUsers()
      } else {
        const err = await res.json()
        setError(err.detail || "Failed to delete user")
      }
    } catch {
      setError("Network error.")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { searchUsers() }, [])

  // Company options for filters
  const companyFilterOptions = Array.from(
    new Set(
      users.flatMap(u => Array.isArray(u.company_title) ? u.company_title : u.company_title ? [u.company_title] : [])
    )
  )

  // Filter and sort
  const filteredUsers = users.filter(u => {
    if (filterCompany === 'global_admin') {
      return u.user_type === 'admin' && (!u.company_id)
    }
    if (filterType === 'global_admin') {
      return u.user_type === 'admin' && (!u.company_id)
    }
    if (filterType !== 'all_types' && filterType !== 'global_admin') {
      if (u.user_type !== filterType) return false
    }
    const titles = Array.isArray(u.company_title) ? u.company_title : u.company_title ? [u.company_title] : []
    return filterCompany === 'all' || titles.includes(filterCompany)
  })

  const sortedUsers = stableSort(filteredUsers, getComparator(order, orderBy))

  const handleRequestSort = (property) => {
    const isAsc = orderBy === property && order === 'asc'
    setOrder(isAsc ? 'desc' : 'asc')
    setOrderBy(property)
  }

  // ========== Company search for Add/Remove Company dialogs ==========
  const searchCompanyOptions = async (searchTerm = "") => {
    setCompanySearchLoading(true)
    setCompanySearchError("")
    try {
      const params = new URLSearchParams()
      if (searchTerm) params.append("company_name", searchTerm)
      const res = await apiCall("/company/search", {
        method: "POST",
        body: params.toString(),
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
      })
      if (res.ok) {
        const data = await res.json()
        setCompanyOptions(data.companies || [])
      } else {
        setCompanyOptions([])
        setCompanySearchError("Error searching companies")
      }
    } catch {
      setCompanyOptions([])
      setCompanySearchError("Network error while searching companies")
    } finally {
      setCompanySearchLoading(false)
    }
  }

  const searchRemoveCompanyOptions = async (searchTerm = "") => {
    setCompanySearchLoading(true)
    setCompanySearchError("")
    try {
      const params = new URLSearchParams()
      if (searchTerm) params.append("company_name", searchTerm)
      const res = await apiCall("/company/search", {
        method: "POST",
        body: params.toString(),
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
      })
      if (res.ok) {
        const data = await res.json()
        const allowedIds = removeDialogUserCompanyIds.current
        const allowedTitles = removeDialogUserCompanyTitles.current
        const filtered = (data.companies || []).filter(c =>
          allowedIds.includes(c.company_id) ||
          allowedTitles.includes(c.company_name)
        )
        setCompanyOptions(filtered)
      } else {
        setCompanyOptions([])
        setCompanySearchError("Error searching companies")
      }
    } catch {
      setCompanyOptions([])
      setCompanySearchError("Network error while searching companies")
    } finally {
      setCompanySearchLoading(false)
    }
  }

  useEffect(() => {
    if (addToCompanyDialog) {
      searchCompanyOptions(companySearchTerm)
      setCompanyActionData((prev) => ({ ...prev, company_id: "" }))
    }
    if (removeFromCompanyDialog) {
      searchRemoveCompanyOptions("")
      setCompanyActionData((prev) => ({ ...prev, company_id: "" }))
    }
    setCompanySearchTerm("")
    setCompanySearchError("")
  }, [addToCompanyDialog, removeFromCompanyDialog])

  useEffect(() => {
    const timeout = setTimeout(() => {
      if (addToCompanyDialog) {
        searchCompanyOptions(companySearchTerm)
      } else if (removeFromCompanyDialog) {
        searchRemoveCompanyOptions(companySearchTerm)
      }
    }, 300)
    return () => clearTimeout(timeout)
  }, [companySearchTerm, addToCompanyDialog, removeFromCompanyDialog])

  // ===== Gear menu state =====
  const [gearMenuAnchor, setGearMenuAnchor] = useState(null)
  const [gearMenuUser, setGearMenuUser] = useState(null)

  const handleOpenGearMenu = (event, user) => {
    setGearMenuAnchor(event.currentTarget)
    setGearMenuUser(user)
  }
  const handleCloseGearMenu = () => {
    setGearMenuAnchor(null)
    setGearMenuUser(null)
  }

  // ---------------- UI ----------------
  return (
    <Box>
      <Typography variant="h5" gutterBottom fontWeight="bold">User Management</Typography>
      {error && <Alert severity="error" sx={{ mb: 2, borderRadius: 2 }}>{error}</Alert>}
      {success && <Alert severity="success" sx={{ mb: 2, borderRadius: 2 }}>{success}</Alert>}

      {/* Controls */}
      <Card sx={{ mb: 3, borderRadius: 2 }}>
        <CardContent>
          <Box sx={{ display: "flex", gap: 2, flexWrap: "wrap", alignItems: "center" }}>
            <FormControl size="small" sx={{ minWidth: 180 }}>
              <InputLabel>User Type</InputLabel>
              <Select
                value={filterType}
                label="User Type"
                onChange={e => setFilterType(e.target.value)}
              >
                {userTypes.map(t => (
                  <MenuItem key={t} value={t}>{userTypeLabels[t]}</MenuItem>
                ))}
              </Select>
            </FormControl>
            <FormControl size="small" sx={{ minWidth: 180 }}>
              <InputLabel>Company</InputLabel>
              <Select
                value={filterCompany}
                label="Company"
                onChange={e => setFilterCompany(e.target.value)}
              >
                <MenuItem value="all">All Companies</MenuItem>
                <MenuItem value="global_admin">Global Administrators</MenuItem>
                {companyFilterOptions.map(c => (
                  <MenuItem key={c} value={c}>{c}</MenuItem>
                ))}
              </Select>
            </FormControl>
            <TextField
              label="Search users"
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
              placeholder="Email, name, or surname"
              size="small"
              onKeyPress={e => e.key === 'Enter' && searchUsers()}
              sx={{ minWidth: 300 }}
            />
            <Box sx={{ flexGrow: 1 }} />
            <Button
              variant="contained"
              startIcon={<Search />}
              onClick={searchUsers}
              disabled={loading}
              sx={{ borderRadius: 2, textTransform: "none", height: 40, minWidth: 120 }}
            >Search</Button>
            <Button
              variant="contained"
              startIcon={<Add />}
              onClick={() => setCreateDialog(true)}
              sx={{ borderRadius: 2, textTransform: "none", height: 40, minWidth: 120 }}
            >Create User</Button>
          </Box>
        </CardContent>
      </Card>

      <TableContainer component={Paper} sx={{ borderRadius: 2 }}>
        <Table>
          <TableHead sx={{ backgroundColor: 'background.paper' }}>
            <TableRow>
              {[
                { id: 'username', label: 'Email' },
                { id: 'name', label: 'Name' },
                { id: 'surname', label: 'Surname' },
                { id: 'user_type', label: 'Type' },
                { id: 'company', label: 'Company' },
              ].map(headCell => (
                <TableCell key={headCell.id} sortDirection={orderBy === headCell.id ? order : false} sx={{ fontWeight: 'bold' }}>
                  <TableSortLabel
                    active={orderBy === headCell.id}
                    direction={orderBy === headCell.id ? order : 'asc'}
                    onClick={() => handleRequestSort(headCell.id)}
                  >{headCell.label}</TableSortLabel>
                </TableCell>
              ))}
              {!canOnlyCreateClient && (
                <TableCell sx={{ fontWeight: 'bold' }}>Actions</TableCell>
              )}
            </TableRow>
          </TableHead>
          <TableBody>
            {sortedUsers.length === 0 ? (
              <TableRow><TableCell colSpan={6} align="center"><Typography>{loading ? 'Loading...' : 'No users found'}</Typography></TableCell></TableRow>
            ) : (
              sortedUsers.map((user, i) => {
                const titles = Array.isArray(user.company_title) ? user.company_title : user.company_title ? [user.company_title] : []
                const displayType = (user.user_type === 'admin' && (!user.company_id || user.company_id === null))
                  ? 'Global Administrator' : userTypeLabels[user.user_type] || user.user_type
                return (
                  <TableRow key={user.id || i} hover>
                    <TableCell>{user.username}</TableCell>
                    <TableCell>{user.name}</TableCell>
                    <TableCell>{user.surname}</TableCell>
                    <TableCell><Chip label={displayType} size="small" variant="outlined" /></TableCell>
                    <TableCell>
                      {titles.length ? titles.map((t, idx) => (
                        <Chip key={idx} label={t} size="small" variant="outlined" sx={{ mr: 0.5, mb: 0.5 }} />
                      )) : '–'}
                    </TableCell>
                    {!canOnlyCreateClient && (
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 1 }}>
                          {/* Your action buttons here, as previously filtered */}
                          <Tooltip title="Edit">
                            <IconButton color="success" onClick={() => { setSelectedUser(user); setEditDialog(true) }}>
                              <Edit />
                            </IconButton>
                          </Tooltip>
                          {isAdmin && (
                            <Tooltip title="More actions">
                              <IconButton color="primary" onClick={e => handleOpenGearMenu(e, user)}>
                                <Settings />
                              </IconButton>
                            </Tooltip>
                          )}
                          <Tooltip title="Delete">
                            <IconButton color="error" onClick={() => { setSelectedUser(user); setDeleteDialog(true) }}>
                              <Delete />
                            </IconButton>
                          </Tooltip>
                        </Box>
                      </TableCell>
                    )}
                  </TableRow>
                )
              })
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* GEAR MENU */}
      <Menu
        anchorEl={gearMenuAnchor}
        open={Boolean(gearMenuAnchor)}
        onClose={handleCloseGearMenu}
      >
        <MenuItem
          onClick={() => {
            setUpdateEmailData({
              old_username: gearMenuUser?.username || "",
              new_username: "",
              confirm_new_username: ""
            })
            setEmailError("")
            setUpdateEmailDialog(true)
            handleCloseGearMenu()
          }}
        >
          <Email sx={{ mr: 1 }} /> Change Email
        </MenuItem>
        {gearMenuUser?.user_type === "company_client" && (
          [
            <MenuItem
              key="add"
              onClick={() => {
                setCompanyActionData({ username: gearMenuUser.username, company_id: "" })
                setAddToCompanyDialog(true)
                handleCloseGearMenu()
              }}
            >
              <Add sx={{ mr: 1 }} /> Add to Company
            </MenuItem>,
            <MenuItem
              key="remove"
              onClick={() => {
                let userCompanyIds = []
                let userCompanyTitles = []
                if (Array.isArray(gearMenuUser.company_id)) {
                  userCompanyIds = gearMenuUser.company_id
                } else if (gearMenuUser.company_id) {
                  userCompanyIds = [gearMenuUser.company_id]
                }
                if (Array.isArray(gearMenuUser.company_title)) {
                  userCompanyTitles = gearMenuUser.company_title
                } else if (gearMenuUser.company_title) {
                  userCompanyTitles = [gearMenuUser.company_title]
                }
                removeDialogUserCompanyIds.current = userCompanyIds
                removeDialogUserCompanyTitles.current = userCompanyTitles
                setCompanyActionData({ username: gearMenuUser.username, company_id: "" })
                setRemoveFromCompanyDialog(true)
                handleCloseGearMenu()
              }}
            >
              <Delete sx={{ mr: 1 }} color="error" /> Remove from Company
            </MenuItem>
          ]
        )}
      </Menu>

      {/* Create User Dialog */}
      <Dialog open={createDialog} onClose={() => setCreateDialog(false)} maxWidth="sm" fullWidth PaperProps={{ sx: { borderRadius: 3 } }}>
        <form onSubmit={handleCreateUser}>
          <DialogTitle><Typography variant="h5" fontWeight="bold">Create New User</Typography></DialogTitle>
          <DialogContent>
            <TextField margin="normal" fullWidth label="Email" type="email" value={newUser.username} onChange={(e) => setNewUser({ ...newUser, username: e.target.value })} required />
            <TextField margin="normal" fullWidth label="First Name" value={newUser.name} onChange={(e) => setNewUser({ ...newUser, name: e.target.value })} required />
            <TextField margin="normal" fullWidth label="Last Name" value={newUser.surname} onChange={(e) => setNewUser({ ...newUser, surname: e.target.value })} required />
            {/* User Type Dropdown */}
            <FormControl fullWidth margin="normal">
              <InputLabel>User Type</InputLabel>
              <Select
                value={newUser.user_type}
                onChange={(e) => setNewUser({ ...newUser, user_type: e.target.value })}
                label="User Type"
              >
                {canOnlyCreateClient ? (
                  <MenuItem value="company_client">{userTypeLabels["company_client"]}</MenuItem>
                ) : isCompanyAdmin ? (
                  userTypes
                    .filter(type => type !== "all_types" && type !== "global_admin")
                    .map(type => (
                      <MenuItem key={type} value={type}>
                        {userTypeLabels[type]}
                      </MenuItem>
                    ))
                ) : (
                  userTypes
                    .filter(type => type !== "all_types")
                    .map(type => (
                      <MenuItem key={type} value={type}>
                        {userTypeLabels[type]}
                      </MenuItem>
                    ))
                )}
              </Select>
            </FormControl>
            {/* Company ID field is visible ONLY for logged-in Global Admins */}
            {isGlobalAdmin && (
              <TextField
                margin="normal"
                fullWidth
                label="Company ID"
                type="number"
                value={newUser.company_id}
                onChange={(e) => setNewUser({ ...newUser, company_id: e.target.value })}
              />
            )}
          </DialogContent>
          <DialogActions sx={{ p: 3 }}><Button onClick={() => setCreateDialog(false)}>Cancel</Button><Button type="submit" variant="contained" disabled={loading}>{loading ? <CircularProgress size={24} /> : "Create"}</Button></DialogActions>
        </form>
      </Dialog>

      {/* Edit User Dialog */}
      <Dialog open={editDialog} onClose={() => setEditDialog(false)} maxWidth="sm" fullWidth PaperProps={{ sx: { borderRadius: 3 } }}>
        <form onSubmit={handleUpdateUser}>
          <DialogTitle><Typography variant="h5" fontWeight="bold">Edit User</Typography></DialogTitle>
          <DialogContent>{selectedUser && (<>
            <TextField margin="normal" fullWidth label="Email" value={selectedUser.username} disabled />
            <TextField margin="normal" fullWidth label="First Name" value={selectedUser.name} onChange={(e) => setSelectedUser({ ...selectedUser, name: e.target.value })} required />
            <TextField margin="normal" fullWidth label="Last Name" value={selectedUser.surname} onChange={(e) => setSelectedUser({ ...selectedUser, surname: e.target.value })} required />
          </>)}
          </DialogContent>
          <DialogActions sx={{ p: 3 }}><Button onClick={() => setEditDialog(false)}>Cancel</Button><Button type="submit" variant="contained" disabled={loading}>{loading ? <CircularProgress size={24} /> : "Update"}</Button></DialogActions>
        </form>
      </Dialog>

      {/* Delete User Dialog */}
      <Dialog open={deleteDialog} onClose={() => setDeleteDialog(false)} PaperProps={{ sx: { borderRadius: 3 } }}>
        <DialogTitle><Typography variant="h5" fontWeight="bold">Delete User</Typography></DialogTitle>
        <DialogContent><Typography>Are you sure you want to delete user <strong>{selectedUser?.username}</strong>? This action cannot be undone.</Typography></DialogContent>
        <DialogActions sx={{ p: 3 }}><Button onClick={() => setDeleteDialog(false)}>Cancel</Button><Button onClick={handleDeleteUser} color="error" variant="contained" disabled={loading}>{loading ? <CircularProgress size={24} /> : "Delete"}</Button></DialogActions>
      </Dialog>

      {/* ----------- ADMIN DIALOGS ----------- */}
      {/* Update Email Dialog */}
      <Dialog
        open={updateEmailDialog}
        onClose={() => {
          setUpdateEmailDialog(false)
          setEmailError("")
        }}
        maxWidth="sm"
        fullWidth
        PaperProps={{ sx: { borderRadius: 3 } }}
      >
        <form
          onSubmit={async (e) => {
            e.preventDefault()
            setEmailLoading(true)
            setEmailError("")
            if (!updateEmailData.new_username || !updateEmailData.confirm_new_username) {
              setEmailError("Both email fields are required.")
              setEmailLoading(false)
              return
            }
            if (updateEmailData.new_username !== updateEmailData.confirm_new_username) {
              setEmailError("Emails do not match.")
              setEmailLoading(false)
              return
            }
            try {
              const params = new URLSearchParams()
              params.append("old_username", updateEmailData.old_username)
              params.append("new_username", updateEmailData.new_username)
              params.append("confirm_new_username", updateEmailData.confirm_new_username)
              const res = await apiCall("/admin/update_username", {
                method: "POST",
                body: params.toString(),
                headers: { "Content-Type": "application/x-www-form-urlencoded" },
              })
              if (res.ok) {
                setSuccess("Email updated!")
                setUpdateEmailDialog(false)
                setEmailError("")
                searchUsers()
              } else {
                const err = await res.json()
                setEmailError(err.detail || "Failed to update email")
              }
            } catch {
              setEmailError("Network error.")
            } finally {
              setEmailLoading(false)
            }
          }}
        >
          <DialogTitle>
            <Typography variant="h5" fontWeight="bold">
              Update User Email
            </Typography>
          </DialogTitle>
          <DialogContent>
            <Typography variant="subtitle1" fontWeight="medium" sx={{ mb: 2 }}>
              Change login email for <b>{updateEmailData.old_username}</b>
            </Typography>
            {emailError && (
              <Alert severity="error" sx={{ mb: 2, borderRadius: 2 }}>
                {emailError}
              </Alert>
            )}
            <TextField
              label="New Email"
              type="email"
              fullWidth
              required
              margin="normal"
              value={updateEmailData.new_username}
              onChange={(e) =>
                setUpdateEmailData((data) => ({
                  ...data,
                  new_username: e.target.value,
                }))
              }
              autoFocus
            />
            <TextField
              label="Confirm New Email"
              type="email"
              fullWidth
              required
              margin="normal"
              value={updateEmailData.confirm_new_username}
              onChange={(e) =>
                setUpdateEmailData((data) => ({
                  ...data,
                  confirm_new_username: e.target.value,
                }))
              }
            />
          </DialogContent>
          <DialogActions sx={{ p: 3 }}>
            <Button
              onClick={() => {
                setUpdateEmailDialog(false)
                setEmailError("")
              }}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="contained"
              disabled={emailLoading}
            >
              {emailLoading ? <CircularProgress size={24} /> : "Update"}
            </Button>
          </DialogActions>
        </form>
      </Dialog>

      {/* Add To Company Dialog */}
      <Dialog open={addToCompanyDialog} onClose={() => setAddToCompanyDialog(false)} maxWidth="sm" fullWidth PaperProps={{ sx: { borderRadius: 3 } }}>
        <form onSubmit={async e => {
          e.preventDefault()
          setLoading(true)
          setError("")
          try {
            const params = new URLSearchParams()
            params.append("username", companyActionData.username)
            params.append("confirm_username", companyActionData.username)
            params.append("company_id", companyActionData.company_id)
            const res = await apiCall("/admin/add_client_user_to_company", {
              method: "POST",
              body: params.toString(),
              headers: { "Content-Type": "application/x-www-form-urlencoded" }
            })
            if (res.ok) {
              setSuccess("User added to company!")
              setAddToCompanyDialog(false)
              searchUsers()
            } else {
              const err = await res.json()
              setError(err.detail || "Failed to add to company")
            }
          } catch {
            setError("Network error.")
          } finally {
            setLoading(false)
          }
        }}>
          <DialogTitle>
            <Typography variant="h5" fontWeight="bold">
              Add User to Company
            </Typography>
          </DialogTitle>
          <DialogContent>
            <Typography variant="subtitle1" fontWeight="medium" sx={{ mb: 2 }}>
              Add <b>{companyActionData.username}</b> to a company
            </Typography>
            {error && (
              <Alert severity="error" sx={{ mb: 2, borderRadius: 2 }}>
                {error}
              </Alert>
            )}
            <TextField
              label="Search companies"
              value={companySearchTerm}
              onChange={e => setCompanySearchTerm(e.target.value)}
              placeholder="Company name or leave empty"
              fullWidth
              size="small"
              margin="dense"
              disabled={companySearchLoading}
              autoFocus
              sx={{ mb: 2 }}
            />
            <FormControl fullWidth margin="normal" required>
              <InputLabel>Select Company</InputLabel>
              <Select
                label="Select Company"
                value={companyActionData.company_id}
                onChange={e => setCompanyActionData(data => ({ ...data, company_id: e.target.value }))}
                disabled={companySearchLoading}
              >
                {companyOptions.length === 0 && (
                  <MenuItem value="" disabled>
                    {companySearchLoading ? "Loading..." : "No companies found"}
                  </MenuItem>
                )}
                {companyOptions.map((company) => (
                  <MenuItem key={company.company_id} value={company.company_id}>
                    {company.company_name || `Company #${company.company_id}`}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            {companySearchError && (
              <Alert severity="error" sx={{ mt: 1 }}>
                {companySearchError}
              </Alert>
            )}
          </DialogContent>
          <DialogActions sx={{ p: 3 }}>
            <Button onClick={() => setAddToCompanyDialog(false)}>Cancel</Button>
            <Button type="submit" variant="contained" disabled={loading || companySearchLoading || !companyActionData.company_id}>
              {loading ? <CircularProgress size={24} /> : "Add"}
            </Button>
          </DialogActions>
        </form>
      </Dialog>

      {/* Remove From Company Dialog */}
      <Dialog open={removeFromCompanyDialog} onClose={() => setRemoveFromCompanyDialog(false)} maxWidth="sm" fullWidth PaperProps={{ sx: { borderRadius: 3 } }}>
        <form onSubmit={async e => {
          e.preventDefault()
          setLoading(true)
          setError("")
          try {
            const params = new URLSearchParams()
            params.append("username", companyActionData.username)
            params.append("confirm_username", companyActionData.username)
            params.append("company_id", companyActionData.company_id)
            const res = await apiCall("/admin/remove_client_user_from_company", {
              method: "POST",
              body: params.toString(),
              headers: { "Content-Type": "application/x-www-form-urlencoded" }
            })
            if (res.ok) {
              setSuccess("User removed from company!")
              setRemoveFromCompanyDialog(false)
              searchUsers()
            } else {
              const err = await res.json()
              setError(err.detail || "Failed to remove from company")
            }
          } catch {
            setError("Network error.")
          } finally {
            setLoading(false)
          }
        }}>
          <DialogTitle>
            <Typography variant="h5" fontWeight="bold">
              Remove User from Company
            </Typography>
          </DialogTitle>
          <DialogContent>
            <Typography variant="subtitle1" fontWeight="medium" sx={{ mb: 2 }}>
              Remove <b>{companyActionData.username}</b> from a company
            </Typography>
            {error && (
              <Alert severity="error" sx={{ mb: 2, borderRadius: 2 }}>
                {error}
              </Alert>
            )}
            <TextField
              label="Search companies"
              value={companySearchTerm}
              onChange={e => setCompanySearchTerm(e.target.value)}
              placeholder="Company name or leave empty"
              fullWidth
              size="small"
              margin="dense"
              disabled={companySearchLoading}
              autoFocus
              sx={{ mb: 2 }}
            />
            <FormControl fullWidth margin="normal" required>
              <InputLabel>Select Company</InputLabel>
              <Select
                label="Select Company"
                value={companyActionData.company_id}
                onChange={e => setCompanyActionData(data => ({ ...data, company_id: e.target.value }))}
                disabled={companySearchLoading}
              >
                {companyOptions.length === 0 && (
                  <MenuItem value="" disabled>
                    {companySearchLoading ? "Loading..." : "No companies found"}
                  </MenuItem>
                )}
                {companyOptions.map((company) => (
                  <MenuItem key={company.company_id} value={company.company_id}>
                    {company.company_name || `Company #${company.company_id}`}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            {companySearchError && (
              <Alert severity="error" sx={{ mt: 1 }}>
                {companySearchError}
              </Alert>
            )}
          </DialogContent>
          <DialogActions sx={{ p: 3 }}>
            <Button onClick={() => setRemoveFromCompanyDialog(false)}>Cancel</Button>
            <Button type="submit" variant="contained" color="error" disabled={loading || companySearchLoading || !companyActionData.company_id}>
              {loading ? <CircularProgress size={24} /> : "Remove"}
            </Button>
          </DialogActions>
        </form>
      </Dialog>
    </Box>
  )
}

export default UserManagement