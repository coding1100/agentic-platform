<template>
  <div class="progress-dashboard">
    <div class="dashboard-header">
      <h2>Your Learning Dashboard</h2>
      <p class="dashboard-subtitle">Keep your streak going! 🔥</p>
    </div>

    <!-- Stats Cards -->
    <div class="stats-grid">
      <div class="stat-card streak-card">
        <div class="stat-icon">🔥</div>
        <div class="stat-content">
          <div class="stat-value">{{ progress.currentStreak }}</div>
          <div class="stat-label">Day Streak</div>
          <div class="stat-subtext">Best: {{ progress.longestStreak }} days</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon">📚</div>
        <div class="stat-content">
          <div class="stat-value">{{ progress.totalLessons }}</div>
          <div class="stat-label">Lessons Completed</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon">⏱️</div>
        <div class="stat-content">
          <div class="stat-value">{{ totalHours }}</div>
          <div class="stat-label">Hours Learned</div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon">📖</div>
        <div class="stat-content">
          <div class="stat-value">{{ progress.topicsLearned.length }}</div>
          <div class="stat-label">Topics Explored</div>
        </div>
      </div>
    </div>

    <!-- Quick Actions -->
    <div class="quick-actions">
      <h3>Quick Actions</h3>
      <div class="actions-grid">
        <button @click="handleStartLesson" class="action-card primary">
          <div class="action-icon">📖</div>
          <div class="action-content">
            <div class="action-title">Start Today's Lesson</div>
            <div class="action-subtitle">{{ timePerDay }} minutes</div>
          </div>
          <div class="action-arrow">→</div>
        </button>

        <button 
          @click="handleReviewFlashcards" 
          class="action-card"
          :class="{ 'has-notifications': cardsDueForReview.length > 0 }"
        >
          <div class="action-icon">🃏</div>
          <div class="action-content">
            <div class="action-title">Review Flashcards</div>
            <div class="action-subtitle">
              {{ cardsDueForReview.length > 0 ? `${cardsDueForReview.length} due` : 'All caught up!' }}
            </div>
          </div>
          <div class="action-arrow">→</div>
          <div v-if="cardsDueForReview.length > 0" class="notification-badge">
            {{ cardsDueForReview.length }}
          </div>
        </button>

        <button @click="handleViewProgress" class="action-card">
          <div class="action-icon">📊</div>
          <div class="action-content">
            <div class="action-title">View Progress</div>
            <div class="action-subtitle">See your learning journey</div>
          </div>
          <div class="action-arrow">→</div>
        </button>
      </div>
    </div>

    <!-- Topics Learned -->
    <div v-if="progress.topicsLearned.length > 0" class="topics-section">
      <h3>Topics You've Learned</h3>
      <div class="topics-grid">
        <div
          v-for="topic in progress.topicsLearned"
          :key="topic"
          class="topic-badge"
        >
          {{ topic }}
        </div>
      </div>
    </div>

    <!-- Daily Reminder -->
    <div v-if="!todayLearned" class="reminder-card">
      <div class="reminder-icon">💡</div>
      <div class="reminder-content">
        <div class="reminder-title">Don't break your streak!</div>
        <div class="reminder-text">Complete a lesson today to keep it going</div>
      </div>
      <button @click="handleStartLesson" class="btn-reminder">
        Start Now →
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useMicroLearningStore } from '@/stores/microLearning'

const emit = defineEmits<{
  'start-lesson': []
  'review-flashcards': []
  'view-progress': []
}>()

const microLearningStore = useMicroLearningStore()

const progress = computed(() => microLearningStore.progress)
const todayLearned = computed(() => microLearningStore.todayLearned)
const cardsDueForReview = computed(() => microLearningStore.cardsDueForReview)
const timePerDay = computed(() => microLearningStore.onboardingData.timePerDay)

const totalHours = computed(() => {
  return Math.round((progress.value.totalTimeMinutes / 60) * 10) / 10
})

function handleStartLesson() {
  emit('start-lesson')
}

function handleReviewFlashcards() {
  emit('review-flashcards')
}

function handleViewProgress() {
  emit('view-progress')
}
</script>

<style scoped>
.progress-dashboard {
  max-width: 1200px;
  margin: 0 auto;
}

.dashboard-header {
  text-align: center;
  margin-bottom: 2rem;
}

.dashboard-header h2 {
  color: white;
  font-size: 2.5rem;
  margin: 0 0 0.5rem 0;
}

.dashboard-subtitle {
  color: rgba(255, 255, 255, 0.9);
  font-size: 1.2rem;
  margin: 0;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  margin-bottom: 3rem;
}

.stat-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 16px;
  padding: 1.5rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s;
}

.stat-card:hover {
  transform: translateY(-2px);
}

.streak-card {
  background: linear-gradient(135deg, #ff6b6b, #ee5a6f);
  color: white;
}

.stat-icon {
  font-size: 3rem;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 2.5rem;
  font-weight: bold;
  line-height: 1;
  margin-bottom: 0.25rem;
}

.stat-label {
  font-size: 1rem;
  opacity: 0.9;
  font-weight: 500;
}

.stat-subtext {
  font-size: 0.85rem;
  opacity: 0.8;
  margin-top: 0.25rem;
}

.quick-actions {
  margin-bottom: 3rem;
}

.quick-actions h3 {
  color: white;
  font-size: 1.5rem;
  margin-bottom: 1rem;
}

.actions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.5rem;
}

.action-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 16px;
  padding: 1.5rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  cursor: pointer;
  border: 2px solid transparent;
  transition: all 0.3s;
  position: relative;
  text-align: left;
  width: 100%;
}

.action-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.action-card.primary {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  border-color: #667eea;
}

.action-card.has-notifications {
  border-color: #ff6b6b;
}

.action-icon {
  font-size: 2.5rem;
}

.action-content {
  flex: 1;
}

.action-title {
  font-size: 1.1rem;
  font-weight: 600;
  margin-bottom: 0.25rem;
}

.action-subtitle {
  font-size: 0.9rem;
  opacity: 0.8;
}

.action-arrow {
  font-size: 1.5rem;
  opacity: 0.6;
}

.notification-badge {
  position: absolute;
  top: -8px;
  right: -8px;
  background: #ff6b6b;
  color: white;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: bold;
  box-shadow: 0 2px 8px rgba(255, 107, 107, 0.4);
}

.topics-section {
  margin-bottom: 2rem;
}

.topics-section h3 {
  color: white;
  font-size: 1.5rem;
  margin-bottom: 1rem;
}

.topics-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.topic-badge {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  padding: 0.75rem 1.5rem;
  border-radius: 20px;
  font-weight: 500;
  color: #333;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.reminder-card {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 16px;
  padding: 1.5rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.reminder-icon {
  font-size: 2.5rem;
}

.reminder-content {
  flex: 1;
}

.reminder-title {
  font-weight: 600;
  font-size: 1.1rem;
  margin-bottom: 0.25rem;
  color: #333;
}

.reminder-text {
  color: #666;
  font-size: 0.9rem;
}

.btn-reminder {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  transition: transform 0.2s;
}

.btn-reminder:hover {
  transform: translateX(4px);
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }

  .actions-grid {
    grid-template-columns: 1fr;
  }

  .reminder-card {
    flex-direction: column;
    text-align: center;
  }
}
</style>

