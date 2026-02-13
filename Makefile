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
	python src/main.py &
	sleep 3 || true
	pyinstaller YouTubeTranscriberPro.spec
	@echo "Build concluído! Executável em: dist/YouTubeTranscriberPro/"

clean:
	rm -rf src/__pycache__
	rm -rf __pycache__
	rm -rf build
	rm -rf dist
	rm -rf YouTubeTranscriberPro
	rm -f temp_*
	rm -f *.mp3
	rm -f *.vtt
