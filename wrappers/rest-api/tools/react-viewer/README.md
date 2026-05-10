# RealSense React Viewer

A modern React-based web UI for Intel RealSense cameras, leveraging the REST API backend.

## Features

- **Device Management**: Discover, select, and reset RealSense devices
- **Stream Viewing**: Real-time video streams via WebRTC (Depth, Color, Infrared)
- **Camera Controls**: Adjust exposure, gain, laser power, and other camera options
- **3D Point Cloud**: Interactive point cloud visualization with Three.js
- **IMU Visualization**: Real-time accelerometer and gyroscope graphs
- **Export**: PLY point cloud export and CSV IMU data export

## Prerequisites

- Node.js 18+ and npm
- RealSense REST API server running (see `../../`)

## Quick Start

You need **two terminals** running in parallel — one for the backend (FastAPI) and one
for the frontend (Vite dev server). Each terminal has a one-time install step followed
by a long-running server. The install steps below assume you start from the repo root.

### Terminal 1 — Backend (REST API)

```bash
cd wrappers/rest-api
python3 install.py    # one-time: installs requirements (and pyrealsense2 if missing)
python3 main.py       # long-running: serves the API on http://localhost:8000
```

`install.py` installs the packages from `requirements.txt` and, if `pyrealsense2` is
not already importable, also pulls it from PyPI (skipped if you already have it
installed locally — built from source, apt, or pip).

### Terminal 2 — Frontend (React viewer)

```bash
cd wrappers/rest-api/tools/react-viewer
npm install           # one-time: installs Node dependencies
npm run dev           # long-running: serves the UI on http://localhost:3000
```

If `npm` is not installed:
```bash
sudo apt install npm
```

### (Optional) Configure environment variables

Before starting the dev server, copy `.env.example` to `.env` and fill in your AI chat
provider key (Groq / OpenAI) and optional backend URL:
```bash
cp .env.example .env
```

### Open in browser

