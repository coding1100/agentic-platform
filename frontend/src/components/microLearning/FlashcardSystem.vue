<template>
  <div class="flashcard-system">
    <div v-if="isLoading" class="loading-state">
      <div class="loading-spinner"></div>
      <p>Creating flashcards...</p>
    </div>

    <div v-else-if="flashcards.length > 0" class="flashcards-container">
      <div class="flashcards-header">
        <h2>Flashcards 🃏</h2>
        <div class="flashcards-progress">
          Card {{ currentIndex + 1 }} of {{ flashcards.length }}
        </div>
      </div>

      <div class="flashcard-wrapper">
        <div
          class="flashcard"
          :class="{ flipped: isFlipped }"
          @click="flipCard"
        >
          <div class="flashcard-front">
            <div class="flashcard-content">
              <div class="flashcard-label">Question</div>
              <div class="flashcard-text">{{ currentCard.question }}</div>
            </div>
            <div class="flip-hint">Click to reveal answer</div>
          </div>
          <div class="flashcard-back">
            <div class="flashcard-content">
              <div class="flashcard-label">Answer</div>
              <div class="flashcard-text">{{ currentCard.answer }}</div>
            </div>
            <div class="mastery-controls">
              <p class="mastery-question">How well did you know this?</p>
              <div class="mastery-buttons">
                <button
                  v-for="level in masteryLevels"
                  :key="level.value"
                  @click.stop="rateMastery(level.value)"
                  class="mastery-btn"
                  :class="level.class"
                >
                  {{ level.label }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="flashcards-actions">
        <button @click="previousCard" :disabled="currentIndex === 0" class="btn-secondary">
          ← Previous
        </button>
        <button @click="shuffleCards" class="btn-secondary">
          🔀 Shuffle
        </button>
        <button @click="nextCard" :disabled="currentIndex === flashcards.length - 1" class="btn-secondary">
          Next →
        </button>
      </div>

      <div class="flashcards-footer">
        <button @click="handleComplete" class="btn-primary btn-large">
          Finish Review
        </button>
      </div>
    </div>

    <div v-else class="flashcards-start">
      <div class="start-card">
        <h2>Create Flashcards</h2>
        <p>Generate flashcards for spaced repetition learning</p>
        <div class="topic-input-group">
          <input
            v-model="topic"
            @keyup.enter="requestFlashcards"
            type="text"
            placeholder="Enter topic (e.g., Python basics)"
            class="input-field"
          />
          <button @click="requestFlashcards" class="btn-primary" :disabled="!topic.trim()">
            Create Flashcards
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useMicroLearningStore } from '@/stores/microLearning'
import { useChatStore } from '@/stores/chat'
import { useRoute } from 'vue-router'

const emit = defineEmits<{
  complete: []
}>()

const microLearningStore = useMicroLearningStore()
const chatStore = useChatStore()
const route = useRoute()

const isLoading = ref(false)
const flashcards = ref<any[]>([])
const currentIndex = ref(0)
const isFlipped = ref(false)
const topic = ref('')

const agentId = route.params.agentId as string

const currentCard = computed(() => {
  return flashcards.value[currentIndex.value] || { question: '', answer: '' }
})

const masteryLevels = [
  { value: 1, label: 'Poor', class: 'poor' },
  { value: 2, label: 'Fair', class: 'fair' },
  { value: 3, label: 'Good', class: 'good' },
  { value: 4, label: 'Great', class: 'great' },
  { value: 5, label: 'Mastered', class: 'mastered' }
]

onMounted(() => {
  // Load existing flashcards or use topic from current lesson
  if (microLearningStore.flashcards.length > 0) {
    flashcards.value = microLearningStore.flashcards
  } else if (microLearningStore.currentLesson?.topic) {
    topic.value = microLearningStore.currentLesson.topic
  }
})

function requestFlashcards() {
  if (!topic.value.trim()) return
  
  isLoading.value = true
  
  const message = `Create flashcards about ${topic.value} for spaced repetition learning. Use the create_flashcards tool with topic="${topic.value}", num_cards=5.`

  chatStore.sendMessage(agentId, message, microLearningStore.conversationId || undefined)
    .then(async (result) => {
      if (result.success) {
        await pollForFlashcards()
      } else {
        isLoading.value = false
      }
    })
    .catch(() => {
      isLoading.value = false
    })
}

async function pollForFlashcards(maxAttempts = 20) {
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    if (microLearningStore.conversationId) {
      try {
        await chatStore.fetchConversation(microLearningStore.conversationId)
        
        const messages = chatStore.messages
        if (messages.length > 0) {
          const lastMessage = messages[messages.length - 1]
          if (lastMessage.role === 'assistant' && lastMessage.content) {
            // Parse flashcards from content
            const cards = parseFlashcards(lastMessage.content)
            if (cards.length > 0) {
              flashcards.value = cards.map((card, idx) => ({
                id: `card-${idx}`,
                question: card.q,
                answer: card.a,
                topic: topic.value,
                masteryLevel: 0,
                timesReviewed: 0
              }))
              
              microLearningStore.addFlashcards(flashcards.value)
              isLoading.value = false
              return
            }
          }
        }
      } catch (error) {
        console.error('Error fetching conversation:', error)
      }
    }
    
    await new Promise(resolve => setTimeout(resolve, 1000))
  }
  
  isLoading.value = false
}

