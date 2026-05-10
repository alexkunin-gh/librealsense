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
├── src/                # React app (TypeScript)
│   ├── api/            # Backend clients (REST, Socket.IO, WebRTC, chat)
│   ├── components/     # React components
│   │   └── ChatBot/    # AI chat UI (Ask + Agent modes)
│   ├── store/          # Zustand state management
│   └── utils/          # Helpers (e.g. AI prompt builder)
├── src-tauri/          # Tauri desktop bridge (Rust)
│   ├── src/            # Rust sources
│   ├── icons/          # App icons (reused from common/res)
│   └── resources/
├── public/             # Static assets (favicon, logos)
├── scripts/            # Build helpers (e.g. bundle-for-prod)
└── tests/              # Vitest unit + Playwright E2E tests
    ├── unit/
    ├── e2e/
    ├── mocks/          # MSW handlers + fixtures
    ├── setup/          # Vitest global setup
    └── utils/          # Test helpers
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

**Linux distro support (Tauri 1.5).** This project currently uses Tauri 1.5, which
links against WebKitGTK 4.0:

| Ubuntu LTS    | Codename | Desktop build (Tauri)                                                 |
|---------------|----------|-----------------------------------------------------------------------|
| 20.04         | Focal    | ✅ Native build                                                        |
| 22.04         | Jammy    | ✅ Native build (recommended)                                          |
| 24.04         | Noble    | ❌ Not supported with Tauri 1.5 (4.0 headers removed; the symlink hack passes pkg-config but the wry crate then fails to compile against the 4.1 API) |
| 26.04         | Resolute | ❌ 4.0 packages no longer shipped                                      |

> **Ubuntu 24.04 / 26.04 users:** the desktop installer build (`build-all.sh`) cannot
> currently produce a working binary on these distros. Use the **two-terminal dev
> setup** described in [Quick Start](#quick-start) instead — it works on every Ubuntu
> version. That gives you the full viewer running locally (FastAPI on `:8000`, React
> on `:3000` in the browser); you just don't get a packaged `.AppImage` / `.deb`.

**Migration to Tauri 2** — planned as a future improvement, and the path that will
unblock Ubuntu 24.04+ desktop builds. Tauri 2 links against WebKitGTK 4.1 and builds
natively on those distros. The migration is medium effort (half a day for an
experienced dev): bump `tauri` / `tauri-build` / wry, run `npm run tauri migrate` to
auto-rewrite ~70 % of `tauri.conf.json` and the JS API imports, then fix residual
compile errors and re-test the FastAPI subprocess spawn.

**Linux only — Tauri build dependencies.** The Rust bundler needs WebKitGTK and a few
other dev headers. On Debian/Ubuntu:
```bash
sudo apt install -y \
  libwebkit2gtk-4.0-dev libgtk-3-dev libsoup2.4-dev \
  libayatana-appindicator3-dev librsvg2-dev libssl-dev \
  pkg-config build-essential
```

**If `build-all.sh` fails with `failed to get cargo metadata` or `cargo: command not
found`**, your shell does not have `cargo` on `PATH`. After installing Rust via
[rustup](https://rustup.rs/), enable it in the current shell with:
```bash
source $HOME/.cargo/env
```
To make this permanent, add the same line to `~/.bashrc`. The build script also
attempts this automatically if it detects `cargo` is missing.

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
