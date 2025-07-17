"use client"

import { useState, useEffect, useMemo, useRef } from "react"
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
  Alert,
  CircularProgress,
  IconButton,
  Card,
  CardContent,
  TableSortLabel,
} from "@mui/material"
import { Add, Edit, Delete } from "@mui/icons-material"
import { useApi } from "../../contexts/ApiContext"

// ---------- Sort helpers ----------
const descendingComparator = (a, b, orderBy) => {
  const valA = (a[orderBy] ?? "").toString().toLowerCase()
  const valB = (b[orderBy] ?? "").toString().toLowerCase()
  if (valB < valA) return -1
  if (valB > valA) return 1
  return 0
}

const getComparator = (order, orderBy) =>
  order === "desc" ? (a, b) => descendingComparator(a, b, orderBy) : (a, b) => -descendingComparator(a, b, orderBy)

const stableSort = (array, comparator) => {
  const stabilized = array.map((el, idx) => [el, idx])
  stabilized.sort((a, b) => {
    const cmp = comparator(a[0], b[0])
    return cmp !== 0 ? cmp : a[1] - b[1]
  })
  return stabilized.map((el) => el[0])
}

const CompanyManagement = () => {
  const { apiCall } = useApi()

  // Data state
  const [allCompanies, setAllCompanies] = useState([]) // Store all companies from API
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")

  // Controls state
  const [searchTerm, setSearchTerm] = useState("")
  const [order, setOrder] = useState("asc")
  const [orderBy, setOrderBy] = useState("company_id")

  // Dialog state
  const [createDialog, setCreateDialog] = useState(false)
  const [editDialog, setEditDialog] = useState(false)
  const [deleteDialog, setDeleteDialog] = useState(false)
  const [selectedCompany, setSelectedCompany] = useState(null)
  const [newCompanyName, setNewCompanyName] = useState("")

  // Use ref to prevent duplicate API calls
  const companiesLoaded = useRef(false)
  const companiesLoading = useRef(false)

  // Fetch all companies (only called once and after CRUD operations)
  const fetchAllCompanies = async () => {
    if (companiesLoaded.current || companiesLoading.current) return

    companiesLoading.current = true
    setLoading(true)
    setError("")
    try {
      const params = new URLSearchParams()
      const response = await apiCall("/company/search", {
        method: "POST",
        body: params.toString(),
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
      })

      if (response.ok) {
        const data = await response.json()
        setAllCompanies(data.companies || [])
        companiesLoaded.current = true
      } else {
        const err = await response.json()
        setError(err.detail || "Failed to fetch companies")
      }
    } catch {
      setError("Network error. Please try again.")
    } finally {
      setLoading(false)
      companiesLoading.current = false
    }
  }

  // Client-side filtering
  const filteredCompanies = useMemo(() => {
    if (!searchTerm) return allCompanies

    const searchLower = searchTerm.toLowerCase()
    return allCompanies.filter(
      (company) =>
        company.company_name?.toLowerCase().includes(searchLower) ||
        company.company_id?.toString().includes(searchLower),
    )
  }, [allCompanies, searchTerm])

  // --- Create Company ---
  const handleCreateCompany = async (e) => {
    e.preventDefault()
    setError("")
    setSuccess("")
    setLoading(true)
    try {
      const params = new URLSearchParams()
      params.append("companyName", newCompanyName)
      const response = await apiCall("/company/create", {
        method: "POST",
        body: params.toString(),
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
      })
      if (response.ok) {
        setSuccess("Company created successfully!")
        setCreateDialog(false)
        setNewCompanyName("")
        // Reset the loaded flag to force refresh
        companiesLoaded.current = false
        fetchAllCompanies()
      } else {
        const err = await response.json()
        setError(err.detail || "Failed to create company")
      }
    } catch {
      setError("Network error. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  // --- Update Company ---
  const handleUpdateCompany = async (e) => {
    e.preventDefault()
    setError("")
    setSuccess("")
    setLoading(true)
    try {
      const params = new URLSearchParams()
      params.append("companyName", selectedCompany.name)
      const response = await apiCall(`/company/update/${selectedCompany.id}`, {
        method: "PUT",
        body: params.toString(),
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
      })
      if (response.ok) {
        setSuccess("Company updated successfully!")
        setEditDialog(false)
        setSelectedCompany(null)
        // Reset the loaded flag to force refresh
        companiesLoaded.current = false
        fetchAllCompanies()
      } else {
        const err = await response.json()
        setError(err.detail || "Failed to update company")
      }
    } catch {
      setError("Network error. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  // --- Delete Company ---
  const handleDeleteCompany = async (e) => {
    if (e) e.preventDefault()
    setError("")
    setSuccess("")
    setLoading(true)
    try {
      const response = await apiCall(`/company/delete/${selectedCompany.id}`, {
        method: "DELETE",
      })
      if (response.ok) {
        setSuccess("Company deleted successfully!")
        setDeleteDialog(false)
        setSelectedCompany(null)
        // Reset the loaded flag to force refresh
        companiesLoaded.current = false
        fetchAllCompanies()
      } else {
        const err = await response.json()
        setError(err.detail || "Failed to delete company")
      }
    } catch {
      setError("Network error. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  // Load companies only once on component mount
  useEffect(() => {
    const loadCompanies = async () => {
      if (companiesLoaded.current || companiesLoading.current) return

      companiesLoading.current = true
      setLoading(true)
      setError("")
      try {
        const params = new URLSearchParams()
        const response = await apiCall("/company/search", {
          method: "POST",
          body: params.toString(),
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
        })

        if (response.ok) {
          const data = await response.json()
          setAllCompanies(data.companies || [])
          companiesLoaded.current = true
        } else {
          const err = await response.json()
          setError(err.detail || "Failed to fetch companies")
        }
      } catch {
        setError("Network error. Please try again.")
      } finally {
        setLoading(false)
        companiesLoading.current = false
      }
    }

    loadCompanies()
  }, [apiCall])

  // Sorting handler
  const handleRequestSort = (property) => {
    const isAsc = orderBy === property && order === "asc"
    setOrder(isAsc ? "desc" : "asc")
    setOrderBy(property)
  }

  // Apply sorting
  const sortedCompanies = useMemo(() => {
    return stableSort(filteredCompanies, getComparator(order, orderBy))
  }, [filteredCompanies, order, orderBy])

  return (
    <Box>
      <Typography variant="h5" gutterBottom fontWeight="bold">
        Company Management
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
          <Box sx={{ display: "flex", gap: 2, flexWrap: "wrap", alignItems: "center" }}>
            <TextField
              label="Search companies"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Company name or ID"
              size="small"
              sx={{ flexGrow: 1, minWidth: 200 }}
            />
            <Button
              variant="contained"
              startIcon={<Add />}
              onClick={() => setCreateDialog(true)}
              sx={{ borderRadius: 2 }}
            >
              Create Company
            </Button>
          </Box>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            Showing {sortedCompanies.length} of {allCompanies.length} companies
          </Typography>
        </CardContent>
      </Card>

      <TableContainer component={Paper} sx={{ borderRadius: 2 }}>
        <Table>
          <TableHead sx={{ backgroundColor: "background.paper" }}>
            <TableRow>
              <TableCell sortDirection={orderBy === "company_id" ? order : false} sx={{ fontWeight: "bold" }}>
                <TableSortLabel
                  active={orderBy === "company_id"}
                  direction={orderBy === "company_id" ? order : "asc"}
                  onClick={() => handleRequestSort("company_id")}
                >
                  ID
                </TableSortLabel>
              </TableCell>
              <TableCell
                sortDirection={orderBy === "company_name" ? order : false}
                sx={{ fontWeight: "bold", textAlign: "left" }}
              >
                <TableSortLabel
                  active={orderBy === "company_name"}
                  direction={orderBy === "company_name" ? order : "asc"}
                  onClick={() => handleRequestSort("company_name")}
                >
                  Company Name
                </TableSortLabel>
              </TableCell>
              <TableCell sx={{ fontWeight: "bold", textAlign: "right" }}>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {sortedCompanies.length === 0 ? (
              <TableRow>
                <TableCell colSpan={3} align="left" sx={{ py: 4 }}>
                  <Typography color="text.secondary">{loading ? "Loading..." : "No companies found"}</Typography>
                </TableCell>
              </TableRow>
            ) : (
              sortedCompanies.map((c, idx) => (
                <TableRow key={c.company_id || idx} hover>
                  <TableCell>{c.company_id}</TableCell>
                  <TableCell sx={{ textAlign: "left" }}>{c.company_name}</TableCell>
                  <TableCell sx={{ textAlign: "right" }}>
                    <IconButton
                      onClick={() => {
                        setSelectedCompany({ id: c.company_id, name: c.company_name })
                        setEditDialog(true)
                      }}
                      color="success"
                    >
                      <Edit />
                    </IconButton>
                    <IconButton
                      onClick={() => {
                        setSelectedCompany({ id: c.company_id, name: c.company_name })
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

      {/* Create Company Dialog */}
      <Dialog
        open={createDialog}
        onClose={() => setCreateDialog(false)}
        maxWidth="sm"
        fullWidth
        PaperProps={{ sx: { borderRadius: 3 } }}
      >
        <form onSubmit={handleCreateCompany}>
          <DialogTitle>
            <Typography variant="h5" fontWeight="bold">
              Create New Company
            </Typography>
          </DialogTitle>
          <DialogContent>
            <TextField
              margin="normal"
              fullWidth
              label="Company Name"
              value={newCompanyName}
              onChange={(e) => setNewCompanyName(e.target.value)}
              variant="outlined"
              required
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

      {/* Edit Company Dialog */}
      <Dialog
        open={editDialog}
        onClose={() => setEditDialog(false)}
        maxWidth="sm"
        fullWidth
        PaperProps={{ sx: { borderRadius: 3 } }}
      >
        <form onSubmit={handleUpdateCompany}>
          <DialogTitle>
            <Typography variant="h5" fontWeight="bold">
              Edit Company
            </Typography>
          </DialogTitle>
          <DialogContent>
            {selectedCompany && (
              <TextField
                margin="normal"
                fullWidth
                label="Company Name"
                value={selectedCompany.name}
                onChange={(e) => setSelectedCompany({ ...selectedCompany, name: e.target.value })}
                variant="outlined"
                required
              />
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

      {/* Delete Company Dialog */}
      <Dialog
        open={deleteDialog}
        onClose={() => setDeleteDialog(false)}
        maxWidth="sm"
        fullWidth
        PaperProps={{ sx: { borderRadius: 3 } }}
      >
        <DialogTitle>
          <Typography variant="h5" fontWeight="bold">
            Delete Company
          </Typography>
        </DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete company <strong>"{selectedCompany?.name}"</strong>? This action cannot be
            undone.
          </Typography>
        </DialogContent>
        <DialogActions sx={{ p: 3 }}>
          <Button onClick={() => setDeleteDialog(false)} sx={{ borderRadius: 2 }}>
            Cancel
          </Button>
          <Button
            onClick={handleDeleteCompany}
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

export default CompanyManagement