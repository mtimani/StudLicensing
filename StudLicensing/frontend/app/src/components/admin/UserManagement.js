"use client"

import { useState, useEffect, useRef, useMemo } from "react"
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
  Menu,
} from "@mui/material"
import { Add, Edit, Delete, Email, Settings } from "@mui/icons-material"
import Autocomplete from "@mui/material/Autocomplete"
import { useApi } from "../../contexts/ApiContext"
import { useAuth } from "../../contexts/AuthContext"

// ---------- Sort helpers ----------
const descendingComparator = (a, b, orderBy) => {
  let valA = ""
  let valB = ""
  if (orderBy === "company") {
    const titlesA = Array.isArray(a.company_title) ? a.company_title.join(", ") : a.company_title || ""
    const titlesB = Array.isArray(b.company_title) ? b.company_title.join(", ") : b.company_title || ""
    valA = titlesA.toLowerCase()
    valB = titlesB.toLowerCase()
  } else {
    valA = (a[orderBy] || "").toString().toLowerCase()
    valB = (b[orderBy] || "").toString().toLowerCase()
  }
  if (valB < valA) return -1
  if (valB > valA) return 1
  return 0
}

const getComparator = (order, orderBy) => {
  return order === "desc"
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

const clearMessageAfterTimeout = (setMessageFn, timeoutRef, setTimeoutRef) => {
  if (timeoutRef) {
    clearTimeout(timeoutRef)
  }
  const timeout = setTimeout(() => {
    setMessageFn("")
    setTimeoutRef(null)
  }, 10000)
  setTimeoutRef(timeout)
}

const UserManagement = () => {
  const { apiCall } = useApi()
  const { hasRole } = useAuth()
  const isAdmin = hasRole(["admin"])
  const canOnlyCreateClient = hasRole(["company_developper", "company_commercial"])
  // Remove the unused variable
  // const isLimitedRole = hasRole(["company_developper", "company_commercial"])
  const isCompanyAdmin = hasRole(["company_admin"])
  const isGlobalAdmin = hasRole(["admin"])

  // ---------- State ----------
  const [allUsers, setAllUsers] = useState([]) // Store all users from API
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")
  const [searchTerm, setSearchTerm] = useState("")
  const [filterType, setFilterType] = useState("all_types")
  const [filterCompany, setFilterCompany] = useState("all")
  const [order, setOrder] = useState("asc")
  const [orderBy, setOrderBy] = useState("username")
  const [createDialog, setCreateDialog] = useState(false)
  const [editDialog, setEditDialog] = useState(false)
  const [deleteDialog, setDeleteDialog] = useState(false)
  const [selectedUser, setSelectedUser] = useState(null)
  const defaultUserType = isGlobalAdmin ? "admin" : "company_client"
  const [newUser, setNewUser] = useState({
    username: "",
    name: "",
    surname: "",
    user_type: defaultUserType,
    company_id: "", // This will now store the selected company's ID
  })

  // Use ref to prevent duplicate API calls
  const usersLoaded = useRef(false)
  const usersLoading = useRef(false)

  // --- Admin-only dialog states ---
  const [updateEmailDialog, setUpdateEmailDialog] = useState(false)
  const [updateEmailData, setUpdateEmailData] = useState({
    old_username: "",
    new_username: "",
    confirm_new_username: "",
  })
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

  // For Remove/Add dialogs: keep the company IDs the user belongs/doesn't belong to
  const removeDialogUserCompanyIds = useRef([])
  const removeDialogUserCompanyTitles = useRef([])
  const addDialogUserCompanyIds = useRef([])
  const addDialogUserCompanyTitles = useRef([])

  // Local filtering for add user to company
  const [filteredCompanyOptions, setFilteredCompanyOptions] = useState([])

  const [createError, setCreateError] = useState("")
  const [editError, setEditError] = useState("")
  const [createErrorTimeout, setCreateErrorTimeout] = useState(null)
  const [editErrorTimeout, setEditErrorTimeout] = useState(null)
  const [successTimeout, setSuccessTimeout] = useState(null)

  // ---------- User Types ----------
  const userTypes = [
    "all_types",
    "global_admin",
    "company_admin",
    "company_client",
    "company_commercial",
    "company_developper",
  ]
  const userTypeLabels = {
    all_types: "All Types",
    global_admin: "Global Administrator",
    admin: "Administrator",
    company_admin: "Company Administrator",
    company_client: "Client",
    company_commercial: "Company Commercial",
    company_developper: "Company Developper",
  }

  // ---------- Fetch Users (only called once and after CRUD operations) ----------
  const fetchAllUsers = async () => {
    if (usersLoaded.current || usersLoading.current) return

    usersLoading.current = true
    setLoading(true)
    setError("")
    try {
      const params = new URLSearchParams()
      const response = await apiCall("/admin/search_user", {
        method: "POST",
        body: params.toString(),
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
      })
      if (response.ok) {
        const data = await response.json()
        setAllUsers(data.users || [])
        usersLoaded.current = true
      } else {
        const err = await response.json()
        setError(err.detail || "Failed to fetch users")
      }
    } catch {
      setError("Network error. Please try again.")
    } finally {
      setLoading(false)
      usersLoading.current = false
    }
  }

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

  const clearMessageAfterTimeout = (setMessageFn, timeoutRef, setTimeoutRef) => {
    if (timeoutRef) {
      clearTimeout(timeoutRef)
    }
    const timeout = setTimeout(() => {
      setMessageFn("")
      setTimeoutRef(null)
    }, 10000)
    setTimeoutRef(timeout)
  }

  // ---------- Client-side filtering ----------
  const filteredUsers = useMemo(() => {
    return allUsers.filter((user) => {
      // Hide administrator@studlicensing.local from actions
      if (user.username === "administrator@studlicensing.local") {
        // Still show in list but will hide actions in render
      }

      // Search term filter
      if (searchTerm) {
        const searchLower = searchTerm.toLowerCase()
        const matchesSearch =
          user.username?.toLowerCase().includes(searchLower) ||
          user.name?.toLowerCase().includes(searchLower) ||
          user.surname?.toLowerCase().includes(searchLower)
        if (!matchesSearch) return false
      }

      // Type filter
      if (filterCompany === "global_admin") {
        return user.user_type === "admin" && !user.company_id
      }
      if (filterType === "global_admin") {
        return user.user_type === "admin" && !user.company_id
      }
      if (filterType !== "all_types" && filterType !== "global_admin") {
        if (user.user_type !== filterType) return false
      }

      // Company filter
      const titles = Array.isArray(user.company_title)
        ? user.company_title
        : user.company_title
          ? [user.company_title]
          : []
      return filterCompany === "all" || titles.includes(filterCompany)
    })
  }, [allUsers, searchTerm, filterType, filterCompany])

  // ---------------- CRUD HANDLERS ----------------

  // CREATE USER (multipart/form-data)
  const handleCreateUser = async (e) => {
    e.preventDefault()
    setLoading(true)
    setCreateError("")
    setSuccess("")

    if (createErrorTimeout) {
      clearTimeout(createErrorTimeout)
      setCreateErrorTimeout(null)
    }

    try {
      const formData = new FormData()
      formData.append("username", newUser.username)
      formData.append("name", newUser.name)
      formData.append("surname", newUser.surname)

      const typeToSend = newUser.user_type === "global_admin" ? "admin" : newUser.user_type
      formData.append("user_type", typeToSend)

      // Only append company_id if it's a global admin creating a user with a company association
      if (isGlobalAdmin && newUser.company_id) {
        formData.append("company_id", newUser.company_id)
      }

      const res = await apiCall("/admin/account_create", {
        method: "POST",
        body: formData,
      })
      if (res.ok || res.status === 201) {
        setSuccess("User created!")
        clearMessageAfterTimeout(setSuccess, successTimeout, setSuccessTimeout)
        setCreateDialog(false)
        setNewUser({ username: "", name: "", surname: "", user_type: "company_client", company_id: "" })
        usersLoaded.current = false
        fetchAllUsers()
      } else {
        const err = await res.json()
        const errorMessage = err.detail || "Failed to create user"
        setCreateError(errorMessage)
        clearErrorAfterTimeout(setCreateError, createErrorTimeout, setCreateErrorTimeout)
      }
    } catch {
      const errorMessage = "Network error. Please try again."
      setCreateError(errorMessage)
      clearErrorAfterTimeout(setCreateError, createErrorTimeout, setCreateErrorTimeout)
    } finally {
      setLoading(false)
    }
  }

  // EDIT/UPDATE USER (application/x-www-form-urlencoded)
  const handleUpdateUser = async (e) => {
    e.preventDefault()
    setLoading(true)
    setEditError("")
    setSuccess("")

    if (editErrorTimeout) {
      clearTimeout(editErrorTimeout)
      setEditErrorTimeout(null)
    }

    try {
      const params = new URLSearchParams()
      params.append("username", selectedUser.username)
      params.append("confirm_username", selectedUser.username)
      if (selectedUser.name) params.append("name", selectedUser.name)
      if (selectedUser.surname) params.append("surname", selectedUser.surname)

      const res = await apiCall("/admin/update_user_profile_info", {
        method: "POST",
        body: params.toString(),
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
      })
      if (res.ok) {
        setSuccess("User updated!")
        clearMessageAfterTimeout(setSuccess, successTimeout, setSuccessTimeout)
        setEditDialog(false)
        setSelectedUser(null)
        usersLoaded.current = false
        fetchAllUsers()
      } else {
        const err = await res.json()
        const errorMessage = err.detail || "Failed to update user"
        setEditError(errorMessage)
        clearErrorAfterTimeout(setEditError, editErrorTimeout, setEditErrorTimeout)
      }
    } catch {
      const errorMessage = "Network error. Please try again."
      setEditError(errorMessage)
      clearErrorAfterTimeout(setEditError, editErrorTimeout, setEditErrorTimeout)
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
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
      })
      if (res.ok) {
        setSuccess("User deleted!")
        clearMessageAfterTimeout(setSuccess, successTimeout, setSuccessTimeout)
        setDeleteDialog(false)
        setSelectedUser(null)
        // Reset the loaded flag to force refresh
        usersLoaded.current = false
        fetchAllUsers()
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

  // Load users only once on component mount
  useEffect(() => {
    const loadUsers = async () => {
      if (usersLoaded.current || usersLoading.current) return

      usersLoading.current = true
      setLoading(true)
      setError("")
      try {
        const params = new URLSearchParams()
        const response = await apiCall("/admin/search_user", {
          method: "POST",
          body: params.toString(),
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
        })
        if (response.ok) {
          const data = await response.json()
          setAllUsers(data.users || [])
          usersLoaded.current = true
        } else {
          const err = await response.json()
          setError(err.detail || "Failed to fetch users")
        }
      } catch {
        setError("Network error. Please try again.")
      } finally {
        setLoading(false)
        usersLoading.current = false
      }
    }

    loadUsers()
  }, [apiCall])

  // Company options for filters (derived from all users)
  const companyFilterOptions = useMemo(() => {
    return Array.from(
      new Set(
        allUsers.flatMap((u) =>
          Array.isArray(u.company_title) ? u.company_title : u.company_title ? [u.company_title] : [],
        ),
      ),
    )
  }, [allUsers])

  // Sort filtered users
  const sortedUsers = useMemo(() => {
    return stableSort(filteredUsers, getComparator(order, orderBy))
  }, [filteredUsers, order, orderBy])

  const handleRequestSort = (property) => {
    const isAsc = orderBy === property && order === "asc"
    setOrder(isAsc ? "desc" : "asc")
    setOrderBy(property)
  }

  // ========== Company search for Add/Remove Company dialogs and Create User dialog ==========

  useEffect(() => {
    const fetchCompanies = async () => {
      setCompanySearchLoading(true)
      try {
        const params = new URLSearchParams()
        const response = await apiCall("/company/search", {
          method: "POST",
          body: params.toString(),
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
        })

        const data = await response.json()
        const allCompanies = data.companies || []

        if (createDialog) {
          setCompanyOptions(allCompanies)
          setFilteredCompanyOptions(allCompanies)
          setCompanySearchTerm("")
          setNewUser((prev) => ({ ...prev, company_id: "" })) // Reset company_id for new user
        } else if (addToCompanyDialog) {
          const userCompanyIds = addDialogUserCompanyIds.current
          const userCompanyNames = addDialogUserCompanyTitles.current
          const filtered = allCompanies.filter(
            (c) => !userCompanyIds.includes(c.company_id) && !userCompanyNames.includes(c.company_name),
          )
          setCompanyOptions(filtered)
          setFilteredCompanyOptions(filtered)
          setCompanySearchTerm("")
          setCompanyActionData((prev) => ({ ...prev, company_id: "" }))
        } else if (removeFromCompanyDialog) {
          const allowedIds = removeDialogUserCompanyIds.current
          const allowedTitles = removeDialogUserCompanyTitles.current
          const filtered = allCompanies.filter(
            (c) => allowedIds.includes(c.company_id) || allowedTitles.includes(c.company_name),
          )
          setCompanyOptions(filtered)
          setFilteredCompanyOptions(filtered)
          setCompanySearchTerm("")
          setCompanyActionData((prev) => ({ ...prev, company_id: "" }))
        }
      } catch {
        setCompanyOptions([])
        setFilteredCompanyOptions([])
        setCompanySearchError("Network error while fetching companies")
      } finally {
        setCompanySearchLoading(false)
      }
    }

    if (createDialog || addToCompanyDialog || removeFromCompanyDialog) {
      fetchCompanies()
    }
  }, [createDialog, addToCompanyDialog, removeFromCompanyDialog, apiCall])

  useEffect(() => {
    const term = companySearchTerm.toLowerCase()
    const filtered = companyOptions.filter(
      (c) => c.company_name?.toLowerCase().includes(term) || c.company_id?.toString().includes(term),
    )
    setFilteredCompanyOptions(filtered)
  }, [companySearchTerm, companyOptions])

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

  // Company action handlers that refresh user list
  const handleAddToCompany = async (e) => {
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
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
      })
      if (res.ok) {
        setSuccess("User added to company!")
        clearMessageAfterTimeout(setSuccess, successTimeout, setSuccessTimeout)
        setAddToCompanyDialog(false)
        // Reset the loaded flag to force refresh
        usersLoaded.current = false
        fetchAllUsers()
      } else {
        const err = await res.json()
        setError(err.detail || "Failed to add to company")
      }
    } catch {
      setError("Network error.")
    } finally {
      setLoading(false)
    }
  }

  const handleRemoveFromCompany = async (e) => {
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
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
      })
      if (res.ok) {
        setSuccess("User removed from company!")
        clearMessageAfterTimeout(setSuccess, successTimeout, setSuccessTimeout)
        setRemoveFromCompanyDialog(false)
        // Reset the loaded flag to force refresh
        usersLoaded.current = false
        fetchAllUsers()
      } else {
        const err = await res.json()
        setError(err.detail || "Failed to remove from company")
      }
    } catch {
      setError("Network error.")
    } finally {
      setLoading(false)
    }
  }

  const handleUpdateEmail = async (e) => {
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
        clearMessageAfterTimeout(setSuccess, successTimeout, setSuccessTimeout)
        setUpdateEmailDialog(false)
        setEmailError("")
        // Reset the loaded flag to force refresh
        usersLoaded.current = false
        fetchAllUsers()
      } else {
        const err = await res.json()
        setEmailError(err.detail || "Failed to update email")
      }
    } catch {
      setEmailError("Network error.")
    } finally {
      setEmailLoading(false)
    }
  }

  // ---------------- UI ----------------
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

      {/* Controls */}
      <Card sx={{ mb: 3, borderRadius: 2 }}>
        <CardContent>
          <Box sx={{ display: "flex", gap: 2, flexWrap: "wrap", alignItems: "center" }}>
            <FormControl size="small" sx={{ minWidth: 180 }}>
              <InputLabel>User Type</InputLabel>
              <Select value={filterType} label="User Type" onChange={(e) => setFilterType(e.target.value)}>
                {userTypes.map((t) => (
                  <MenuItem key={t} value={t}>
                    {userTypeLabels[t]}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <FormControl size="small" sx={{ minWidth: 180 }}>
              <InputLabel>Company</InputLabel>
              <Select value={filterCompany} label="Company" onChange={(e) => setFilterCompany(e.target.value)}>
                <MenuItem value="all">All Companies</MenuItem>
                <MenuItem value="global_admin">Global Administrators</MenuItem>
                {companyFilterOptions.map((c) => (
                  <MenuItem key={c} value={c}>
                    {c}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <TextField
              label="Search users"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Email, name, or surname"
              size="small"
              sx={{ flexGrow: 1, minWidth: { xs: 200, sm: 300 } }}
            />
            <Box sx={{ flexGrow: 1 }} />
            <Button
              variant="contained"
              startIcon={<Add />}
              onClick={() => setCreateDialog(true)}
              sx={{ borderRadius: 2, textTransform: "none", height: 40, minWidth: 120 }}
            >
              Create User
            </Button>
          </Box>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            Showing {sortedUsers.length} of {allUsers.length} users
          </Typography>
        </CardContent>
      </Card>

      <TableContainer component={Paper} sx={{ borderRadius: 2 }}>
        <Table>
          <TableHead sx={{ backgroundColor: "background.paper" }}>
            <TableRow>
              {[
                { id: "username", label: "Email" },
                { id: "name", label: "Name" },
                { id: "surname", label: "Surname" },
                { id: "user_type", label: "Type" },
                { id: "company", label: "Company" },
              ].map((headCell) => (
                <TableCell
                  key={headCell.id}
                  sortDirection={orderBy === headCell.id ? order : false}
                  sx={{ fontWeight: "bold" }}
                >
                  <TableSortLabel
                    active={orderBy === headCell.id}
                    direction={orderBy === headCell.id ? order : "asc"}
                    onClick={() => handleRequestSort(headCell.id)}
                  >
                    {headCell.label}
                  </TableSortLabel>
                </TableCell>
              ))}
              {!canOnlyCreateClient && <TableCell sx={{ fontWeight: "bold" }}>Actions</TableCell>}
            </TableRow>
          </TableHead>
          <TableBody>
            {sortedUsers.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} align="center">
                  <Typography>{loading ? "Loading..." : "No users found"}</Typography>
                </TableCell>
              </TableRow>
            ) : (
              sortedUsers.map((user, i) => {
                const titles = Array.isArray(user.company_title)
                  ? user.company_title
                  : user.company_title
                    ? [user.company_title]
                    : []
                const displayType =
                  user.user_type === "admin" && (!user.company_id || user.company_id === null)
                    ? "Global Administrator"
                    : userTypeLabels[user.user_type] || user.user_type

                const isProtectedUser = user.username === "administrator@studlicensing.local"

                return (
                  <TableRow key={user.id || i} hover>
                    <TableCell>{user.username}</TableCell>
                    <TableCell>{user.name}</TableCell>
                    <TableCell>{user.surname}</TableCell>
                    <TableCell>
                      <Chip label={displayType} size="small" variant="outlined" />
                    </TableCell>
                    <TableCell>
                      {titles.length
                        ? titles.map((t, idx) => (
                            <Chip key={idx} label={t} size="small" variant="outlined" sx={{ mr: 0.5, mb: 0.5 }} />
                          ))
                        : "–"}
                    </TableCell>
                    {!canOnlyCreateClient && (
                      <TableCell>
                        {!isProtectedUser ? (
                          <Box sx={{ display: "flex", alignItems: "center", justifyContent: "flex-end", gap: 1 }}>
                            <Tooltip title="Edit">
                              <IconButton
                                color="success"
                                onClick={() => {
                                  setSelectedUser(user)
                                  setEditDialog(true)
                                }}
                              >
                                <Edit />
                              </IconButton>
                            </Tooltip>
                            {isAdmin && (
                              <Tooltip title="More actions">
                                <IconButton color="primary" onClick={(e) => handleOpenGearMenu(e, user)}>
                                  <Settings />
                                </IconButton>
                              </Tooltip>
                            )}
                            <Tooltip title="Delete">
                              <IconButton
                                color="error"
                                onClick={() => {
                                  setSelectedUser(user)
                                  setDeleteDialog(true)
                                }}
                              >
                                <Delete />
                              </IconButton>
                            </Tooltip>
                          </Box>
                        ) : (
                          <Typography variant="body2" color="text.secondary" sx={{ textAlign: "center" }}>
                            Protected
                          </Typography>
                        )}
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
      <Menu anchorEl={gearMenuAnchor} open={Boolean(gearMenuAnchor)} onClose={handleCloseGearMenu}>
        <MenuItem
          onClick={() => {
            setUpdateEmailData({
              old_username: gearMenuUser?.username || "",
              new_username: "",
              confirm_new_username: "",
            })
            setEmailError("")
            setUpdateEmailDialog(true)
            handleCloseGearMenu()
          }}
        >
          <Email sx={{ mr: 1 }} /> Change Email
        </MenuItem>
        {gearMenuUser?.user_type === "company_client" && [
          <MenuItem
            key="add"
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
              addDialogUserCompanyIds.current = userCompanyIds
              addDialogUserCompanyTitles.current = userCompanyTitles

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
          </MenuItem>,
        ]}
      </Menu>

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
            {createError && (
              <Alert severity="error" sx={{ mb: 2, borderRadius: 2 }}>
                {createError}
              </Alert>
            )}
            <TextField
              margin="normal"
              fullWidth
              label="Email"
              type="email"
              value={newUser.username}
              onChange={(e) => setNewUser({ ...newUser, username: e.target.value })}
              required
            />
            <TextField
              margin="normal"
              fullWidth
              label="First Name"
              value={newUser.name}
              onChange={(e) => setNewUser({ ...newUser, name: e.target.value })}
              required
            />
            <TextField
              margin="normal"
              fullWidth
              label="Last Name"
              value={newUser.surname}
              onChange={(e) => setNewUser({ ...newUser, surname: e.target.value })}
              required
            />
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
                    .filter((type) => type !== "all_types" && type !== "global_admin")
                    .map((type) => (
                      <MenuItem key={type} value={type}>
                        {userTypeLabels[type]}
                      </MenuItem>
                    ))
                ) : (
                  userTypes
                    .filter((type) => type !== "all_types")
                    .map((type) => (
                      <MenuItem key={type} value={type}>
                        {userTypeLabels[type]}
                      </MenuItem>
                    ))
                )}
              </Select>
            </FormControl>
            {isGlobalAdmin && (
              <Autocomplete
                options={filteredCompanyOptions}
                getOptionLabel={(option) => option.company_name || `Company #${option.company_id}`}
                loading={companySearchLoading}
                inputValue={companySearchTerm}
                onInputChange={(event, newInputValue) => {
                  setCompanySearchTerm(newInputValue)
                }}
                value={filteredCompanyOptions.find((opt) => opt.company_id === newUser.company_id) || null}
                onChange={(event, newValue) => {
                  setNewUser((prev) => ({
                    ...prev,
                    company_id: newValue?.company_id || "",
                  }))
                }}
                renderInput={(params) => <TextField {...params} label="Company Name" margin="normal" fullWidth />}
                disabled={loading || companySearchLoading}
              />
            )}
          </DialogContent>
          <DialogActions sx={{ p: 3 }}>
            <Button onClick={() => setCreateDialog(false)}>Cancel</Button>
            <Button type="submit" variant="contained" disabled={loading}>
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
            {editError && (
              <Alert severity="error" sx={{ mb: 2, borderRadius: 2 }}>
                {editError}
              </Alert>
            )}
            {selectedUser && (
              <>
                <TextField margin="normal" fullWidth label="Email" value={selectedUser.username} disabled />
                <TextField
                  margin="normal"
                  fullWidth
                  label="First Name"
                  value={selectedUser.name}
                  onChange={(e) => setSelectedUser({ ...selectedUser, name: e.target.value })}
                  required
                />
                <TextField
                  margin="normal"
                  fullWidth
                  label="Last Name"
                  value={selectedUser.surname}
                  onChange={(e) => setSelectedUser({ ...selectedUser, surname: e.target.value })}
                  required
                />
              </>
            )}
          </DialogContent>
          <DialogActions sx={{ p: 3 }}>
            <Button onClick={() => setEditDialog(false)}>Cancel</Button>
            <Button type="submit" variant="contained" disabled={loading}>
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
          <Button onClick={() => setDeleteDialog(false)}>Cancel</Button>
          <Button onClick={handleDeleteUser} color="error" variant="contained" disabled={loading}>
            {loading ? <CircularProgress size={24} /> : "Delete"}
          </Button>
        </DialogActions>
      </Dialog>

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
        <form onSubmit={handleUpdateEmail}>
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
            <Button type="submit" variant="contained" disabled={emailLoading}>
              {emailLoading ? <CircularProgress size={24} /> : "Update"}
            </Button>
          </DialogActions>
        </form>
      </Dialog>

      {/* Add To Company Dialog */}
      <Dialog
        open={addToCompanyDialog}
        onClose={() => setAddToCompanyDialog(false)}
        maxWidth="sm"
        fullWidth
        PaperProps={{ sx: { borderRadius: 3 } }}
      >
        <form onSubmit={handleAddToCompany}>
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
            <Autocomplete
              options={filteredCompanyOptions}
              getOptionLabel={(option) => option.company_name || `Company #${option.company_id}`}
              loading={companySearchLoading}
              inputValue={companySearchTerm}
              onInputChange={(event, newInputValue) => {
                setCompanySearchTerm(newInputValue)
              }}
              value={filteredCompanyOptions.find((opt) => opt.company_id === companyActionData.company_id) || null}
              onChange={(event, newValue) => {
                setCompanyActionData((prev) => ({
                  ...prev,
                  company_id: newValue?.company_id || "",
                }))
              }}
              renderInput={(params) => (
                <TextField {...params} label="Search and Select Company" margin="normal" fullWidth required />
              )}
            />
            {companySearchError && (
              <Alert severity="error" sx={{ mt: 1 }}>
                {companySearchError}
              </Alert>
            )}
          </DialogContent>
          <DialogActions sx={{ p: 3 }}>
            <Button onClick={() => setAddToCompanyDialog(false)}>Cancel</Button>
            <Button
              type="submit"
              variant="contained"
              disabled={loading || companySearchLoading || !companyActionData.company_id}
            >
              {loading ? <CircularProgress size={24} /> : "Add"}
            </Button>
          </DialogActions>
        </form>
      </Dialog>

      {/* Remove From Company Dialog */}
      <Dialog
        open={removeFromCompanyDialog}
        onClose={() => setRemoveFromCompanyDialog(false)}
        maxWidth="sm"
        fullWidth
        PaperProps={{ sx: { borderRadius: 3 } }}
      >
        <form onSubmit={handleRemoveFromCompany}>
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
            <Autocomplete
              options={filteredCompanyOptions}
              getOptionLabel={(option) => option.company_name || `Company #${option.company_id}`}
              loading={companySearchLoading}
              inputValue={companySearchTerm}
              onInputChange={(event, newInputValue) => {
                setCompanySearchTerm(newInputValue)
              }}
              value={filteredCompanyOptions.find((opt) => opt.company_id === companyActionData.company_id) || null}
              onChange={(event, newValue) => {
                setCompanyActionData((prev) => ({
                  ...prev,
                  company_id: newValue?.company_id || "",
                }))
              }}
              renderInput={(params) => (
                <TextField {...params} label="Select Company to Remove" margin="normal" fullWidth required />
              )}
            />
            {companySearchError && (
              <Alert severity="error" sx={{ mt: 1 }}>
                {companySearchError}
              </Alert>
            )}
          </DialogContent>
          <DialogActions sx={{ p: 3 }}>
            <Button onClick={() => setRemoveFromCompanyDialog(false)}>Cancel</Button>
            <Button
              type="submit"
              variant="contained"
              color="error"
              disabled={loading || companySearchLoading || !companyActionData.company_id}
            >
              {loading ? <CircularProgress size={24} /> : "Remove"}
            </Button>
          </DialogActions>
        </form>
      </Dialog>
    </Box>
  )
}

export default UserManagement