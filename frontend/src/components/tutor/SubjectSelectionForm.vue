<template>
  <div class="subject-selection-form">
    <div class="form-card">
      <h2>Choose a Subject 📚</h2>
      <p class="form-description">
        What subject would you like to learn today? Enter any subject and I'll help you get started!
      </p>
      
      <!-- Subject Input -->
      <div class="subject-input-container">
        <input
          v-model="subjectInput"
          @keyup.enter="handleSubmit"
          type="text"
          placeholder="e.g., Mathematics, Science, English, History, Geography..."
          :disabled="isValidating"
          class="subject-input"
        />
        <button
          @click="handleSubmit"
          class="btn-submit"
          :disabled="!subjectInput.trim() || isValidating"
        >
          <span v-if="!isValidating">Continue</span>
          <span v-else class="validating-text">Validating...</span>
        </button>
      </div>

      <!-- Validation Message -->
      <div v-if="validationMessage" :class="['validation-message', validationMessage.type]">
        <p>{{ validationMessage.text }}</p>
      </div>

      <!-- Loading State -->
      <div v-if="isValidating" class="validating-state">
        <div class="spinner-small"></div>
        <p>AI is analyzing your subject...</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRoute } from 'vue-router'
import { useChatStore } from '@/stores/chat'
import { useTutorStore } from '@/stores/tutor'
import type { Subject } from '@/stores/tutor'

const emit = defineEmits<{
  complete: [subject: Subject]
}>()

const route = useRoute()
const chatStore = useChatStore()
const tutorStore = useTutorStore()

const subjectInput = ref('')
const isValidating = ref(false)
const validationMessage = ref<{ type: 'error' | 'success'; text: string } | null>(null)

async function handleSubmit() {
  if (!subjectInput.value.trim() || isValidating.value) return

  const subject = subjectInput.value.trim()
  isValidating.value = true
  validationMessage.value = null

  try {
    const agentId = route.params.agentId as string
    const childName = tutorStore.childDetails.name

    const message = `The student ${childName} wants to learn "${subject}". 

Please validate if this is a valid educational subject. 

If it's valid, respond with:
**VALID_SUBJECT:** [subject name]

If it's not a valid subject, respond with:
**INVALID_SUBJECT:** Please enter a valid educational subject. Examples include: Mathematics, Science, English, History, Geography, Physics, Chemistry, Biology, Literature, Art, Music, etc.`

    const result = await chatStore.sendMessage(
      agentId,
      message,
      tutorStore.conversationId || undefined
    )

    if (result.success) {
      // Poll for the response
      await pollForValidation(subject)
    } else {
      validationMessage.value = {
        type: 'error',
        text: result.error || 'Failed to validate subject. Please try again.'
      }
      isValidating.value = false
    }
  } catch (err: any) {
    validationMessage.value = {
      type: 'error',
      text: err.message || 'An error occurred while validating the subject'
    }
    isValidating.value = false
  }
}

async function pollForValidation(subject: string, maxAttempts = 15, delay = 1000) {
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    if (tutorStore.conversationId) {
      try {
        await chatStore.fetchConversation(tutorStore.conversationId)
        
        const newMessages = chatStore.messages
        if (newMessages.length > 0) {
          // Check the last few messages for validation result
          const recentMessages = [...newMessages].reverse().slice(0, 5)
          
          for (const message of recentMessages) {
            if (message.role === 'assistant' && message.content) {
              const validationResult = parseValidationResponse(message.content)
              
              if (validationResult.isValid) {
                // Subject is valid - proceed
                isValidating.value = false
                validationMessage.value = {
                  type: 'success',
                  text: `Great! Let's learn ${validationResult.subjectName || subject}!`
                }
                
                // Store the validated subject name (AI might normalize it)
                const validatedSubject = validationResult.subjectName || subject
                tutorStore.setSelectedSubject(validatedSubject.toLowerCase())
                
                // Small delay to show success message, then proceed
                setTimeout(() => {
                  emit('complete', validatedSubject.toLowerCase() as Subject)
                }, 1000)
                return
              } else if (validationResult.isInvalid) {
                // Subject is invalid - show error
                isValidating.value = false
                validationMessage.value = {
                  type: 'error',
                  text: validationResult.errorMessage || 'Please enter a valid educational subject.'
                }
                return
              }
            }
          }
        }
      } catch (err) {
        console.error('Error fetching conversation:', err)
      }
    }
    
    const waitTime = Math.min(delay * Math.pow(1.2, attempt), 2500)
    await new Promise(resolve => setTimeout(resolve, waitTime))
  }
  
  // Timeout - assume valid and proceed (better UX than blocking)
  isValidating.value = false
  validationMessage.value = {
    type: 'success',
    text: `Let's proceed with ${subject}!`
  }
  tutorStore.setSelectedSubject(subject.toLowerCase())
  setTimeout(() => {
    emit('complete', subject.toLowerCase() as Subject)
  }, 1000)
}

