<template>
  <div class="concept-mapping-form">
    <div class="form-card">
      <h2>Concept Mapping 🗺️</h2>
      <p class="form-description">Visualize relationships between key concepts in your course.</p>
      
      <!-- Visual Concept Map Preview -->
      <div v-if="formData.mainConcept || relatedConcepts.length > 0" class="concept-map-visual">
        <h3>Concept Map Visualization</h3>
        <div class="concept-diagram">
          <!-- Main Concept (Center) -->
          <div v-if="formData.mainConcept" class="concept-node main-concept">
            <div class="concept-circle">{{ formData.mainConcept.charAt(0).toUpperCase() }}</div>
            <div class="concept-label">{{ formData.mainConcept }}</div>
          </div>
          
          <!-- Related Concepts (Around Main) -->
          <div 
            v-for="(concept, index) in relatedConcepts" 
            :key="index"
            class="concept-node related-concept"
            :style="getConceptPosition(index, relatedConcepts.length)"
          >
            <div class="concept-circle small">{{ concept.charAt(0).toUpperCase() }}</div>
            <div class="concept-label">{{ concept }}</div>
            <!-- Connection Line -->
            <svg class="connection-line" v-if="formData.mainConcept">
              <line 
                :x1="'50%'" 
                :y1="'50%'" 
                :x2="getLineEndX(index, relatedConcepts.length)" 
                :y2="getLineEndY(index, relatedConcepts.length)"
                stroke="rgba(255, 255, 255, 0.3)" 
                stroke-width="2"
              />
            </svg>
          </div>
        </div>
      </div>
      
      <form @submit.prevent="handleSubmit" class="form">
        <div class="form-group">
          <label for="main-concept">Main Concept</label>
          <input
            id="main-concept"
            v-model="formData.mainConcept"
            type="text"
            placeholder="e.g., Web Development"
            required
            class="form-input"
            @input="updateVisualMap"
          />
        </div>

        <div class="form-group">
          <label for="related-concepts">Related Concepts</label>
          <p class="form-hint">Enter each concept on a new line. The map will update automatically.</p>
          <textarea
            id="related-concepts"
            v-model="relatedConceptsText"
            rows="6"
            placeholder="HTML&#10;CSS&#10;JavaScript&#10;React&#10;Node.js"
            class="form-input"
            @input="updateVisualMap"
          ></textarea>
        </div>
        
        <div v-if="relatedConcepts.length > 0" class="concept-actions">
          <button type="button" @click="generateWithAI" class="btn-ai">
            🤖 Generate Concept Relationships with AI
          </button>
        </div>
        
        <div class="form-actions">
          <button @click="handleBack" class="btn-back">← Back</button>
          <button type="submit" class="btn-primary">
            Continue to Workflow Automation →
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { ConceptMap } from '@/stores/courseCreation'

const emit = defineEmits<{
  complete: [map: ConceptMap]
}>()

const formData = ref<ConceptMap>({
  mainConcept: '',
  relatedConcepts: []
})

const relatedConceptsText = ref('')
const relatedConcepts = ref<string[]>([])

function updateVisualMap() {
  relatedConcepts.value = relatedConceptsText.value
    .split('\n')
    .map(c => c.trim())
    .filter(c => c.length > 0)
}

function getConceptPosition(index: number, total: number) {
  const angle = (index / total) * 2 * Math.PI - Math.PI / 2
  const radius = 150
  const x = 50 + (radius * Math.cos(angle)) / 10
  const y = 50 + (radius * Math.sin(angle)) / 10
  return {
    position: 'absolute',
    left: `${x}%`,
    top: `${y}%`,
    transform: 'translate(-50%, -50%)'
  }
}

function getLineEndX(index: number, total: number) {
  const angle = (index / total) * 2 * Math.PI - Math.PI / 2
  const radius = 150
  return 50 + (radius * Math.cos(angle)) / 10
}

function getLineEndY(index: number, total: number) {
  const angle = (index / total) * 2 * Math.PI - Math.PI / 2
  const radius = 150
  return 50 + (radius * Math.sin(angle)) / 10
}

function generateWithAI() {
  // This would call the AI agent to generate concept relationships
  alert('AI-powered concept relationship generation coming soon! This will analyze your concepts and suggest relationships.')
}

function handleSubmit() {
  updateVisualMap()
  formData.value.relatedConcepts = relatedConcepts.value.map((name, index) => ({
    id: `concept-${index}`,
    name: name,
    relationship: 'related',
    level: 1
  }))

  emit('complete', { ...formData.value })
}

import { useCourseCreationStore } from '@/stores/courseCreation'

const courseCreationStore = useCourseCreationStore()

function handleBack() {
  courseCreationStore.setStep('assessment-design')
}
</script>

<style scoped>
.concept-mapping-form {
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

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 24px;
}

label {
  color: white;
  font-size: 14px;
  font-weight: 600;
}

.form-hint {
  color: rgba(255, 255, 255, 0.7);
  font-size: 12px;
  margin: -4px 0 4px 0;
}

.form-input {
  padding: 14px 18px;
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 12px;
  font-size: 16px;
  color: white;
  transition: all 0.3s ease;
  font-family: inherit;
}

.form-input::placeholder {
  color: rgba(255, 255, 255, 0.6);
}

.form-input:focus {
  outline: none;
  border-color: rgba(255, 255, 255, 0.5);
  background: rgba(255, 255, 255, 0.25);
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

.concept-map-visual {
  margin-bottom: 32px;
  padding: 24px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.concept-map-visual h3 {
  color: white;
  font-size: 18px;
  margin: 0 0 20px 0;
  text-align: center;
}

.concept-diagram {
  position: relative;
  width: 100%;
  height: 400px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  overflow: visible;
}

.concept-node {
  position: absolute;
  display: flex;
  flex-direction: column;
  align-items: center;
  z-index: 10;
}

.concept-circle {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.3), rgba(255, 255, 255, 0.1));
  border: 3px solid rgba(255, 255, 255, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
  font-weight: 700;
  color: white;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
  transition: all 0.3s ease;
}

.concept-circle.small {
  width: 60px;
  height: 60px;
  font-size: 24px;
  border-width: 2px;
}

.concept-node:hover .concept-circle {
  transform: scale(1.1);
  box-shadow: 0 6px 30px rgba(0, 0, 0, 0.3);
}

.concept-label {
  margin-top: 8px;
  color: white;
  font-size: 12px;
  font-weight: 600;
  text-align: center;
  max-width: 100px;
  background: rgba(0, 0, 0, 0.3);
  padding: 4px 8px;
  border-radius: 6px;
  backdrop-filter: blur(10px);
}

.main-concept {
  left: 50% !important;
  top: 50% !important;
  transform: translate(-50%, -50%);
}

.main-concept .concept-circle {
  width: 100px;
  height: 100px;
  font-size: 40px;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.5), rgba(118, 75, 162, 0.5));
  border-color: rgba(255, 255, 255, 0.7);
}

.connection-line {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 1;
}

.concept-actions {
  margin-top: 16px;
  display: flex;
  justify-content: center;
}

.btn-ai {
  padding: 12px 24px;
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.3), rgba(118, 75, 162, 0.3));
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 12px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-ai:hover {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.4), rgba(118, 75, 162, 0.4));
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
}
</style>

