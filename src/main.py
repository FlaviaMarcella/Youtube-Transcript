import os
import threading
import customtkinter as ctk
from tkinter import messagebox, filedialog
from PIL import Image, ImageDraw
from transcriber import TranscriberCore
from ffmpeg_manager import FFmpegManager

# Configurar tema de cores
bg_color = "#0F0F0F"
primary_color = "#FF0000"  # Vermelho (cor do YouTube)
secondary_color = "#282828"
text_color = "#FFFFFF"
accent_color = "#FF4444"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

class VideoSelectionWindow(ctk.CTkToplevel):
    """Janela para seleção de vídeos da playlist"""
    def __init__(self, parent, videos, playlist_title):
        super().__init__(parent)
        self.title(f"Selecionar Vídeos - {playlist_title}")
        self.geometry("700x600")
        self.resizable(True, True)
        
        self.videos = videos
        self.selected_indices = []
        self.checkboxes = []
        
        # Frame para título
        title_frame = ctk.CTkFrame(self, fg_color=secondary_color)
        title_frame.pack(fill="x", padx=0, pady=0)
        
        title_label = ctk.CTkLabel(
            title_frame, 
            text=f"🎬 {playlist_title}", 
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=primary_color
        )
        title_label.pack(side="left", padx=20, pady=15)
        
        info_label = ctk.CTkLabel(
            title_frame, 
            text=f"Total: {len(videos)} vídeos", 
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        info_label.pack(side="right", padx=20, pady=15)
        
        # Botões de seleção rápida
        button_frame = ctk.CTkFrame(self, fg_color=secondary_color)
        button_frame.pack(fill="x", padx=0, pady=0)
        
        select_all_btn = ctk.CTkButton(
            button_frame, 
            text="✓ Selecionar Todos", 
            command=self.select_all, 
            width=100,
            fg_color=primary_color,
            hover_color=accent_color
        )
        select_all_btn.pack(side="left", padx=10, pady=10)
        
        deselect_all_btn = ctk.CTkButton(
            button_frame, 
            text="✗ Desselecionar Todos", 
            command=self.deselect_all, 
            width=100,
            fg_color="gray30",
            hover_color="gray25"
        )
        deselect_all_btn.pack(side="left", padx=10, pady=10)
        
        # Frame scrollável para a lista de vídeos
        self.scrollable_frame = ctk.CTkScrollableFrame(self, fg_color=secondary_color)
        self.scrollable_frame.pack(fill="both", expand=True, padx=0, pady=10)
        
        # Adicionar checkboxes para cada vídeo
        for idx, video in enumerate(videos):
            title = video.get('title', 'Sem título')
            if title in ['[Deleted video]', '[Private video]']:
                continue
            
            checkbox_var = ctk.BooleanVar(value=True)  # Marcado por padrão
            checkbox = ctk.CTkCheckBox(
                self.scrollable_frame, 
                text=f"{idx+1}. {title[:65]}", 
                variable=checkbox_var,
                onvalue=True,
                offvalue=False,
                font=ctk.CTkFont(size=11),
                checkbox_width=20,
                checkbox_height=20
            )
            checkbox.pack(anchor="w", padx=20, pady=6)
            self.checkboxes.append((idx, checkbox_var))
        
        # Botões de ação
        action_frame = ctk.CTkFrame(self)
        action_frame.pack(fill="x", padx=20, pady=15)
        
        confirm_btn = ctk.CTkButton(
            action_frame, 
            text="▶ Confirmar Seleção", 
            command=self.confirm,
            font=ctk.CTkFont(size=12, weight="bold"),
            height=40,
            fg_color=primary_color,
            hover_color=accent_color
        )
        confirm_btn.pack(side="left", padx=5, fill="x", expand=True)
        
        cancel_btn = ctk.CTkButton(
            action_frame, 
            text="✕ Cancelar", 
            command=self.cancel,
            font=ctk.CTkFont(size=12, weight="bold"),
            height=40,
            fg_color="gray30",
            hover_color="gray25"
        )
        cancel_btn.pack(side="left", padx=5, fill="x", expand=True)
        
        self.result = None
    
    def select_all(self):
        for _, var in self.checkboxes:
            var.set(True)
    
    def deselect_all(self):
        for _, var in self.checkboxes:
            var.set(False)
    
    def confirm(self):
        self.selected_indices = [idx for idx, var in self.checkboxes if var.get()]
        if not self.selected_indices:
            messagebox.showwarning("Aviso", "Selecione pelo menos um vídeo!")
            return
        self.result = self.selected_indices
        self.destroy()
    
    def cancel(self):
        self.result = None
        self.destroy()

class TranscriberApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("YouTube Transcriber Pro")
        self.geometry("900x800")
        
        # Garantir que FFmpeg está disponível
        self.check_ffmpeg()
        
        # Configurar favicon
        self.setup_favicon()
        
        # Configuração de Grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(5, weight=1)
        
        # Carregar e exibir banner
        self.setup_banner()
        
        # URL Input
        self.url_entry = ctk.CTkEntry(
            self, 
            placeholder_text="Insira a URL da Playlist do YouTube...", 
            width=600,
            height=40,
            font=ctk.CTkFont(size=12)
        )
        self.url_entry.grid(row=2, column=0, padx=20, pady=15, sticky="ew")

        # Seletor de Pasta
        folder_frame = ctk.CTkFrame(self, fg_color=secondary_color)
        folder_frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        
        folder_label = ctk.CTkLabel(folder_frame, text="📁 Pasta de Saída:", font=ctk.CTkFont(size=12, weight="bold"))
        folder_label.pack(side="left", padx=15, pady=15)
        
        self.folder_var = ctk.StringVar(value=os.getcwd())
        folder_entry = ctk.CTkEntry(folder_frame, textvariable=self.folder_var, width=350, height=35)
        folder_entry.pack(side="left", padx=10, fill="x", expand=True, pady=15)
        
        browse_btn = ctk.CTkButton(
            folder_frame, 
            text="Procurar", 
            command=self.select_folder, 
            width=90,
            height=35,
            fg_color=primary_color,
            hover_color=accent_color
        )
        browse_btn.pack(side="left", padx=10, pady=15)

        # Configurações de Otimização
        self.settings_frame = ctk.CTkFrame(self, fg_color=secondary_color)
        self.settings_frame.grid(row=4, column=0, padx=20, pady=10, sticky="ew")
        
        self.label_workers = ctk.CTkLabel(
            self.settings_frame, 
            text="⚙️ Processos Simultâneos:",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.label_workers.pack(side="left", padx=15, pady=15)
        
        self.workers_slider = ctk.CTkSlider(
            self.settings_frame, 
            from_=1, 
            to=5, 
            number_of_steps=4,
            fg_color=primary_color
        )
        self.workers_slider.set(3)
        self.workers_slider.pack(side="left", padx=10, pady=15, fill="x", expand=True)
        
        self.label_worker_val = ctk.CTkLabel(
            self.settings_frame, 
            text="3",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=primary_color
        )
        self.label_worker_val.pack(side="left", padx=15, pady=15)
        self.workers_slider.configure(command=self.update_worker_label)

        # Botões de Ação
        buttons_frame = ctk.CTkFrame(self)
        buttons_frame.grid(row=5, column=0, padx=20, pady=15, sticky="ew")
        
        self.fetch_button = ctk.CTkButton(
            buttons_frame, 
            text="🎬 Buscar Vídeos da Playlist", 
            command=self.fetch_videos, 
            font=ctk.CTkFont(size=14, weight="bold"),
            height=45,
            fg_color=primary_color,
            hover_color=accent_color
        )
        self.fetch_button.pack(side="left", padx=10, fill="x", expand=True)

        self.cancel_op_button = ctk.CTkButton(
            buttons_frame, 
            text="🛑 Cancelar Operação", 
            command=self.cancel_operation, 
            font=ctk.CTkFont(size=14, weight="bold"),
            height=45,
            fg_color="gray30",
            hover_color="gray25",
            state="disabled"
        )
        self.cancel_op_button.pack(side="left", padx=10, fill="x", expand=True)

        # Barra de Progresso
        self.progress_bar = ctk.CTkProgressBar(self, fg_color=primary_color)
        self.progress_bar.grid(row=6, column=0, padx=20, pady=(0, 10), sticky="ew")
        self.progress_bar.set(0)

        # Console de Log
        console_label = ctk.CTkLabel(
            self, 
            text="📋 Log de Execução:",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=primary_color
        )
        console_label.grid(row=7, column=0, padx=20, pady=(10, 5), sticky="w")
        
        self.console = ctk.CTkTextbox(self, height=150, fg_color=secondary_color)
        self.console.grid(row=8, column=0, padx=20, pady=(0, 20), sticky="nsew")
        self.console.insert("0.0", "Aguardando URL...\n")
        self.console.configure(state="disabled")

        self.core = TranscriberCore(logger_callback=self.update_console)
        self.playlist_data = None

    def check_ffmpeg(self):
        """Verifica e baixa FFmpeg se necessário"""
        if not FFmpegManager.is_ffmpeg_available() and not FFmpegManager.is_local_ffmpeg_available():
            # Criar janela de progresso
            progress_window = ctk.CTkToplevel(self)
            progress_window.title("Configurando FFmpeg")
            progress_window.geometry("400x150")
            progress_window.resizable(False, False)
            
            label = ctk.CTkLabel(
                progress_window, 
                text="⬇️  Baixando FFmpeg (necessário para transcrição)...\nEsto pode levar alguns minutos.",
                font=ctk.CTkFont(size=12)
            )
            label.pack(padx=20, pady=20)
            
            progress_bar = ctk.CTkProgressBar(progress_window, fg_color=primary_color)
            progress_bar.pack(padx=20, pady=10, fill="x")
            progress_bar.set(0)
            
            status_label = ctk.CTkLabel(progress_window, text="0%", font=ctk.CTkFont(size=10))
            status_label.pack(pady=5)
            
            def download_with_progress():
                def callback(percent):
                    progress_bar.set(percent / 100)
                    status_label.configure(text=f"{percent}%")
                    progress_window.update()
                
                success = FFmpegManager.download_ffmpeg(progress_callback=callback)
                
                if success:
                    progress_window.destroy()
                else:
                    messagebox.showerror(
                        "Erro", 
                        "Não foi possível baixar FFmpeg automaticamente.\n"
                        "Por favor, instale o FFmpeg manualmente.\n"
                        "Site: https://ffmpeg.org/"
                    )
                    progress_window.destroy()
            
            thread = threading.Thread(target=download_with_progress, daemon=True)
            thread.start()
        else:
            FFmpegManager.add_ffmpeg_to_path()
    
    def setup_favicon(self):
        """Cria e define o favicon baseado no logo"""
        try:
            logo_path = os.path.join(os.path.dirname(__file__), "..", "assets", "logo.png")
            if os.path.exists(logo_path):
                # Carregar a imagem do logo
                logo_pil = Image.open(logo_path)
                
                # Redimensionar para tamanho do favicon (256x256 é mantido, Windows vai reduzir)
                favicon_pil = logo_pil.resize((256, 256), Image.Resampling.LANCZOS)
                
                # Salvar como ICO na pasta src
                ico_path = os.path.join(os.path.dirname(__file__), "favicon.ico")
                favicon_pil.save(ico_path)
                
                # Definir como ícone da janela
                self.iconbitmap(ico_path)
        except Exception as e:
            pass  # Silenciosamente ignorar erros de ícone

    def setup_banner(self):
        """Carrega e exibe o banner como imagem principal"""
        try:
            banner_path = os.path.join(os.path.dirname(__file__), "..", "assets", "banner.png")
            if os.path.exists(banner_path):
                banner_pil = Image.open(banner_path)
                # Manter aspect ratio - calcular altura proporcional
                width = 850
                aspect_ratio = banner_pil.height / banner_pil.width
                height = int(width * aspect_ratio)
                # Garantir altura máxima razoável
                if height > 150:
                    height = 150
                    width = int(height / aspect_ratio)
                
                banner_pil = banner_pil.resize((width, height), Image.Resampling.LANCZOS)
                banner_image = ctk.CTkImage(light_image=banner_pil, dark_image=banner_pil, size=(width, height))
                
                banner_label = ctk.CTkLabel(self, image=banner_image, text="")
                banner_label.image = banner_image  # Manter referência
                banner_label.grid(row=0, column=0, padx=20, pady=(15, 5), sticky="ew")
            else:
                # Fallback com estilo
                title_label = ctk.CTkLabel(
                    self, 
                    text="▶ YouTube Transcriber Pro", 
                    font=ctk.CTkFont(size=28, weight="bold"),
                    text_color=primary_color
                )
                title_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        except Exception as e:
            pass

    def select_folder(self):
        """Abre diálogo para selecionar pasta"""
        folder = filedialog.askdirectory(title="Selecionar pasta de saída")
        if folder:
            self.folder_var.set(folder)

    def update_worker_label(self, value):
        self.label_worker_val.configure(text=str(int(value)))

    def update_console(self, message):
        self.after(0, self._safe_update_console, message)

    def _safe_update_console(self, message):
        self.console.configure(state="normal")
        self.console.insert("end", f"> {message}\n")
        self.console.see("end")
        self.console.configure(state="disabled")

    def fetch_videos(self):
        """Busca os vídeos da playlist e abre janela de seleção"""
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Aviso", "Por favor, insira uma URL.")
            return

        self.fetch_button.configure(state="disabled")
        self.progress_bar.configure(mode="indeterminate")
        self.progress_bar.start()
        
        thread = threading.Thread(target=self.run_fetch)
        thread.daemon = True
        thread.start()

    def run_fetch(self):
        """Executa a busca em thread separada"""
        try:
            url = self.url_entry.get().strip()
            playlist_title, videos = self.core.fetch_playlist_videos(url)
            self.playlist_data = (playlist_title, videos, url)
            
            self.after(0, self.show_video_selection, playlist_title, videos)
        except Exception as e:
            self.update_console(f"ERRO: {e}")
            self.after(0, lambda: messagebox.showerror("Erro", str(e)))
        finally:
            self.after(0, self.reset_fetch_ui)

    def show_video_selection(self, playlist_title, videos):
        """Mostra janela de seleção de vídeos"""
        selection_window = VideoSelectionWindow(self, videos, playlist_title)
        self.wait_window(selection_window)
        
        if selection_window.result is not None:
            self.start_transcription(selection_window.result)

    def start_transcription(self, selected_indices):
        """Inicia a transcrição dos vídeos selecionados"""
        if not self.playlist_data:
            messagebox.showerror("Erro", "Dados da playlist não disponíveis.")
            return
        
        playlist_title, videos, url = self.playlist_data
        
        output_folder = self.folder_var.get()
        if not output_folder:
            messagebox.showwarning("Aviso", "Selecione uma pasta de saída.")
            return
        
        self.core.reset_cancel()
        self.fetch_button.configure(state="disabled")
        self.cancel_op_button.configure(state="normal", fg_color="#CC0000")
        self.progress_bar.configure(mode="indeterminate")
        self.progress_bar.start()
        
        workers = int(self.workers_slider.get())
        
        thread = threading.Thread(target=self.run_core, args=(url, output_folder, selected_indices, workers))
        thread.daemon = True
        thread.start()

    def cancel_operation(self):
        """Cancela a operação em curso"""
        if messagebox.askyesno("Confirmar", "Deseja realmente cancelar a operação?"):
            self.core.cancel()
            self.cancel_op_button.configure(state="disabled", fg_color="gray30")

    def run_core(self, url, output_folder, selected_indices, workers):
        try:
            self.core.run_playlist(url, output_folder, selected_video_indices=selected_indices, max_workers=workers)
            self.after(0, lambda: messagebox.showinfo("Sucesso", "Transcrição concluída!"))
        except Exception as e:
            self.update_console(f"ERRO: {e}")
            self.after(0, lambda: messagebox.showerror("Erro", str(e)))
        finally:
            self.after(0, self.reset_ui)

    def reset_fetch_ui(self):
        self.fetch_button.configure(state="normal")
        self.progress_bar.stop()
        self.progress_bar.set(0)

    def reset_ui(self):
        self.fetch_button.configure(state="normal")
        self.cancel_op_button.configure(state="disabled", fg_color="gray30")
        self.progress_bar.stop()
        self.progress_bar.set(0)

if __name__ == "__main__":
    app = TranscriberApp()
    app.mainloop()
