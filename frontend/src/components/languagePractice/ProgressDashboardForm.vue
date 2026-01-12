<template>
  <div class="progress-dashboard-form">
    <div class="form-card">
      <h2>Your Progress Dashboard 📊</h2>
      <p class="form-description">Track your learning journey and celebrate your achievements!</p>
      
      <!-- Stats Overview -->
      <div class="stats-overview">
        <div class="stat-card">
          <div class="stat-icon">📚</div>
          <div class="stat-content">
            <div class="stat-value">{{ languagePracticeStore.progressStats.totalWordsLearned }}</div>
            <div class="stat-label">Words Learned</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon">🔥</div>
          <div class="stat-content">
            <div class="stat-value">{{ languagePracticeStore.progressStats.currentStreak }}</div>
            <div class="stat-label">Day Streak</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon">⭐</div>
          <div class="stat-content">
            <div class="stat-value">Level {{ languagePracticeStore.progressStats.level }}</div>
            <div class="stat-label">{{ languagePracticeStore.progressStats.xp }} / {{ languagePracticeStore.progressStats.xpToNextLevel }} XP</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon">⏱️</div>
          <div class="stat-content">
            <div class="stat-value">{{ languagePracticeStore.progressStats.totalPracticeTime }}</div>
            <div class="stat-label">Minutes Practiced</div>
          </div>
        </div>
      </div>

      <!-- Level Progress -->
      <div class="level-progress-section">
        <h3>Level Progress</h3>
        <div class="level-bar">
          <div class="level-fill" :style="{ width: `${(languagePracticeStore.progressStats.xp / languagePracticeStore.progressStats.xpToNextLevel) * 100}%` }"></div>
        </div>
        <p class="level-text">
          {{ languagePracticeStore.progressStats.xpToNextLevel - languagePracticeStore.progressStats.xp }} XP until Level {{ languagePracticeStore.progressStats.level + 1 }}
        </p>
      </div>

      <!-- Skill Mastery -->
      <div class="skill-mastery-section">
        <h3>Skill Mastery</h3>
        <div class="skill-list">
          <div class="skill-item">
            <div class="skill-header">
              <span class="skill-name">📖 Vocabulary</span>
              <span class="skill-percentage">{{ languagePracticeStore.progressStats.vocabularyMastery }}%</span>
            </div>
            <div class="skill-bar">
              <div class="skill-fill" :style="{ width: `${languagePracticeStore.progressStats.vocabularyMastery}%` }"></div>
            </div>
          </div>
          <div class="skill-item">
            <div class="skill-header">
              <span class="skill-name">📝 Grammar</span>
              <span class="skill-percentage">{{ languagePracticeStore.progressStats.grammarMastery }}%</span>
            </div>
            <div class="skill-bar">
              <div class="skill-fill" :style="{ width: `${languagePracticeStore.progressStats.grammarMastery}%` }"></div>
            </div>
          </div>
          <div class="skill-item">
            <div class="skill-header">
              <span class="skill-name">🗣️ Speaking</span>
              <span class="skill-percentage">{{ languagePracticeStore.progressStats.speakingMastery }}%</span>
            </div>
            <div class="skill-bar">
              <div class="skill-fill" :style="{ width: `${languagePracticeStore.progressStats.speakingMastery}%` }"></div>
            </div>
          </div>
          <div class="skill-item">
            <div class="skill-header">
              <span class="skill-name">👂 Listening</span>
              <span class="skill-percentage">{{ languagePracticeStore.progressStats.listeningMastery }}%</span>
            </div>
            <div class="skill-bar">
              <div class="skill-fill" :style="{ width: `${languagePracticeStore.progressStats.listeningMastery}%` }"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Weekly Goal -->
      <div class="weekly-goal-section">
        <h3>Weekly Goal</h3>
        <div class="goal-progress">
          <div class="goal-bar">
            <div class="goal-fill" :style="{ width: `${(languagePracticeStore.progressStats.weeklyProgress / languagePracticeStore.progressStats.weeklyGoal) * 100}%` }"></div>
          </div>
          <p class="goal-text">
            {{ languagePracticeStore.progressStats.weeklyProgress }} / {{ languagePracticeStore.progressStats.weeklyGoal }} minutes this week
          </p>
        </div>
      </div>

      <!-- Badges -->
      <div v-if="languagePracticeStore.progressStats.badges.length > 0" class="badges-section">
        <h3>Your Badges 🏆</h3>
        <div class="badges-grid">
          <div v-for="badge in languagePracticeStore.progressStats.badges" :key="badge" class="badge-item">
            <span class="badge-icon">🏅</span>
            <span class="badge-name">{{ badge }}</span>
          </div>
        </div>
      </div>

      <!-- Strengths & Weaknesses -->
      <div class="analysis-section">
        <div class="analysis-card strengths">
          <h4>💪 Your Strengths</h4>
          <ul>
            <li v-for="strength in languagePracticeStore.progressStats.strengths" :key="strength">
              {{ strength }}
            </li>
            <li v-if="languagePracticeStore.progressStats.strengths.length === 0">
              Keep practicing to discover your strengths!
            </li>
          </ul>
        </div>
        <div class="analysis-card weaknesses">
          <h4>📈 Areas to Improve</h4>
          <ul>
            <li v-for="weakness in languagePracticeStore.progressStats.weaknesses" :key="weakness">
              {{ weakness }}
            </li>
            <li v-if="languagePracticeStore.progressStats.weaknesses.length === 0">
              Great job! Keep up the excellent work!
            </li>
          </ul>
        </div>
      </div>
        
      <div class="form-actions">
        <button @click="handleBack" class="btn-back">← Back</button>
        <button @click="continueLearning" class="btn-primary">
          Continue Learning →
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useLanguagePracticeStore } from '@/stores/languagePractice'

