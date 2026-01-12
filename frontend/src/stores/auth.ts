import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/services/api'
import type { User } from '@/types'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('token'))
  const currentUser = ref<User | null>(null)

  const isAuthenticated = computed(() => !!token.value)

  async function login(email: string, password: string) {
    try {
      const response = await authApi.login({ email, password })
      token.value = response.access_token
      localStorage.setItem('token', response.access_token)
      
      // Fetch user info
      await fetchCurrentUser()
      return { success: true }
    } catch (error: any) {
      return { success: false, error: error.response?.data?.detail || 'Login failed' }
    }
  }

  async function signup(email: string, password: string) {
    try {
      await authApi.signup({ email, password })
      return { success: true }
    } catch (error: any) {
      return { success: false, error: error.response?.data?.detail || 'Signup failed' }
    }
  }

  async function fetchCurrentUser() {
    try {
      const user = await authApi.getCurrentUser()
      currentUser.value = user
    } catch (error) {
      logout()
    }
  }

  function logout() {
    token.value = null
    currentUser.value = null
    localStorage.removeItem('token')
  }

  // Initialize user if token exists
  if (token.value) {
    fetchCurrentUser()
  }

  return {
    token,
    currentUser,
    isAuthenticated,
    login,
    signup,
    logout,
    fetchCurrentUser
  }
})

