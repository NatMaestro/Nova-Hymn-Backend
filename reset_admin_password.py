#!/usr/bin/env python
"""
Script to reset Django admin password
Run with: python reset_admin_password.py
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# List all superusers
superusers = User.objects.filter(is_superuser=True)
print("\n" + "="*60)
print("Existing Superusers:")
print("="*60)
if not superusers.exists():
    print("No superusers found!")
    print("\nWould you like to create a new superuser?")
    print("Run: python manage.py createsuperuser")
    sys.exit(0)

for idx, user in enumerate(superusers, 1):
    print(f"{idx}. Username: {user.username}")
    print(f"   Email: {user.email or '(no email)'}")
    print(f"   Active: {user.is_active}")
    print()

# Get user selection
try:
    choice = input("Enter the number of the user to reset password (or 'q' to quit): ").strip()
    if choice.lower() == 'q':
        print("Cancelled.")
        sys.exit(0)
    
    choice_idx = int(choice) - 1
    if choice_idx < 0 or choice_idx >= len(superusers):
        print("Invalid selection!")
        sys.exit(1)
    
    selected_user = superusers[choice_idx]
    print(f"\nSelected user: {selected_user.username}")
    
    # Get new password
    new_password = input("Enter new password: ").strip()
    if not new_password:
        print("Password cannot be empty!")
        sys.exit(1)
    
    confirm_password = input("Confirm new password: ").strip()
    if new_password != confirm_password:
        print("Passwords do not match!")
        sys.exit(1)
    
    # Set password
    selected_user.set_password(new_password)
    selected_user.save()
    
    print(f"\n✅ Password successfully reset for user: {selected_user.username}")
    print("You can now login to the admin panel with this password.")
    
except ValueError:
    print("Invalid input! Please enter a number.")
    sys.exit(1)
except KeyboardInterrupt:
    print("\n\nCancelled.")
    sys.exit(0)
except Exception as e:
    print(f"\n❌ Error: {str(e)}")
    sys.exit(1)
