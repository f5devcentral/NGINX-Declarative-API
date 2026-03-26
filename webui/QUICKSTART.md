# Quick Start Guide - NGINX Declarative API Web UI

## 🚀 5-Minute Setup

### Prerequisites

- Docker & Docker Compose installed
- Ports available: 3000 (Web UI), 5000 (API), 5001 (DevPortal), 6379 (Redis)

### Step 1: Clone Repository

```bash
git clone https://github.com/f5devcentral/NGINX-Declarative-API
cd NGINX-Declarative-API/contrib/docker-compose
```

### Step 2: Build & Start

```bash
# Build all Docker images (first time only)
./nginx-dapi.sh -c build

# Start all services
./nginx-dapi.sh -c start
```

Expected output:

```text
-> Deploying NGINX Declarative API
   NGINX Declarative API port: 5000
   Web UI port: 3000
   Developer Portal port: 5001
   Redis port: 6379
[+] Running 5/5
 ✔ Network nginx-dapi_dapi-network  Created
 ✔ Container redis                  Started
 ✔ Container nginx-dapi             Started
 ✔ Container devportal              Started
 ✔ Container nginx-dapi-webui       Started
```

### Step 3: Access Web UI

Open browser: <http://localhost:3000>

### Step 4: Create Your First Configuration

1. Click "Create Config" in navigation
2. Edit the JSON declaration
3. Click "Create Configuration"

Example minimal config:

```json
{
  "output": {
    "type": "nms",
    "nms": {
      "url": "https://nginx-manager.example.com",
      "username": "admin",
      "password": "yourpassword",
      "instancegroup": "production"
    }
  },
  "declaration": {
    "http": []
  }
}
```

## 🔧 Common Tasks

### Use Custom Ports

If default ports are in use:

```bash
./nginx-dapi.sh -c start -a 8080 -w 8081 -d 8082 -r 6380
```

Then access Web UI at: <http://localhost:8081>

### Stop Services

```bash
./nginx-dapi.sh -c stop
```

### View Logs

```bash
# Web UI logs
docker logs nginx-dapi-webui

# API logs  
docker logs nginx-dapi

# All logs
docker-compose -p nginx-dapi logs -f
```

### Rebuild After Changes

```bash
./nginx-dapi.sh -c stop
./nginx-dapi.sh -c build
./nginx-dapi.sh -c start
```

## 🐛 Troubleshooting

### Port Already in Use

**Error:** `Bind for 0.0.0.0:3000 failed: port is already allocated`

**Solution:**

```bash
# Check what's using the port
lsof -i :3000

# Use custom port
./nginx-dapi.sh -c start -w 8080
```

### Can't Connect to API

**Issue:** Web UI loads but can't connect to backend

**Check:**

1. Verify nginx-dapi container is running: `docker ps`
2. Check API logs: `docker logs nginx-dapi`
3. Test API directly: `curl http://localhost:5000/docs`

### Web UI Shows Blank Page

**Solutions:**

1. Check browser console for errors (F12)
2. Rebuild Web UI:

   ```bash
   ./nginx-dapi.sh -c stop
   docker rmi nginx-declarative-api-webui
   ./nginx-dapi.sh -c build
   ./nginx-dapi.sh -c start
   ```

## 📱 Development Setup

Want to modify the Web UI?

```bash
cd webui

# Install dependencies
npm install

# Start dev server (hot reload)
npm run dev

# Run tests
npm test

# Build for production
npm run build
```

Dev server runs at <http://localhost:3000> with auto-reload.

## 🎯 Next Steps

1. ✅ Login to Web UI
2. ✅ Explore the Dashboard
3. ✅ Create a test configuration
4. 📖 Read the API v5.5 usage guide in `/USAGE-v5.5.md` for API details
5. 📚 Check [Web UI Documentation](README.md)
6. 🧪 Try the Postman collection in `/contrib/postman`

## 💡 Tips

- **API Docs:** Visit <http://localhost:5000/docs> for interactive API documentation
- **Templates:** Look in `webui/src/pages/CreateConfigPage.tsx` for example configurations
- **Docker Compose:** See `contrib/docker-compose/docker-compose.yaml` for service configuration

## 🆘 Need Help?

- 📖 [Full Documentation](../README.md)
- 🐛 [Report Issues](https://github.com/f5devcentral/NGINX-Declarative-API/issues)
- 💬 [Discussions](https://github.com/f5devcentral/NGINX-Declarative-API/discussions)

---

Happy configuring! 🎉
