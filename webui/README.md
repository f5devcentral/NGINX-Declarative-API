# NGINX Declarative API Web UI

Modern React TypeScript web interface for the NGINX Declarative API v5.5.

## Features

- � Create and manage NGINX configurations
- 🎨 Modern, responsive UI with dark theme
- 🔄 Real-time status monitoring
- 🧪 Automated test suite with Vitest
- 🚀 Built with React 19, TypeScript, and Vite

## Tech Stack

- **React 19** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **React Router** - Client-side routing
- **Monaco Editor** - JSON editor with schema validation
- **Vitest** - Testing framework
- **React Testing Library** - Component testing

## Development

### Prerequisites

- Node.js 24+
- npm or yarn

### Install dependencies

```bash
npm install
```

### Start development server

```bash
npm run dev
```

The app will be available at <http://localhost:3000>

### Local Development with Docker Backend

For the best development experience, run the Web UI locally while keeping backend services (Redis, NGINX DAPI, DevPortal) in Docker containers:

**1. Start backend services:**

```bash
cd ../contrib/docker-compose
docker-compose -f docker-compose.dev.yaml up -d
```

**2. Run Web UI locally:**

```bash
cd ../../webui  # or back to webui directory
npm install     # first time only
npm run dev
```

This setup provides:

- ⚡ Instant hot-reload for UI changes
- 🐛 Full browser DevTools debugging
- 🔧 Backend isolation in containers
- 🚀 Faster iteration cycles

The Vite proxy automatically forwards `/v5.5` API requests to the containerized backend.

**Important:** If you started the backend with a custom port using `nginx-dapi.sh -a <port>`, you must set `VITE_DAPI_PORT` to match:

```bash
# Example: Backend running on port 8088
cd ../contrib/docker-compose
./nginx-dapi.sh -c start -m dev -a 8088

# Start webui with matching port
cd ../../webui
VITE_DAPI_PORT=8088 npm run dev
```

**Using a custom DAPI port:**

If your NGINX Declarative API is running on a custom port (e.g., 8080), set the environment variable:

```bash
# Linux/macOS
export VITE_DAPI_PORT=8080
npm run dev

# Or inline
VITE_DAPI_PORT=8080 npm run dev

# Windows (PowerShell)
$env:VITE_DAPI_PORT=8080
npm run dev
```

Or create a `.env.local` file:

```bash
VITE_DAPI_PORT=8080
```

### Run tests

```bash
# Run tests once
npx vitest run

# Run tests in watch mode
npm test

# Run tests with UI
npm run test:ui

# Generate coverage report
npm run test:coverage
```

### Build for production

```bash
npm run build
```

### Preview production build

```bash
npm run preview
```

## Docker

### Build Docker image

```bash
docker build -t nginx-dapi-webui .
```

### Run Docker container

```bash
docker run -p 8080:80 nginx-dapi-webui
```

## Usage

### Create Configuration

- Use JSON editor to create configurations
- Based on v5.5 API schema
- Support for NIM and NGINX One outputs

## API Endpoints

The web UI uses the following v5.5 API endpoints:

- `POST /v5.5/config` - Create configuration
- `GET /v5.5/config/{configUid}` - Get configuration
- `PATCH /v5.5/config/{configUid}` - Update configuration
- `DELETE /v5.5/config/{configUid}` - Delete configuration
- `GET /v5.5/config/{configUid}/status` - Get status
- `GET /v5.5/config/{configUid}/submission/{submissionUid}` - Get submission status

## Configuration

### Development Mode

The Vite dev server proxies API requests to the backend:

```typescript
'/v5.5': {
  target: 'http://localhost:5000',  // NGINX Declarative API
  changeOrigin: true,
}
```

You can customize the backend port using the `VITE_DAPI_PORT` environment variable:

```bash
VITE_DAPI_PORT=8080 npm run dev
```

This is especially useful when:
- Running the backend on a custom port
- Developing locally with Docker backend services
- Testing against different API instances

### Production Mode

In production, NGINX handles the proxy configuration (see `nginx.conf`).

## Project Structure

```text
webui/
├── src/
│   ├── components/    # Reusable components
│   ├── pages/         # Page components
│   ├── test/          # Test files
│   ├── types/         # TypeScript type definitions
│   ├── App.tsx        # Main app component
│   ├── main.tsx       # Entry point
│   └── index.css      # Global styles
├── public/            # Static assets
├── Dockerfile         # Production Docker image
├── nginx.conf         # NGINX configuration for production
├── vite.config.ts     # Vite configuration
├── tsconfig.json      # TypeScript configuration
└── package.json       # Dependencies and scripts
```

## Security Considerations

- Enable HTTPS/TLS in production
- Configure CORS headers appropriately on the backend
- Add rate limiting to API endpoints
- Enable security headers (CSP, HSTS, X-Frame-Options)
- Validate and sanitize all user inputs

## Contributing

See the main project [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

## License

Apache License 2.0 - See [LICENSE.md](../LICENSE.md)