function parseFlashcards(content: string): Array<{ q: string; a: string }> {
  const cards: Array<{ q: string; a: string }> = []
  
  // Pattern: **Card N:** Q: ... A: ...
  const cardPattern = /\*\*Card\s+\d+:\*\*\s*Q:\s*(.+?)\s*A:\s*(.+?)(?=\*\*Card|$)/gis
  let match
  
  while ((match = cardPattern.exec(content)) !== null) {
    cards.push({
      q: match[1].trim(),
      a: match[2].trim()
    })
  }
  
  return cards
}

function flipCard() {
  isFlipped.value = !isFlipped.value
}

function rateMastery(level: number) {
  const card = flashcards.value[currentIndex.value]
  if (card) {
    microLearningStore.updateFlashcardMastery(card.id, level)
    // Move to next card after rating
    setTimeout(() => {
      if (currentIndex.value < flashcards.value.length - 1) {
        nextCard()
      }
    }, 500)
  }
}

function nextCard() {
  if (currentIndex.value < flashcards.value.length - 1) {
    currentIndex.value++
    isFlipped.value = false
  }
}

function previousCard() {
  if (currentIndex.value > 0) {
    currentIndex.value--
    isFlipped.value = false
  }
}

function shuffleCards() {
  // Fisher-Yates shuffle
  for (let i = flashcards.value.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [flashcards.value[i], flashcards.value[j]] = [flashcards.value[j], flashcards.value[i]]
  }
  currentIndex.value = 0
  isFlipped.value = false
}

function handleComplete() {
  emit('complete')
}
</script>

<style scoped>
.flashcard-system {
  max-width: 700px;
  margin: 0 auto;
}

.loading-state {
  text-align: center;
  padding: 4rem 2rem;
  color: white;
}

.loading-spinner {
  width: 50px;
  height: 50px;
  border: 4px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.flashcards-container {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 24px;
  padding: 2rem;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.flashcards-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #f0f0f0;
}

.flashcards-header h2 {
  margin: 0;
  color: #333;
}

.flashcards-progress {
  color: #666;
  font-weight: 500;
}

.flashcard-wrapper {
  perspective: 1000px;
  margin-bottom: 2rem;
  min-height: 400px;
}

.flashcard {
  position: relative;
  width: 100%;
  height: 400px;
  transform-style: preserve-3d;
  transition: transform 0.6s;
  cursor: pointer;
}

.flashcard.flipped {
  transform: rotateY(180deg);
}

.flashcard-front,
.flashcard-back {
  position: absolute;
  width: 100%;
  height: 100%;
  backface-visibility: hidden;
  border-radius: 16px;
  padding: 2rem;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.flashcard-front {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
}

.flashcard-back {
  background: linear-gradient(135deg, #f093fb, #f5576c);
  color: white;
  transform: rotateY(180deg);
}

.flashcard-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.flashcard-label {
  font-size: 0.9rem;
  opacity: 0.8;
  margin-bottom: 1rem;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.flashcard-text {
  font-size: 1.5rem;
  line-height: 1.6;
  font-weight: 500;
}

.flip-hint {
  text-align: center;
  opacity: 0.7;
  font-size: 0.9rem;
  margin-top: 1rem;
}

.mastery-controls {
  margin-top: 2rem;
}

.mastery-question {
  text-align: center;
  margin-bottom: 1rem;
  font-weight: 500;
}

.mastery-buttons {
  display: flex;
  gap: 0.5rem;
  justify-content: center;
  flex-wrap: wrap;
}

.mastery-btn {
  background: rgba(255, 255, 255, 0.2);
  border: 2px solid rgba(255, 255, 255, 0.3);
  color: white;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s;
}

.mastery-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: translateY(-2px);
}

.flashcards-actions {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.btn-secondary {
  background: white;
  color: #667eea;
  border: 2px solid #667eea;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.2s;
}

.btn-secondary:hover:not(:disabled) {
  background: #f0f0f0;
}

.btn-secondary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.flashcards-footer {
  text-align: center;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  border: none;
  padding: 0.75rem 2rem;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  transition: transform 0.2s;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-large {
  width: 100%;
  padding: 1rem;
  font-size: 1.1rem;
}

.flashcards-start {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
}

.start-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 24px;
  padding: 3rem;
  text-align: center;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  max-width: 500px;
  width: 100%;
}

.start-card h2 {
  color: #333;
  margin-bottom: 1rem;
}

.topic-input-group {
  display: flex;
  gap: 0.5rem;
  margin-top: 1.5rem;
}

.input-field {
  flex: 1;
  padding: 0.75rem 1rem;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  font-size: 1rem;
}

.input-field:focus {
  outline: none;
  border-color: #667eea;
}

@media (max-width: 768px) {
  .flashcard-wrapper {
    min-height: 300px;
  }

  .flashcard {
    height: 300px;
  }

  .flashcard-text {
    font-size: 1.2rem;
  }

  .flashcards-actions {
    flex-direction: column;
  }
}
</style>






