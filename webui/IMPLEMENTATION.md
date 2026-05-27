# NGINX Declarative API - Web UI Implementation Details

## Overview

A React 19 TypeScript single-page application for creating and submitting NGINX Declarative API v5.6 configurations. The UI renders a structured form and submits the resulting JSON to the backend API.

## Features Implemented

### Configuration Form

- Output section — target NGINX Instance Manager or NGINX One Console, with license (JWT token upload, boolean enforce-initial-report toggle)
- HTTP section — policies, TLS certificates, and log profiles (moved to declaration body in v5.6), plus profiles (rate limiting, auth, authz, caching, maps, log), servers, and upstreams
- Sticky sidebar navigation with IntersectionObserver-based active-section highlighting
- Layer 4 section — TCP/UDP servers and upstreams
- API Gateway editor — per-location OpenAPI schema integration (URL / file upload / base64)

### API Integration

All v5.6 endpoints are integrated:

- POST /v5.6/config — Create configuration
- GET /v5.6/config/{configUid} — Retrieve configuration
- PATCH /v5.6/config/{configUid} — Update configuration
- DELETE /v5.6/config/{configUid} — Delete configuration
- GET /v5.6/config/{configUid}/status — Get status
- GET /v5.6/config/{configUid}/submission/{submissionUid} — Get async submission status

### Testing

- Vitest + React Testing Library
- 91 tests across 5 files
- Component tests (ConfigForm API Gateway, validation, profile dropdowns, OutputSection)
- Page-level integration tests (CreateConfigPage)
- Coverage reporting configured

### DevOps

- Docker support with multi-stage build
- NGINX reverse proxy configuration
- Integration with docker-compose
- Configurable ports
- Development and production builds

## 📁 Project Structure

```text
webui/
├── src/
│   ├── components/           # Reusable components
│   │   ├── ConfigForm.tsx    # Root form (thin wrapper)
│   │   ├── ConfigForm.css
│   │   ├── Header.tsx
│   │   ├── Layout.tsx
│   │   └── configForm/       # Form sub-modules
│   │       ├── types.ts      # All TypeScript interfaces
│   │       ├── defaults.ts   # Factory functions, parseConfig, toJson
│   │       ├── primitives.tsx
│   │       ├── ApiGatewayEditor.tsx
│   │       ├── LocationEditors.tsx
│   │       ├── LocationsEditor.tsx
│   │       ├── TlsEditor.tsx
│   │       ├── ServersSection.tsx
│   │       ├── UpstreamsSection.tsx
│   │       ├── ProfilesSection.tsx
│   │       ├── HttpSection.tsx
│   │       ├── OutputSection.tsx
│   │       └── Layer4Section.tsx
│   ├── pages/                # Page components
│   │   └── CreateConfigPage.tsx
│   ├── test/                 # Test files
│   │   ├── setup.ts
│   │   ├── ConfigForm.agw.test.tsx
│   │   ├── ConfigForm.agw.validation.test.tsx
│   │   ├── ConfigForm.agw.profiles.test.tsx
│   │   ├── ConfigForm.output.test.tsx
│   │   └── CreateConfigPage.test.tsx
│   ├── types/                # TypeScript definitions
│   │   └── index.ts
│   ├── App.tsx               # Main app with routing
│   ├── main.tsx              # Entry point
│   └── index.css             # Global styles
├── Dockerfile                # Production Docker build
├── nginx.conf                # NGINX config for production
├── vite.config.ts            # Vite configuration
├── tsconfig.json             # TypeScript config
└── package.json              # Dependencies
```

## 🛠 Technology Stack

| Category | Technology | Purpose |
|-|-|-|
| **Framework** | React 19 | UI library |
| **Language** | TypeScript | Type safety |
| **Build Tool** | Vite | Fast dev server & build |
| **Routing** | React Router v7 | Client-side routing |
| **HTTP Client** | Axios | API requests |
| **JSON Editor** | Monaco Editor | Schema-aware JSON editing |
| **UI Feedback** | React Hot Toast | Notifications |
| **Testing** | Vitest + Testing Library | Unit & component tests |

## 🚀 Getting Started

### Development

```bash
cd webui
npm install
npm run dev
```

Access at <http://localhost:5173\>

### Running Tests

```bash
npm test              # Run tests
npm run test:ui       # Test UI
npm run test:coverage # Coverage report
```

### Production Build

```bash
npm run build
npm run preview
```

### Docker

```bash
cd contrib/docker-compose

# Build all images including Web UI
./nginx-dapi.sh -c build

# Start with default ports
./nginx-dapi.sh -c start

# Start with custom ports
./nginx-dapi.sh -c start -a 8080 -w 8081 -d 8082 -r 6380
```

**Access Points:**

- Web UI: <http://localhost:3000\> (or custom port)
- API: <http://localhost:5000\> (or custom port)
- DevPortal: <http://localhost:5001\> (or custom port)

## 📋 Type Definitions

Key TypeScript interfaces (see `src/components/configForm/types.ts`):

```typescript
interface ConfigData {
  output?: OutputConfig;
  declaration?: {
    http?: HttpConfig;
    layer4?: Layer4Config;
    resolvers?: ResolverConfig[];
  };
}
```

## 🎨 UI Design

**Theme:** Dark mode with gradient backgrounds

**Color Scheme:**

- Primary: `#646cff` (purple-blue)
- Success: `#34c759` (green)
- Error: `#ff3b30` (red)
- Background: Gradient from `#1a1a2e` to `#16213e`

**Key Features:**

- Glassmorphism effects
- Smooth animations and transitions
- Responsive grid layouts
- Status indicators with color coding

## 📊 API Request Flow

```text
User Action → React Component → Fetch/Axios → Backend API
                    ↓
            State Update (useState)
                    ↓
              UI Re-render
```

## 🌐 API Proxy Configuration

**Development (Vite):**

```typescript
'/v5.5': {
  target: 'http://localhost:5000',
  changeOrigin: true,
}
```

**Production (NGINX):**

```nginx
location /v5.5/ {
  proxy_pass http://nginx-dapi:5000;
  # ... proxy headers
}
```

## 📦 Docker Multi-Stage Build

1. **Build stage:** Node.js 24 Alpine — install dependencies, build production bundle
2. **Production stage:** NGINX Alpine — copy built files, serve with NGINX, proxy API requests to backend

## 🧪 Test Coverage

Tests implemented for:

- API Gateway section toggle and OpenAPI schema modes
- Field validation (required error messages)
- Profile dropdown population from HTTP-level profiles
- Live profile name propagation to API Gateway location dropdowns
- Page-level integration (submit, JSON editor round-trip, status polling)

## 📚 Related Documentation

- [Web UI README](README.md) - Setup and usage guide
- [USAGE-v5.5.md](../USAGE-v5.5.md) - API v5.5 usage guide
- [Docker Compose README](../contrib/docker-compose/README.md) - Deployment guide
- [OpenAPI Spec](../openapi.json) - Complete API specification

## 🤝 Contributing

When contributing to the Web UI:

1. Follow TypeScript best practices
2. Write tests for new features
3. Update type definitions when API changes
4. Document new components

## 📄 License

Apache License 2.0 - See [LICENSE.md](../LICENSE.md)
