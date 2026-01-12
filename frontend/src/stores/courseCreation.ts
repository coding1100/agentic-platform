import { defineStore } from 'pinia'
import { ref } from 'vue'

export type CourseCreationStep = 
  | 'course-overview'
  | 'course-structure'
  | 'assessment-design'
  | 'concept-mapping'
  | 'workflow-automation'
  | 'validation-review'
  | 'final-review'

export interface CourseOverview {
  title: string
  subject: string
  duration: number // weeks
  learningObjectives: string[]
  targetAudience: string
  difficulty: 'beginner' | 'intermediate' | 'advanced'
}

export interface CourseModule {
  id: string
  name: string
  description: string
  lessons: CourseLesson[]
  order: number
}

export interface CourseLesson {
  id: string
  title: string
  description: string
  duration: number // hours
  topics: string[]
  order: number
}

export interface AssessmentDesign {
  diagnostic: boolean
  formative: boolean
  summative: boolean
  comprehensive: boolean
  assessmentDetails: {
    type: string
    questions: number
    weight: number
  }[]
}

export interface ConceptMap {
  mainConcept: string
  relatedConcepts: {
    id: string
    name: string
    relationship: string
    level: number
  }[]
}

export interface WorkflowAutomation {
  enabled: boolean
  workflowName: string
  steps: string[]
  automationType: 'learning' | 'assessment' | 'content_creation' | 'course_delivery'
}

export interface ValidationResult {
  passed: boolean
  issues: {
    severity: 'high' | 'medium' | 'low'
    description: string
    recommendation: string
  }[]
  score: number
}

export interface MeetingNotes {
  date: string
  participants: string[]
  agenda: string[]
  decisions: string[]
  actionItems: {
    task: string
    owner: string
    dueDate: string
  }[]
}

export const useCourseCreationStore = defineStore('courseCreation', () => {
  const currentStep = ref<CourseCreationStep>('course-overview')
  const courseOverview = ref<CourseOverview>({
    title: '',
    subject: '',
    duration: 8,
    learningObjectives: [],
    targetAudience: '',
    difficulty: 'beginner'
  })
  const courseModules = ref<CourseModule[]>([])
  const assessmentDesign = ref<AssessmentDesign>({
    diagnostic: false,
    formative: false,
    summative: false,
    comprehensive: false,
    assessmentDetails: []
  })
  const conceptMap = ref<ConceptMap | null>(null)
  const workflowAutomation = ref<WorkflowAutomation>({
    enabled: false,
    workflowName: '',
    steps: [],
    automationType: 'learning'
  })
  const validationResult = ref<ValidationResult | null>(null)
  const meetingNotes = ref<MeetingNotes | null>(null)
  const conversationId = ref<string | null>(null)

  function setStep(step: CourseCreationStep) {
    currentStep.value = step
  }

  function setCourseOverview(overview: CourseOverview) {
    courseOverview.value = overview
  }

  function setCourseModules(modules: CourseModule[]) {
    courseModules.value = modules
  }

  function addModule(module: CourseModule) {
    courseModules.value.push(module)
  }

  function updateModule(moduleId: string, updates: Partial<CourseModule>) {
    const index = courseModules.value.findIndex(m => m.id === moduleId)
    if (index !== -1) {
      courseModules.value[index] = { ...courseModules.value[index], ...updates }
    }
  }

  function setAssessmentDesign(design: AssessmentDesign) {
    assessmentDesign.value = design
  }

  function setConceptMap(map: ConceptMap) {
    conceptMap.value = map
  }

  function setWorkflowAutomation(workflow: WorkflowAutomation) {
    workflowAutomation.value = workflow
  }

  function setValidationResult(result: ValidationResult) {
    validationResult.value = result
  }

  function setMeetingNotes(notes: MeetingNotes) {
    meetingNotes.value = notes
  }

  function setConversationId(id: string | null) {
    conversationId.value = id
  }

  function reset() {
    currentStep.value = 'course-overview'
    courseOverview.value = {
      title: '',
      subject: '',
      duration: 8,
      learningObjectives: [],
      targetAudience: '',
      difficulty: 'beginner'
    }
    courseModules.value = []
    assessmentDesign.value = {
      diagnostic: false,
      formative: false,
      summative: false,
      comprehensive: false,
      assessmentDetails: []
    }
    conceptMap.value = null
    workflowAutomation.value = {
      enabled: false,
      workflowName: '',
      steps: [],
      automationType: 'learning'
    }
    validationResult.value = null
    meetingNotes.value = null
    conversationId.value = null
  }

  return {
    // State
    currentStep,
    courseOverview,
    courseModules,
    assessmentDesign,
    conceptMap,
    workflowAutomation,
    validationResult,
    meetingNotes,
    conversationId,
    // Actions
    setStep,
    setCourseOverview,
    setCourseModules,
    addModule,
    updateModule,
    setAssessmentDesign,
    setConceptMap,
    setWorkflowAutomation,
    setValidationResult,
    setMeetingNotes,
    setConversationId,
    reset
  }
})