Once both terminals are up (backend on `:8000`, frontend on `:3000`), navigate to
[http://localhost:3000](http://localhost:3000). The frontend proxies API calls to the
backend automatically.

## Project Structure

```
react-viewer/
├── src/
│   ├── api/                          # Backend clients
│   │   ├── client.ts                 # REST API client
│   │   ├── socket.ts                 # Socket.IO client
│   │   ├── webrtc.ts                 # WebRTC handler
│   │   ├── chat.ts                   # AI chat client
│   │   ├── types.ts                  # TypeScript types
│   │   └── index.ts
│   ├── components/                   # React components
│   │   ├── Header.tsx
│   │   ├── DevicePanel.tsx
│   │   ├── StreamViewer.tsx
│   │   ├── ControlsPanel.tsx
│   │   ├── PointCloudViewer.tsx
│   │   ├── IMUViewer.tsx
│   │   ├── DepthLegend.tsx
│   │   ├── FirmwareProgressModal.tsx
│   │   ├── ApiDiagnostics.tsx
│   │   ├── LoadingSplash.tsx
│   │   ├── Toast.tsx
│   │   ├── WhatsNew.tsx
│   │   ├── ChatBot/                  # AI chat UI (Ask + Agent modes)
│   │   │   ├── ChatButton.tsx
│   │   │   ├── ChatPanel.tsx
│   │   │   ├── ChatMessage.tsx
│   │   │   ├── CodeExport.tsx
│   │   │   ├── SettingsPreview.tsx
│   │   │   └── index.ts
│   │   └── index.ts
│   ├── store/                        # Zustand state management
│   │   └── index.ts
│   ├── utils/
│   │   └── chatPrompt.ts             # AI prompt builder
│   ├── App.tsx                       # Main application
│   ├── main.tsx                      # Entry point
│   └── index.css                     # Global styles
├── src-tauri/                        # Tauri desktop bridge (Rust)
│   ├── src/                          # Rust sources
│   ├── icons/                        # App icons (reused from common/res)
│   ├── resources/
│   ├── Cargo.toml
│   └── build.rs
├── public/                           # Static assets (favicon, logos)
├── scripts/
│   └── bundle-for-prod.js            # Production bundler
├── tests/
│   ├── unit/                         # Vitest unit/integration tests
│   ├── e2e/                          # Playwright E2E tests
│   ├── mocks/                        # MSW handlers + fixtures
│   ├── setup/                        # Vitest global setup
│   ├── utils/                        # Test helpers
│   ├── INSTALLATION.md
│   └── README.md
├── DESKTOP_BUILD.md                  # Tauri build instructions
├── LICENSE-THIRD-PARTY.md            # Third-party JS/Rust licenses
├── build-all.ps1                     # One-shot Windows build (FastAPI exe + Tauri MSI/NSIS)
├── build-all.sh                      # One-shot Linux/macOS build (FastAPI exe + Tauri .deb/AppImage/.dmg)
├── index.html
├── package.json
├── tsconfig.json
├── tsconfig.node.json
├── vite.config.ts
├── vitest.config.ts
├── playwright.config.ts
├── postcss.config.js
└── tailwind.config.js
```

## Available Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start development server with hot reload |
| `npm run build` | Build for production |
| `npm run preview` | Preview production build locally |
| `npm run lint` | Run ESLint |
| `npm run bundle` | Copy build to FastAPI static folder |

## Testing

- `npm test`: Run unit and integration tests (Vitest)
- `npm run test:coverage`: Generate coverage report (HTML/LCOV)
- `npm run test:e2e`: Run Playwright E2E tests (headless)
- First time E2E setup: `npx playwright install`

See detailed instructions in `tests/README.md`.

## Desktop Application (Tauri)

Build a **standalone cross-platform desktop app** for Windows, macOS, and Linux that
bundles both the React UI and the FastAPI backend into a single installer.

For Tauri dev mode (hot-reload window for the desktop app), see the
[Development Workflow section in DESKTOP_BUILD.md](DESKTOP_BUILD.md#development-workflow-hot-reload).

### Production Build

A one-shot build script is provided for both Windows and Linux/macOS. It runs all
three stages (PyInstaller → Vite → Tauri bundle) and produces platform-native
installers.

**Linux / macOS:**
```bash
cd wrappers/rest-api/tools/react-viewer
chmod +x build-all.sh
./build-all.sh             # build everything
./build-all.sh --clean     # clean + rebuild
```

**Windows (PowerShell):**
```powershell
cd wrappers\rest-api\tools\react-viewer
.\build-all.ps1            # build everything
.\build-all.ps1 -Clean     # clean + rebuild
```

Both scripts produce, under the repository root:
- `build/rest-api-dist/realsense_api/` - PyInstaller bundle of the FastAPI backend
- `build/tauri-target/release/bundle/` - native installer(s):
  - Windows: `.msi` + `.exe` (NSIS)
  - Linux: `.deb` + `.AppImage`
  - macOS: `.dmg`

Prerequisites: Node.js 18+, Python 3.8+, Rust 1.56+ (https://rustup.rs/), PyInstaller
(`pip install pyinstaller`).

**Linux only — Tauri build dependencies.** The Rust bundler needs WebKitGTK and a few
other dev headers. On Debian/Ubuntu:
```bash
sudo apt install -y \
  libwebkit2gtk-4.0-dev libgtk-3-dev libsoup2.4-dev \
  libayatana-appindicator3-dev librsvg2-dev libssl-dev \
  pkg-config build-essential
```

For Tauri internals (architecture, subprocess management, config reference),
manual build steps, dev mode and troubleshooting, see
[DESKTOP_BUILD.md](DESKTOP_BUILD.md).

## Production Deployment

### Option 1: Web Browser

1. Start the FastAPI backend (separate)
2. Deploy React app on any static hosting (Vercel, Netlify, etc.)
3. Configure API URL for your backend server

### Option 2: Bundled Web (FastAPI serves React)

1. Build the React app:
   ```bash
   npm run build
   npm run bundle
   ```

2. This copies the build to `../rest-api/static/`

3. Add static file serving to `main.py`:
   ```python
   from fastapi.staticfiles import StaticFiles
   
   # Add at the end, after all API routes
   app.mount("/", StaticFiles(directory="static", html=True), name="static")
   ```

4. Run FastAPI server - it will serve both API and UI:
   ```bash
   python main.py
   ```

## Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **TailwindCSS** - Styling
- **Zustand** - State management
- **React Three Fiber** - 3D point cloud rendering
- **Recharts** - IMU data charts
- **Socket.IO Client** - Real-time metadata
- **WebRTC** - Low-latency video streaming

## API Integration

The viewer connects to the REST API at `/api/v1/`:

- `GET /devices` - List connected devices
- `GET /devices/{id}/sensors` - Get device sensors
- `PUT /devices/{id}/sensors/{sid}/options/{oid}` - Update camera option
- `POST /devices/{id}/streams/start` - Start streaming
- `POST /webrtc/offer` - WebRTC signaling

Real-time data is received via Socket.IO on the `/socket` path.

## License

Apache License 2.0 - See the main librealsense repository for details.
