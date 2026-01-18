#!/usr/bin/env python
"""
Simple script to reset Django admin password
Usage: python reset_password_simple.py <username> <new_password>
Or run without args for interactive mode
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Check if username and password provided as arguments
if len(sys.argv) >= 3:
    username = sys.argv[1]
    new_password = sys.argv[2]
    
    try:
        user = User.objects.get(username=username, is_superuser=True)
        user.set_password(new_password)
        user.save()
        print(f"✅ Password successfully reset for user: {username}")
        sys.exit(0)
    except User.DoesNotExist:
        print(f"❌ Superuser with username '{username}' not found!")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)
else:
    # Interactive mode
    print("\nUsage: python reset_password_simple.py <username> <new_password>")
    print("\nOr run the interactive script: python reset_admin_password.py")
    print("\nFound superusers:")
    superusers = User.objects.filter(is_superuser=True)
    for user in superusers:
        print(f"  - {user.username} ({user.email or 'no email'})")
    sys.exit(0)

