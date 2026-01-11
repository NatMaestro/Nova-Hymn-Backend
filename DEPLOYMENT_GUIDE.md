# Deployment Guide for Render.com

## Prerequisites

1. Render.com account
2. GitHub repository with your backend code
3. Neon Postgres database (or use Render's PostgreSQL)

## Step 1: Prepare Backend for Production

### 1.1 Update Environment Variables

Create a `.env` file for production or set in Render dashboard:

```env
DEBUG=False
ENV=production
SECRET_KEY=your-very-secure-secret-key-here
ALLOWED_HOSTS=nova-hymnal-be.onrender.com
CORS_ALLOW_ALL_ORIGINS=False
CORS_ALLOWED_ORIGINS=https://your-frontend-domain.com
CSRF_TRUSTED_ORIGINS=https://your-frontend-domain.com
REVENUECAT_WEBHOOK_SECRET=your_webhook_secret
```

### 1.2 Database Configuration

If using Neon Postgres (recommended):
- Keep your existing database connection string
- Add to Render environment variables

If using Render's PostgreSQL:
- Create PostgreSQL database in Render
- Update connection variables

## Step 2: Deploy to Render

### Option A: Using Render Dashboard

1. **Create New Web Service**
   - Connect your GitHub repository
   - Select branch (usually `main` or `master`)
   - Choose Python environment

2. **Configure Build Settings**
   - Build Command: `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate`
   - Start Command: `gunicorn config.wsgi:application`

3. **Set Environment Variables**
   - Copy from `.env` file
   - Add all required variables
   - **Important**: Set `DEBUG=False` and `ENV=production`

4. **Deploy**
   - Click "Create Web Service"
   - Wait for build to complete
   - Check logs for errors

### Option B: Using Render Blueprint

1. **Add `render.yaml` to Repository**
   - Already included in the project
   - Update with your specific values

2. **Deploy via Blueprint**
   - Go to Render Dashboard
   - Click "New" > "Blueprint"
   - Connect repository
   - Render will read `render.yaml`

## Step 3: Update Frontend Configuration

### 3.1 Update API URL

In `Nova-Hymnal-Premium/.env`:

```env
EXPO_PUBLIC_PROD_API_URL=https://nova-hymnal-be.onrender.com/api/v1
EXPO_PUBLIC_USE_MOCK_DATA=false
```

### 3.2 Test Connection

1. Build app with production API URL
2. Test authentication
3. Test API endpoints
4. Verify CORS is working

## Step 4: Configure CORS

### For Development
```env
CORS_ALLOW_ALL_ORIGINS=True
```

### For Production
```env
CORS_ALLOW_ALL_ORIGINS=False
CORS_ALLOWED_ORIGINS=https://your-frontend-domain.com,https://expo.dev
```

**Note**: React Native apps don't use CORS, but web builds do. Set this for web compatibility.

## Step 5: Set Up Webhooks

### RevenueCat Webhook

1. Get your Render URL: `https://nova-hymnal-be.onrender.com`
2. Add webhook in RevenueCat dashboard:
   - URL: `https://nova-hymnal-be.onrender.com/api/v1/webhooks/revenuecat/`
   - Select all subscription events
   - Copy webhook secret
3. Add webhook secret to Render environment variables

## Step 6: Static Files

Render automatically handles static files with WhiteNoise. Ensure:

1. `whitenoise` is in `requirements.txt`
2. `STATIC_ROOT` is set in `settings.py`
3. `collectstatic` runs during build

## Step 7: Database Migrations

Migrations run automatically during build. To run manually:

```bash
# SSH into Render instance (if available) or use Render Shell
python manage.py migrate
```

## Step 8: Admin Access

1. Create superuser locally or via Django shell
2. Access admin at: `https://nova-hymnal-be.onrender.com/admin/`
3. Use HTTPS in production

## Troubleshooting

### Build Fails

- Check Python version matches (3.11+)
- Verify all dependencies in `requirements.txt`
- Check build logs for specific errors

### 500 Errors

- Check application logs
- Verify environment variables are set
- Check database connection
- Verify `SECRET_KEY` is set

### CORS Errors

- Verify `CORS_ALLOWED_ORIGINS` includes your frontend URL
- Check `ALLOWED_HOSTS` includes your Render domain
- For React Native, CORS doesn't apply (only for web)

### Database Connection Issues

- Verify database credentials
- Check database is accessible from Render
- Verify SSL mode if using external database

## Environment Variables Checklist

- [ ] `DEBUG=False`
- [ ] `ENV=production`
- [ ] `SECRET_KEY` (secure random string)
- [ ] `ALLOWED_HOSTS` (your Render domain)
- [ ] `CORS_ALLOWED_ORIGINS` (your frontend URLs)
- [ ] `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`
- [ ] `REVENUECAT_WEBHOOK_SECRET`

## Post-Deployment

1. **Test All Endpoints**
   - Authentication
   - Hymns API
   - Subscriptions
   - Webhooks

2. **Monitor Logs**
   - Check for errors
   - Monitor performance
   - Watch for security issues

3. **Update Frontend**
   - Point to production API
   - Test end-to-end
   - Deploy frontend

4. **Set Up Monitoring**
   - Render provides basic monitoring
   - Consider adding Sentry for error tracking
   - Set up uptime monitoring

## Security Checklist

- [ ] `DEBUG=False` in production
- [ ] `SECRET_KEY` is secure and unique
- [ ] `ALLOWED_HOSTS` is restricted
- [ ] CORS is properly configured
- [ ] HTTPS is enabled (automatic on Render)
- [ ] Database credentials are secure
- [ ] Webhook secrets are set

