/**
 * Local Agent Desktop App - Electron
 */

const { app, BrowserWindow, Tray, Menu, ipcMain, shell, dialog, globalShortcut } = require('electron');
const path = require('path');
const Store = require('electron-store');
const store = new Store();
const OllamaInstaller = require('./installer/ollama_setup');

let mainWindow = null;
let tray = null;

async function ensureAIIsReady() {
    const installer = new OllamaInstaller();
    
    // Create progress window
    const progressWindow = new BrowserWindow({
        width: 400,
        height: 300,
        parent: mainWindow,
        modal: true,
        show: false,
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false
        }
    });
    
    progressWindow.loadFile(path.join(__dirname, 'installer', 'progress.html'));
    
    const updateProgress = (progress) => {
        progressWindow.webContents.send('progress-update', progress);
    };
    
    progressWindow.show();
    
    try {
        await installer.ensureReady('phi3:mini', updateProgress);
        progressWindow.close();
        return true;
    } catch (error) {
        progressWindow.close();
        
        const result = await dialog.showMessageBox({
            type: 'error',
            title: 'AI Setup Failed',
            message: 'Could not set up AI infrastructure.',
            detail: error.message,
            buttons: ['Retry', 'Continue Anyway', 'Exit'],
            defaultId: 0,
            cancelId: 2
        });
        
        if (result.response === 0) {
            return await ensureAIIsReady();
        } else if (result.response === 2) {
            app.quit();
            return false;
        }
        return false;
    }
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200, height: 800,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
    },
    backgroundColor: '#0a0a0f',
  });

  // Load web UI
  mainWindow.loadURL('http://localhost:3000');
  
  mainWindow.on('close', (e) => {
    if (!app.isQuitting) {
      e.preventDefault();
      mainWindow.hide();
    }
  });
}

function createTray() {
  tray = new Tray(path.join(__dirname, 'tray-icon.png'));
  const contextMenu = Menu.buildFromTemplate([
    { label: 'Show Agent', click: () => mainWindow.show() },
    { type: 'separator' },
    { label: 'Quit', click: () => { app.isQuitting = true; app.quit(); } }
  ]);
  tray.setContextMenu(contextMenu);
}

app.whenReady().then(async () => {
  // Check AI infrastructure first
  const aiReady = await ensureAIIsReady();
  
  if (aiReady) {
    createWindow();
    createTray();
    
    globalShortcut.register('CommandOrControl+Shift+Space', () => {
      mainWindow.isVisible() ? mainWindow.hide() : (mainWindow.show(), mainWindow.focus());
    });
  }
});

ipcMain.handle('open-file', async () => {
  return await dialog.showOpenDialog(mainWindow, { properties: ['openFile'] });
});
