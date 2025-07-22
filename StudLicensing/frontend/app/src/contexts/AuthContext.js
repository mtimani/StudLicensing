"use client"

import { createContext, useContext, useState, useEffect } from "react"
import { jwtDecode } from "jwt-decode"

const AuthContext = createContext(undefined)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider")
  }
  return context
}

const getRoleDisplayName = (role) => {
  const roleMap = {
    admin: "Global Administrator",
    company_admin: "Company Administrator",
    company_developper: "Company Developer",
    company_commercial: "Company Commercial",
    company_client: "Client",
    basic: "Basic User",
  }
  return roleMap[role] || role
}

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [token, setToken] = useState(null)

  useEffect(() => {
    const storedToken = localStorage.getItem("token")
    if (storedToken) {
      try {
        const decoded = jwtDecode(storedToken)
        if (decoded.exp * 1000 > Date.now()) {
          setToken(storedToken)
          setUser({
            id: decoded.sub,
            email: decoded.sub,
            name: decoded.name || "",
            surname: decoded.surname || "",
            type: decoded.type || "basic",
            roleDisplayName: getRoleDisplayName(decoded.type || "basic"),
          })
        } else {
          localStorage.removeItem("token")
        }
      } catch (error) {
        localStorage.removeItem("token")
      }
    }
  }, [])

  const login = (newToken) => {
    try {
      const decoded = jwtDecode(newToken)
      setToken(newToken)
      setUser({
        id: decoded.sub,
        email: decoded.sub,
        name: decoded.name || "",
        surname: decoded.surname || "",
        type: decoded.type || "basic",
        roleDisplayName: getRoleDisplayName(decoded.type || "basic"),
      })
      localStorage.setItem("token", newToken)
    } catch (error) {
      console.error("Invalid token in login:", error)
    }
  }

  const logout = () => {
    setUser(null)
    setToken(null)
    localStorage.removeItem("token")
  }

  const hasRole = (roles) => {
    return user ? roles.includes(user.type) : false
  }

  const fetchProfileInfo = async () => {
    if (!token) return null

    try {
      const response = await fetch(`${process.env.REACT_APP_API_BASE_URL || "http://localhost:8000"}/profile/info`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
        mode: "cors",
      })

      if (response.ok) {
        const data = await response.json()
        return {
          name: data.name || "",
          surname: data.surname || "",
        }
      }
    } catch (error) {
      console.error("Error fetching profile info:", error)
    }
    return null
  }

  const value = {
    user,
    token,
    login,
    logout,
    isAuthenticated: !!user,
    hasRole,
    fetchProfileInfo,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}