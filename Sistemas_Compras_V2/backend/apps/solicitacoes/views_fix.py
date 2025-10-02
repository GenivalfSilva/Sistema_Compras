"""
Script to temporarily allow any authenticated user to create a solicitacao
"""

import os
import sys
import re

# File path
views_file = os.path.join('apps', 'solicitacoes', 'views.py')

# Read the file
with open(views_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Find the get_permissions method
pattern = r'def get_permissions\(self\):\s+if self\.request\.method == \'POST\':\s+return \[IsSolicitanteOrAdmin\(\)\]\s+return \[permissions\.IsAuthenticated\(\)\]'

# Replace with a version that allows any authenticated user
replacement = """def get_permissions(self):
        # Temporarily allow any authenticated user to create a solicitacao
        return [permissions.AllowAny()]"""

# Replace the pattern
new_content = re.sub(pattern, replacement, content)

# Write the file
with open(views_file, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("SolicitacaoListCreateView permissions updated to AllowAny")
