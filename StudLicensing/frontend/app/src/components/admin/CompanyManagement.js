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
  Alert,
  CircularProgress,
  IconButton,
  Card,
  CardContent,
} from "@mui/material"
import { Add, Edit, Delete, Search } from "@mui/icons-material"
import { useApi } from "../../contexts/ApiContext"

const CompanyManagement = () => {
  const [companies, setCompanies] = useState([])
  const [searchTerm, setSearchTerm] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const [success, setSuccess] = useState("")
  const [createDialog, setCreateDialog] = useState(false)
  const [editDialog, setEditDialog] = useState(false)
  const [deleteDialog, setDeleteDialog] = useState(false)
  const [selectedCompany, setSelectedCompany] = useState(null)
  const [newCompanyName, setNewCompanyName] = useState("")
  const { apiCall } = useApi()

  const searchCompanies = async () => {
    setLoading(true)
    setError("")

    try {
      const requestBody = searchTerm ? { company_name: searchTerm } : {}

      const response = await apiCall("/company/search", {
        method: "POST",
        body: JSON.stringify(requestBody),
        headers: {
          "Content-Type": "application/json",
        },
      })

      if (response.ok) {
        const data = await response.json()
        console.log("Companies API Response:", data) // Debug log
        // Handle the correct API response format
        const companies = data.companies || []
        setCompanies(companies)
      } else {
        const errorData = await response.json()
        setError(errorData.detail || "Failed to search companies")
      }
    } catch (err) {
      setError("Network error. Please try again.")
      console.error("Search error:", err)
    } finally {
      setLoading(false)
    }
  }

  const handleCreateCompany = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError("")
    setSuccess("")

    try {
      const formData = new FormData()
      formData.append("companyName", newCompanyName)

      const response = await apiCall("/company/create", {
        method: "POST",
        body: formData,
      })

      if (response.ok) {
        setSuccess("Company created successfully")
        setCreateDialog(false)
        setNewCompanyName("")
        searchCompanies()
      } else {
        const errorData = await response.json()
        setError(errorData.detail || "Failed to create company")
      }
    } catch (err) {
      setError("Network error. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  const handleUpdateCompany = async (e) => {
    e.preventDefault()
    if (!selectedCompany) return

    setLoading(true)
    setError("")
    setSuccess("")

    try {
      const formData = new FormData()
      formData.append("companyName", selectedCompany.name)

      const response = await apiCall(`/company/update/${selectedCompany.id}`, {
        method: "PUT",
        body: formData,
      })

      if (response.ok) {
        setSuccess("Company updated successfully")
        setEditDialog(false)
        setSelectedCompany(null)
        searchCompanies()
      } else {
        const errorData = await response.json()
        setError(errorData.detail || "Failed to update company")
      }
    } catch (err) {
      setError("Network error. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  const handleDeleteCompany = async () => {
    if (!selectedCompany) return

    setLoading(true)
    setError("")
    setSuccess("")

    try {
      const response = await apiCall(`/company/delete/${selectedCompany.id}`, {
        method: "DELETE",
      })

      if (response.ok) {
        setSuccess("Company deleted successfully")
        setDeleteDialog(false)
        setSelectedCompany(null)
        searchCompanies()
      } else {
        const errorData = await response.json()
        setError(errorData.detail || "Failed to delete company")
      }
    } catch (err) {
      setError("Network error. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    searchCompanies()
  }, [])

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
          <Box sx={{ display: "flex", gap: 2, alignItems: "center", flexWrap: "wrap" }}>
            <TextField
              label="Search companies"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Company name"
              sx={{ flexGrow: 1, minWidth: 200 }}
              variant="outlined"
              size="small"
              onKeyPress={(e) => {
                if (e.key === "Enter") {
                  searchCompanies()
                }
              }}
            />
            <Button
              variant="outlined"
              startIcon={<Search />}
              onClick={searchCompanies}
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
              Create Company
            </Button>
          </Box>
        </CardContent>
      </Card>

      <TableContainer component={Paper} sx={{ borderRadius: 2 }}>
        <Table>
          <TableHead>
            <TableRow sx={{ bgcolor: "grey.50" }}>
              <TableCell sx={{ fontWeight: "bold" }}>ID</TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>Company Name</TableCell>
              <TableCell sx={{ fontWeight: "bold" }}>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {companies.length === 0 ? (
              <TableRow>
                <TableCell colSpan={3} align="center" sx={{ py: 4 }}>
                  <Typography color="text.secondary">{loading ? "Loading..." : "No companies found"}</Typography>
                </TableCell>
              </TableRow>
            ) : (
              companies.map((company, index) => (
                <TableRow key={company.company_id || index} hover>
                  <TableCell>{company.company_id}</TableCell>
                  <TableCell>{company.company_name}</TableCell>
                  <TableCell>
                    <IconButton
                      onClick={() => {
                        setSelectedCompany({ id: company.company_id, name: company.company_name })
                        setEditDialog(true)
                      }}
                      color="primary"
                    >
                      <Edit />
                    </IconButton>
                    <IconButton
                      onClick={() => {
                        setSelectedCompany({ id: company.company_id, name: company.company_name })
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
      <Dialog open={deleteDialog} onClose={() => setDeleteDialog(false)} PaperProps={{ sx: { borderRadius: 3 } }}>
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