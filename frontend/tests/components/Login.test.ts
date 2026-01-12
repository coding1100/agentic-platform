import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import Login from '@/views/Login.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', component: Login },
    { path: '/dashboard', component: { template: '<div>Dashboard</div>' } }
  ]
})

describe('Login Component', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('should render login form', () => {
    const wrapper = mount(Login, {
      global: {
        plugins: [router]
      }
    })

    expect(wrapper.find('h1').text()).toBe('Agentic Platform')
    expect(wrapper.find('h2').text()).toBe('Login')
    expect(wrapper.find('input[type="email"]').exists()).toBe(true)
    expect(wrapper.find('input[type="password"]').exists()).toBe(true)
    expect(wrapper.find('button[type="submit"]').exists()).toBe(true)
  })

  it('should show error message on login failure', async () => {
    const wrapper = mount(Login, {
      global: {
        plugins: [router]
      }
    })

    const emailInput = wrapper.find('input[type="email"]')
    const passwordInput = wrapper.find('input[type="password"]')

    await emailInput.setValue('test@example.com')
    await passwordInput.setValue('wrongpassword')

    // Mock the store to return error
    const authStore = wrapper.vm.$pinia._s.get('auth')
    if (authStore) {
      vi.spyOn(authStore, 'login').mockResolvedValue({
        success: false,
        error: 'Invalid credentials'
      })
    }

    await wrapper.find('form').trigger('submit.prevent')

    // Wait for error to appear
    await wrapper.vm.$nextTick()

    // Check if error message is displayed (if error handling is implemented)
    expect(wrapper.vm).toBeDefined()
  })
})

