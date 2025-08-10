import os
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.clock import Clock
from pytubefix import YouTube
from threading import Thread

# Android specific imports
from android.permissions import request_permissions, Permission
from android.storage import app_storage_path, primary_external_storage_path


def download_video(url, output_path, callback):
    """Download the YouTube video and call callback after completion."""
    try:
        yt = YouTube(url)
        video = yt.streams.get_highest_resolution()
        video.download(output_path=output_path)
        callback("Download complete!", True)
    except Exception as e:
        callback(f"Error: {e}", False)


class DownloaderApp(App):
    def build(self):
        # Ask permissions at startup
        request_permissions(
            [Permission.WRITE_EXTERNAL_STORAGE, Permission.READ_EXTERNAL_STORAGE],
            self.on_permissions_result
        )

        self.has_permission = False

        # Main layout
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        self.link_input = TextInput(hint_text='Enter YouTube video URL', multiline=False)
        self.download_button = Button(text='Download', disabled=True)  # Disabled until permission granted
        self.status_label = Label(text='Status: Waiting for permissions')

        self.download_button.bind(on_press=self.start_download)

        layout.add_widget(self.link_input)
        layout.add_widget(self.download_button)
        layout.add_widget(self.status_label)

        return layout

    def on_permissions_result(self, permissions, grants):
        """Check if all requested permissions are granted."""
        if all(grants):
            self.has_permission = True
            self.status_label.text = "Status: Ready to download"
            self.download_button.disabled = False
        else:
            self.has_permission = False
            self.status_label.text = "Status: Permission denied"

    def start_download(self, instance):
        url = self.link_input.text.strip()
        if not url:
            self.show_popup("Error", "Please enter a YouTube video URL.")
            return

        self.download_button.disabled = True
        self.status_label.text = "Status: Downloading..."

        # Save to external storage Download folder
        primary_ext = primary_external_storage_path()
        download_path = os.path.join(primary_ext, 'Download', 'YTDownloader')
        os.makedirs(download_path, exist_ok=True)

        # Run in a thread
        Thread(target=download_video, args=(url, download_path, self.on_download_complete)).start()

    def on_download_complete(self, message, success):
        """Run on main thread after download."""
        Clock.schedule_once(lambda dt: self.update_ui_after_download(message, success))

    def update_ui_after_download(self, message, success):
        self.status_label.text = f"Status: {message}"
        self.download_button.disabled = False
        self.show_popup("Success" if success else "Error", message)

    def show_popup(self, title, message):
        popup = Popup(title=title, content=Label(text=message), size_hint=(0.8, 0.4))
        popup.open()
        Clock.schedule_once(lambda dt: popup.dismiss(), 2)  # Auto-close after 2 seconds


if __name__ == '__main__':
    DownloaderApp().run()
