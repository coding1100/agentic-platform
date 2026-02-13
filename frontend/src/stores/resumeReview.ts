import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface ResumeReviewReport {
  overall_score: number
  ats_score: number
  match_summary: string
  strengths: string[]
  weaknesses: string[]
  missing_keywords: string[]
  formatting_issues: string[]
  recommendations: string[]
  sections_to_improve: {
    summary: {
      current: string
      suggested: string
      reason: string
    }
    experience: {
      current: string
      suggested: string
      reason: string
    }[]
    skills: {
      current: string
      suggested: string
      reason: string
    }
  }
  error?: string
  message?: string
}

export const useResumeReviewStore = defineStore('resumeReview', () => {
  const resumeText = ref<string>('')
  const jobDescription = ref<string>('')
  const targetRole = ref<string>('')
  const seniority = ref<'junior' | 'mid' | 'senior' | 'lead'>('mid')

  const loading = ref(false)
  const error = ref<string | null>(null)
  const report = ref<ResumeReviewReport | null>(null)
  const conversationId = ref<string | null>(null)

  function setConversationId(id: string | null) {
    conversationId.value = id
  }

  function setReport(newReport: ResumeReviewReport | null) {
    report.value = newReport
  }

  function setError(message: string | null) {
    error.value = message
  }

  function setLoading(value: boolean) {
    loading.value = value
  }

  function reset() {
    resumeText.value = ''
    jobDescription.value = ''
    targetRole.value = ''
    seniority.value = 'mid'
    loading.value = false
    error.value = null
    report.value = null
    conversationId.value = null
  }

  return {
    resumeText,
    jobDescription,
    targetRole,
    seniority,
    loading,
    error,
    report,
    conversationId,
    setConversationId,
    setReport,
    setError,
    setLoading,
    reset,
  }
})

