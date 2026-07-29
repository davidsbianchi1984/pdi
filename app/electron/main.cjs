// Electron main process. In dev it loads the Vite dev server
// (ELECTRON_START_URL); in production it loads the built bundle from dist/.
const { app, BrowserWindow, dialog, shell } = require("electron");
const path = require("path");

function createWindow() {
  const win = new BrowserWindow({
    width: 1180,
    height: 820,
    minWidth: 900,
    minHeight: 640,
    backgroundColor: "#0d0a20",
    title: "PDI",
    webPreferences: {
      preload: path.join(__dirname, "preload.cjs"),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  // Open external links in the real browser, not inside the app window.
  win.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: "deny" };
  });

  const devUrl = process.env.ELECTRON_START_URL;
  if (devUrl) {
    win.loadURL(devUrl);
  } else {
    win.loadFile(path.join(__dirname, "..", "dist", "index.html"));
  }
}

// Keep the install current. On launch, ask GitHub Releases whether a newer
// version exists. Windows and Linux download it in the background and offer
// a restart; macOS cannot swap an unsigned app under itself, so it gets told
// and taken to the download instead. Every failure path is silent on
// purpose: an update check must never stand between the user and the app.
function setupAutoUpdate() {
  if (!app.isPackaged) return;
  let autoUpdater;
  try {
    ({ autoUpdater } = require("electron-updater"));
  } catch {
    return; // updater not bundled (e.g. a dev build) — the app is unaffected
  }
  const canSelfInstall = process.platform !== "darwin";
  autoUpdater.autoDownload = canSelfInstall;
  autoUpdater.on("error", () => {});
  autoUpdater.on("update-available", async (info) => {
    if (canSelfInstall) return; // downloading; the next event handles it
    const { response } = await dialog.showMessageBox({
      type: "info",
      title: "Update available",
      message: `Version ${info.version} is out (you have ${app.getVersion()}).`,
      detail: "The download page has the new installer.",
      buttons: ["Open download page", "Later"],
      defaultId: 0,
    });
    if (response === 0) {
      shell.openExternal(
        `https://github.com/davidsbianchi1984/pdi/releases/latest`);
    }
  });
  autoUpdater.on("update-downloaded", async (info) => {
    const { response } = await dialog.showMessageBox({
      type: "info",
      title: "Update ready",
      message: `Version ${info.version} is downloaded.`,
      detail: "Restart to switch to it. Your data stays where it is.",
      buttons: ["Restart now", "Later"],
      defaultId: 0,
    });
    if (response === 0) autoUpdater.quitAndInstall();
  });
  autoUpdater.checkForUpdates().catch(() => {});
}

app.whenReady().then(() => {
  createWindow();
  setupAutoUpdate();
  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});
