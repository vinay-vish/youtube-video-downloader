import os
import ssl
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.clock import Clock
from threading import Thread
from pytubefix import YouTube

# The URL of the video to be downloaded
VIDEO_URL = "https://youtu.be/s01QuLpjISc?si=2PM0aLNdpiPgSWGu"

# This line directly disables SSL certificate verification,
# which is the most reliable way to fix the 'CERTIFICATE_VERIFY_FAILED' error.
ssl._create_default_https_context = ssl._create_unverified_context

class DownloaderApp(App):
    def build(self):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        self.status_label = Label(text='Status: Ready to download')
        download_button = Button(text='Download Video')
        download_button.bind(on_press=self.on_button_press)
        
        layout.add_widget(self.status_label)
        layout.add_widget(download_button)
        return layout

    def on_button_press(self, instance):
        self.status_label.text = "Downloading..."
        instance.disabled = True
        Thread(target=self.start_download, args=(instance,)).start()

    def start_download(self, button_instance):
        try:
            yt = YouTube(VIDEO_URL)
            video_stream = yt.streams.get_highest_resolution()

            # Using app_storage_path for internal storage,
            # which does not require special permissions.
            from android.storage import app_storage_path
            download_path = app_storage_path()
            os.makedirs(download_path, exist_ok=True)
            video_stream.download(output_path=download_path)

            Clock.schedule_once(lambda dt: self.update_status("Download complete!", button_instance))
        except Exception as e:
            Clock.schedule_once(lambda dt: self.update_status(f"An error occurred: {e}", button_instance))

    def update_status(self, message, button_instance):
        self.status_label.text = message
        button_instance.disabled = False

if __name__ == '__main__':
    DownloaderApp().run()
