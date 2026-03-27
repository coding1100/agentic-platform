import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import { createPinia, setActivePinia } from 'pinia'
import Login from '@/views/Login.vue'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', component: Login },
    { path: '/signup', component: { template: '<div>Signup</div>' } },
    { path: '/dashboard', component: { template: '<div>Dashboard</div>' } }
  ]
})

let pinia: ReturnType<typeof createPinia>

describe('Login Component', () => {
  beforeEach(async () => {
    pinia = createPinia()
    setActivePinia(pinia)
    await router.push('/login')
    await router.isReady()
  })

  it('should render login form', () => {
    const wrapper = mount(Login, {
      global: {
        plugins: [pinia, router]
      }
    })

    expect(wrapper.find('h1').text()).toBe('Agentic Platform')
    expect(wrapper.find('h2').text()).toBe('Login')
    expect(wrapper.find('input[type="email"]').exists()).toBe(true)
    expect(wrapper.find('input[type="password"]').exists()).toBe(true)
    expect(wrapper.find('button[type="submit"]').exists()).toBe(true)
  })

  it('should show error message on login failure', async () => {
    const authStore = useAuthStore()
    vi.spyOn(authStore, 'login').mockResolvedValue({
      success: false,
      error: 'Invalid credentials'
    })

    const wrapper = mount(Login, {
      global: {
        plugins: [pinia, router]
      }
    })

    const emailInput = wrapper.find('input[type="email"]')
    const passwordInput = wrapper.find('input[type="password"]')

    await emailInput.setValue('test@example.com')
    await passwordInput.setValue('wrongpassword')

    await wrapper.find('form').trigger('submit.prevent')
    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('Invalid credentials')
  })
})

