# CORS Configuration for React Native

## 🔑 Key Point: CORS Doesn't Apply to Native Apps!

**CORS (Cross-Origin Resource Sharing) is a browser security feature.** It does NOT apply to:
- ✅ Native iOS apps
- ✅ Native Android apps
- ✅ React Native apps running on physical devices
- ✅ React Native apps running in simulators/emulators

**CORS DOES apply to:**
- ⚠️ Expo Web (browser-based testing)
- ⚠️ Browser-based development tools
- ⚠️ Web previews of your app

---

## 📱 How React Native Makes API Requests

### Native Apps (iOS/Android)
```
React Native App (Native)
    ↓
Direct HTTP Request (No CORS check)
    ↓
Django Backend
```

**No CORS headers needed!** The app makes direct HTTP requests just like a server would.

### Expo Web (Browser)
```
React Native App (Expo Web)
    ↓
Browser HTTP Request (CORS check happens)
    ↓
Django Backend (must send CORS headers)
```

**CORS headers are required** because it's running in a browser.

---

## ⚙️ Current Configuration

### Development (DEBUG=True)
```python
CORS_ALLOW_ALL_ORIGINS = True  # Allows all origins (convenient for dev)
```

This means:
- ✅ All web origins are allowed (Expo Web, browser testing)
- ✅ Native apps work without any CORS configuration
- ⚠️ Less secure (only use in development!)

### Production (DEBUG=False)
```python
CORS_ALLOW_ALL_ORIGINS = False  # Must specify allowed origins
CORS_ALLOWED_ORIGINS = [
    'http://localhost:19006',  # Expo Web
    'http://localhost:8081',   # Expo Web alternative port
    # Add your production web URLs here
]
```

---

## 🚀 Setting Up for Different Scenarios

### 1. Native App Development (Most Common)

**No CORS configuration needed!** Your React Native app will work out of the box.

Just make sure your API base URL is correct:
```typescript
// lib/config.ts
BASE_URL: "http://localhost:8000/api/v1"  // For simulator/emulator
// OR
BASE_URL: "http://YOUR_COMPUTER_IP:8000/api/v1"  // For physical device
```

### 2. Physical Device Testing

When testing on a physical device, you need to use your computer's IP address instead of `localhost`:

1. **Find your computer's IP address:**
   ```bash
   # Windows
   ipconfig
   # Look for IPv4 Address (e.g., 192.168.1.100)
   
   # Mac/Linux
   ifconfig
   # Look for inet (e.g., 192.168.1.100)
   ```

2. **Update your React Native config:**
   ```typescript
   // lib/config.ts
   BASE_URL: "http://192.168.1.100:8000/api/v1"  // Your computer's IP
   ```

3. **Make sure your computer and device are on the same WiFi network**

4. **No CORS changes needed** - native apps don't use CORS!

### 3. Expo Web Testing

If you're testing in Expo Web (browser), you need CORS headers:

**Current setup already handles this:**
- `CORS_ALLOW_ALL_ORIGINS = True` in development
- Includes `http://localhost:19006` and `http://localhost:8081` in allowed origins

**If you get CORS errors in Expo Web:**
1. Check that `DEBUG=True` in your `.env` file
2. Or add your specific Expo Web URL to `CORS_ALLOWED_ORIGINS`

### 4. Production Deployment

For production, you need to be more restrictive:

```python
# settings.py (production)
DEBUG = False
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    'https://your-production-domain.com',
    'https://www.your-production-domain.com',
    # Add any web-based admin panels or web previews here
]
```

**Note:** Native apps still don't need CORS, but you should:
- Use HTTPS in production
- Implement proper authentication (JWT tokens)
- Use API keys or other security measures

---

## 🔒 Security Best Practices

### For Native Apps
1. **Use HTTPS in production** - encrypt all API traffic
2. **Implement JWT authentication** - secure user sessions
3. **Validate API responses** - don't trust client-side data
4. **Use certificate pinning** (advanced) - prevent man-in-the-middle attacks

### For Web (Expo Web)
1. **Restrict CORS origins** - only allow specific domains
2. **Use HTTPS** - encrypt all traffic
3. **Implement CSRF protection** - prevent cross-site attacks
4. **Validate all inputs** - server-side validation

---

## 🐛 Troubleshooting

### "CORS Error" in Expo Web
**Solution:** Make sure `CORS_ALLOW_ALL_ORIGINS = True` in development, or add your Expo Web URL to `CORS_ALLOWED_ORIGINS`.

### "Network Error" on Physical Device
**Solution:** 
1. Use your computer's IP address instead of `localhost`
2. Make sure both devices are on the same WiFi network
3. Check that your firewall allows connections on port 8000

### "Connection Refused" in Simulator
**Solution:**
1. Make sure Django server is running: `python manage.py runserver 0.0.0.0:8000`
2. Use `0.0.0.0` instead of `127.0.0.1` to allow external connections
3. Check that port 8000 is not blocked by firewall

### API Works in Native App but Not in Expo Web
**Solution:** This is expected! Native apps don't use CORS, but Expo Web does. Make sure CORS is properly configured for web origins.

---

## 📝 Summary

| Scenario | CORS Needed? | Configuration |
|----------|--------------|---------------|
| Native iOS/Android App | ❌ No | Just set correct API URL |
| Physical Device | ❌ No | Use computer's IP address |
| Simulator/Emulator | ❌ No | Use localhost or IP |
| Expo Web | ✅ Yes | Configure CORS headers |
| Browser Testing | ✅ Yes | Configure CORS headers |
| Production Native | ❌ No | Use HTTPS + JWT auth |
| Production Web | ✅ Yes | Restrict CORS origins |

---

## 🎯 Quick Reference

**For 99% of React Native development, you don't need to worry about CORS!**

- Native apps: Just works ✅
- Physical devices: Use IP address instead of localhost ✅
- Expo Web: Already configured ✅
- Production: Restrict CORS origins ✅

The current configuration handles all these cases automatically!



