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
  const currentTokenRef = useRef(token)
  const requestCounterRef = useRef(0)

  useEffect(() => {
    currentTokenRef.current = token
  }, [token])

  const apiCall = async (endpoint, options = {}) => {
    const requestId = ++requestCounterRef.current
    const url = `${API_BASE_URL}${endpoint}`

    const headers = {
      ...options.headers,
    }

    // Use the most current token available
    const currentToken = currentTokenRef.current || token
    if (currentToken) {
      headers.Authorization = `Bearer ${currentToken}`
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

      // Check for token refresh header
      const refreshToken = response.headers.get("x-refresh-token")
      if (refreshToken && refreshToken !== currentTokenRef.current) {
        // Update the ref immediately
        currentTokenRef.current = refreshToken
        // Update AuthContext state (this will also update localStorage)
        login(refreshToken)
      }

      // Handle 401 Unauthorized
      if (response.status === 401) {
        try {
          const errorData = await response.json()
          if (errorData.detail === "Invalid user.") {
            logout()
            window.location.href = "/login?message=session_expired"
            return response
          }
        } catch (e) {
          // Error parsing response, continue
        }
      }

      return response
    } catch (error) {
      throw error
    }
  }

  const value = {
    apiCall,
  }

  return <ApiContext.Provider value={value}>{children}</ApiContext.Provider>
}