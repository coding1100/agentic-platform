import { onMounted, onBeforeUnmount, ref, watch } from 'vue'
import { stateApi } from '@/services/api'
import { debounce } from '@/utils/debounce'

export function usePersistedStore(
  namespace: string,
  getState: () => Record<string, any>,
  setState: (data: Record<string, any>) => void,
  watchSource?: () => any
) {
  const isHydrating = ref(false)
  const hydrated = ref(false)
  let resolveReady: (() => void) | null = null
  const ready = new Promise<void>((resolve) => {
    resolveReady = resolve
  })

  const saveState = debounce(async () => {
    if (isHydrating.value) return
    try {
      await stateApi.save(namespace, getState())
    } catch (error) {
      // Avoid noisy UI errors; persistence is best-effort.
      console.error(`Failed to save state for ${namespace}:`, error)
    }
  }, 800)

  onMounted(async () => {
    isHydrating.value = true
    try {
      const response = await stateApi.get(namespace)
      if (response?.data && Object.keys(response.data).length > 0) {
        setState(response.data)
      }
    } catch (error) {
      console.error(`Failed to load state for ${namespace}:`, error)
    } finally {
      isHydrating.value = false
      hydrated.value = true
      if (resolveReady) {
        resolveReady()
        resolveReady = null
      }
    }
  })

  watch(
    () => (watchSource ? watchSource() : getState()),
    () => {
      saveState()
    },
    { deep: true }
  )

  onBeforeUnmount(() => {
    saveState.flush()
  })

  return { isHydrating, hydrated, ready }
}
