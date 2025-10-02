#!/usr/bin/env python
"""
Script to fix middleware permissions for solicitante role
"""

import os
import sys
import re

# Add the project directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'compras_project.settings')

# File path
middleware_file = os.path.join('apps', 'usuarios', 'middleware.py')

# Read the file
with open(middleware_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Update the can_create_solicitation method to directly check the V1 user's perfil
can_create_solicitation_pattern = r"def can_create_solicitation\(\):[^}]*?\)"
can_create_solicitation_replacement = """def can_create_solicitation():
            if not user or isinstance(user, AnonymousUser):
                return False
            # Direct check of V1 user's perfil
            v1 = _get_v1_usuario(getattr(user, "username", ""))
            if v1 and v1.perfil in ["Solicitante", "Admin"]:
                print(f"User {getattr(user, 'username', '')} has Solicitante permissions")
                return True
            return False"""

# Update the is_admin method to directly check the V1 user's perfil
is_admin_pattern = r"def is_admin\(\):[^}]*?\)"
is_admin_replacement = """def is_admin():
            if not user or isinstance(user, AnonymousUser):
                return False
            # Direct check of V1 user's perfil
            v1 = _get_v1_usuario(getattr(user, "username", ""))
            if v1 and v1.perfil == "Admin":
                print(f"User {getattr(user, 'username', '')} has Admin permissions")
                return True
            return False"""

# Replace the patterns
new_content = re.sub(can_create_solicitation_pattern, can_create_solicitation_replacement, content)
new_content = re.sub(is_admin_pattern, is_admin_replacement, new_content)

# Write the file
with open(middleware_file, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Middleware permissions updated successfully!")