function parseValidationResponse(content: string): {
  isValid: boolean
  isInvalid: boolean
  subjectName?: string
  errorMessage?: string
} {
  // Check for VALID_SUBJECT marker
  const validMatch = content.match(/\*\*VALID_SUBJECT:\*\*\s*(.+)/i)
  if (validMatch) {
    return {
      isValid: true,
      isInvalid: false,
      subjectName: validMatch[1].trim()
    }
  }

  // Check for INVALID_SUBJECT marker
  const invalidMatch = content.match(/\*\*INVALID_SUBJECT:\*\*\s*(.+)/i)
  if (invalidMatch) {
    return {
      isValid: false,
      isInvalid: true,
      errorMessage: invalidMatch[1].trim()
    }
  }

  // Fallback: Check if response contains validation keywords
  const lowerContent = content.toLowerCase()
  if (lowerContent.includes('valid') && (lowerContent.includes('subject') || lowerContent.includes('educational'))) {
    // Extract subject name if mentioned
    const subjectMatch = content.match(/(?:subject|learn|study)\s+(?:is\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)/i)
    if (subjectMatch) {
      return {
        isValid: true,
        isInvalid: false,
        subjectName: subjectMatch[1].trim()
      }
    }
    return { isValid: true, isInvalid: false }
  }

  if (lowerContent.includes('invalid') || lowerContent.includes('not a valid') || lowerContent.includes('please enter')) {
    // Extract error message
    const errorMatch = content.match(/(?:please|try|enter|use).+?subject[^.]*\.?/i)
    return {
      isValid: false,
      isInvalid: true,
      errorMessage: errorMatch ? errorMatch[0] : 'Please enter a valid educational subject.'
    }
  }

  // Default: assume valid if we can't determine
  return { isValid: false, isInvalid: false }
}
</script>

<style scoped>
.subject-selection-form {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100%;
}

.form-card {
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 24px;
  padding: 40px;
  width: 100%;
  max-width: 700px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

h2 {
  color: white;
  font-size: 28px;
  margin: 0 0 12px 0;
  font-weight: 700;
  text-align: center;
}

.form-description {
  color: rgba(255, 255, 255, 0.9);
  font-size: 16px;
  text-align: center;
  margin-bottom: 32px;
  line-height: 1.6;
}

.subject-input-container {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
}

.subject-input {
  flex: 1;
  padding: 16px 20px;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border: 2px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  color: white;
  font-size: 16px;
  transition: all 0.3s ease;
}

.subject-input::placeholder {
  color: rgba(255, 255, 255, 0.5);
}

.subject-input:focus {
  outline: none;
  border-color: rgba(255, 255, 255, 0.4);
  background: rgba(255, 255, 255, 0.15);
}

.subject-input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-submit {
  padding: 16px 32px;
  background: rgba(255, 255, 255, 0.25);
  backdrop-filter: blur(10px);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  white-space: nowrap;
}

.btn-submit:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.35);
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
}

.btn-submit:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.validating-text {
  display: flex;
  align-items: center;
  gap: 8px;
}

.validation-message {
  padding: 16px 20px;
  border-radius: 12px;
  margin-top: 16px;
  animation: slideIn 0.3s ease;
}

.validation-message.success {
  background: rgba(76, 175, 80, 0.2);
  border: 1px solid rgba(76, 175, 80, 0.4);
}

.validation-message.error {
  background: rgba(244, 67, 54, 0.2);
  border: 1px solid rgba(244, 67, 54, 0.4);
}

.validation-message p {
  color: white;
  margin: 0;
  font-size: 14px;
  line-height: 1.5;
}

.validating-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  padding: 20px;
  margin-top: 16px;
}

.spinner-small {
  width: 32px;
  height: 32px;
  border: 3px solid rgba(255, 255, 255, 0.2);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.validating-state p {
  color: rgba(255, 255, 255, 0.9);
  font-size: 14px;
  margin: 0;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>

