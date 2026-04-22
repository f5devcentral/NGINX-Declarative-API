# Web UI Summary - NGINX Declarative API

## Project Overview

A React TypeScript web interface for the NGINX Declarative API v5.5, providing a form-driven UI for creating and submitting NGINX configurations.

## 📦 Core Features

- Form-driven NGINX configuration builder (HTTP, Layer 4, Output)
- API Gateway editor with OpenAPI schema support
- Profile management (rate limiting, authentication, authorization, caching)
- Real-time JSON preview and submission
- Toast notifications for user feedback
- Dark-themed responsive UI

## 📁 Source Structure

```text
webui/
├── src/
│   ├── components/
│   │   ├── ConfigForm.tsx               # Root config form (thin wrapper)
│   │   ├── ConfigForm.css               # Form styles
│   │   ├── Header.tsx                   # Navigation header
│   │   ├── Header.css
│   │   ├── Layout.tsx                   # Page layout wrapper
│   │   ├── Layout.css
│   │   └── configForm/                  # Config form modules
│   │       ├── types.ts                 # All TypeScript interfaces
│   │       ├── defaults.ts              # Factory functions, parseConfig, toJson
│   │       ├── primitives.tsx           # Shared UI primitives (Field, TextInput, etc.)
│   │       ├── ApiGatewayEditor.tsx     # API Gateway location editor
│   │       ├── LocationEditors.tsx      # Location sub-editors (auth, cache, etc.)
│   │       ├── LocationsEditor.tsx      # Locations list editor
│   │       ├── TlsEditor.tsx            # TLS configuration editor
│   │       ├── ServersSection.tsx       # HTTP servers section
│   │       ├── UpstreamsSection.tsx     # HTTP upstreams section
│   │       ├── ProfilesSection.tsx      # HTTP profiles (rate limit, auth, etc.)
│   │       ├── HttpSection.tsx          # HTTP section wrapper
│   │       ├── OutputSection.tsx        # Output target section (NIM / NGINX One)
│   │       └── Layer4Section.tsx        # Layer 4 TCP/UDP section
│   ├── pages/
│   │   ├── CreateConfigPage.tsx         # Main (and only) page
│   │   └── CreateConfigPage.css
│   ├── test/
│   │   ├── setup.ts                     # Test setup (IntersectionObserver + clipboard polyfills)
│   │   ├── ConfigForm.agw.test.tsx      # AGW section toggle + OpenAPI schema tests
│   │   ├── ConfigForm.agw.validation.test.tsx  # AGW field validation tests
│   │   ├── ConfigForm.agw.profiles.test.tsx    # Profile dropdown tests
│   │   ├── ConfigForm.output.test.tsx   # OutputSection — type cards, license, resolver, sidebar, clipboard
│   │   └── CreateConfigPage.test.tsx    # Page-level integration tests
│   ├── types/index.ts                   # Shared type definitions
│   ├── App.tsx                          # App entry — single route to CreateConfigPage
│   ├── main.tsx                         # React entry point
│   └── index.css                        # Global styles
├── Dockerfile                           # Production build
├── nginx.conf                           # NGINX serving config
├── vite.config.ts                       # Vite config
├── tsconfig.json                        # TypeScript config
├── package.json                         # Dependencies
└── index.html                           # HTML template
```

## 🚀 How to Use

### Development

```bash
cd webui
npm install
npm run dev
```

Access at: <http://localhost:5173\>

### Production (Docker Compose)

```bash
cd contrib/docker-compose
./nginx-dapi.sh -c build
./nginx-dapi.sh -c start
```

Access at: <http://localhost:3000\>

### Testing

```bash
cd webui
npm test
npm run test:coverage
```

## 🎨 UI Structure

### Page

**Create Config** (`/`) — the single page of the application.

- Output section (NGINX Instance Manager or NGINX One Console target, license with JWT upload, policies, certificates, log profiles)
- HTTP section (profiles, servers, upstreams — resolver field uses a ProfileSelect dropdown)
- Layer 4 section (TCP/UDP servers and upstreams)
- Sticky sidebar navigation with active-section highlighting
- Submit button sends the generated JSON to the API

### Components

- **Header** — application title bar
- **Layout** — consistent page wrapper
- **ConfigForm** — root form, composed from 13 focused sub-modules in `configForm/`

## 📊 Technology Stack

| Layer | Technology |
|---|---|
| Framework | React 19 |
| Language | TypeScript |
| Build | Vite |
| Routing | React Router v7 |
| HTTP | Fetch / Axios |
| Styling | CSS3 with custom properties |
| Testing | Vitest + Testing Library |
| Container | Docker + NGINX |

## 🧪 Test Coverage

- ✅ API Gateway section toggle behaviour
- ✅ OpenAPI schema URL/file/base64 modes
- ✅ Field validation (required errors)
- ✅ Profile dropdown population from HTTP-level profiles
- ✅ Live profile name propagation to API Gateway dropdowns
- ✅ Page-level integration (submit, JSON editor round-trip)
- ✅ Output type card labels (NGINX Instance Manager / NGINX One Console)
- ✅ License section toggle, grace_period boolean, JWT file upload
- ✅ Resolver ProfileSelect dropdown population and emission
- ✅ Sidebar navigation rendering and indented subsection links
- ✅ Clipboard execCommand fallback (non-secure context)

## 🌐 API Endpoints Used

- `POST /v5.5/config`
- `GET /v5.5/config/{configUid}`
- `PATCH /v5.5/config/{configUid}`
- `DELETE /v5.5/config/{configUid}`
- `GET /v5.5/config/{configUid}/status`
- `GET /v5.5/config/{configUid}/submission/{submissionUid}`

## 📚 Documentation

1. **README.md** — Overview and setup instructions
2. **QUICKSTART.md** — 5-minute getting started guide
3. **IMPLEMENTATION.md** — Technical implementation details
