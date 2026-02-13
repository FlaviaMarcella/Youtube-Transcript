#!/usr/bin/env python
"""Script para compilar a aplicação em executável"""
import subprocess
import sys
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

print("🔨 Compilando YouTubeTranscriberPro...")
result = subprocess.run(
    [sys.executable, "-m", "PyInstaller", "YouTubeTranscriberPro.spec"],
    capture_output=False
)

if result.returncode == 0:
    print("\n✅ Build concluído com sucesso!")
    print("📦 Executável disponível em: dist/YouTubeTranscriberPro/")
else:
    print("\n❌ Erro ao compilar!")
    sys.exit(1)
