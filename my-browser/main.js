const { app, BrowserWindow, ipcMain, nativeImage, Menu, MenuItem } = require('electron')
const path = require('path')
const fs = require('fs')
const https = require('https')
const http = require('http')

function createWindow() {
  const mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      webviewTag: true,
      nodeIntegration: true, // We need this for the renderer to use ipcRenderer
      contextIsolation: false // Simplifies communication for this demo
    }
  })

  mainWindow.loadFile('index.html')
}

// Handle image downloads
ipcMain.handle('save-image', async (event, url) => {
  try {
    const win = BrowserWindow.fromWebContents(event.sender)
    const downloadPath = app.getPath('downloads')
    const filename = `image-${Date.now()}-${Math.floor(Math.random() * 1000)}.jpg`
    const filePath = path.join(downloadPath, filename)

    // Simple download using net module or just returning path for renderer to handle?
    // Actually, let's use the webContents download method if possible, or a simple https get.
    // For simplicity in this environment, let's assume we just return the path and let the renderer/preload handle fetching if needed,
    // BUT preload can't write files. So main must do it.

    // We'll use a helper to download
    const downloadFile = (url, dest) => {
      return new Promise((resolve, reject) => {
        const file = fs.createWriteStream(dest)
        const request = url.startsWith('https') ? require('https').get(url) : require('http').get(url)

        request.on('response', (response) => {
          response.pipe(file)
          file.on('finish', () => {
            file.close(() => resolve(dest))
          })
        }).on('error', (err) => {
          fs.unlink(dest, () => reject(err))
        })
      })
    }

    await downloadFile(url, filePath)
    return { success: true, path: filePath }
  } catch (error) {
    console.error('Download failed:', error)
    return { success: false, error: error.message }
  }
})

// Handle context menu
ipcMain.on('show-context-menu', (event) => {
  const template = [
    { role: 'cut' },
    { role: 'copy' },
    { role: 'paste' },
    { type: 'separator' },
    { role: 'selectAll' },
    { type: 'separator' },
    {
      label: 'Inspect Element',
      click: () => {
        event.sender.inspectElement(0, 0)
        if (event.sender.isDevToolsOpened()) {
          event.sender.devToolsWebContents.focus()
        }
      }
    }
  ]
  const menu = Menu.buildFromTemplate(template)
  menu.popup(BrowserWindow.fromWebContents(event.sender))
})

app.whenReady().then(() => {
  createWindow()

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow()
    }
  })
})

app.on('window-all-closed', function () {
  if (process.platform !== 'darwin') app.quit()
})
