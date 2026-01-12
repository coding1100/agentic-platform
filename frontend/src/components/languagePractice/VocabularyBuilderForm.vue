<template>
  <div class="vocabulary-builder-form">
    <div class="form-card">
      <h2>Vocabulary Builder 📚</h2>
      <p class="form-description">Learn new words with spaced repetition for maximum retention.</p>
      
      <!-- Category Selection -->
      <div class="category-section">
        <h3>Choose a Category</h3>
        <div class="category-grid">
          <button
            v-for="category in categories"
            :key="category.id"
            @click="selectCategory(category)"
            :class="['category-btn', { active: selectedCategory === category.id }]"
          >
            <span class="category-icon">{{ category.icon }}</span>
            <span class="category-name">{{ category.name }}</span>
          </button>
        </div>
      </div>

      <!-- Flashcard Practice -->
      <div v-if="selectedCategory && currentCard" class="flashcard-section">
        <div class="flashcard-stats">
          <span>Card {{ currentCardIndex + 1 }} of {{ cardsToReview.length }}</span>
          <span>Mastery: {{ currentCard.masteryLevel }}%</span>
        </div>

        <div class="flashcard-container">
          <div 
            class="flashcard"
            :class="{ flipped: isFlipped }"
            @click="flipCard"
          >
            <div class="flashcard-inner">
              <div class="flashcard-front">
                <div class="card-word">{{ currentCard.word }}</div>
                <div class="card-phonetic">{{ currentCard.phonetic }}</div>
                <button class="btn-audio" @click.stop="playAudio">🔊</button>
                <p class="flip-hint">Click to reveal translation</p>
              </div>
              <div class="flashcard-back">
                <div class="card-translation">{{ currentCard.translation }}</div>
                <div class="card-example">
                  <p class="example-sentence">{{ currentCard.exampleSentence }}</p>
                  <p class="example-translation">{{ currentCard.exampleTranslation }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="flashcard-actions">
          <button @click="markDifficult" class="btn-difficult">😓 Difficult</button>
          <button @click="markGood" class="btn-good">👍 Good</button>
          <button @click="markEasy" class="btn-easy">✨ Easy</button>
        </div>

        <div class="progress-info">
          <div class="mastery-bar">
            <div class="mastery-fill" :style="{ width: `${currentCard.masteryLevel}%` }"></div>
          </div>
          <p>Next Review: {{ formatNextReview(currentCard.nextReview) }}</p>
        </div>
      </div>

      <!-- Empty State -->
      <div v-else-if="selectedCategory && cardsToReview.length === 0" class="empty-state">
        <p>🎉 Great job! You've mastered all words in this category.</p>
        <p>Select another category or add new words!</p>
      </div>

      <!-- Study Stats -->
      <div v-if="selectedCategory" class="study-stats">
        <div class="stat-item">
          <span class="stat-label">Words Learned</span>
          <span class="stat-value">{{ languagePracticeStore.progressStats.totalWordsLearned }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">Today's Reviews</span>
          <span class="stat-value">{{ todayReviews }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">Streak</span>
          <span class="stat-value">🔥 {{ languagePracticeStore.progressStats.currentStreak }} days</span>
        </div>
      </div>
        
      <div class="form-actions">
        <button @click="handleBack" class="btn-back">← Back</button>
        <button @click="handleContinue" class="btn-primary">
          Continue to Grammar →
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useLanguagePracticeStore } from '@/stores/languagePractice'
import type { VocabularyCard } from '@/stores/languagePractice'

const emit = defineEmits<{
  complete: []
}>()

const languagePracticeStore = useLanguagePracticeStore()

const selectedCategory = ref<string | null>(null)
const isFlipped = ref(false)
const currentCardIndex = ref(0)
const todayReviews = ref(0)

interface Category {
  id: string
  name: string
  icon: string
}

const categories: Category[] = [
  { id: 'general', name: 'General', icon: '📖' },
  { id: 'travel', name: 'Travel', icon: '✈️' },
  { id: 'food', name: 'Food & Dining', icon: '🍽️' },
  { id: 'business', name: 'Business', icon: '💼' },
  { id: 'family', name: 'Family & Friends', icon: '👨‍👩‍👧‍👦' },
  { id: 'numbers', name: 'Numbers & Time', icon: '🔢' },
  { id: 'colors', name: 'Colors', icon: '🎨' },
  { id: 'emotions', name: 'Emotions', icon: '😊' }
]

const cardsToReview = computed(() => {
  if (!selectedCategory.value) return []
  // Filter cards by category and that need review
  const now = new Date()
  return languagePracticeStore.vocabularyCards
    .filter(card => card.category === selectedCategory.value && new Date(card.nextReview) <= now)
    .sort((a, b) => new Date(a.nextReview).getTime() - new Date(b.nextReview).getTime())
})

const currentCard = computed(() => {
  return cardsToReview.value[currentCardIndex.value] || null
})

function selectCategory(category: Category) {
  selectedCategory.value = category.id
  isFlipped.value = false
  currentCardIndex.value = 0
  
  // Generate sample cards if none exist (in production, this would come from AI)
  if (languagePracticeStore.vocabularyCards.length === 0) {
    generateSampleCards(category.id)
  }
}

function generateSampleCards(category: string) {
  const sampleWords: Record<string, Array<Partial<VocabularyCard>>> = {
    general: [
      { word: 'Hola', translation: 'Hello', phonetic: '/ˈo.la/', exampleSentence: 'Hola, ¿cómo estás?', exampleTranslation: 'Hello, how are you?', category: 'general', difficulty: 1 },
      { word: 'Gracias', translation: 'Thank you', phonetic: '/ˈɡɾa.sjas/', exampleSentence: 'Muchas gracias por tu ayuda.', exampleTranslation: 'Thank you very much for your help.', category: 'general', difficulty: 1 },
      { word: 'Por favor', translation: 'Please', phonetic: '/poɾ faˈβoɾ/', exampleSentence: 'Por favor, pásame el libro.', exampleTranslation: 'Please, pass me the book.', category: 'general', difficulty: 1 }
    ],
    travel: [
      { word: 'Aeropuerto', translation: 'Airport', phonetic: '/a.e.ɾoˈpweɾ.to/', exampleSentence: 'El aeropuerto está lejos.', exampleTranslation: 'The airport is far.', category: 'travel', difficulty: 2 },
      { word: 'Hotel', translation: 'Hotel', phonetic: '/oˈtel/', exampleSentence: 'Necesito una habitación en el hotel.', exampleTranslation: 'I need a room at the hotel.', category: 'travel', difficulty: 2 }
    ]
  }
  
  const words = sampleWords[category] || sampleWords.general
  words.forEach((word, index) => {
    const now = new Date()
    const nextReview = new Date(now.getTime() + (index * 60000)) // Stagger reviews
    
    languagePracticeStore.addVocabularyCard({
      id: `card-${category}-${index}`,
      word: word.word!,
      translation: word.translation!,
      phonetic: word.phonetic!,
      exampleSentence: word.exampleSentence!,
      exampleTranslation: word.exampleTranslation!,
      category: word.category!,
      difficulty: word.difficulty!,
      lastReviewed: null,
      nextReview: nextReview,
      reviewCount: 0,
      masteryLevel: 0
    })
  })
}

function flipCard() {
  isFlipped.value = !isFlipped.value
}

function playAudio() {
  // In production, this would use TTS API
  alert('Audio playback would be available here')
}

function markDifficult() {
  updateCardMastery(0.2)
}

function markGood() {
  updateCardMastery(0.6)
}

function markEasy() {
  updateCardMastery(1.0)
}

function updateCardMastery(performance: number) {
  if (!currentCard.value) return
  
  const newMastery = Math.min(100, currentCard.value.masteryLevel + (performance * 20))
  const now = new Date()
  
  // Spaced repetition algorithm: adjust next review based on performance
  let daysUntilNextReview = 1
  if (performance >= 0.8) {
    daysUntilNextReview = Math.min(30, Math.pow(2, currentCard.value.reviewCount))
  } else if (performance >= 0.5) {
    daysUntilNextReview = 1
  } else {
    daysUntilNextReview = 0.5 // Review again today
  }
  
  const nextReview = new Date(now.getTime() + (daysUntilNextReview * 24 * 60 * 60 * 1000))
  
  languagePracticeStore.updateVocabularyCard(currentCard.value.id, {
    masteryLevel: newMastery,
    lastReviewed: now,
    nextReview: nextReview,
    reviewCount: currentCard.value.reviewCount + 1
  })
  
  languagePracticeStore.addXP(10)
  languagePracticeStore.updateProgressStats({
    totalWordsLearned: languagePracticeStore.progressStats.totalWordsLearned + (newMastery >= 80 ? 1 : 0)
  })
  
  todayReviews.value++
  isFlipped.value = false
  
  // Move to next card
  if (currentCardIndex.value < cardsToReview.value.length - 1) {
    currentCardIndex.value++
  } else {
    // All cards reviewed, reset or show completion
    currentCardIndex.value = 0
  }
}

function formatNextReview(date: Date): string {
  const now = new Date()
  const diff = date.getTime() - now.getTime()
  const days = Math.ceil(diff / (1000 * 60 * 60 * 24))
  
  if (days <= 0) return 'Now'
  if (days === 1) return 'Tomorrow'
  return `In ${days} days`
}

function handleBack() {
  languagePracticeStore.setStep('learning-goals')
}

function handleContinue() {
  emit('complete')
}
</script>

<style scoped>
.vocabulary-builder-form {
  display: flex;
  justify-content: center;
  align-items: flex-start;
  min-height: 100%;
  padding: 20px 0;
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

.category-section {
  margin-bottom: 32px;
}

.category-section h3 {
  color: white;
  font-size: 18px;
  margin-bottom: 16px;
}

.category-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 12px;
}

.category-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.1);
  border: 2px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  color: white;
  cursor: pointer;
  transition: all 0.3s ease;
}

