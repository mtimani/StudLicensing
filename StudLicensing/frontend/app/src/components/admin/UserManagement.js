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
  TableSortLabel,
} from "@mui/material"
import { Add, Edit, Delete, Search } from "@mui/icons-material"
import { useApi } from "../../contexts/ApiContext"

// Sort helper functions
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

  // Core data state
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")

  // Controls state
  const [searchTerm, setSearchTerm] = useState("")
  const [filterType, setFilterType] = useState('all_types')
  const [filterCompany, setFilterCompany] = useState('all')
  const [order, setOrder] = useState('asc')
  const [orderBy, setOrderBy] = useState('username')

  // Dialog state
  const [createDialog, setCreateDialog] = useState(false)
  const [editDialog, setEditDialog] = useState(false)
  const [deleteDialog, setDeleteDialog] = useState(false)
  const [selectedUser, setSelectedUser] = useState(null)
  const [newUser, setNewUser] = useState({ username: "", name: "", surname: "", user_type: "company_client", company_id: "" })

  // User type options and labels
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

  // Fetch users using x-www-form-urlencoded
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

  // CRUD handlers (unchanged)
  const handleCreateUser = async (e) => { /* ... */ }
  const handleUpdateUser = async (e) => { /* ... */ }
  const handleDeleteUser = async () => { /* ... */ }

  useEffect(() => { searchUsers() }, [])

  // Derive company options dynamically
  const companyOptions = Array.from(
    new Set(
      users.flatMap(u => Array.isArray(u.company_title) ? u.company_title : u.company_title ? [u.company_title] : [])
    )
  )

  // Apply filters
  const filteredUsers = users.filter(u => {
    // Global Admin filter if selected
    if (filterCompany === 'global_admin') {
      return u.user_type === 'admin' && (!u.company_id)
    }
    // Type-based global admin
    if (filterType === 'global_admin') {
      return u.user_type === 'admin' && (!u.company_id)
    }
    if (filterType !== 'all_types' && filterType !== 'global_admin') {
      if (u.user_type !== filterType) return false
    }
    // Company filter
    const titles = Array.isArray(u.company_title) ? u.company_title : u.company_title ? [u.company_title] : []
    return filterCompany === 'all' || titles.includes(filterCompany)
  })

  // Apply sorting after filtering
  const sortedUsers = stableSort(filteredUsers, getComparator(order, orderBy))

  const handleRequestSort = (property) => {
    const isAsc = orderBy === property && order === 'asc'
    setOrder(isAsc ? 'desc' : 'asc')
    setOrderBy(property)
  }

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
                {companyOptions.map(c => (
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
              <TableCell sx={{ fontWeight: 'bold' }}>Actions</TableCell>
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
                    <TableCell>
                      <IconButton onClick={() => { setSelectedUser(user); setEditDialog(true) }}><Edit /></IconButton>
                      <IconButton onClick={() => { setSelectedUser(user); setDeleteDialog(true) }} color="error"><Delete /></IconButton>
                    </TableCell>
                  </TableRow>
                )
              })
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Create User Dialog */}
      <Dialog open={createDialog} onClose={() => setCreateDialog(false)} maxWidth="sm" fullWidth PaperProps={{ sx: { borderRadius: 3 } }}>
        <form onSubmit={handleCreateUser}>
          <DialogTitle><Typography variant="h5" fontWeight="bold">Create New User</Typography></DialogTitle>
          <DialogContent>
            <TextField margin="normal" fullWidth label="Email" type="email" value={newUser.username} onChange={(e)=>setNewUser({...newUser,username:e.target.value})} required />
            <TextField margin="normal" fullWidth label="First Name" value={newUser.name} onChange={(e)=>setNewUser({...newUser,name:e.target.value})} required />
            <TextField margin="normal" fullWidth label="Last Name" value={newUser.surname} onChange={(e)=>setNewUser({...newUser,surname:e.target.value})} required />
            <FormControl fullWidth margin="normal"><InputLabel>User Type</InputLabel><Select value={newUser.user_type} onChange={(e)=>setNewUser({...newUser,user_type:e.target.value})} label="User Type">{userTypes.map(type=> <MenuItem key={type} value={type}>{userTypeLabels[type]}</MenuItem>)}</Select></FormControl>
            <TextField margin="normal" fullWidth label="Company ID (optional)" type="number" value={newUser.company_id} onChange={(e)=>setNewUser({...newUser,company_id:e.target.value})} />
          </DialogContent>
          <DialogActions sx={{ p:3 }}><Button onClick={()=>setCreateDialog(false)}>Cancel</Button><Button type="submit" variant="contained" disabled={loading}>{loading?<CircularProgress size={24}/>:"Create"}</Button></DialogActions>
        </form>
      </Dialog>

      {/* Edit User Dialog */}
      <Dialog open={editDialog} onClose={()=>setEditDialog(false)} maxWidth="sm" fullWidth PaperProps={{ sx:{borderRadius:3} }}>
        <form onSubmit={handleUpdateUser}>
          <DialogTitle><Typography variant="h5" fontWeight="bold">Edit User</Typography></DialogTitle>
          <DialogContent>{selectedUser && (<>
            <TextField margin="normal" fullWidth label="Email" value={selectedUser.username} disabled />
            <TextField margin="normal" fullWidth label="First Name" value={selectedUser.name} onChange={(e)=>setSelectedUser({...selectedUser,name:e.target.value})} required />
            <TextField margin="normal" fullWidth label="Last Name" value={selectedUser.surname} onChange={(e)=>setSelectedUser({...selectedUser,surname:e.target.value})} required />
          </>)}
          </DialogContent>
          <DialogActions sx={{ p:3 }}><Button onClick={()=>setEditDialog(false)}>Cancel</Button><Button type="submit" variant="contained" disabled={loading}>{loading?<CircularProgress size={24}/>:"Update"}</Button></DialogActions>
        </form>
      </Dialog>

      {/* Delete User Dialog */}
      <Dialog open={deleteDialog} onClose={()=>setDeleteDialog(false)} PaperProps={{ sx:{borderRadius:3} }}>
        <DialogTitle><Typography variant="h5" fontWeight="bold">Delete User</Typography></DialogTitle>
        <DialogContent><Typography>Are you sure you want to delete user <strong>{selectedUser?.username}</strong>? This action cannot be undone.</Typography></DialogContent>
        <DialogActions sx={{ p:3 }}><Button onClick={()=>setDeleteDialog(false)}>Cancel</Button><Button onClick={handleDeleteUser} color="error" variant="contained" disabled={loading}>{loading?<CircularProgress size={24}/>:"Delete"}</Button></DialogActions>
      </Dialog>
    </Box>
  )
}

export default UserManagement