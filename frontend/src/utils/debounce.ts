export type DebouncedFn<T extends (...args: any[]) => void> = ((...args: Parameters<T>) => void) & {
  flush: () => void
  cancel: () => void
}

export function debounce<T extends (...args: any[]) => void>(fn: T, delay = 500): DebouncedFn<T> {
  let timer: number | undefined
  let lastArgs: Parameters<T> | null = null

  const wrapped = (...args: Parameters<T>) => {
    lastArgs = args
    if (timer) {
      window.clearTimeout(timer)
    }
    timer = window.setTimeout(() => {
      timer = undefined
      if (lastArgs) {
        fn(...lastArgs)
        lastArgs = null
      }
    }, delay)
  }

  wrapped.flush = () => {
    if (timer) {
      window.clearTimeout(timer)
      timer = undefined
    }
    if (lastArgs) {
      fn(...lastArgs)
      lastArgs = null
    }
  }

  wrapped.cancel = () => {
    if (timer) {
      window.clearTimeout(timer)
      timer = undefined
    }
    lastArgs = null
  }

  return wrapped as DebouncedFn<T>
}
