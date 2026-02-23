import os
import re
import glob
import shutil
import warnings
from concurrent.futures import ThreadPoolExecutor
from yt_dlp import YoutubeDL

warnings.filterwarnings("ignore")

class TranscriberCore:
    def __init__(self, logger_callback=None):
        self.logger = logger_callback
        self.has_ffmpeg = shutil.which("ffmpeg") is not None
        self.has_whisper = False
        self._is_cancelled = False
        try:
            import whisper
            self.has_whisper = True
        except ImportError:
            pass

    def cancel(self):
        self._is_cancelled = True
        self.log("⚠️ Operação cancelada pelo usuário.")

    def reset_cancel(self):
        self._is_cancelled = False

    def log(self, message):
        if self.logger:
            self.logger(message)
        else:
            print(message)

    def sanitize_filename(self, name):
        return re.sub(r'[\\/*?:"<>|]', "", name)

    def vtt_to_text(self, vtt_path):
        text_lines = []
        seen_lines = set()
        try:
            with open(vtt_path, 'r', encoding='utf-8') as f:
                content = f.read()
            for line in content.splitlines():
                if 'WEBVTT' in line or '-->' in line or not line.strip(): continue
                clean = re.sub(r'<[^>]+>', '', line).strip()
                clean = re.sub(r'\d{2}:\d{2}:\d{2}\.\d{3}', '', clean).strip()
                if clean and clean not in seen_lines:
                    text_lines.append(clean)
                    seen_lines.add(clean)
                    if len(seen_lines) > 10: seen_lines.remove(next(iter(seen_lines)))
            return " ".join(text_lines)
        except:
            return ""

    def transcribe_with_ai(self, video_url, output_base):
        if not self.has_ffmpeg or not self.has_whisper:
            return "[Erro: Falta FFmpeg ou Whisper]"

        import whisper
        audio_file = f"{output_base}.mp3"
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_base,
            'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3'}],
            'quiet': True, 'no_warnings': True, 'nocheckcertificate': True
        }
        
        try:
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
            
            if not os.path.exists(audio_file):
                return "[Erro: Download falhou]"

            model = whisper.load_model("base")
            result = model.transcribe(audio_file)
            
            try: os.remove(audio_file)
            except: pass
                
            return result["text"].strip()
        except Exception as e:
            return f"[Erro IA: {str(e)}]"

    def process_single_video(self, video_data, folder, index, total):
        if self._is_cancelled:
            return False
        title = video_data.get('title', 'SemTitulo')
        vid_id = video_data.get('id')
        video_url = f"https://www.youtube.com/watch?v={vid_id}"
        
        if title in ['[Deleted video]', '[Private video]']:
            return False

        safe_title = self.sanitize_filename(title)
        filepath = os.path.join(folder, f"{index+1:02d} - {safe_title}.txt")
        temp_base = os.path.join(folder, f"temp_{vid_id}")
        
        self.log(f"[{index+1}/{total}] Processando: {title[:40]}...")
        
        full_text = None
        source = "Nenhum"

        # 1. Tenta Legenda
        ydl_opts_subs = {
            'skip_download': True, 'write_sub': True, 'write_auto_sub': True,
            'sub_langs': ['pt.*', 'en.*'], 'quiet': True, 'outtmpl': temp_base,
            'nocheckcertificate': True
        }
        
        try:
            with YoutubeDL(ydl_opts_subs) as ydl:
                ydl.download([video_url])
            vtt_files = glob.glob(f"{temp_base}*.vtt")
            if vtt_files:
                pt_subs = [f for f in vtt_files if '.pt' in f]
                target_vtt = pt_subs[0] if pt_subs else vtt_files[0]
                full_text = self.vtt_to_text(target_vtt)
                source = "Legenda YouTube"
                for f in vtt_files: os.remove(f)
        except: pass

        # 2. Tenta IA
        if (not full_text or len(full_text) < 50) and self.has_ffmpeg and self.has_whisper:
            self.log(f"   -> Usando IA para: {title[:20]}...")
            full_text = self.transcribe_with_ai(video_url, temp_base)
            if full_text and not full_text.startswith("[Erro"):
                source = "IA Whisper"

        if full_text and not full_text.startswith("[Erro"):
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"Título: {title}\nLink: {video_url}\nFonte: {source}\n\n{full_text}")
            return True
        return False

    def fetch_playlist_videos(self, playlist_url):
        """Busca os vídeos da playlist sem processar. Retorna (playlist_title, videos)"""
        self.log(f"🔍 Analisando playlist...")
        ydl_opts = {'extract_flat': True, 'quiet': True, 'nocheckcertificate': True}
        
        with YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(playlist_url, download=False)
                playlist_title = info.get('title', 'Playlist_Youtube')
                videos = info.get('entries', [])
            except Exception as e:
                self.log(f"❌ Erro: {e}")
                raise Exception(f"Erro ao buscar playlist: {e}")

        if not videos:
            raise Exception("Nenhum vídeo encontrado na playlist.")
            
        return playlist_title, videos

    def run_playlist(self, playlist_url, output_folder, selected_video_indices=None, max_workers=3):
        """Processa vídeos da playlist. Se selected_video_indices for None, processa todos."""
        try:
            playlist_title, videos = self.fetch_playlist_videos(playlist_url)
        except Exception as e:
            self.log(str(e))
            return

        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
        
        # Se nenhum índice foi selecionado, processa todos
        if selected_video_indices is None:
            selected_video_indices = list(range(len(videos)))
        
        # Filtra apenas os vídeos selecionados
        selected_videos = [videos[i] for i in selected_video_indices if i < len(videos)]
        
        self.log(f"📂 Pasta: {output_folder} | Processando {len(selected_videos)} vídeos com {max_workers} workers...")
        
        total = len(selected_videos)
        success_count = 0
        
        # Otimização: Processamento Paralelo
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(self.process_single_video, vid, output_folder, i, total) for i, vid in enumerate(selected_videos)]
            for future in futures:
                if self._is_cancelled:
                    executor.shutdown(wait=False, cancel_futures=True)
                    break
                if future.result():
                    success_count += 1

        self.log(f"\n✅ Concluído! {success_count}/{total} transcritos.")
