<template>
  <section class="practice-panel">
    <div class="panel-header">
      <div>
        <h3>{{ practiceSet.title }}</h3>
        <p>{{ practiceSet.instructions }}</p>
      </div>
      <button v-if="submitted" type="button" class="btn-secondary" @click="resetSession">
        Try Again
      </button>
    </div>

    <div v-if="practiceSet.questions.length === 0" class="empty-state">
      No practice questions were returned for this activity.
    </div>

    <div v-for="(question, index) in practiceSet.questions" :key="question.id" class="question-card">
      <div class="question-top">
        <span class="question-index">Q{{ index + 1 }}</span>
        <span v-if="question.concept" class="concept-chip">{{ question.concept }}</span>
      </div>
      <p class="question-prompt">{{ question.prompt }}</p>

      <div v-if="question.type === 'multiple_choice'" class="options-list">
        <label
          v-for="option in question.options"
          :key="option.id"
          :class="['option-row', submitted ? getOptionState(question, option.id) : '']"
        >
          <input
            v-model="answers[question.id]"
            :value="option.id"
            :disabled="submitted"
            type="radio"
            :name="question.id"
          />
          <span>{{ option.id }}. {{ option.text }}</span>
        </label>
      </div>

      <div v-else class="answer-field">
        <input
          v-model="answers[question.id]"
          :disabled="submitted"
          type="text"
          placeholder="Type your answer"
        />
      </div>

      <div v-if="submitted" :class="['feedback-box', isQuestionCorrect(question) ? 'correct' : 'incorrect']">
        <p>
          <strong>{{ isQuestionCorrect(question) ? 'Correct' : 'Needs review' }}.</strong>
          <span v-if="question.answer"> Expected answer: {{ question.answer }}.</span>
        </p>
        <p v-if="question.explanation">{{ question.explanation }}</p>
      </div>
    </div>

    <div v-if="practiceSet.questions.length > 0" class="actions-row">
      <button
        v-if="!submitted"
        type="button"
        class="btn-primary"
        :disabled="!allQuestionsAnswered"
        @click="submitPractice"
      >
        Submit Practice
      </button>
      <div v-else class="score-summary">
        <strong>{{ score }}%</strong>
        <span>{{ correctCount }} / {{ practiceSet.questions.length }} correct</span>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { TutorPracticeQuestion, TutorPracticeSet } from '@/types'

const props = defineProps<{
  practiceSet: TutorPracticeSet
}>()

const emit = defineEmits<{
  completed: [payload: { title: string; score: number; weakTopics: string[]; masteredTopics: string[] }]
}>()

const answers = ref<Record<string, string>>({})
const submitted = ref(false)
const score = ref(0)
const correctCount = ref(0)

watch(
  () => props.practiceSet,
  () => {
    resetSession()
  },
  { deep: true }
)

const allQuestionsAnswered = computed(() => {
  if (props.practiceSet.questions.length === 0) return false
  return props.practiceSet.questions.every((question) => {
    const value = answers.value[question.id]
    return typeof value === 'string' && value.trim().length > 0
  })
})

function normalizeValue(value: string | null | undefined) {
  return (value || '').trim().toLowerCase()
}

function isQuestionCorrect(question: TutorPracticeQuestion) {
  const submittedAnswer = answers.value[question.id]
  if (!submitted.value) return false
  return normalizeValue(submittedAnswer) === normalizeValue(question.answer)
}

function getOptionState(question: TutorPracticeQuestion, optionId: string) {
  const isSelected = answers.value[question.id] === optionId
  const isAnswer = normalizeValue(question.answer) === normalizeValue(optionId)
  if (isAnswer) return 'is-correct'
  if (isSelected && !isAnswer) return 'is-incorrect'
  return ''
}

function submitPractice() {
  const total = props.practiceSet.questions.length
  let correct = 0
  const weakTopics: string[] = []
  const masteredTopics: string[] = []

  for (const question of props.practiceSet.questions) {
    if (isQuestionCorrect(question)) {
      correct += 1
      if (question.concept) {
        masteredTopics.push(question.concept)
      }
    } else if (question.concept) {
      weakTopics.push(question.concept)
    } else {
      weakTopics.push(question.prompt.slice(0, 60))
    }
  }

  correctCount.value = correct
  score.value = Math.round((correct / total) * 100)
  submitted.value = true

  emit('completed', {
    title: props.practiceSet.title,
    score: score.value,
    weakTopics: Array.from(new Set(weakTopics)),
    masteredTopics: Array.from(new Set(masteredTopics)),
  })
}

function resetSession() {
  answers.value = {}
  submitted.value = false
  score.value = 0
  correctCount.value = 0
}
</script>

<style scoped>
.practice-panel {
  padding: 24px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.18);
  box-shadow: 0 16px 32px rgba(15, 23, 42, 0.12);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
  margin-bottom: 18px;
}

.panel-header h3 {
  color: white;
  margin: 0 0 6px 0;
  font-size: 22px;
}

.panel-header p {
  margin: 0;
  color: rgba(255, 255, 255, 0.82);
  line-height: 1.6;
}

.empty-state {
  color: rgba(255, 255, 255, 0.8);
  padding: 12px 0 4px;
}

.question-card {
  padding: 18px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.12);
  margin-bottom: 16px;
}

.question-top {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
}

.question-index {
  color: white;
  font-weight: 700;
}

.concept-chip {
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.16);
  color: white;
  font-size: 12px;
}

.question-prompt {
  color: white;
  font-size: 16px;
  line-height: 1.6;
  margin: 0 0 12px 0;
}

.options-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.option-row {
  display: flex;
  gap: 10px;
  align-items: center;
  padding: 12px 14px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.08);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.12);
}

.option-row input {
  margin: 0;
}

.option-row.is-correct {
  border-color: rgba(52, 211, 153, 0.7);
  background: rgba(16, 185, 129, 0.18);
}

.option-row.is-incorrect {
  border-color: rgba(248, 113, 113, 0.7);
  background: rgba(239, 68, 68, 0.18);
}

.answer-field input {
  width: 100%;
  padding: 12px 14px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.22);
  background: rgba(255, 255, 255, 0.12);
  color: white;
  font-size: 15px;
}

.answer-field input::placeholder {
  color: rgba(255, 255, 255, 0.62);
}

.feedback-box {
  margin-top: 14px;
  padding: 12px 14px;
  border-radius: 12px;
  color: white;
}

.feedback-box.correct {
  background: rgba(16, 185, 129, 0.18);
  border: 1px solid rgba(52, 211, 153, 0.45);
}

.feedback-box.incorrect {
  background: rgba(239, 68, 68, 0.18);
  border: 1px solid rgba(248, 113, 113, 0.45);
}

.feedback-box p {
  margin: 0 0 6px 0;
  line-height: 1.6;
}

.feedback-box p:last-child {
  margin-bottom: 0;
}

.actions-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  margin-top: 12px;
}

.btn-primary,
.btn-secondary {
  border: none;
  border-radius: 999px;
  padding: 10px 18px;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
}

.btn-primary {
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.95), rgba(29, 78, 216, 0.95));
  color: white;
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secondary {
  background: rgba(255, 255, 255, 0.16);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.18);
}

.score-summary {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  color: white;
}

.score-summary strong {
  font-size: 24px;
}

@media (max-width: 768px) {
  .panel-header,
  .actions-row {
    flex-direction: column;
    align-items: stretch;
  }

  .score-summary {
    align-items: flex-start;
  }
}
</style>
