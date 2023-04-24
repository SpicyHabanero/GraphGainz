const { app, BrowserWindow } = require('electron');

function createWindow() {
    mainWindow = new BrowserWindow({
      width: 800,
      height: 600,
      webPreferences: {
        nodeIntegration: true,
        contextIsolation: false,
        enableRemoteModule: true,
      },
    });
  
    mainWindow.loadFile('index.html');
    mainWindow.webContents.openDevTools();
  
    mainWindow.on('closed', () => {
      mainWindow = null;
    });
  }

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});
