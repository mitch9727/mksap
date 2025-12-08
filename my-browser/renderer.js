const webview = document.querySelector('webview')
const urlInput = document.getElementById('url-input')
const goButton = document.getElementById('go')
const backButton = document.getElementById('back')
const forwardButton = document.getElementById('forward')
const reloadButton = document.getElementById('reload')

// Helper to ensure URL has protocol
function formatUrl(url) {
    if (!url.startsWith('http://') && !url.startsWith('https://')) {
        return 'https://' + url
    }
    return url
}

// Navigate to URL
function loadUrl() {
    const url = formatUrl(urlInput.value)
    webview.loadURL(url)
}

goButton.addEventListener('click', loadUrl)

urlInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
        loadUrl()
    }
})

backButton.addEventListener('click', () => {
    if (webview.canGoBack()) {
        webview.goBack()
    }
})

forwardButton.addEventListener('click', () => {
    if (webview.canGoForward()) {
        webview.goForward()
    }
})

const inspectButton = document.getElementById('inspect')
let isInspectMode = false

// --- Mode Switching Logic ---
const modeControls = document.getElementById('mode-controls')
const modeBtns = document.querySelectorAll('.mode-btn')
let currentMode = 'text' // text, image, table

modeBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        // Update UI
        modeBtns.forEach(b => b.classList.remove('active'))
        btn.classList.add('active')

        // Update State
        if (btn.id === 'mode-text') currentMode = 'text'
        if (btn.id === 'mode-image') currentMode = 'image'
        if (btn.id === 'mode-table') currentMode = 'table'

        console.log('Switched to mode:', currentMode)

        // Notify Webview
        webview.send('set-mode', currentMode)
    })
})

// Update Inspect Button to show/hide controls
inspectButton.addEventListener('click', () => {
    if (isInspectMode) {
        // Turning OFF
        webview.send('toggle-inspect-mode', false)
        inspectButton.textContent = 'Inspect'
        inspectButton.classList.remove('active')
        isInspectMode = false
        modeControls.style.display = 'none'
    } else {
        // Turning ON
        webview.send('toggle-inspect-mode', true)
        // Send current mode immediately to ensure sync
        webview.send('set-mode', currentMode)
        inspectButton.textContent = 'Done'
        inspectButton.classList.add('active')
        isInspectMode = true
        modeControls.style.display = 'flex'
    }
})

reloadButton.addEventListener('click', () => {
    // Execute reload inside the page to ensure we reload the current content
    webview.executeJavaScript('location.reload()')
})

// Update address bar when page loads
webview.addEventListener('did-start-loading', () => {
    // Optional: Show loading state
})

webview.addEventListener('console-message', (e) => {
    console.log('Webview:', e.message)
})

const homeButton = document.getElementById('home')
const historyButton = document.getElementById('history-btn')
const historyDropdown = document.getElementById('history-dropdown')

// History storage - Load from localStorage
let navigationHistory = []
try {
    const saved = localStorage.getItem('browserHistory')
    if (saved) {
        navigationHistory = JSON.parse(saved)
    }
} catch (e) {
    console.error('Failed to load history', e)
}

// Initial Load
webview.src = 'https://mksap.acponline.org/app/dashboard'

// Save history helper
function saveHistory() {
    localStorage.setItem('browserHistory', JSON.stringify(navigationHistory))
}

// Home Button
homeButton.addEventListener('click', () => {
    webview.loadURL('https://mksap.acponline.org/app/dashboard')
})

// History Button
historyButton.addEventListener('click', () => {
    if (historyDropdown.style.display === 'block') {
        historyDropdown.style.display = 'none'
    } else {
        renderHistory()
        historyDropdown.style.display = 'block'
    }
})

// Close history when clicking outside
document.addEventListener('click', (e) => {
    if (!historyButton.contains(e.target) && !historyDropdown.contains(e.target)) {
        historyDropdown.style.display = 'none'
    }
})

function renderHistory() {
    historyDropdown.innerHTML = ''
    if (navigationHistory.length === 0) {
        const div = document.createElement('div')
        div.className = 'history-item'
        div.textContent = 'No history yet'
        historyDropdown.appendChild(div)
        return
    }

    // Show newest first
    [...navigationHistory].reverse().forEach(item => {
        const div = document.createElement('div')
        div.className = 'history-item'
        div.textContent = item.title || item.url
        div.title = item.url // Tooltip
        div.addEventListener('click', () => {
            webview.loadURL(item.url)
            historyDropdown.style.display = 'none'
        })
        historyDropdown.appendChild(div)
    })
}

// Track navigation
function handleNavigation(url) {
    if (url.endsWith('start.html')) return // Don't track start page

    // Add to history if it's different from the last one
    const last = navigationHistory[navigationHistory.length - 1]
    if (!last || last.url !== url) {
        navigationHistory.push({ url: url, title: webview.getTitle() })
        // Keep only last 50 items
        if (navigationHistory.length > 50) {
            navigationHistory.shift()
        }
        saveHistory()
    }
}

webview.addEventListener('did-navigate', (e) => handleNavigation(e.url))
webview.addEventListener('did-navigate-in-page', (e) => handleNavigation(e.url))

// Update title in history when it becomes available
webview.addEventListener('page-title-updated', (e) => {
    const last = navigationHistory[navigationHistory.length - 1]
    if (last && last.url === webview.getURL()) {
        last.title = e.title
        saveHistory()
    }
})


// Listen for messages from the webview
webview.addEventListener('ipc-message', async (event) => {
    if (event.channel === 'download-image') {
        const url = event.args[0]
        console.log('Downloading image:', url)

        // Ask main process to save it
        try {
            const { ipcRenderer } = require('electron')
            const result = await ipcRenderer.invoke('save-image', url)

            if (result.success) {
                // We could notify the webview back, but for now we'll just log
                console.log('Image saved to:', result.path)
            } else {
                console.error('Failed to save image:', result.error)
            }
        } catch (err) {
            console.error('IPC error:', err)
        }
    } else if (event.channel === 'copy-to-clipboard') {
        console.log('Received copy-to-clipboard message')
        const { content, imageCount } = event.args[0]
        console.log('Content length:', content.length)
        try {
            const { clipboard } = require('electron')
            clipboard.writeText(content)
            console.log('Successfully wrote to clipboard')

            let msg = `Copied HTML`
            if (imageCount > 0) msg += ` & Saved ${imageCount} Image${imageCount === 1 ? '' : 's'}`
            // alert(msg) // Removed blocking alert
            console.log(msg)
        } catch (err) {
            console.error('Clipboard error:', err)
            alert('Failed to copy to clipboard')
        }
    } else if (event.channel === 'preload-error') {
        console.error('Preload Script Error:', event.args[0])
        alert('Browser Error: ' + event.args[0])
    }
})

// Context Menu
webview.addEventListener('context-menu', (e) => {
    e.preventDefault()
    const { ipcRenderer } = require('electron')
    ipcRenderer.send('show-context-menu')
})

// Trigger auto-run on navigation
webview.addEventListener('did-stop-loading', () => {
    const url = webview.getURL()
    // If we are on our local start page, show "Start Page" or empty
    if (url.endsWith('start.html')) {
        urlInput.value = ''
        urlInput.placeholder = 'Search or enter website name'
    } else {
        urlInput.value = url

        // Restore Inspect Mode state if active
        if (isInspectMode) {
            webview.send('toggle-inspect-mode', true)
        }
    }
})

// Prevent default app reload and handle shortcuts
window.addEventListener('keydown', (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'r') {
        e.preventDefault() // Stop the app from reloading
        webview.executeJavaScript('location.reload()')
    }
})
