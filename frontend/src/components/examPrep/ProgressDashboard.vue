<template>
  <div class="progress-dashboard">
    <div class="view-card">
      <h2>Progress Dashboard 📊</h2>
      <p class="view-description">Track your exam preparation progress and performance.</p>
      
      <!-- Loading State -->
      <div v-if="isLoading" class="loading-container">
        <div class="loading-spinner"></div>
        <p class="loading-text">Loading your progress...</p>
      </div>

      <!-- No Progress Data State -->
      <div v-else-if="!hasProgressData" class="empty-state">
        <div class="empty-icon">📈</div>
        <h3>No Progress Data Yet</h3>
        <p>Complete a practice exam to start tracking your progress.</p>
        <button @click="handleTakePractice" class="btn-primary">Start Practice Exam</button>
      </div>

      <!-- Progress Content -->
      <div v-else class="progress-content">
        <!-- Main Stats -->
        <div class="progress-stats">
          <div class="stat-card highlight">
            <div class="stat-icon">🎯</div>
            <div class="stat-value">{{ Math.round(displayProgress.readinessPercentage) }}%</div>
            <div class="stat-label">Exam Readiness</div>
            <div class="progress-bar">
              <div class="progress-fill" :style="{ width: Math.round(displayProgress.readinessPercentage) + '%' }"></div>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon">📊</div>
            <div class="stat-value">{{ displayProgress.averageScore.toFixed(1) }}%</div>
            <div class="stat-label">Average Score</div>
          </div>
          <div class="stat-card">
            <div class="stat-icon">🏆</div>
            <div class="stat-value">{{ displayProgress.bestScore }}%</div>
            <div class="stat-label">Best Score</div>
          </div>
          <div class="stat-card">
            <div class="stat-icon">📝</div>
            <div class="stat-value">{{ displayProgress.totalExams }}</div>
            <div class="stat-label">Exams Taken</div>
          </div>
        </div>

        <!-- Improvement Trend -->
        <div v-if="displayProgress.improvementRate !== 0" class="improvement-section">
          <div :class="['improvement-badge', displayProgress.improvementRate > 0 ? 'positive' : 'negative']">
            <span class="improvement-icon">{{ displayProgress.improvementRate > 0 ? '📈' : '📉' }}</span>
            <span class="improvement-text">
              {{ displayProgress.improvementRate > 0 ? '+' : '' }}{{ displayProgress.improvementRate.toFixed(1) }}% 
              improvement rate
            </span>
          </div>
        </div>

        <!-- Recent Scores -->
        <div v-if="recentScores.length > 0" class="recent-scores">
          <h3>Recent Practice Exams</h3>
          <div class="scores-list">
            <div v-for="(score, index) in recentScores" :key="index" class="score-item">
              <div class="score-info">
                <span class="score-subject">{{ score.subject || 'Practice Exam' }}</span>
                <span class="score-date">{{ formatDate(score.date) }}</span>
              </div>
              <div class="score-value" :class="getScoreClass(score.score)">
                {{ score.score }}%
              </div>
            </div>
          </div>
        </div>

        <!-- Milestones -->
        <div v-if="displayProgress.milestonesAchieved.length > 0" class="milestones-section">
          <h3>Milestones Achieved 🏅</h3>
          <div class="milestones-list">
            <div v-for="(milestone, index) in displayProgress.milestonesAchieved" :key="index" class="milestone-badge">
              ✓ {{ milestone }}
            </div>
          </div>
        </div>

        <!-- Quick Actions -->
        <div class="dashboard-actions">
          <button @click="handleViewWeakAreas" class="btn-action">
            🔍 View Weak Areas
          </button>
          <button @click="handleTakePractice" class="btn-primary">
            📝 Take Practice Exam
          </button>
        </div>
      </div>

      <div class="view-actions">
        <button @click="handleBack" class="btn-secondary">← Back to Schedule</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useExamPrepStore, type PracticeScore } from '@/stores/examPrep'

const emit = defineEmits<{
  'view-weak-areas': []
  'review-topic': [topic: string]
  'take-practice': []
}>()

