const { ipcRenderer } = require('electron')

// --- State ---
let isInspectMode = false
let lastHighlightedElement = null
let selectedElements = new Set()
let downloadedImageUrls = new Set()

// --- Styles ---
const highlightStyle = document.createElement('style')
highlightStyle.textContent = `
  .my-browser-highlight {
    outline: 2px solid #3498db !important;
    background-color: rgba(52, 152, 219, 0.2) !important;
    cursor: default !important;
  }
  .my-browser-selected {
    outline: 2px solid #e74c3c !important;
    background-color: rgba(231, 76, 60, 0.2) !important;
  }
`

// --- Core Inspect Logic ---

function enableInspectMode() {
    if (isInspectMode) return
    console.log('Enabling Inspect Mode')
    isInspectMode = true
    document.head.appendChild(highlightStyle)
    document.addEventListener('mouseover', onMouseOver, true)
    document.addEventListener('mouseout', onMouseOut, true)
    document.addEventListener('click', onClick, true)
}

function disableInspectMode() {
    if (!isInspectMode) return
    isInspectMode = false
    if (highlightStyle.parentNode) highlightStyle.remove()

    // Clear highlights
    if (lastHighlightedElement) {
        lastHighlightedElement.classList.remove('my-browser-highlight')
        lastHighlightedElement = null
    }

    // Clear selections
    selectedElements.forEach(el => el.classList.remove('my-browser-selected'))
    selectedElements.clear()
    downloadedImageUrls.clear()

    document.removeEventListener('mouseover', onMouseOver, true)
    document.removeEventListener('mouseout', onMouseOut, true)
    document.removeEventListener('click', onClick, true)
}

function onMouseOver(e) {
    if (!isInspectMode) return
    e.stopPropagation()
    const target = e.target

    // Ensure it's an element
    if (target.nodeType !== Node.ELEMENT_NODE) return

    if (selectedElements.has(target)) return

    if (target !== lastHighlightedElement) {
        if (lastHighlightedElement) {
            lastHighlightedElement.classList.remove('my-browser-highlight')
        }
        target.classList.add('my-browser-highlight')
        lastHighlightedElement = target
    }
}

function onMouseOut(e) {
    if (!isInspectMode) return
    e.stopPropagation()
    const target = e.target
    target.classList.remove('my-browser-highlight')
    if (lastHighlightedElement === target) {
        lastHighlightedElement = null
    }
}

function onClick(e) {
    if (!isInspectMode) return
    e.preventDefault()
    e.stopPropagation()

    const target = e.target

    if (selectedElements.has(target)) {
        selectedElements.delete(target)
        target.classList.remove('my-browser-selected')
        target.classList.add('my-browser-highlight')
        lastHighlightedElement = target
    } else {
        selectedElements.add(target)
        target.classList.remove('my-browser-highlight')
        target.classList.add('my-browser-selected')
        lastHighlightedElement = null
    }

    processSelection()
}

let currentMode = 'text' // text, image, table

ipcRenderer.on('set-mode', (event, mode) => {
    console.log('Mode set to:', mode)
    currentMode = mode
    // Update highlight color based on mode
    if (highlightStyle.sheet.cssRules.length > 0) {
        highlightStyle.sheet.deleteRule(0)
    }
    let color = 'rgba(255, 0, 0, 0.3)' // Default Red (Text)
    if (mode === 'image') color = 'rgba(0, 255, 0, 0.3)' // Green
    if (mode === 'table') color = 'rgba(255, 165, 0, 0.3)' // Orange

    highlightStyle.sheet.insertRule(`.my-browser-highlight { background-color: ${color} !important; outline: 2px solid ${color.replace('0.3', '1')}; cursor: pointer; }`, 0)
})

function processSelection() {
    console.log('Processing selection, mode:', currentMode)
    if (selectedElements.size === 0) return

    if (currentMode === 'image') {
        // --- IMAGE MODE ---
        let imageCount = 0
        selectedElements.forEach(el => {
            const images = []
            if (el.tagName === 'IMG') images.push(el)
            el.querySelectorAll('img').forEach(img => images.push(img))

            images.forEach(img => {
                const src = img.src
                if (src) {
                    ipcRenderer.sendToHost('download-image', src)
                    imageCount++
                }
            })
        })

        if (imageCount > 0) {
            showNotification(`Downloading ${imageCount} Image${imageCount === 1 ? '' : 's'}`)
        } else {
            showNotification('No images found in selection')
        }
        return // Done, no clipboard copy
    }

    if (currentMode === 'table') {
        // --- TABLE MODE ---
        // Try to find a table in the selection or parent
        let table = null
        const el = selectedElements.values().next().value // Just take first for now
        if (el.tagName === 'TABLE') table = el
        else table = el.closest('table') || el.querySelector('table')

        if (!table) {
            showNotification('No table found')
            return
        }

        // Parse Table to TSV (Excel friendly)
        const rows = Array.from(table.querySelectorAll('tr'))
        const tsv = rows.map(row => {
            const cells = Array.from(row.querySelectorAll('th, td'))
            return cells.map(cell => cell.innerText.replace(/\t/g, ' ').trim()).join('\t')
        }).join('\n')

        ipcRenderer.sendToHost('copy-to-clipboard', {
            content: tsv,
            imageCount: 0
        })
        showNotification('Copied Table Data')
        return
    }

    // --- TEXT MODE (Default) ---
    const htmlParts = []

    selectedElements.forEach(el => {
        const clone = el.cloneNode(true)

        // Remove images in Text Mode
        clone.querySelectorAll('img').forEach(img => img.remove())
        if (clone.tagName === 'IMG') return // Skip standalone images

        htmlParts.push(clone.outerHTML)
    })

    const content = htmlParts.join('\n\n')

    if (!content.trim()) {
        showNotification('No text content')
        return
    }

    ipcRenderer.sendToHost('copy-to-clipboard', {
        content: content,
        imageCount: 0
    })

    showNotification('Copied Text (No Images)')
}

function showNotification(text) {
    const div = document.createElement('div')
    div.textContent = text
    Object.assign(div.style, {
        position: 'fixed', top: '20px', left: '50%', transform: 'translateX(-50%)',
        background: 'rgba(0,0,0,0.8)', color: 'white', padding: '10px 20px',
        borderRadius: '5px', zIndex: '999999', fontFamily: 'sans-serif', pointerEvents: 'none'
    })
    document.body.appendChild(div)
    setTimeout(() => {
        div.style.opacity = '0'
        div.style.transition = 'opacity 0.5s'
        setTimeout(() => div.remove(), 500)
    }, 2000)
}

// --- IPC Listeners ---

ipcRenderer.on('toggle-inspect-mode', (event, shouldEnable) => {
    console.log('Toggle inspect mode:', shouldEnable)
    if (shouldEnable) {
        enableInspectMode()
    } else {
        disableInspectMode()
    }
})
