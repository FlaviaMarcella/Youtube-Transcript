import os
import threading
import customtkinter as ctk
from tkinter import messagebox, filedialog
from PIL import Image
from transcriber import TranscriberCore

class VideoSelectionWindow(ctk.CTkToplevel):
    """Janela para seleção de vídeos da playlist"""
    def __init__(self, parent, videos, playlist_title):
        super().__init__(parent)
        self.title(f"Selecionar Vídeos - {playlist_title}")
        self.geometry("600x500")
        self.resizable(True, True)
        
        self.videos = videos
        self.selected_indices = []
        self.checkboxes = []
        
        # Frame para título
        title_frame = ctk.CTkFrame(self)
        title_frame.pack(fill="x", padx=10, pady=10)
        
        title_label = ctk.CTkLabel(title_frame, text=f"Playlist: {playlist_title}", font=ctk.CTkFont(size=14, weight="bold"))
        title_label.pack(side="left")
        
        info_label = ctk.CTkLabel(title_frame, text=f"Total: {len(videos)} vídeos", font=ctk.CTkFont(size=12))
        info_label.pack(side="right")
        
        # Botões de seleção rápida
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(fill="x", padx=10, pady=5)
        
        select_all_btn = ctk.CTkButton(button_frame, text="Selecionar Todos", command=self.select_all, width=100)
        select_all_btn.pack(side="left", padx=5)
        
        deselect_all_btn = ctk.CTkButton(button_frame, text="Desselecionar Todos", command=self.deselect_all, width=100)
        deselect_all_btn.pack(side="left", padx=5)
        
        # Frame scrollável para a lista de vídeos
        self.scrollable_frame = ctk.CTkScrollableFrame(self)
        self.scrollable_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Adicionar checkboxes para cada vídeo
        for idx, video in enumerate(videos):
            title = video.get('title', 'Sem título')
            if title in ['[Deleted video]', '[Private video]']:
                continue
            
            checkbox_var = ctk.BooleanVar(value=True)  # Marcado por padrão
            checkbox = ctk.CTkCheckBox(
                self.scrollable_frame, 
                text=f"{idx+1}. {title[:70]}", 
                variable=checkbox_var,
                onvalue=True,
                offvalue=False
            )
            checkbox.pack(anchor="w", padx=10, pady=5)
            self.checkboxes.append((idx, checkbox_var))
        
        # Botões de ação
        action_frame = ctk.CTkFrame(self)
        action_frame.pack(fill="x", padx=10, pady=10)
        
        confirm_btn = ctk.CTkButton(action_frame, text="Confirmar Seleção", command=self.confirm)
        confirm_btn.pack(side="left", padx=5)
        
        cancel_btn = ctk.CTkButton(action_frame, text="Cancelar", command=self.cancel)
        cancel_btn.pack(side="left", padx=5)
        
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
        self.geometry("800x700")
        
        # Configuração de Grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(6, weight=1)
        
        # Carregar imagens
        self.setup_images()
        
        # Logo (pequeno, no topo)
        if self.logo_image:
            logo_label = ctk.CTkLabel(self, image=self.logo_image, text="")
            logo_label.grid(row=0, column=0, padx=20, pady=(10, 5))
        
        # Banner
        if self.banner_image:
            banner_label = ctk.CTkLabel(self, image=self.banner_image, text="")
            banner_label.grid(row=1, column=0, padx=20, pady=(0, 10))
        else:
            # Fallback se a imagem não carregar
            title_label = ctk.CTkLabel(self, text="YouTube Transcriber Pro", font=ctk.CTkFont(size=24, weight="bold"))
            title_label.grid(row=1, column=0, padx=20, pady=(10, 10))

        # URL Input
        self.url_entry = ctk.CTkEntry(self, placeholder_text="Insira a URL da Playlist do YouTube...", width=600)
        self.url_entry.grid(row=2, column=0, padx=20, pady=10)

        # Seletor de Pasta
        folder_frame = ctk.CTkFrame(self)
        folder_frame.grid(row=3, column=0, padx=20, pady=10, sticky="ew")
        
        folder_label = ctk.CTkLabel(folder_frame, text="Pasta de Saída:")
        folder_label.pack(side="left", padx=10)
        
        self.folder_var = ctk.StringVar(value=os.getcwd())
        folder_entry = ctk.CTkEntry(folder_frame, textvariable=self.folder_var, width=400)
        folder_entry.pack(side="left", padx=10, fill="x", expand=True)
        
        browse_btn = ctk.CTkButton(folder_frame, text="Procurar...", command=self.select_folder, width=80)
        browse_btn.pack(side="left", padx=10)

        # Configurações de Otimização
        self.settings_frame = ctk.CTkFrame(self)
        self.settings_frame.grid(row=4, column=0, padx=20, pady=10, sticky="ew")
        
        self.label_workers = ctk.CTkLabel(self.settings_frame, text="Processos Simultâneos:")
        self.label_workers.pack(side="left", padx=10, pady=10)
        
        self.workers_slider = ctk.CTkSlider(self.settings_frame, from_=1, to=5, number_of_steps=4)
        self.workers_slider.set(3)
        self.workers_slider.pack(side="left", padx=10, pady=10, fill="x", expand=True)
        
        self.label_worker_val = ctk.CTkLabel(self.settings_frame, text="3")
        self.label_worker_val.pack(side="left", padx=10, pady=10)
        self.workers_slider.configure(command=self.update_worker_label)

        # Botão Buscar Vídeos
        self.fetch_button = ctk.CTkButton(self, text="Buscar Vídeos da Playlist", command=self.fetch_videos, font=ctk.CTkFont(weight="bold"))
        self.fetch_button.grid(row=5, column=0, padx=20, pady=10)

        # Barra de Progresso
        self.progress_bar = ctk.CTkProgressBar(self)
        self.progress_bar.grid(row=7, column=0, padx=20, pady=(0, 10), sticky="ew")
        self.progress_bar.set(0)

        # Console de Log
        self.console = ctk.CTkTextbox(self, height=200)
        self.console.grid(row=8, column=0, padx=20, pady=(0, 20), sticky="nsew")
        self.console.insert("0.0", "Aguardando URL...\n")
        self.console.configure(state="disabled")

        self.core = TranscriberCore(logger_callback=self.update_console)
        self.playlist_data = None

    def setup_images(self):
        """Carrega as imagens do banner e logo"""
        self.logo_image = None
        self.banner_image = None
        
        try:
            logo_path = os.path.join(os.path.dirname(__file__), "..", "assets", "logo.png")
            if os.path.exists(logo_path):
                logo_pil = Image.open(logo_path)
                logo_pil = logo_pil.resize((80, 80), Image.Resampling.LANCZOS)
                self.logo_image = ctk.CTkImage(light_image=logo_pil, dark_image=logo_pil, size=(80, 80))
        except Exception as e:
            self.update_console(f"Aviso: Não foi possível carregar logo.png - {e}")
        
        try:
            banner_path = os.path.join(os.path.dirname(__file__), "..", "assets", "banner.png")
            if os.path.exists(banner_path):
                banner_pil = Image.open(banner_path)
                banner_pil = banner_pil.resize((650, 100), Image.Resampling.LANCZOS)
                self.banner_image = ctk.CTkImage(light_image=banner_pil, dark_image=banner_pil, size=(650, 100))
        except Exception as e:
            self.update_console(f"Aviso: Não foi possível carregar banner.png - {e}")

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
        
        self.fetch_button.configure(state="disabled")
        self.progress_bar.configure(mode="indeterminate")
        self.progress_bar.start()
        
        workers = int(self.workers_slider.get())
        
        thread = threading.Thread(target=self.run_core, args=(url, output_folder, selected_indices, workers))
        thread.daemon = True
        thread.start()

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
        self.progress_bar.stop()
        self.progress_bar.set(0)

if __name__ == "__main__":
    app = TranscriberApp()
    app.mainloop()
