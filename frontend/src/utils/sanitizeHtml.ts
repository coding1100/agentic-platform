const ALLOWED_TAGS = new Set([
  'a',
  'b',
  'strong',
  'i',
  'em',
  'br',
  'p',
  'ul',
  'ol',
  'li',
  'h1',
  'h2',
  'h3',
  'h4',
  'h5',
  'h6',
  'code',
  'pre',
  'blockquote',
  'hr',
  'span',
  'div',
  'table',
  'thead',
  'tbody',
  'tr',
  'th',
  'td',
])

const ALLOWED_ATTRS = new Set(['class', 'href', 'rel', 'target'])

function sanitizeElement(el: Element) {
  const tag = el.tagName.toLowerCase()
  if (!ALLOWED_TAGS.has(tag)) {
    // Unwrap disallowed elements but keep their text/children
    const parent = el.parentNode
    if (!parent) return
    while (el.firstChild) {
      parent.insertBefore(el.firstChild, el)
    }
    parent.removeChild(el)
    return
  }

  // Remove disallowed attributes
  const attrs = Array.from(el.attributes)
  for (const attr of attrs) {
    const name = attr.name.toLowerCase()
    if (!ALLOWED_ATTRS.has(name)) {
      el.removeAttribute(attr.name)
      continue
    }

    // Block javascript: in hrefs
    if (name === 'href') {
      const value = attr.value.trim().toLowerCase()
      if (value.startsWith('javascript:')) {
        el.removeAttribute(attr.name)
      }
    }
  }
}

export function sanitizeHtml(html: string): string {
  if (!html) return ''
  const template = document.createElement('template')
  template.innerHTML = html

  const walker = document.createTreeWalker(template.content, NodeFilter.SHOW_ELEMENT)
  const nodes: Element[] = []
  while (walker.nextNode()) {
    nodes.push(walker.currentNode as Element)
  }

  nodes.forEach(sanitizeElement)
  return template.innerHTML
}
