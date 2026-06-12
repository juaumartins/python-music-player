import os
from pathlib import Path

from kivy.app import App
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.metrics import dp
from kivy.properties import StringProperty, NumericProperty, BooleanProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.slider import Slider
from kivy.utils import platform


AUDIO_EXTENSIONS = {
    ".mp3",
    ".wav",
    ".ogg",
    ".flac",
    ".m4a",
    ".aac",
}


def request_android_audio_permission():
    if platform != "android":
        return

    try:
        from android.permissions import request_permissions, Permission

        permissions = []

        read_media_audio = getattr(
            Permission,
            "READ_MEDIA_AUDIO",
            "android.permission.READ_MEDIA_AUDIO"
        )

        permissions.append(read_media_audio)

        if hasattr(Permission, "READ_EXTERNAL_STORAGE"):
            permissions.append(Permission.READ_EXTERNAL_STORAGE)

        request_permissions(permissions)

    except Exception as error:
        print("Não foi possível solicitar permissão Android:", error)


def get_android_music_folders():
    return [
        "/storage/emulated/0/Music",
        "/storage/emulated/0/Download",
        "/storage/emulated/0/Downloads",
        "/storage/emulated/0/Audio",
        "/sdcard/Music",
        "/sdcard/Download",
        "/sdcard/Downloads",
        "/sdcard/Audio",
        "/storage/emulated/0/WhatsApp/Media/WhatsApp Audio",
        "/storage/emulated/0/Android/media/com.whatsapp/WhatsApp/Media/WhatsApp Audio",
    ]


def get_desktop_music_folders():
    home = str(Path.home())
    return [
        os.path.join(home, "Music"),
        os.path.join(home, "Downloads"),
        os.getcwd(),
    ]


def format_seconds(seconds):
    try:
        seconds = int(seconds)
    except Exception:
        seconds = 0

    minutes = seconds // 60
    seconds = seconds % 60
    return f"{minutes:02d}:{seconds:02d}"


