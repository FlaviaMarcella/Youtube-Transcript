.PHONY: install run clean help

help:
	@echo "Comandos disponíveis:"
	@echo "  make install  - Instala as dependências necessárias"
	@echo "  make run      - Executa a aplicação com interface gráfica"
	@echo "  make clean    - Remove arquivos temporários e cache"

install:
	pip install yt-dlp openai-whisper customtkinter

run:
	python3 src/main.py

clean:
	rm -rf src/__pycache__
	rm -rf __pycache__
	rm -f temp_*
	rm -f *.mp3
	rm -f *.vtt
