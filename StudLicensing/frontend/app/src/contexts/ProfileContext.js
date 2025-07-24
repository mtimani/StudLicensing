"use client"

import { createContext, useContext, useState, useEffect, useRef, useCallback } from "react"
import { useAuth } from "./AuthContext"
import { useApi } from "./ApiContext"

const ProfileContext = createContext(undefined)

export const useProfile = () => {
  const context = useContext(ProfileContext)
  if (context === undefined) {
    throw new Error("useProfile must be used within a ProfileProvider")
  }
  return context
}

// Helper function to improve error messages
const improveErrorMessage = (message) => {
  if (message === "value is not a valid phone number") {
    return "Please enter a valid international phone number starting with + followed by country code and number (e.g., +1234567890)"
  }
  return message
}

export const ProfileProvider = ({ children }) => {
  const [profileInfo, setProfileInfo] = useState({ name: "", surname: "", phoneNumber: "" })
  const [profilePicture, setProfilePicture] = useState(null)
  const [loading, setLoading] = useState(false)
  const [pictureLoading, setPictureLoading] = useState(false)
  const { isAuthenticated } = useAuth()
  const { apiCall } = useApi()

  // Use refs to prevent duplicate calls
  const profileInfoLoaded = useRef(false)
  const profilePictureLoaded = useRef(false)
  const profileInfoLoading = useRef(false)
  const profilePictureLoading = useRef(false)

  const loadProfileInfo = useCallback(async () => {
    if (!isAuthenticated || profileInfoLoaded.current || profileInfoLoading.current) return

    profileInfoLoading.current = true
    setLoading(true)
    try {
      const response = await apiCall("/profile/info")
      if (response.ok) {
        const data = await response.json()
        setProfileInfo({
          name: data.name || "",
          surname: data.surname || "",
          phoneNumber: data.phoneNumber || "",
        })
        profileInfoLoaded.current = true
      }
    } catch (error) {
      console.error("Error loading profile info:", error)
    } finally {
      setLoading(false)
      profileInfoLoading.current = false
    }
  }, [isAuthenticated, apiCall])

  const loadProfilePicture = useCallback(async () => {
    if (!isAuthenticated || profilePictureLoaded.current || profilePictureLoading.current) return

    profilePictureLoading.current = true
    setPictureLoading(true)
    try {
      const response = await apiCall("/profile/picture")
      if (response.ok) {
        const blob = await response.blob()
        const imageUrl = URL.createObjectURL(blob)
        setProfilePicture(imageUrl)
        profilePictureLoaded.current = true
      }
    } catch (error) {
      console.error("Error loading profile picture:", error)
    } finally {
      setPictureLoading(false)
      profilePictureLoading.current = false
    }
  }, [isAuthenticated, apiCall])

  const updateProfileInfo = async (newInfo) => {
    try {
      const response = await apiCall("/profile/info", {
        method: "PUT",
        body: JSON.stringify(newInfo),
        headers: {
          "Content-Type": "application/json",
        },
      })

      if (response.ok) {
        setProfileInfo((prev) => ({ ...prev, ...newInfo }))
        return { success: true }
      } else {
        const errorData = await response.json()

        // Handle 422 validation errors with detail array
        if (errorData.detail && Array.isArray(errorData.detail)) {
          const errorMessages = errorData.detail
            .map((err) => {
              if (typeof err === "object" && err.msg) {
                return improveErrorMessage(err.msg)
              }
              return String(err)
            })
            .join(", ")
          return { success: false, error: errorMessages }
        }

        // Handle single detail string
        if (typeof errorData.detail === "string") {
          return { success: false, error: improveErrorMessage(errorData.detail) }
        }

        // Handle validation error object with msg property
        if (typeof errorData === "object" && errorData.msg) {
          return { success: false, error: improveErrorMessage(errorData.msg) }
        }

        return { success: false, error: "Failed to update profile" }
      }
    } catch (err) {
      return { success: false, error: "Network error. Please try again." }
    }
  }

  const updateProfilePicture = async (file) => {
    try {
      const formData = new FormData()
      formData.append("new_picture", file)

      const response = await apiCall("/profile/picture", {
        method: "PUT",
        body: formData,
      })

      if (response.ok) {
        // Refresh the profile picture
        const newResponse = await apiCall("/profile/picture")
        if (newResponse.ok) {
          const blob = await newResponse.blob()
          const imageUrl = URL.createObjectURL(blob)
          setProfilePicture(imageUrl)
        }
        return { success: true }
      } else {
        const errorData = await response.json()

        // Handle 422 validation errors with detail array
        if (errorData.detail && Array.isArray(errorData.detail)) {
          const errorMessages = errorData.detail
            .map((err) => {
              if (typeof err === "object" && err.msg) {
                return improveErrorMessage(err.msg)
              }
              return String(err)
            })
            .join(", ")
          return { success: false, error: errorMessages }
        }

        // Handle single detail string
        if (typeof errorData.detail === "string") {
          return { success: false, error: improveErrorMessage(errorData.detail) }
        }

        // Handle validation error object with msg property
        if (typeof errorData === "object" && errorData.msg) {
          return { success: false, error: improveErrorMessage(errorData.msg) }
        }

        return { success: false, error: "Failed to update profile picture" }
      }
    } catch (err) {
      return { success: false, error: "Network error. Please try again." }
    }
  }

  useEffect(() => {
    if (isAuthenticated) {
      loadProfileInfo()
      loadProfilePicture()
    } else {
      // Reset state when user logs out
      setProfileInfo({ name: "", surname: "", phoneNumber: "" })
      setProfilePicture(null)
      profileInfoLoaded.current = false
      profilePictureLoaded.current = false
      profileInfoLoading.current = false
      profilePictureLoading.current = false
    }
  }, [isAuthenticated, loadProfileInfo, loadProfilePicture])

  const value = {
    profileInfo,
    profilePicture,
    loading,
    pictureLoading,
    loadProfileInfo,
    loadProfilePicture,
    updateProfileInfo,
    updateProfilePicture,
  }

  return <ProfileContext.Provider value={value}>{children}</ProfileContext.Provider>
}