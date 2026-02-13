.PHONY: install run clean help build

help:
	@echo "Comandos disponíveis:"
	@echo "  make install  - Instala as dependências necessárias"
	@echo "  make run      - Executa a aplicação com interface gráfica"
	@echo "  make build    - Gera executável standalone (requer PyInstaller)"
	@echo "  make clean    - Remove arquivos temporários e cache"

install:
	pip install -r requirements.txt

run:
	python src/main.py

build:
	pip install --upgrade pyinstaller
	pyinstaller YouTubeTranscriberPro.spec
	@echo "Build concluído! Executável em: dist/YouTubeTranscriberPro/"

clean:
	powershell -Command "Remove-Item -Path 'src/__pycache__' -Recurse -Force -ErrorAction SilentlyContinue"
	powershell -Command "Remove-Item -Path '__pycache__' -Recurse -Force -ErrorAction SilentlyContinue"
	powershell -Command "Remove-Item -Path 'build' -Recurse -Force -ErrorAction SilentlyContinue"
	powershell -Command "Remove-Item -Path 'dist' -Recurse -Force -ErrorAction SilentlyContinue"
	powershell -Command "Remove-Item -Path 'YouTubeTranscriberPro' -Recurse -Force -ErrorAction SilentlyContinue"
	powershell -Command "Remove-Item -Path 'temp_*' -Force -ErrorAction SilentlyContinue"
	powershell -Command "Remove-Item -Path '*.mp3' -Force -ErrorAction SilentlyContinue"
	powershell -Command "Remove-Item -Path '*.vtt' -Force -ErrorAction SilentlyContinue"
