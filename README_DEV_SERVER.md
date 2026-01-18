# Development Server Setup

## Problem: Network Errors in React Native

If you're getting "Network Error" even though the backend is running, it's likely because:

1. **Backend is bound to `127.0.0.1`** - Only accessible from the same machine
2. **React Native emulator/device can't reach `localhost`** - Needs `0.0.0.0` binding

## Solution: Run Server on 0.0.0.0

### Windows

```bash
python manage.py runserver 0.0.0.0:8000
```

Or use the provided script:
```bash
.\start_dev_server.bat
```

### Mac/Linux

```bash
python manage.py runserver 0.0.0.0:8000
```

Or use the provided script:
```bash
chmod +x start_dev_server.sh
./start_dev_server.sh
```

## Why 0.0.0.0?

- `127.0.0.1` or `localhost` - Only accessible from the same machine
- `0.0.0.0` - Accessible from:
  - Same machine (localhost)
  - Android emulator (10.0.2.2)
  - iOS simulator (localhost)
  - Physical devices on same network (your computer's IP)

## Testing Connection

### From Browser
- `http://localhost:8000/api/v1/` - Should work
- `http://127.0.0.1:8000/api/v1/` - Should work

### From React Native
- `http://localhost:8000/api/v1/` - Works in simulator/emulator
- `http://10.0.2.2:8000/api/v1/` - Android emulator (alternative)
- `http://YOUR_IP:8000/api/v1/` - Physical devices

## Physical Device Testing

If testing on a physical device:

1. **Find your computer's IP address**:
   ```bash
   # Windows
   ipconfig
   
   # Mac/Linux
   ifconfig
   ```

2. **Update frontend `.env`**:
   ```env
   EXPO_PUBLIC_DEV_API_URL=http://192.168.1.100:8000/api/v1
   ```

3. **Update backend CORS** (if needed for web):
   ```env
   CORS_ALLOWED_ORIGINS=http://192.168.1.100:19006,http://192.168.1.100:8081
   ```

## Security Note

⚠️ **Only use `0.0.0.0` in development!**

In production, always bind to specific interfaces and use proper security measures.

## Quick Start

1. **Start backend**:
   ```bash
   python manage.py runserver 0.0.0.0:8000
   ```

2. **Verify it's accessible**:
   - Browser: `http://localhost:8000/swagger/`
   - Should see Swagger UI

3. **Start frontend**:
   ```bash
   cd Nova-Hymnal-Premium
   npm start
   ```

4. **Test connection**:
   - App should connect successfully
   - Check console for API calls



