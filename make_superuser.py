#!/usr/bin/env python
"""
Script to make a user a superuser and reset password
Usage: python make_superuser.py <username> <new_password>
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

if len(sys.argv) < 3:
    print("Usage: python make_superuser.py <username> <new_password>")
    print("\nExisting users:")
    for user in User.objects.all():
        superuser_marker = " [SUPERUSER]" if user.is_superuser else ""
        print(f"  - {user.username} ({user.email or 'no email'}){superuser_marker}")
    sys.exit(1)

username = sys.argv[1]
new_password = sys.argv[2]

try:
    user = User.objects.get(username=username)
    user.set_password(new_password)
    user.is_superuser = True
    user.is_staff = True
    user.is_active = True
    user.save()
    
    print(f"SUCCESS: User '{username}' is now a superuser with the new password.")
    print(f"You can login to admin with:")
    print(f"  Username: {username}")
    print(f"  Password: {new_password}")
    
except User.DoesNotExist:
    print(f"ERROR: User '{username}' not found!")
    print("\nAvailable users:")
    for user in User.objects.all():
        print(f"  - {user.username}")
    sys.exit(1)
except Exception as e:
    print(f"ERROR: {str(e)}")
    sys.exit(1)

