// Check a running Slidev deck with every click revealed; save a JSON report.
// Usage: node slides/scripts/verify-deck.mjs http://localhost:3030 /tmp/lecture-check
import { chromium } from 'playwright-chromium'
import { mkdir, writeFile } from 'node:fs/promises'

const base = process.argv[2] || 'http://localhost:3030'
const output = process.argv[3] || '/tmp/lecture-check'
await mkdir(output, { recursive: true })
const browser = await chromium.launch({ headless: true })
try {
  const page = await browser.newPage({ viewport: { width: 1200, height: 800 } })
  const errors = []
  page.on('pageerror', error => errors.push(error.message))
  await page.goto(`${base}/export`, { waitUntil: 'networkidle' })
  await page.locator('.slidev-layout').first().waitFor()
  await page.evaluate(() => document.fonts.ready)
  await page.evaluate(async () => {
    await Promise.all([...document.images].map(img => img.decode().catch(() => {})))
  })
  const slides = await page.locator('.slidev-layout').evaluateAll(layouts => layouts.map((layout, index) => {
    const bounds = layout.getBoundingClientRect()
    const visible = element => {
      const style = getComputedStyle(element)
      return style.display !== 'none' && style.visibility !== 'hidden' && style.opacity !== '0'
    }
    const overflow = [...layout.querySelectorAll('h1,h2,h3,p,li,table,img,.katex-display')]
      .filter(visible)
      .filter(element => {
        const box = element.getBoundingClientRect()
        return box.width && box.height && (box.bottom > bounds.bottom + 2 || box.right > bounds.right + 2 || box.left < bounds.left - 2)
      }).map(element => ({ tag: element.tagName, text: (element.innerText || element.alt || '').slice(0, 150) }))
    return {
      slide: index + 1,
      title: layout.querySelector('h1')?.innerText,
      overflow,
      mathErrors: [...layout.querySelectorAll('.katex-error')].map(element => element.textContent),
      brokenImages: [...layout.querySelectorAll('img')].filter(img => !img.complete || !img.naturalWidth).map(img => img.src),
    }
  }))
  for (const item of slides) {
    await page.locator('.slidev-layout').nth(item.slide - 1).screenshot({ path: `${output}/slide-${String(item.slide).padStart(2, '0')}.png` })
  }
  const problems = slides.filter(item => item.overflow.length || item.mathErrors.length || item.brokenImages.length)
  await writeFile(`${output}/report.json`, JSON.stringify({ errors, slides }, null, 2))
  console.log(JSON.stringify({ checked: slides.length, errors, problems, output }, null, 2))
  if (errors.length || problems.length) process.exitCode = 1
} finally {
  await browser.close()
}
