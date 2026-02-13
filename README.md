# YouTube Playlist Transcriber Pro

Uma ferramenta profissional para transcrição de playlists do YouTube utilizando IA (Whisper) e processamento paralelo para máxima performance.

## 🚀 Funcionalidades

- **Interface Gráfica Moderna**: Interface intuitiva construída com CustomTkinter.
- **Otimização de Performance**: Processamento paralelo para transcrever múltiplos vídeos simultaneamente.
- **Transcrição Híbrida**: Tenta capturar legendas oficiais/automáticas do YouTube e recorre ao Whisper (IA) apenas quando necessário.
- **Organização Automática**: Salva as transcrições em pastas organizadas pelo nome da playlist.

## 📂 Estrutura do Projeto

- `/src`: Código fonte da aplicação.
- `/assets`: Imagens, logos e banners.
- `Makefile`: Atalhos para instalação e execução.

## 🛠️ Instalação

1. Certifique-se de ter o **FFmpeg** instalado no seu sistema.
2. Instale as dependências:
   ```bash
   make install
   ```

## 💻 Como Usar

Para iniciar a aplicação com interface gráfica:
```bash
make run
```

## ⚙️ Requisitos

- Python 3.8+
- FFmpeg
- yt-dlp
- openai-whisper
- customtkinter
