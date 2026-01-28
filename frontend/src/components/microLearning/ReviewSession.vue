<template>
  <div class="review-session">
    <div v-if="cardsToReview.length === 0" class="no-review">
      <div class="no-review-card">
        <div class="no-review-icon">✅</div>
        <h2>All Caught Up!</h2>
        <p>You don't have any cards due for review right now.</p>
        <button @click="handleComplete" class="btn-primary">
          Back to Dashboard
        </button>
      </div>
    </div>

    <div v-else class="review-container">
      <div class="review-header">
        <h2>Review Session 🔄</h2>
        <div class="review-progress">
          {{ currentIndex + 1 }} of {{ cardsToReview.length }} cards
        </div>
      </div>

      <div class="review-card-wrapper">
        <div
          class="review-card"
          :class="{ flipped: isFlipped }"
          @click="flipCard"
        >
          <div class="review-card-front">
            <div class="review-card-content">
              <div class="review-label">Question</div>
              <div class="review-text">{{ currentCard.question }}</div>
            </div>
            <div class="flip-hint">Click to see answer</div>
          </div>
          <div class="review-card-back">
            <div class="review-card-content">
              <div class="review-label">Answer</div>
              <div class="review-text">{{ currentCard.answer }}</div>
            </div>
            <div class="review-controls">
              <p class="review-question">How well do you remember this?</p>
              <div class="review-buttons">
                <button
                  @click.stop="rateCard(1)"
                  class="review-btn poor"
                >
                  Again
                </button>
                <button
                  @click.stop="rateCard(2)"
                  class="review-btn fair"
                >
                  Hard
                </button>
                <button
                  @click.stop="rateCard(3)"
                  class="review-btn good"
                >
                  Good
                </button>
                <button
                  @click.stop="rateCard(4)"
                  class="review-btn great"
                >
                  Easy
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="review-summary">
        <div class="summary-stats">
          <div class="stat">
            <span class="stat-value">{{ reviewedCount }}</span>
            <span class="stat-label">Reviewed</span>
          </div>
          <div class="stat">
            <span class="stat-value">{{ remainingCount }}</span>
            <span class="stat-label">Remaining</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useMicroLearningStore } from '@/stores/microLearning'

const emit = defineEmits<{
  complete: []
}>()

const microLearningStore = useMicroLearningStore()

const cardsToReview = computed(() => microLearningStore.cardsDueForReview)
const currentIndex = ref(0)
const isFlipped = ref(false)
const reviewedCount = ref(0)

const currentCard = computed(() => {
  return cardsToReview.value[currentIndex.value] || { question: '', answer: '', id: '' }
})

const remainingCount = computed(() => {
  return cardsToReview.value.length - reviewedCount.value
})

function flipCard() {
  isFlipped.value = !isFlipped.value
}

function rateCard(level: number) {
  const card = currentCard.value
  if (card && card.id) {
    microLearningStore.updateFlashcardMastery(card.id, level)
    reviewedCount.value++
    
    // Move to next card
    setTimeout(() => {
      if (currentIndex.value < cardsToReview.value.length - 1) {
        currentIndex.value++
        isFlipped.value = false
      } else {
        // All cards reviewed
        handleComplete()
      }
    }, 500)
  }
}

function handleComplete() {
  emit('complete')
}
</script>

<style scoped>
.review-session {
  max-width: 700px;
  margin: 0 auto;
}

.no-review {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
}

.no-review-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 24px;
  padding: 3rem;
  text-align: center;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  max-width: 500px;
}

.no-review-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
}

.no-review-card h2 {
  color: #333;
  margin-bottom: 1rem;
}

.no-review-card p {
  color: #666;
  margin-bottom: 2rem;
}

.review-container {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 24px;
  padding: 2rem;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.review-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #f0f0f0;
}

.review-header h2 {
  margin: 0;
  color: #333;
}

.review-progress {
  color: #666;
  font-weight: 500;
}

.review-card-wrapper {
  perspective: 1000px;
  margin-bottom: 2rem;
  min-height: 400px;
}

.review-card {
  position: relative;
  width: 100%;
  height: 400px;
  transform-style: preserve-3d;
  transition: transform 0.6s;
  cursor: pointer;
}

.review-card.flipped {
  transform: rotateY(180deg);
}

.review-card-front,
.review-card-back {
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

.review-card-front {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
}

.review-card-back {
  background: linear-gradient(135deg, #f093fb, #f5576c);
  color: white;
  transform: rotateY(180deg);
}

.review-card-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.review-label {
  font-size: 0.9rem;
  opacity: 0.8;
  margin-bottom: 1rem;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.review-text {
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

.review-controls {
  margin-top: 2rem;
}

.review-question {
  text-align: center;
  margin-bottom: 1rem;
  font-weight: 500;
}

.review-buttons {
  display: flex;
  gap: 0.5rem;
  justify-content: center;
  flex-wrap: wrap;
}

.review-btn {
  background: rgba(255, 255, 255, 0.2);
  border: 2px solid rgba(255, 255, 255, 0.3);
  color: white;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s;
  flex: 1;
  min-width: 100px;
}

.review-btn:hover {
  background: rgba(255, 255, 255, 0.3);
  transform: translateY(-2px);
}

.review-summary {
  margin-top: 2rem;
  padding-top: 1.5rem;
  border-top: 2px solid #f0f0f0;
}

.summary-stats {
  display: flex;
  justify-content: center;
  gap: 3rem;
}

.stat {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-value {
  font-size: 2rem;
  font-weight: bold;
  color: #667eea;
}

.stat-label {
  color: #666;
  font-size: 0.9rem;
  margin-top: 0.25rem;
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

.btn-primary:hover {
  transform: translateY(-2px);
}

@media (max-width: 768px) {
  .review-card-wrapper {
    min-height: 300px;
  }

  .review-card {
    height: 300px;
  }

  .review-text {
    font-size: 1.2rem;
  }

  .review-buttons {
    flex-direction: column;
  }
}
</style>





