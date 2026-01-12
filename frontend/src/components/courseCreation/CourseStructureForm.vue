<template>
  <div class="course-structure-form">
    <div class="form-card">
      <h2>Course Structure 🏗️</h2>
      <p class="form-description">Define the modules and lessons for your course.</p>
      
      <div v-if="modules.length === 0" class="empty-state">
        <p>Click "Add Module" to start building your course structure.</p>
      </div>

      <div v-else class="modules-list">
        <div 
          v-for="(module, index) in modules" 
          :key="module.id" 
          class="module-card"
          :draggable="true"
          @dragstart="handleDragStart(index, $event)"
          @dragover.prevent
          @drop="handleDrop(index, $event)"
        >
          <div class="module-header">
            <div class="module-drag-handle">☰</div>
            <div class="module-content">
              <h3>Module {{ index + 1 }}: {{ module.name }}</h3>
              <p class="module-description">{{ module.description }}</p>
            </div>
            <div class="module-actions">
              <button @click="editModule(index)" class="btn-edit" title="Edit Module">✏️</button>
              <button @click="addLesson(index)" class="btn-add-lesson" title="Add Lesson">+ Lesson</button>
              <button @click="removeModule(index)" class="btn-remove" title="Remove Module">🗑️</button>
            </div>
          </div>
          
          <!-- Lessons List -->
          <div v-if="module.lessons.length > 0" class="lessons-list">
            <div 
              v-for="(lesson, lessonIndex) in module.lessons" 
              :key="lesson.id"
              class="lesson-item"
            >
              <span class="lesson-number">{{ lessonIndex + 1 }}</span>
              <div class="lesson-info">
                <strong>{{ lesson.title }}</strong>
                <span class="lesson-duration">{{ lesson.duration }}h</span>
              </div>
              <button @click="removeLesson(index, lessonIndex)" class="btn-remove-small">×</button>
            </div>
          </div>
          
          <div v-else class="no-lessons">
            <p>No lessons yet. Click "+ Lesson" to add one.</p>
          </div>
        </div>
      </div>
      
      <!-- Lesson Editor Modal -->
      <div v-if="editingLesson" class="lesson-modal-overlay" @click="closeLessonEditor">
        <div class="lesson-modal" @click.stop>
          <h3>{{ editingLesson.moduleIndex !== null ? 'Edit' : 'Add' }} Lesson</h3>
          <div class="form-group">
            <label>Lesson Title</label>
            <input v-model="lessonForm.title" type="text" class="form-input" placeholder="e.g., Introduction to HTML Basics" />
          </div>
          <div class="form-group">
            <label>Description</label>
            <textarea v-model="lessonForm.description" rows="3" class="form-input" placeholder="What will students learn in this lesson?"></textarea>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>Duration (hours)</label>
              <input v-model.number="lessonForm.duration" type="number" min="0.5" max="10" step="0.5" class="form-input" />
            </div>
            <div class="form-group">
              <label>Topics (comma-separated)</label>
              <input v-model="lessonForm.topics" type="text" class="form-input" placeholder="HTML, CSS, Structure" />
            </div>
          </div>
          <div class="modal-actions">
            <button @click="closeLessonEditor" class="btn-secondary">Cancel</button>
            <button @click="saveLesson" class="btn-primary">Save Lesson</button>
          </div>
        </div>
      </div>

      <form @submit.prevent="handleAddModule" class="add-module-form">
        <h3>Add New Module</h3>
        <div class="form-group">
          <label for="module-name">Module Name</label>
          <input
            id="module-name"
            v-model="newModule.name"
            type="text"
            placeholder="e.g., Introduction to HTML"
            class="form-input"
          />
        </div>
        <div class="form-group">
          <label for="module-description">Description</label>
          <textarea
            id="module-description"
            v-model="newModule.description"
            rows="3"
            placeholder="Brief description of this module"
            class="form-input"
          ></textarea>
        </div>
        <button type="submit" class="btn-secondary">Add Module</button>
      </form>
        
      <div class="form-actions">
        <button @click="handleBack" class="btn-back">← Back</button>
        <button @click="handleContinue" class="btn-primary" :disabled="modules.length === 0">
          Continue to Assessments →
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { CourseModule } from '@/stores/courseCreation'

