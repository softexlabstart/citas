#!/usr/bin/env python3
"""Script para reemplazar .objects.db_manager('default') con ._base_manager"""

import re

file_path = 'citas/services.py'

with open(file_path, 'r') as f:
    content = f.read()

# Reemplazos específicos
replacements = [
    (r"Sede\.objects\.db_manager\('default'\)", "Sede._base_manager"),
    (r"Servicio\.objects\.db_manager\('default'\)", "Servicio._base_manager"),
    (r"Colaborador\.objects\.db_manager\('default'\)", "Colaborador._base_manager"),
    (r"Horario\.objects\.db_manager\('default'\)", "Horario._base_manager"),
    (r"Cita\.objects\.db_manager\('default'\)", "Cita._base_manager"),
    (r"Bloqueo\.objects\.db_manager\('default'\)", "Bloqueo._base_manager"),
]

for pattern, replacement in replacements:
    content = re.sub(pattern, replacement, content)

with open(file_path, 'w') as f:
    f.write(content)

print("✓ Reemplazos completados")
print(f"✓ Archivo actualizado: {file_path}")