class MusicPlayerRoot(BoxLayout):
    current_track_name = StringProperty("Nenhuma música selecionada")
    status_text = StringProperty("Toque em “Buscar músicas” para carregar seus áudios.")
    progress_text = StringProperty("00:00 / 00:00")
    progress_value = NumericProperty(0)
    volume_value = NumericProperty(0.8)
    is_playing = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=dp(12), spacing=dp(10), **kwargs)

        self.tracks = []
        self.current_index = -1
        self.sound = None
        self.paused_position = 0

        request_android_audio_permission()
        self.build_ui()
        Clock.schedule_interval(self.update_progress, 0.5)

    def build_ui(self):
        title = Label(
            text="[b]Python Music Player[/b]",
            markup=True,
            font_size=dp(24),
            size_hint_y=None,
            height=dp(42),
        )
        self.add_widget(title)

        self.track_label = Label(
            text=self.current_track_name,
            font_size=dp(16),
            size_hint_y=None,
            height=dp(35),
            shorten=True,
            shorten_from="middle",
        )
        self.bind(current_track_name=lambda *_: setattr(self.track_label, "text", self.current_track_name))
        self.add_widget(self.track_label)

        self.status_label = Label(
            text=self.status_text,
            font_size=dp(13),
            size_hint_y=None,
            height=dp(35),
            shorten=True,
            shorten_from="right",
        )
        self.bind(status_text=lambda *_: setattr(self.status_label, "text", self.status_text))
        self.add_widget(self.status_label)

        control_row = BoxLayout(
            orientation="horizontal",
            spacing=dp(8),
            size_hint_y=None,
            height=dp(48),
        )

        btn_scan = Button(text="Buscar músicas")
        btn_folder = Button(text="Escolher pasta")
        btn_prev = Button(text="Anterior")
        self.btn_play_pause = Button(text="Play")
        btn_stop = Button(text="Stop")
        btn_next = Button(text="Próxima")

        btn_scan.bind(on_release=lambda *_: self.scan_default_folders())
        btn_folder.bind(on_release=lambda *_: self.open_folder_picker())
        btn_prev.bind(on_release=lambda *_: self.previous_track())
        self.btn_play_pause.bind(on_release=lambda *_: self.toggle_play_pause())
        btn_stop.bind(on_release=lambda *_: self.stop_track())
        btn_next.bind(on_release=lambda *_: self.next_track())

        control_row.add_widget(btn_scan)
        control_row.add_widget(btn_folder)
        control_row.add_widget(btn_prev)
        control_row.add_widget(self.btn_play_pause)
        control_row.add_widget(btn_stop)
        control_row.add_widget(btn_next)

        self.add_widget(control_row)

        progress_box = BoxLayout(
            orientation="vertical",
            spacing=dp(4),
            size_hint_y=None,
            height=dp(70),
        )

        self.progress_slider = Slider(min=0, max=100, value=0)
        self.progress_slider.bind(on_touch_up=self.on_progress_touch_up)

        self.progress_label = Label(
            text=self.progress_text,
            size_hint_y=None,
            height=dp(24),
            font_size=dp(13),
        )
        self.bind(progress_text=lambda *_: setattr(self.progress_label, "text", self.progress_text))
        self.bind(progress_value=lambda *_: setattr(self.progress_slider, "value", self.progress_value))

        progress_box.add_widget(self.progress_slider)
        progress_box.add_widget(self.progress_label)
        self.add_widget(progress_box)

        volume_box = BoxLayout(
            orientation="horizontal",
            spacing=dp(8),
            size_hint_y=None,
            height=dp(42),
        )
        volume_box.add_widget(Label(text="Volume", size_hint_x=None, width=dp(70)))

        volume_slider = Slider(min=0, max=1, value=self.volume_value)
        volume_slider.bind(value=self.on_volume_change)
        volume_box.add_widget(volume_slider)
        self.add_widget(volume_box)

        self.scroll = ScrollView()
        self.list_layout = GridLayout(cols=1, spacing=dp(6), size_hint_y=None)
        self.list_layout.bind(minimum_height=self.list_layout.setter("height"))
        self.scroll.add_widget(self.list_layout)
        self.add_widget(self.scroll)

    def on_volume_change(self, instance, value):
        self.volume_value = value
        if self.sound:
            self.sound.volume = value

    def scan_default_folders(self):
        folders = get_android_music_folders() if platform == "android" else get_desktop_music_folders()
        self.scan_folders(folders)

    def scan_folders(self, folders):
        self.status_text = "Buscando músicas..."
        found = []

        for folder in folders:
            if not folder or not os.path.exists(folder):
                continue

            try:
                for root, dirs, files in os.walk(folder):
                    dirs[:] = [
                        d for d in dirs
                        if d not in {"Android", ".thumbnails", ".cache"}
                    ]

                    for filename in files:
                        ext = os.path.splitext(filename)[1].lower()
                        if ext in AUDIO_EXTENSIONS:
                            full_path = os.path.join(root, filename)
                            found.append(full_path)
            except Exception as error:
                print("Erro ao ler pasta:", folder, error)

        found = sorted(set(found), key=lambda path: os.path.basename(path).lower())
        self.tracks = found
        self.refresh_track_list()

        if found:
            self.status_text = f"{len(found)} música(s) encontrada(s)."
        else:
            self.status_text = "Nenhuma música encontrada. Tente “Escolher pasta”."

    def refresh_track_list(self):
        self.list_layout.clear_widgets()

        if not self.tracks:
            empty = Label(
                text="Nenhuma música carregada.",
                size_hint_y=None,
                height=dp(45),
            )
            self.list_layout.add_widget(empty)
            return

        for index, path in enumerate(self.tracks):
            name = os.path.basename(path)
            button = Button(
                text=name,
                size_hint_y=None,
                height=dp(48),
                halign="left",
                valign="middle",
            )
            button.bind(
                width=lambda instance, value: setattr(instance, "text_size", (value - dp(16), None))
            )
            button.bind(on_release=lambda instance, i=index: self.load_track(i, auto_play=True))
            self.list_layout.add_widget(button)

    def open_folder_picker(self):
        start_path = "/storage/emulated/0" if platform == "android" else str(Path.home())

        chooser = FileChooserListView(
            path=start_path,
            dirselect=True,
            filters=[],
        )

        popup_layout = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(8))
        popup_layout.add_widget(chooser)

        buttons = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        btn_cancel = Button(text="Cancelar")
        btn_select = Button(text="Usar esta pasta")

        buttons.add_widget(btn_cancel)
        buttons.add_widget(btn_select)
        popup_layout.add_widget(buttons)

        popup = Popup(
            title="Escolha uma pasta com músicas",
            content=popup_layout,
            size_hint=(0.95, 0.9),
        )

        btn_cancel.bind(on_release=popup.dismiss)

        def select_folder(*_):
            selected_folder = chooser.path
            if chooser.selection and os.path.isdir(chooser.selection[0]):
                selected_folder = chooser.selection[0]

            popup.dismiss()
            self.scan_folders([selected_folder])

        btn_select.bind(on_release=select_folder)
        popup.open()

    def load_track(self, index, auto_play=False):
        if index < 0 or index >= len(self.tracks):
            return

        self.stop_track(reset_label=False)

        self.current_index = index
        path = self.tracks[index]
        self.current_track_name = os.path.basename(path)

        self.sound = SoundLoader.load(path)

        if not self.sound:
            self.status_text = "Não foi possível carregar esta música."
            return

        self.sound.volume = self.volume_value
        self.paused_position = 0
        self.status_text = f"Música carregada: {self.current_track_name}"

        if auto_play:
            self.play_track()

    def play_track(self):
        if not self.sound:
            if self.tracks:
                self.load_track(0, auto_play=True)
            else:
                self.status_text = "Nenhuma música selecionada."
            return

        try:
            self.sound.play()

            if self.paused_position > 0:
                try:
                    self.sound.seek(self.paused_position)
                except Exception:
                    pass

            self.is_playing = True
            self.btn_play_pause.text = "Pause"
            self.status_text = "Tocando..."
        except Exception as error:
            self.status_text = f"Erro ao tocar: {error}"

    def pause_track(self):
        if not self.sound:
            return

        try:
            self.paused_position = self.sound.get_pos() or 0
            self.sound.stop()
            self.is_playing = False
            self.btn_play_pause.text = "Play"
            self.status_text = "Pausado."
        except Exception as error:
            self.status_text = f"Erro ao pausar: {error}"

    def toggle_play_pause(self):
        if self.is_playing:
            self.pause_track()
        else:
            self.play_track()

    def stop_track(self, reset_label=True):
        if self.sound:
            try:
                self.sound.stop()
            except Exception:
                pass

        self.is_playing = False
        self.btn_play_pause.text = "Play"
        self.paused_position = 0
        self.progress_value = 0
        self.progress_text = "00:00 / 00:00"

        if reset_label:
            self.status_text = "Parado."

    def next_track(self):
        if not self.tracks:
            return

        next_index = self.current_index + 1
        if next_index >= len(self.tracks):
            next_index = 0

        self.load_track(next_index, auto_play=True)

    def previous_track(self):
        if not self.tracks:
            return

        previous_index = self.current_index - 1
        if previous_index < 0:
            previous_index = len(self.tracks) - 1

        self.load_track(previous_index, auto_play=True)

    def on_progress_touch_up(self, instance, touch):
        if not instance.collide_point(*touch.pos):
            return

        if not self.sound:
            return

        try:
            duration = self.sound.length or 0
            if duration <= 0:
                return

            target_position = (instance.value / 100) * duration
            self.paused_position = target_position

            was_playing = self.is_playing
            self.sound.stop()
            self.sound.play()
            self.sound.seek(target_position)

            if not was_playing:
                self.sound.stop()

        except Exception as error:
            print("Erro ao mover progresso:", error)

    def update_progress(self, dt):
        if not self.sound:
            return

        try:
            duration = self.sound.length or 0
            current = self.sound.get_pos() or self.paused_position or 0

            if duration > 0:
                self.progress_value = min(100, max(0, (current / duration) * 100))
                self.progress_text = f"{format_seconds(current)} / {format_seconds(duration)}"

                if self.is_playing and current >= duration - 0.8:
                    self.next_track()
            else:
                self.progress_text = f"{format_seconds(current)} / 00:00"

        except Exception:
            pass


class PythonMusicPlayerApp(App):
    def build(self):
        self.title = "Python Music Player"
        return MusicPlayerRoot()


if __name__ == "__main__":
    PythonMusicPlayerApp().run()
