# Environment Configuration Setup Guide

## 🔒 Security First

This guide will help you properly configure environment variables for your wedding website to ensure security and proper functionality.

## Step 1: Create Your Local .env File

1. Copy the `.env.example` file to `.env`:
   ```bash
   cp .env.example .env
   ```

2. **NEVER** commit the `.env` file to Git (it's already in `.gitignore`)

## Step 2: Generate Secure Keys

Run the included script to generate secure keys:

```bash
python generate_secrets.py
```

This will output secure values for:
- `SECRET_KEY` - Flask session encryption key
- `ADMIN_PASSWORD` - Admin panel password
- API keys for future services

**Save these values securely!** Use a password manager for the admin password.

## Step 3: Configure Each Section

### 🔐 Flask Configuration

```env
SECRET_KEY=<generated-secret-key>
FLASK_ENV=development  # Use 'production' for production
```

### 🗄️ Database Configuration

For local PostgreSQL:
```env
DATABASE_URL=postgresql://username:password@localhost/wedding_db
```

For Heroku (production):
```env
# Heroku provides this automatically as DATABASE_URL
```

### 👤 Admin Configuration

```env
ADMIN_PASSWORD=<strong-password>
ADMIN_EMAIL=your-email@domain.com
ADMIN_PHONE=+1-234-567-8900
```

### 📧 Email Configuration

#### Option 1: Gmail SMTP (Development/Small Scale)

1. Enable 2-factor authentication on your Google account
2. Generate an app-specific password:
   - Go to [Google Account Security](https://myaccount.google.com/security)
   - Select "2-Step Verification"
   - Select "App passwords"
   - Generate a password for "Mail"

```env
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-gmail@gmail.com
MAIL_PASSWORD=<app-specific-password>
```

#### Option 2: SendGrid (Production - Recommended)

1. Sign up for [SendGrid](https://sendgrid.com) (free tier available)
2. Create an API key
3. Configure:

```env
MAIL_SERVER=smtp.sendgrid.net
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=apikey
MAIL_PASSWORD=<your-sendgrid-api-key>
```

### 📅 Wedding Configuration

```env
WEDDING_DATE=2026-06-06        # Format: YYYY-MM-DD
RSVP_DEADLINE=2026-05-06       # One month before wedding
REMINDER_DAYS_BEFORE=30         # Send reminder 30 days before deadline
WARNING_CUTOFF_DAYS=7           # No edits 7 days before wedding
```

## Step 4: Production Deployment (Heroku)

### Set Environment Variables on Heroku:

```bash
# Set each variable
heroku config:set SECRET_KEY=<production-secret-key>
heroku config:set ADMIN_PASSWORD=<production-password>
heroku config:set ADMIN_EMAIL=admin@yourwedding.com
# ... etc

# Or set all at once from .env file (be careful!)
heroku config:set $(cat .env.production | grep -v '^#' | xargs)
```

### Verify Configuration:

```bash
heroku config
```

## Step 5: Test Your Configuration

Run this Python script to test your configuration:

```python
# test_config.py
from app import create_app
from app.config import Config

app = create_app()
with app.app_context():
    print("✅ Configuration loaded successfully!")
    print(f"Database URL: {app.config['SQLALCHEMY_DATABASE_URI'][:20]}...")
    print(f"Admin email: {app.config['ADMIN_EMAIL']}")
    print(f"Wedding date: {app.config['WEDDING_DATE']}")
    print(f"RSVP deadline: {app.config['RSVP_DEADLINE']}")
```

## 🚨 Security Checklist

- [ ] `.env` file is NOT in version control
- [ ] Generated new SECRET_KEY for production
- [ ] Admin password is strong and unique
- [ ] Database password is secure
- [ ] Email passwords use app-specific passwords
- [ ] Different credentials for development and production
- [ ] All sensitive defaults removed from `config.py`

## 📝 Environment Variables Reference

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `SECRET_KEY` | ✅ | Flask session key | 32+ character hex string |
| `DATABASE_URL` | ✅ | PostgreSQL connection | `postgresql://...` |
| `ADMIN_PASSWORD` | ✅ | Admin panel password | Strong password |
| `ADMIN_EMAIL` | ✅ | Admin contact email | `admin@domain.com` |
| `MAIL_SERVER` | ✅ | SMTP server | `smtp.gmail.com` |
| `MAIL_USERNAME` | ✅ | SMTP username | Email address |
| `MAIL_PASSWORD` | ✅ | SMTP password | App password |
| `WEDDING_DATE` | ✅ | Wedding date | `2026-06-06` |
| `RSVP_DEADLINE` | ✅ | RSVP cutoff | `2026-05-06` |
| `SENDGRID_API_KEY` | ❌ | SendGrid API | For production email |
| `SENTRY_DSN` | ❌ | Error tracking | For production monitoring |

## 🆘 Troubleshooting

### "Environment variable not found"
- Ensure `.env` file exists in project root
- Check variable names match exactly
- Restart Flask application after changes

### "Database connection failed"
- Verify PostgreSQL is running: `pg_ctl status`
- Check credentials in DATABASE_URL
- Test connection: `psql -U username -d wedding_db`

### "Email sending failed"
- For Gmail: Ensure app-specific password is used
- Check 2FA is enabled on Google account
- Verify SMTP settings match provider requirements

## Next Steps

After configuring your environment:

1. Test database connection: `python -c "from app import db; db.create_all()"`
2. Test email sending: `python test_email.py`
3. Run application: `python run.py`
4. Access admin panel: `http://localhost:5001/admin`