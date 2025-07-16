"use client"

import { createContext, useContext } from "react"
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
  const { token } = useAuth()

  const apiCall = async (endpoint, options = {}) => {
    const url = `${API_BASE_URL}${endpoint}`
    const headers = {
      ...options.headers,
    }

    if (token) {
      headers.Authorization = `Bearer ${token}`
    }

    if (options.body && typeof options.body === "object" && !(options.body instanceof FormData)) {
      headers["Content-Type"] = "application/json"
    }

    const response = await fetch(url, {
      ...options,
      headers,
      mode: 'cors', // Add CORS mode
    })

    return response
  }

  const value = {
    apiCall,
  }

  return <ApiContext.Provider value={value}>{children}</ApiContext.Provider>
}