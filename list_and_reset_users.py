#!/usr/bin/env python
"""
Script to list all users and reset password for existing user
Run with: python list_and_reset_users.py
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# List all users
all_users = User.objects.all().order_by('username')
superusers = User.objects.filter(is_superuser=True)

print("\n" + "="*70)
print("ALL USERS IN DATABASE:")
print("="*70)
if not all_users.exists():
    print("No users found!")
    sys.exit(0)

for idx, user in enumerate(all_users, 1):
    superuser_marker = " [SUPERUSER]" if user.is_superuser else ""
    active_marker = "" if user.is_active else " [INACTIVE]"
    print(f"{idx}. Username: {user.username}")
    print(f"   Email: {user.email or '(no email)'}")
    print(f"   Active: {user.is_active}{superuser_marker}{active_marker}")
    print()

print("\n" + "="*70)
print("SUPERUSERS:")
print("="*70)
if not superusers.exists():
    print("No superusers found!")
else:
    for idx, user in enumerate(superusers, 1):
        print(f"{idx}. {user.username} ({user.email or 'no email'})")

# Check if email exists
email_to_check = "nathanielguggisberg@gmail.com"
user_with_email = User.objects.filter(email=email_to_check).first()

if user_with_email:
    print(f"\n" + "="*70)
    print(f"Found user with email '{email_to_check}':")
    print("="*70)
    print(f"Username: {user_with_email.username}")
    print(f"Is Superuser: {user_with_email.is_superuser}")
    print(f"Is Active: {user_with_email.is_active}")
    print()
    
    # Ask if they want to reset password
    try:
        choice = input(f"Do you want to reset password for '{user_with_email.username}'? (y/n): ").strip().lower()
        if choice == 'y':
            new_password = input("Enter new password: ").strip()
            if not new_password:
                print("Password cannot be empty!")
                sys.exit(1)
            
            confirm_password = input("Confirm new password: ").strip()
            if new_password != confirm_password:
                print("Passwords do not match!")
                sys.exit(1)
            
            # Set password
            user_with_email.set_password(new_password)
            user_with_email.is_superuser = True  # Make sure they're a superuser
            user_with_email.is_active = True  # Make sure they're active
            user_with_email.save()
            
            print(f"\n✅ Password successfully reset for user: {user_with_email.username}")
            print("✅ User is now a superuser and active.")
            print("You can now login to the admin panel with:")
            print(f"   Username: {user_with_email.username}")
            print(f"   Password: (the password you just set)")
        else:
            print("Cancelled.")
    except KeyboardInterrupt:
        print("\n\nCancelled.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        sys.exit(1)
else:
    print(f"\nNo user found with email '{email_to_check}'")
    print("You can create a new superuser with a different email/username.")

