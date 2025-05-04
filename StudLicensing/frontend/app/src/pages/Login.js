import React, { useState } from "react";
import { postToken } from "../services/api";

export default function Login() {
  // State for storing username, password
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  // Login function to handle the login request
  const handleLogin = async () => {
    try {
      // Sending a request to the backend API with username and password
      const data = await postToken(`grant_type=password&username=${username}&password=${password}`);
      alert(`Welcome, ${data.name}`);
    } catch (err) {
      alert("Login failed. Please check your credentials.");
    }
  };

  return (
    <div className="flex flex-col items-center justify-center h-screen bg-gray-100">
      <h1 className="text-3xl font-bold text-blue-500 mb-6">StudLicensing</h1> {/* Website Name */}
      
      <div className="w-full max-w-xs bg-white p-8 rounded-lg shadow-lg">
        <h2 className="text-2xl font-semibold mb-4">Login</h2>
        
        <div className="mb-4">
          <label htmlFor="username" className="block text-sm font-medium text-gray-700">Username</label>
          <input
            id="username"
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="mt-1 p-2 w-full border border-gray-300 rounded-md"
            placeholder="Enter your username"
          />
        </div>
        
        <div className="mb-6">
          <label htmlFor="password" className="block text-sm font-medium text-gray-700">Password</label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="mt-1 p-2 w-full border border-gray-300 rounded-md"
            placeholder="Enter your password"
          />
        </div>
        
        <button
          onClick={handleLogin}
          className="w-full py-2 bg-blue-500 text-white font-semibold rounded-md hover:bg-blue-600"
        >
          Login
        </button>
      </div>
    </div>
  );
}