const emit = defineEmits<{
  complete: []
}>()

const languagePracticeStore = useLanguagePracticeStore()

onMounted(() => {
  // Update stats based on practice
  const stats = languagePracticeStore.progressStats
  const vocabularyCards = languagePracticeStore.vocabularyCards
  const grammarExercises = languagePracticeStore.grammarExercises
  
  if (vocabularyCards.length > 0) {
    const avgMastery = vocabularyCards.reduce((sum, card) => sum + card.masteryLevel, 0) / vocabularyCards.length
    languagePracticeStore.updateProgressStats({
      vocabularyMastery: Math.round(avgMastery)
    })
  }
  
  if (grammarExercises.length > 0) {
    const completed = grammarExercises.filter(e => e.completed).length
    const grammarMastery = (completed / grammarExercises.length) * 100
    languagePracticeStore.updateProgressStats({
      grammarMastery: Math.round(grammarMastery)
    })
  }
  
  // Award badges
  const badges: string[] = []
  if (stats.totalWordsLearned >= 10) badges.push('First 10 Words')
  if (stats.currentStreak >= 7) badges.push('Week Warrior')
  if (stats.level >= 5) badges.push('Rising Star')
  if (stats.totalPracticeTime >= 60) badges.push('Hour Hero')
  
  languagePracticeStore.updateProgressStats({
    badges: [...new Set([...stats.badges, ...badges])]
  })
})

function continueLearning() {
  languagePracticeStore.setStep('vocabulary-builder')
}

function handleBack() {
  languagePracticeStore.setStep('pronunciation-practice')
}
</script>

<style scoped>
.progress-dashboard-form {
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
  max-width: 800px;
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

.stats-overview {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px;
  margin-bottom: 32px;
}

.stat-card {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  font-size: 32px;
}

.stat-content {
  flex: 1;
}

.stat-value {
  color: white;
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 4px;
}

.stat-label {
  color: rgba(255, 255, 255, 0.7);
  font-size: 12px;
}

.level-progress-section, .skill-mastery-section, .weekly-goal-section, .badges-section {
  margin-bottom: 32px;
  padding: 24px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 16px;
}

.level-progress-section h3, .skill-mastery-section h3, .weekly-goal-section h3, .badges-section h3 {
  color: white;
  font-size: 20px;
  margin: 0 0 16px 0;
}

.level-bar, .goal-bar {
  width: 100%;
  height: 12px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 6px;
  overflow: hidden;
  margin-bottom: 12px;
}

.level-fill, .goal-fill {
  height: 100%;
  background: linear-gradient(90deg, rgba(76, 175, 80, 0.8), rgba(102, 126, 234, 0.8));
  transition: width 0.3s ease;
}

.level-text, .goal-text {
  color: white;
  font-size: 14px;
  text-align: center;
}

.skill-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.skill-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.skill-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.skill-name {
  color: white;
  font-size: 16px;
  font-weight: 600;
}

.skill-percentage {
  color: white;
  font-size: 16px;
  font-weight: 600;
}

.skill-bar {
  width: 100%;
  height: 8px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 4px;
  overflow: hidden;
}

.skill-fill {
  height: 100%;
  background: linear-gradient(90deg, rgba(76, 175, 80, 0.8), rgba(102, 126, 234, 0.8));
  transition: width 0.3s ease;
}

.badges-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 12px;
}

.badge-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 16px;
  background: rgba(255, 193, 7, 0.2);
  border-radius: 12px;
}

.badge-icon {
  font-size: 32px;
}

.badge-name {
  color: white;
  font-size: 12px;
  text-align: center;
}

.analysis-section {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 32px;
}

.analysis-card {
  padding: 20px;
  border-radius: 12px;
}

.analysis-card.strengths {
  background: rgba(76, 175, 80, 0.2);
}

.analysis-card.weaknesses {
  background: rgba(255, 193, 7, 0.2);
}

.analysis-card h4 {
  color: white;
  font-size: 18px;
  margin: 0 0 12px 0;
}

.analysis-card ul {
  color: white;
  font-size: 14px;
  line-height: 1.8;
  margin: 0;
  padding-left: 20px;
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

@media (max-width: 768px) {
  .stats-overview {
    grid-template-columns: 1fr 1fr;
  }
  
  .analysis-section {
    grid-template-columns: 1fr;
  }
}
</style>





