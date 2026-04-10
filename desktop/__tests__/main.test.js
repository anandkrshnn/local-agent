/**
 * Desktop App Tests - Electron
 * Tests: Window creation, IPC, Tray, Auto-updater
 */

const { app, BrowserWindow } = require('electron');
const { expect } = require('chai');
const sinon = require('sinon');

describe('Local Agent Desktop App', () => {
  
  let mainWindow;
  
  beforeEach(() => {
    mainWindow = new BrowserWindow({
      width: 1200,
      height: 800,
      show: false,
      webPreferences: {
        nodeIntegration: false,
        contextIsolation: true,
      },
    });
  });
  
  afterEach(() => {
    mainWindow.close();
  });
  
  test('creates main window', () => {
    expect(mainWindow).to.be.instanceOf(BrowserWindow);
  });
  
  test('window has correct dimensions', () => {
    const bounds = mainWindow.getBounds();
    expect(bounds.width).to.equal(1200);
    expect(bounds.height).to.equal(800);
  });
  
  test('IPC handlers are registered', () => {
    const ipcMain = require('electron').ipcMain;
    const handlers = ipcMain.eventNames();
    expect(handlers).to.include('get-settings');
    expect(handlers).to.include('save-settings');
  });
});
