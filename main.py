import os
import certifi
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.clock import mainthread
from pytubefix import YouTube
from threading import Thread
from kivy.utils import platform

# Import Android storage API and permissions only if available
if platform == 'android':
    try:
        from android.storage import primary_external_storage_path
        from android.permissions import request_permissions, Permission
    except ImportError:
        # Fallback if android modules aren't available
        request_permissions = None
else:
    request_permissions = None

# Set the SSL certificate file path for pytubefix to work on Android
os.environ['SSL_CERT_FILE'] = certifi.where()

class YouTubeDownloaderApp(App):
    def build(self):
        # Request permissions on startup, but only if the function exists
        if request_permissions:
            request_permissions([
                Permission.WRITE_EXTERNAL_STORAGE, 
                Permission.READ_EXTERNAL_STORAGE
            ])

        # Main layout
        self.layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Title label
        title_label = Label(text="YouTube Video Downloader", font_size='24sp', size_hint_y=0.1)
        self.layout.add_widget(title_label)

        # Input field for the URL
        self.url_input = TextInput(hint_text="Enter YouTube Video URL", size_hint_y=0.1, multiline=False)
        self.layout.add_widget(self.url_input)

        # Download button
        download_button = Button(text="Download", size_hint_y=0.1, on_press=self.start_download)
        self.layout.add_widget(download_button)

        # Status label
        self.status_label = Label(text="", size_hint_y=0.1)
        self.layout.add_widget(self.status_label)

        return self.layout

    def start_download(self, instance):
        url = self.url_input.text
        if url:
            self.status_label.text = "Starting download..."
            # Start the download in a separate thread to avoid freezing the UI
            Thread(target=self.download_video, args=(url,)).start()
        else:
            self.status_label.text = "Please enter a valid URL."

    def download_video(self, url):
        try:
            yt = YouTube(url, on_progress_callback=self.on_progress)
            stream = yt.streams.get_highest_resolution()
            
            # Determine the download path based on the platform
            if platform == 'android' and 'primary_external_storage_path' in globals():
                primary_path = primary_external_storage_path()
                download_path = os.path.join(primary_path, 'Download')
            else:
                # Fallback for desktop testing
                download_path = os.path.join(os.path.expanduser('~'), 'Downloads')

            if not os.path.exists(download_path):
                os.makedirs(download_path)

            self.update_status(f"Downloading: {yt.title}")
            stream.download(output_path=download_path)
            self.update_status("Download complete!")
        except Exception as e:
            self.update_status(f"An error occurred: {e}")

    @mainthread
    def update_status(self, text):
        self.status_label.text = text

    @mainthread
    def on_progress(self, stream, chunk, bytes_remaining):
        total_size = stream.filesize
        bytes_downloaded = total_size - bytes_remaining
        percentage_of_completion = bytes_downloaded / total_size * 100
        self.status_label.text = f"Downloading: {percentage_of_completion:.2f}%"

if __name__ == '__main__':
    YouTubeDownloaderApp().run()
