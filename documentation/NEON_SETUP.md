# Neon Postgres Setup Guide

This guide will help you set up Neon Postgres for the Nova Hymnal Backend.

## 📋 Prerequisites

- A Neon account (sign up at https://neon.tech - it's free!)
- Python 3.8+ installed
- Virtual environment activated

---

## 🚀 Step 1: Create a Neon Account and Project

1. **Sign up for Neon**: Go to https://neon.tech and create a free account
2. **Create a new project**:
   - Click "Create Project"
   - Choose a project name (e.g., "nova-hymnal")
   - Select a region closest to you
   - Click "Create Project"

---

## 🔑 Step 2: Get Your Connection Details

After creating your project, Neon will show you connection details:

1. **In the Neon Dashboard**, you'll see:
   - **Database name**: Usually `neondb` or your project name
   - **User**: Usually `neondb_owner` or similar
   - **Password**: Generated password (save this!)
   - **Host**: Something like `ep-cool-name-123456.us-east-2.aws.neon.tech`
   - **Port**: `5432`

2. **Copy these details** - you'll need them for your `.env` file

---

## 📝 Step 3: Install PostgreSQL Driver

Install the PostgreSQL adapter for Python:

```bash
cd Nova-Hymnal-Backend
pip install psycopg2-binary
```

Or install all requirements:

```bash
pip install -r requirements.txt
```

---

## ⚙️ Step 4: Configure Environment Variables

1. **Copy the example env file**:
   ```bash
   cp env.example .env
   ```

2. **Edit `.env` file** and update the database configuration:

   ```env
   # Database Configuration - Neon Postgres
   DB_ENGINE=django.db.backends.postgresql
   DB_NAME=neondb
   DB_USER=neondb_owner
   DB_PASSWORD=your_neon_password_here
   DB_HOST=ep-cool-name-123456.us-east-2.aws.neon.tech
   DB_PORT=5432
   ```

   **Replace with your actual Neon values!**

3. **Keep other settings**:
   ```env
   SECRET_KEY=your-secret-key-here
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1
   CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:19006
   ```

---

## 🗄️ Step 5: Run Migrations

1. **Test the connection**:
   ```bash
   python manage.py check --database default
   ```

2. **Create migrations** (if needed):
   ```bash
   python manage.py makemigrations
   ```

3. **Run migrations**:
   ```bash
   python manage.py migrate
   ```

   This will create all the necessary tables in your Neon database.

---

## ✅ Step 6: Verify Setup

1. **Create a superuser**:
   ```bash
   python manage.py createsuperuser
   ```

2. **Run the development server**:
   ```bash
   python manage.py runserver
   ```

3. **Test the admin**:
   - Go to http://127.0.0.1:8000/admin
   - Log in with your superuser credentials
   - You should see all your models

4. **Test the API**:
   - Go to http://127.0.0.1:8000/swagger/
   - You should see the Swagger documentation

---

## 🔒 Step 7: Security Best Practices

### For Production:

1. **Update `.env` for production**:
   ```env
   DEBUG=False
   SECRET_KEY=your-very-secure-secret-key-here
   ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
   ```

2. **Never commit `.env` to Git**:
   - `.env` should be in `.gitignore`
   - Use `.env.example` as a template

3. **Use environment variables in production**:
   - Set environment variables in your hosting platform
   - Don't store `.env` files in production

---

## 🧪 Step 8: Test Database Operations

Test that everything works:

1. **Create a hymn via admin**:
   - Go to http://127.0.0.1:8000/admin/hymns/hymn/add/
   - Fill in the form and save
   - Verify it appears in the list

2. **Test API endpoints**:
   ```bash
   # Get all hymns
   curl http://127.0.0.1:8000/api/hymns/

   # Get a specific hymn
   curl http://127.0.0.1:8000/api/hymns/1/
   ```

---

## 🔄 Switching Between SQLite and Postgres

### To use SQLite (Development):
```env
DB_ENGINE=django.db.backends.sqlite3
DB_NAME=db.sqlite3
```

### To use Neon Postgres:
```env
DB_ENGINE=django.db.backends.postgresql
DB_NAME=neondb
DB_USER=neondb_owner
DB_PASSWORD=your_password
DB_HOST=ep-cool-name-123456.us-east-2.aws.neon.tech
DB_PORT=5432
```

**Just change your `.env` file and restart the server!**

---

## 🐛 Troubleshooting

### Error: `psycopg2.OperationalError: could not connect to server`

**Solutions**:
1. Check your `.env` file has correct values
2. Verify your Neon project is active (not paused)
3. Check if your IP is whitelisted (Neon allows all by default)
4. Verify the host doesn't have `https://` prefix

### Error: `django.db.utils.OperationalError: FATAL: password authentication failed`

**Solutions**:
1. Double-check your password in `.env`
2. Reset password in Neon dashboard if needed
3. Make sure there are no extra spaces in `.env` values

### Error: `ModuleNotFoundError: No module named 'psycopg2'`

**Solution**:
```bash
pip install psycopg2-binary
```

### Database connection timeout

**Solution**:
- Neon free tier may pause inactive databases
- Wake it up from the Neon dashboard
- Or upgrade to a paid plan for always-on

---

## 📚 Additional Resources

- **Neon Documentation**: https://neon.tech/docs
- **Django Database Setup**: https://docs.djangoproject.com/en/stable/ref/databases/
- **PostgreSQL Documentation**: https://www.postgresql.org/docs/

---

## 🎉 You're All Set!

Your Nova Hymnal Backend is now connected to Neon Postgres! 

**Next Steps**:
- Seed your database with hymns using the admin bulk upload
- Test all API endpoints
- Set up your frontend to connect to the backend

---

## 💡 Pro Tips

1. **Database Branching**: Neon allows you to create branches of your database (like Git branches) - perfect for testing!

2. **Connection Pooling**: For production, consider using Neon's connection pooling feature

3. **Monitoring**: Use Neon's dashboard to monitor your database usage and performance

4. **Backups**: Neon automatically backs up your database - check the dashboard for restore options

5. **Free Tier Limits**: 
   - 0.5 GB storage
   - 1 project
   - Databases pause after inactivity (wake up from dashboard)

---

## 🔗 Quick Links

- **Neon Dashboard**: https://console.neon.tech
- **Neon Docs**: https://neon.tech/docs
- **Django ORM**: https://docs.djangoproject.com/en/stable/topics/db/