.category-btn:hover {
  background: rgba(255, 255, 255, 0.15);
  border-color: rgba(255, 255, 255, 0.3);
  transform: translateY(-2px);
}

.category-btn.active {
  background: rgba(102, 126, 234, 0.3);
  border-color: rgba(255, 255, 255, 0.5);
}

.category-icon {
  font-size: 32px;
}

.category-name {
  font-size: 14px;
  font-weight: 600;
}

.flashcard-section {
  margin-bottom: 32px;
}

.flashcard-stats {
  display: flex;
  justify-content: space-between;
  color: white;
  font-size: 14px;
  margin-bottom: 16px;
}

.flashcard-container {
  margin-bottom: 24px;
  perspective: 1000px;
  height: 300px;
}

.flashcard {
  width: 100%;
  height: 100%;
  position: relative;
  cursor: pointer;
}

.flashcard-inner {
  position: relative;
  width: 100%;
  height: 100%;
  transition: transform 0.6s;
  transform-style: preserve-3d;
}

.flashcard.flipped .flashcard-inner {
  transform: rotateY(180deg);
}

.flashcard-front,
.flashcard-back {
  position: absolute;
  width: 100%;
  height: 100%;
  backface-visibility: hidden;
  -webkit-backface-visibility: hidden;
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(20px);
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 20px;
  padding: 40px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.flashcard-back {
  transform: rotateY(180deg);
}

.card-word {
  font-size: 48px;
  font-weight: 700;
  color: white;
  margin-bottom: 12px;
}

.card-phonetic {
  font-size: 20px;
  color: rgba(255, 255, 255, 0.8);
  font-family: monospace;
  margin-bottom: 20px;
}

.btn-audio {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  border-radius: 50%;
  width: 50px;
  height: 50px;
  font-size: 24px;
  cursor: pointer;
  margin-top: 20px;
}

.flip-hint {
  margin-top: 20px;
  color: rgba(255, 255, 255, 0.7);
  font-size: 12px;
}

.card-translation {
  font-size: 36px;
  font-weight: 600;
  color: white;
  margin-bottom: 24px;
}

.card-example {
  margin-top: 24px;
}

.example-sentence {
  font-size: 18px;
  color: white;
  font-style: italic;
  margin-bottom: 8px;
}

.example-translation {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.8);
}

