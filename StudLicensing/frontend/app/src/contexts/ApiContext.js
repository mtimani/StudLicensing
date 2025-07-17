"use client"
import { createContext, useContext, useRef, useEffect } from "react"
import { useAuth } from "./AuthContext"

const ApiContext = createContext(undefined)

export const useApi = () => {
  const context = useContext(ApiContext)
  if (context === undefined) {
    throw new Error("useApi must be used within an ApiProvider")
  }
  return context
}

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || "http://localhost:8000"

export const ApiProvider = ({ children }) => {
  const { token, login, logout } = useAuth()
  // We still keep currentTokenRef for the x-refresh-token logic within apiCall,
  // but the initial header will use the direct 'token' from useAuth().
  const currentTokenRef = useRef(token)

  // This useEffect ensures currentTokenRef is always in sync with the AuthContext's token state.
  useEffect(() => {
    currentTokenRef.current = token
  }, [token])

  const apiCall = async (endpoint, options = {}) => {
    const url = `${API_BASE_URL}${endpoint}`
    const headers = {
      ...options.headers,
    }

    // Use the direct 'token' from useAuth() for the initial request header.
    // This ensures we always use the latest token from AuthContext state.
    if (token) {
      headers.Authorization = `Bearer ${token}`
    }

    if (options.body && typeof options.body === "object" && !(options.body instanceof FormData)) {
      headers["Content-Type"] = "application/json"
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
        mode: "cors",
      })

      // Check for token refresh header IMMEDIATELY and update token
      const refreshToken = response.headers.get("x-refresh-token")
      if (refreshToken && refreshToken !== currentTokenRef.current) {
        // Compare with ref for internal consistency
        console.log("Token refreshed automatically - updating immediately")
        login(refreshToken) // This will update the token in AuthContext and localStorage
        currentTokenRef.current = refreshToken // Update our ref immediately for any subsequent calls in the same chain
      }

      // Handle 401 Unauthorized with "Invalid user." detail
      if (response.status === 401) {
        try {
          const errorData = await response.json()
          if (errorData.detail === "Invalid user.") {
            logout()
            window.location.href = "/login?message=session_expired"
            return response
          }
        } catch (e) {
          // If we can't parse the JSON, just continue with normal flow
        }
      }

      return response
    } catch (error) {
      console.error("API call failed:", error)
      throw error
    }
  }

  const value = {
    apiCall,
  }

  return <ApiContext.Provider value={value}>{children}</ApiContext.Provider>
}