const examPrepStore = useExamPrepStore()
const isLoading = ref(false)

const hasProgressData = computed(() => {
  const progress = examPrepStore.progressData
  return progress && progress.practiceScores && progress.practiceScores.length > 0
})

const displayProgress = computed(() => {
  const progress = examPrepStore.progressData
  if (!progress) {
    return {
      averageScore: 0,
      bestScore: 0,
      readinessPercentage: 0,
      improvementRate: 0,
      totalExams: 0,
      milestonesAchieved: []
    }
  }
  
  // Calculate readiness percentage if not set or if it needs recalculation
  let readinessPercentage = progress.readinessPercentage || 0
  if (readinessPercentage === 0 && progress.averageScore > 0) {
    // Base readiness on average score with improvement bonus
    const improvementBonus = Math.max(0, progress.improvementRate || 0) * 0.5
    readinessPercentage = Math.min(100, Math.round(progress.averageScore + improvementBonus))
  }
  
  return {
    averageScore: progress.averageScore || 0,
    bestScore: progress.bestScore || 0,
    readinessPercentage: readinessPercentage,
    improvementRate: progress.improvementRate || 0,
    totalExams: progress.practiceScores?.length || 0,
    milestonesAchieved: progress.milestonesAchieved || []
  }
})

const recentScores = computed((): PracticeScore[] => {
  const progress = examPrepStore.progressData
  if (!progress || !progress.practiceScores) return []
  return [...progress.practiceScores].reverse().slice(0, 5)
})

function formatDate(dateStr: string): string {
  try {
    const date = new Date(dateStr)
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  } catch {
    return dateStr
  }
}

function getScoreClass(score: number): string {
  if (score >= 80) return 'score-excellent'
  if (score >= 60) return 'score-good'
  if (score >= 40) return 'score-average'
  return 'score-needs-work'
}

function handleViewWeakAreas() {
  examPrepStore.setStep('weak-areas')
  emit('view-weak-areas')
}

function handleTakePractice() {
  examPrepStore.setStep('practice-exam')
  emit('take-practice')
}

function handleBack() {
  examPrepStore.setStep('study-schedule')
}

onMounted(() => {
  // If no progress data exists, initialize with empty structure
  if (!examPrepStore.progressData) {
    examPrepStore.setProgressData({
      practiceScores: [],
      averageScore: 0,
      bestScore: 0,
      improvementRate: 0,
      readinessPercentage: 0,
      milestonesAchieved: [],
      areasOfImprovement: []
    })
  }
  
  // If we just submitted an exam, automatically trigger weak area analysis
  if (examPrepStore.justSubmittedExam && hasProgressData.value) {
    examPrepStore.setJustSubmittedExam(false)
    // Small delay to let the progress dashboard render first
    setTimeout(() => {
      handleViewWeakAreas()
    }, 1000)
  }
})
</script>

<style scoped>
.progress-dashboard {
  display: flex;
  justify-content: center;
  align-items: flex-start;
  min-height: 100%;
  padding: 20px 0;
}

.view-card {
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 24px;
  padding: 40px;
  width: 100%;
  max-width: 900px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

h2 {
  color: white;
  font-size: 28px;
  margin: 0 0 12px 0;
  font-weight: 700;
  text-align: center;
}

.view-description {
  color: rgba(255, 255, 255, 0.9);
  font-size: 16px;
  text-align: center;
  margin-bottom: 32px;
}

/* Loading State */
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 60px 20px;
}

.loading-spinner {
  width: 50px;
  height: 50px;
  border: 4px solid rgba(255, 255, 255, 0.2);
  border-top-color: #64ffda;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-text {
  color: white;
  font-size: 18px;
  margin-top: 20px;
}

/* Empty State */
.empty-state {
  text-align: center;
  padding: 60px 20px;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 20px;
}

.empty-state h3 {
  color: white;
  font-size: 24px;
  margin: 0 0 12px 0;
}

.empty-state p {
  color: rgba(255, 255, 255, 0.8);
  font-size: 16px;
  margin-bottom: 24px;
}

