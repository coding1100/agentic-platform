<template>
  <div class="quiz-container">
    <div v-if="parsed.introText && parsed.introText.length > 10" class="quiz-intro">
      {{ parsed.introText }}
    </div>

    <div v-if="parsed.questions.length > 0" class="quiz-questions">
      <div
        v-for="question in parsed.questions"
        :key="question.number"
        class="quiz-question"
      >
        <div class="question-header">
          <span class="question-number">Question {{ question.number }}</span>
        </div>
        <div class="question-text">{{ question.question }}</div>
        
        <div v-if="question.options.length > 0" class="question-options">
          <div
            v-for="option in question.options"
            :key="option.letter"
            class="option"
          >
            <span class="option-letter">{{ option.letter }})</span>
            <span class="option-text">{{ option.text }}</span>
          </div>
        </div>
      </div>
    </div>

    <div v-if="parsed.outroText && parsed.outroText.length > 10" class="quiz-outro">
      {{ parsed.outroText }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { parseQuiz, type ParsedQuiz } from '@/utils/quizParser'

const props = defineProps<{
  content: string
}>()

const parsed = computed<ParsedQuiz>(() => parseQuiz(props.content))
</script>

<style scoped>
.quiz-container {
  width: 100%;
}

.quiz-intro,
.quiz-outro {
  margin-bottom: 20px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  line-height: 1.6;
}

.quiz-questions {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.quiz-question {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  padding: 20px;
  transition: all 0.3s ease;
}

.quiz-question:hover {
  background: rgba(255, 255, 255, 0.15);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

.question-header {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
}

.question-number {
  font-weight: 700;
  font-size: 16px;
  color: rgba(255, 255, 255, 0.95);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.question-text {
  font-size: 16px;
  line-height: 1.6;
  color: rgba(255, 255, 255, 0.95);
  margin-bottom: 16px;
  font-weight: 500;
}

.question-options {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 16px;
}

.option {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 8px;
  transition: all 0.2s ease;
}

.option:hover {
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(255, 255, 255, 0.25);
}

.option-letter {
  font-weight: 700;
  color: rgba(255, 255, 255, 0.9);
  min-width: 24px;
}

.option-text {
  flex: 1;
  color: rgba(255, 255, 255, 0.9);
  line-height: 1.5;
}

@media (max-width: 768px) {
  .quiz-question {
    padding: 16px;
  }

  .question-text {
    font-size: 15px;
  }

  .option {
    padding: 10px;
  }
}
</style>