.flashcard-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  margin-bottom: 24px;
}

.btn-difficult, .btn-good, .btn-easy {
  flex: 1;
  padding: 12px 20px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 12px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-difficult {
  background: rgba(255, 87, 34, 0.3);
  color: white;
}

.btn-difficult:hover {
  background: rgba(255, 87, 34, 0.4);
}

.btn-good {
  background: rgba(255, 193, 7, 0.3);
  color: white;
}

.btn-good:hover {
  background: rgba(255, 193, 7, 0.4);
}

.btn-easy {
  background: rgba(76, 175, 80, 0.3);
  color: white;
}

.btn-easy:hover {
  background: rgba(76, 175, 80, 0.4);
}

.progress-info {
  text-align: center;
}

.mastery-bar {
  width: 100%;
  height: 8px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 12px;
}

.mastery-fill {
  height: 100%;
  background: linear-gradient(90deg, rgba(76, 175, 80, 0.8), rgba(102, 126, 234, 0.8));
  transition: width 0.3s ease;
}

.progress-info p {
  color: white;
  font-size: 12px;
}

.study-stats {
  display: flex;
  justify-content: space-around;
  padding: 20px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  margin-bottom: 24px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.stat-label {
  color: rgba(255, 255, 255, 0.7);
  font-size: 12px;
}

.stat-value {
  color: white;
  font-size: 18px;
  font-weight: 600;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: white;
}

.form-actions {
  display: flex;
  gap: 12px;
  margin-top: 24px;
}

.btn-back {
  flex: 1;
  padding: 14px 28px;
  background: rgba(255, 255, 255, 0.15);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 12px;
  font-size: 16px;
  cursor: pointer;
}

.btn-primary {
  flex: 2;
  padding: 14px 28px;
  background: rgba(255, 255, 255, 0.25);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
}
</style>