/* Progress Stats */
.progress-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 24px;
  text-align: center;
  transition: all 0.3s ease;
}

.stat-card:hover {
  background: rgba(255, 255, 255, 0.15);
  transform: translateY(-2px);
}

.stat-card.highlight {
  background: linear-gradient(135deg, rgba(100, 255, 218, 0.2), rgba(100, 255, 218, 0.1));
  border: 1px solid rgba(100, 255, 218, 0.3);
  grid-column: span 2;
}

@media (max-width: 640px) {
  .stat-card.highlight {
    grid-column: span 1;
  }
}

.stat-icon {
  font-size: 28px;
  margin-bottom: 8px;
}

.stat-value {
  color: white;
  font-size: 32px;
  font-weight: 700;
  margin-bottom: 4px;
}

.stat-card.highlight .stat-value {
  color: #64ffda;
  font-size: 40px;
}

.stat-label {
  color: rgba(255, 255, 255, 0.8);
  font-size: 14px;
}

.progress-bar {
  height: 8px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 4px;
  margin-top: 12px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #64ffda, #00bcd4);
  border-radius: 4px;
  transition: width 0.5s ease;
}

/* Improvement Section */
.improvement-section {
  display: flex;
  justify-content: center;
  margin-bottom: 24px;
}

.improvement-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  border-radius: 20px;
  font-weight: 600;
}

.improvement-badge.positive {
  background: rgba(76, 175, 80, 0.2);
  color: #4caf50;
  border: 1px solid rgba(76, 175, 80, 0.4);
}

.improvement-badge.negative {
  background: rgba(255, 107, 107, 0.2);
  color: #ff6b6b;
  border: 1px solid rgba(255, 107, 107, 0.4);
}

.improvement-icon {
  font-size: 20px;
}

/* Recent Scores */
.recent-scores {
  margin-bottom: 24px;
}

.recent-scores h3 {
  color: white;
  font-size: 18px;
  margin: 0 0 16px 0;
}

.scores-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.score-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 12px;
}

.score-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.score-subject {
  color: white;
  font-weight: 500;
}

.score-date {
  color: rgba(255, 255, 255, 0.6);
  font-size: 13px;
}

.score-value {
  font-size: 20px;
  font-weight: 700;
  padding: 4px 12px;
  border-radius: 8px;
}

.score-excellent {
  background: rgba(76, 175, 80, 0.2);
  color: #4caf50;
}

.score-good {
  background: rgba(100, 255, 218, 0.2);
  color: #64ffda;
}

.score-average {
  background: rgba(255, 206, 84, 0.2);
  color: #ffce54;
}

.score-needs-work {
  background: rgba(255, 107, 107, 0.2);
  color: #ff6b6b;
}

/* Milestones */
.milestones-section {
  margin-bottom: 24px;
}

.milestones-section h3 {
  color: white;
  font-size: 18px;
  margin: 0 0 16px 0;
}

.milestones-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.milestone-badge {
  background: rgba(100, 255, 218, 0.15);
  color: #64ffda;
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 14px;
  font-weight: 500;
}

/* Dashboard Actions */
.dashboard-actions {
  display: flex;
  gap: 16px;
  justify-content: center;
  margin-bottom: 24px;
}

.btn-action, .btn-primary {
  padding: 14px 28px;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-primary {
  background: linear-gradient(135deg, #64ffda, #00bcd4);
  border: none;
  color: #1a1a2e;
}

.btn-action {
  background: rgba(255, 255, 255, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: white;
}

.btn-primary:hover, .btn-action:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.btn-primary:hover {
  box-shadow: 0 8px 25px rgba(100, 255, 218, 0.4);
}

/* View Actions */
.view-actions {
  display: flex;
  justify-content: center;
  padding-top: 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.btn-secondary {
  padding: 14px 28px;
  background: rgba(255, 255, 255, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  color: white;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.25);
}

@media (max-width: 640px) {
  .view-card {
    padding: 24px;
  }
  
  .dashboard-actions {
    flex-direction: column;
  }
  
  .btn-action, .btn-primary {
    width: 100%;
  }
}
</style>
