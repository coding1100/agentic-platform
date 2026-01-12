import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '@/stores/auth'
import { authApi } from '@/services/api'

vi.mock('@/services/api', () => ({
  authApi: {
    login: vi.fn(),
    signup: vi.fn(),
    getCurrentUser: vi.fn(),
  }
}))

describe('Auth Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    localStorage.clear()
  })

  it('should initialize with no token', () => {
    const store = useAuthStore()
    expect(store.isAuthenticated).toBe(false)
    expect(store.token).toBe(null)
  })

  it('should login successfully', async () => {
    const store = useAuthStore()
    const mockToken = 'test-token'
    const mockUser = { id: '1', email: 'test@example.com', created_at: '2024-01-01' }

    vi.mocked(authApi.login).mockResolvedValue({ access_token: mockToken, token_type: 'bearer' })
    vi.mocked(authApi.getCurrentUser).mockResolvedValue(mockUser)

    const result = await store.login('test@example.com', 'password123')

    expect(result.success).toBe(true)
    expect(store.token).toBe(mockToken)
    expect(localStorage.setItem).toHaveBeenCalledWith('token', mockToken)
    expect(authApi.getCurrentUser).toHaveBeenCalled()
  })

  it('should handle login failure', async () => {
    const store = useAuthStore()
    vi.mocked(authApi.login).mockRejectedValue({ response: { data: { detail: 'Invalid credentials' } } })

    const result = await store.login('test@example.com', 'wrongpassword')

    expect(result.success).toBe(false)
    expect(result.error).toBe('Invalid credentials')
    expect(store.token).toBe(null)
  })

  it('should signup successfully', async () => {
    const store = useAuthStore()
    vi.mocked(authApi.signup).mockResolvedValue({ id: '1', email: 'test@example.com', created_at: '2024-01-01' })

    const result = await store.signup('test@example.com', 'password123')

    expect(result.success).toBe(true)
    expect(authApi.signup).toHaveBeenCalledWith({ email: 'test@example.com', password: 'password123' })
  })

  it('should logout', () => {
    const store = useAuthStore()
    store.token = 'test-token'
    store.currentUser = { id: '1', email: 'test@example.com', created_at: '2024-01-01' }

    store.logout()

    expect(store.token).toBe(null)
    expect(store.currentUser).toBe(null)
    expect(localStorage.removeItem).toHaveBeenCalledWith('token')
  })

  it('should fetch current user when token exists', async () => {
    localStorage.setItem('token', 'test-token')
    const store = useAuthStore()
    const mockUser = { id: '1', email: 'test@example.com', created_at: '2024-01-01' }
    vi.mocked(authApi.getCurrentUser).mockResolvedValue(mockUser)

    await store.fetchCurrentUser()

    expect(store.currentUser).toEqual(mockUser)
  })
})