const emit = defineEmits<{
  complete: [modules: CourseModule[]]
}>()

const modules = ref<CourseModule[]>([])
const newModule = ref({
  name: '',
  description: ''
})
const draggedIndex = ref<number | null>(null)
const editingLesson = ref<{ moduleIndex: number | null, lessonIndex: number | null } | null>(null)
const lessonForm = ref({
  title: '',
  description: '',
  duration: 1,
  topics: ''
})

function handleAddModule() {
  if (!newModule.value.name.trim()) return

  modules.value.push({
    id: `module-${Date.now()}`,
    name: newModule.value.name,
    description: newModule.value.description,
    lessons: [],
    order: modules.value.length + 1
  })

  newModule.value = { name: '', description: '' }
}

function removeModule(index: number) {
  modules.value.splice(index, 1)
  // Update order
  modules.value.forEach((m, i) => { m.order = i + 1 })
}

function handleDragStart(index: number, event: DragEvent) {
  draggedIndex.value = index
  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = 'move'
  }
}

function handleDrop(dropIndex: number, event: DragEvent) {
  event.preventDefault()
  if (draggedIndex.value === null || draggedIndex.value === dropIndex) return
  
  const draggedModule = modules.value[draggedIndex.value]
  modules.value.splice(draggedIndex.value, 1)
  modules.value.splice(dropIndex, 0, draggedModule)
  
  // Update order
  modules.value.forEach((m, i) => { m.order = i + 1 })
  draggedIndex.value = null
}

function editModule(index: number) {
  const module = modules.value[index]
  newModule.value = {
    name: module.name,
    description: module.description
  }
  // Could open a modal or inline edit
  const newName = prompt('Edit module name:', module.name)
  if (newName) {
    module.name = newName
  }
  const newDesc = prompt('Edit module description:', module.description)
  if (newDesc !== null) {
    module.description = newDesc
  }
}

function addLesson(moduleIndex: number) {
  editingLesson.value = { moduleIndex, lessonIndex: null }
  lessonForm.value = {
    title: '',
    description: '',
    duration: 1,
    topics: ''
  }
}

function removeLesson(moduleIndex: number, lessonIndex: number) {
  modules.value[moduleIndex].lessons.splice(lessonIndex, 1)
  // Update lesson order
  modules.value[moduleIndex].lessons.forEach((l, i) => { l.order = i + 1 })
}

function saveLesson() {
  if (!editingLesson.value || editingLesson.value.moduleIndex === null) return
  
  const module = modules.value[editingLesson.value.moduleIndex]
  const topics = lessonForm.value.topics.split(',').map(t => t.trim()).filter(t => t)
  
  if (editingLesson.value.lessonIndex !== null) {
    // Edit existing lesson
    const lesson = module.lessons[editingLesson.value.lessonIndex]
    lesson.title = lessonForm.value.title
    lesson.description = lessonForm.value.description
    lesson.duration = lessonForm.value.duration
    lesson.topics = topics
  } else {
    // Add new lesson
    module.lessons.push({
      id: `lesson-${Date.now()}`,
      title: lessonForm.value.title,
      description: lessonForm.value.description,
      duration: lessonForm.value.duration,
      topics: topics,
      order: module.lessons.length + 1
    })
  }
  
  closeLessonEditor()
}

function closeLessonEditor() {
  editingLesson.value = null
  lessonForm.value = {
    title: '',
    description: '',
    duration: 1,
    topics: ''
  }
}

function handleContinue() {
  emit('complete', modules.value)
}

import { useCourseCreationStore } from '@/stores/courseCreation'

