# DisasterLens AI Frontend

Modern React.js frontend for DisasterLens AI - Real-Time Climate Emergency Intelligence System.

## Tech Stack

- **React 18** - UI library
- **Vite** - Build tool and dev server
- **Tailwind CSS** - Styling
- **React Leaflet** - Interactive maps
- **Recharts** - Data visualization
- **React Query** - Data fetching and caching
- **Axios** - HTTP client
- **Lucide React** - Icons

## Installation

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install
# or
yarn install
```

## Development

```bash
# Start development server (runs on http://localhost:3000)
npm run dev
# or
yarn dev
```

The dev server will proxy API requests to `http://localhost:8080` automatically.

## Build

```bash
# Build for production
npm run build
# or
yarn build

# Preview production build
npm run preview
# or
yarn preview
```

## Environment Variables

Create a `.env` file in the frontend directory (optional):

```env
VITE_API_URL=http://localhost:8080/api
VITE_WS_URL=ws://localhost:8080/ws
```

## Features

- 🗺️ Interactive disaster map with real-time markers
- 🔍 RAG query interface with multi-modal support
- 🖼️ Satellite imagery viewer with GPT-4 Vision analysis
- 📊 Statistics dashboard with charts
- 📡 Real-time WebSocket updates
- 🎨 Dark mode UI
- 📱 Responsive design

## Project Structure

```
frontend/
├── public/
│   └── index.html
├── src/
│   ├── components/      # React components
│   │   ├── Dashboard/
│   │   ├── Events/
│   │   ├── Header/
│   │   ├── Imagery/
│   │   ├── Map/
│   │   ├── Query/
│   │   └── Sidebar/
│   ├── hooks/           # Custom React hooks
│   ├── services/        # API and WebSocket services
│   ├── utils/           # Utility functions
│   ├── App.jsx
│   ├── index.js
│   └── index.css
├── package.json
├── vite.config.js
└── tailwind.config.js
```
