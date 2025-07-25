import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom"
import { AuthProvider } from "./contexts/AuthContext"
import { ApiProvider } from "./contexts/ApiContext"
import { ThemeContextProvider } from "./contexts/ThemeContext"
import ProtectedRoute from "./components/ProtectedRoute"
import LoginPage from "./pages/LoginPage"
import ForgotPasswordPage from "./pages/ForgotPasswordPage"
import ValidateEmailPage from "./pages/ValidateEmailPage"
import ResetPasswordPage from "./pages/ResetPasswordPage"
import Dashboard from "./pages/Dashboard"
import AdminDashboard from "./pages/AdminDashboard"
import ProfilePage from "./pages/ProfilePage"
import ViewUserProfilePage from "./pages/ViewUserProfilePage" // Import the new page
import { ProfileProvider } from "./contexts/ProfileContext"

function App() {
  return (
    <ThemeContextProvider>
      <AuthProvider>
        <ApiProvider>
          <ProfileProvider>
            <Router>
              <Routes>
                <Route path="/login" element={<LoginPage />} />
                <Route path="/forgot-password" element={<ForgotPasswordPage />} />
                <Route path="/validate-email/:token" element={<ValidateEmailPage />} />
                <Route path="/reset-password/:token" element={<ResetPasswordPage />} />
                <Route
                  path="/dashboard"
                  element={
                    <ProtectedRoute>
                      <Dashboard />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/admin"
                  element={
                    <ProtectedRoute
                      requiredRoles={["admin", "company_admin", "company_developper", "company_commercial"]}
                    >
                      <AdminDashboard />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/profile"
                  element={
                    <ProtectedRoute>
                      <ProfilePage />
                    </ProtectedRoute>
                  }
                />
                {/* New route for viewing other user profiles */}
                <Route
                  path="/admin/users/:username/profile"
                  element={
                    <ProtectedRoute
                      requiredRoles={["admin", "company_admin", "company_developper", "company_commercial"]}
                    >
                      <ViewUserProfilePage />
                    </ProtectedRoute>
                  }
                />
                <Route path="/" element={<Navigate to="/login" replace />} />
              </Routes>
            </Router>
          </ProfileProvider>
        </ApiProvider>
      </AuthProvider>
    </ThemeContextProvider>
  )
}

export default App