const courseCreationStore = useCourseCreationStore()

function handleBack() {
  courseCreationStore.setStep('course-overview')
}
</script>

<style scoped>
.course-structure-form {
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

.empty-state {
  text-align: center;
  padding: 40px;
  color: rgba(255, 255, 255, 0.7);
}

.modules-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 32px;
}

.module-card {
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  padding: 20px;
  cursor: move;
  transition: all 0.3s ease;
  margin-bottom: 16px;
}

.module-card:hover {
  background: rgba(255, 255, 255, 0.15);
  border-color: rgba(255, 255, 255, 0.3);
  transform: translateX(4px);
}

.module-card[draggable="true"]:active {
  opacity: 0.5;
}

.module-header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 12px;
}

.module-drag-handle {
  color: rgba(255, 255, 255, 0.6);
  cursor: grab;
  font-size: 20px;
  padding: 4px;
  user-select: none;
}

.module-drag-handle:active {
  cursor: grabbing;
}

.module-content {
  flex: 1;
}

.module-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.module-header h3 {
  color: white;
  font-size: 18px;
  margin: 0;
}

.btn-edit, .btn-add-lesson, .btn-remove {
  padding: 6px 10px;
  background: rgba(255, 255, 255, 0.15);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-edit:hover {
  background: rgba(255, 193, 7, 0.3);
}

.btn-add-lesson:hover {
  background: rgba(76, 175, 80, 0.3);
}

.btn-remove:hover {
  background: rgba(255, 0, 0, 0.3);
}

.module-description {
  color: rgba(255, 255, 255, 0.8);
  font-size: 14px;
  margin: 8px 0;
}

.lessons-count {
  color: rgba(255, 255, 255, 0.6);
  font-size: 12px;
}

.add-module-form {
  border-top: 1px solid rgba(255, 255, 255, 0.2);
  padding-top: 24px;
  margin-bottom: 24px;
}

.add-module-form h3 {
  color: white;
  font-size: 18px;
  margin-bottom: 16px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}

label {
  color: white;
  font-size: 14px;
  font-weight: 600;
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

.btn-secondary {
  padding: 10px 20px;
  background: rgba(255, 255, 255, 0.2);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 12px;
  font-size: 14px;
  cursor: pointer;
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

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.lessons-list {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.lesson-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  margin-bottom: 8px;
}

.lesson-number {
  width: 24px;
  height: 24px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  color: white;
  flex-shrink: 0;
}

.lesson-info {
  flex: 1;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.lesson-info strong {
  color: white;
  font-size: 14px;
}

.lesson-duration {
  color: rgba(255, 255, 255, 0.6);
  font-size: 12px;
  background: rgba(255, 255, 255, 0.1);
  padding: 4px 8px;
  border-radius: 6px;
}

.btn-remove-small {
  background: rgba(255, 0, 0, 0.2);
  color: white;
  border: none;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  cursor: pointer;
  font-size: 18px;
  line-height: 1;
  transition: all 0.2s ease;
}

.btn-remove-small:hover {
  background: rgba(255, 0, 0, 0.4);
}

.no-lessons {
  margin-top: 12px;
  padding: 16px;
  text-align: center;
  color: rgba(255, 255, 255, 0.6);
  font-size: 14px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
}

.lesson-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.lesson-modal {
  background: rgba(102, 126, 234, 0.95);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 24px;
  padding: 32px;
  width: 90%;
  max-width: 600px;
  max-height: 90vh;
  overflow-y: auto;
}

.lesson-modal h3 {
  color: white;
  font-size: 24px;
  margin: 0 0 24px 0;
}

.modal-actions {
  display: flex;
  gap: 12px;
  margin-top: 24px;
  justify-content: flex-end;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

@media (max-width: 768px) {
  .form-row {
    grid-template-columns: 1fr;
  }
  
  .module-actions {
    flex-direction: column;
  }
}
</style>

