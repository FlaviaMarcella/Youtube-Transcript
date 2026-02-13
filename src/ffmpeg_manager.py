import os
import shutil
import subprocess
import zipfile
from pathlib import Path
import urllib.request
import sys

class FFmpegManager:
    """Gerencia download e configuração automática do FFmpeg"""
    
    FFMPEG_DIR = os.path.join(os.path.expanduser("~"), ".youtube_transcriber", "ffmpeg")
    FFMPEG_BIN = os.path.join(FFMPEG_DIR, "bin", "ffmpeg.exe")
    FFMPEG_VERSION = "6.1"
    
    @staticmethod
    def get_ffmpeg_url():
        """Retorna a URL de download do FFmpeg para Windows"""
        # Usando ffmpeg-static no GitHub - versão pré-compilada
        return f"https://github.com/BtbN/FFmpeg-Builds/releases/download/autobuild-2024-12-14/ffmpeg-N-118938-g1f8d06e27a-win64-gpl.zip"
    
    @staticmethod
    def is_ffmpeg_available():
        """Verifica se FFmpeg está disponível no PATH"""
        return shutil.which("ffmpeg") is not None
    
    @staticmethod
    def is_local_ffmpeg_available():
        """Verifica se FFmpeg está instalado localmente"""
        return os.path.exists(FFmpegManager.FFMPEG_BIN)
    
    @staticmethod
    def add_ffmpeg_to_path():
        """Adiciona FFmpeg local ao PATH"""
        ffmpeg_bin_dir = os.path.dirname(FFmpegManager.FFMPEG_BIN)
        if ffmpeg_bin_dir not in os.environ.get("PATH", ""):
            os.environ["PATH"] = ffmpeg_bin_dir + os.pathsep + os.environ.get("PATH", "")
    
    @staticmethod
    def download_ffmpeg(progress_callback=None):
        """Faz download e instala FFmpeg automaticamente"""
        try:
            print("🔍 Verificando FFmpeg...")
            
            # Se já existe no PATH, usar esse
            if FFmpegManager.is_ffmpeg_available():
                print("✅ FFmpeg já está instalado no PATH")
                return True
            
            # Se já está instalado localmente, adicionar ao PATH
            if FFmpegManager.is_local_ffmpeg_available():
                print("✅ FFmpeg já está instalado localmente")
                FFmpegManager.add_ffmpeg_to_path()
                return True
            
            # Fazer download
            print("⬇️  Baixando FFmpeg (isso pode levar alguns minutos)...")
            
            os.makedirs(FFmpegManager.FFMPEG_DIR, exist_ok=True)
            
            url = FFmpegManager.get_ffmpeg_url()
            zip_path = os.path.join(FFmpegManager.FFMPEG_DIR, "ffmpeg.zip")
            
            # Download com barra de progresso
            def download_with_progress(url, filepath):
                def reporthook(blocknum, blocksize, totalsize):
                    downloaded = blocknum * blocksize
                    if totalsize > 0:
                        percent = min(downloaded * 100 // totalsize, 100)
                        if progress_callback:
                            progress_callback(percent)
                        else:
                            print(f"  Progresso: {percent}%", end="\r")
                
                urllib.request.urlretrieve(url, filepath, reporthook)
            
            download_with_progress(url, zip_path)
            print("\n✅ Download concluído!")
            
            # Extrair
            print("📦 Extraindo FFmpeg...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(FFmpegManager.FFMPEG_DIR)
            
            # Mover arquivos para a estrutura esperada
            extracted = os.path.join(FFmpegManager.FFMPEG_DIR, "ffmpeg-N-118938-g1f8d06e27a-win64-gpl", "bin")
            if os.path.exists(extracted):
                os.makedirs(os.path.dirname(FFmpegManager.FFMPEG_BIN), exist_ok=True)
                for file in os.listdir(extracted):
                    shutil.copy2(os.path.join(extracted, file), os.path.dirname(FFmpegManager.FFMPEG_BIN))
            
            # Limpar ZIP
            os.remove(zip_path)
            print("✅ FFmpeg instalado com sucesso!")
            
            # Adicionar ao PATH
            FFmpegManager.add_ffmpeg_to_path()
            
            # Verificar
            if shutil.which("ffmpeg"):
                print("✅ FFmpeg verificado e pronto para usar!")
                return True
            else:
                print("⚠️  FFmpeg baixado, mas não foi encontrado no PATH")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao baixar FFmpeg: {e}")
            return False
    
    @staticmethod
    def ensure_ffmpeg_installed(progress_callback=None):
        """Garante que FFmpeg está disponível, faz download se necessário"""
        if FFmpegManager.is_ffmpeg_available() or FFmpegManager.is_local_ffmpeg_available():
            FFmpegManager.add_ffmpeg_to_path()
            return True
        else:
            return FFmpegManager.download_ffmpeg(progress_callback)


if __name__ == "__main__":
    # Teste
    FFmpegManager.ensure_ffmpeg_installed()
