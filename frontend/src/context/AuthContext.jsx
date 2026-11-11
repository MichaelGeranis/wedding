import { useState } from 'react'
import { AuthContext } from './auth'

const TOKEN_KEY = 'authToken'

export const AuthProvider = ({ children }) => {
  // Read a stored token on first render, so there is no logged-out flash.
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY))

  const login = (authToken) => {
    localStorage.setItem(TOKEN_KEY, authToken)
    setToken(authToken)
  }

  const logout = () => {
    localStorage.removeItem(TOKEN_KEY)
    setToken(null)
  }

  const value = {
    token,
    isAuthenticated: token !== null,
    login,
    logout,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
