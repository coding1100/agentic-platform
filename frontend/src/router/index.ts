import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useAgentsStore } from '@/stores/agents'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/Login.vue'),
      meta: { requiresAuth: false }
    },
    {
      path: '/signup',
      name: 'Signup',
      component: () => import('@/views/Signup.vue'),
      meta: { requiresAuth: false }
    },
    {
      path: '/dashboard',
      name: 'Dashboard',
      component: () => import('@/views/Dashboard.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/agents/new',
      name: 'AgentNew',
      component: () => import('@/views/AgentForm.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/agents/:agentId/edit',
      name: 'AgentEdit',
      component: () => import('@/views/AgentForm.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/agents/:agentId/chat',
      name: 'Chat',
      component: () => import('@/views/Chat.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/agents/:agentId/resume-review',
      name: 'ResumeReview',
      component: () => import('@/views/ResumeReview.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/agents/:agentId/course-creation',
      name: 'CourseCreation',
      component: () => import('@/views/CourseCreation.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/agents/:agentId/course-syllabus',
      name: 'CourseSyllabus',
      component: () => import('@/views/CourseSyllabus.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/api-keys',
      name: 'ApiKeys',
      component: () => import('@/views/ApiKeys.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/api-keys/documentation',
      name: 'ApiDocumentation',
      component: () => import('@/views/ApiDocumentation.vue'),
      meta: { requiresAuth: true }
    },
    {
      path: '/',
      redirect: '/dashboard'
    }
  ]
})

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/login')
  } else if ((to.path === '/login' || to.path === '/signup') && authStore.isAuthenticated) {
    next('/dashboard')
  } else {
    next()
  }
})

export default router

