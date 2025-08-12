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
from functools import partial

# Android specific imports
from android.permissions import request_permissions, Permission, check_permission
from android.storage import app_storage_path, primary_external_storage_path
# The following import is crucial for API 29+
from android.storage import get_downloads_dir

def download_video(url, output_path, callback):
    """Download the YouTube video and call callback after completion."""
    try:
        yt = YouTube(url)
        video = yt.streams.get_highest_resolution()
        
        # Save to the specific directory and get the filename
        filename = video.default_filename
        full_path = os.path.join(output_path, filename)
        
        # Ensure the directory exists before downloading
        os.makedirs(output_path, exist_ok=True)
        
        video.download(output_path=output_path)
        callback("Download complete!", True)
    except Exception as e:
        callback(f"Error: {e}", False)


class DownloaderApp(App):
    def build(self):
        # The new approach: check permission first, then request if needed.
        # This is not strictly necessary as request_permissions will do this,
        # but it's good practice for clarity.
        if check_permission(Permission.WRITE_EXTERNAL_STORAGE):
            self.has_permission = True
        else:
            self.has_permission = False
            # Request permissions at startup
            request_permissions(
                [Permission.WRITE_EXTERNAL_STORAGE, Permission.READ_EXTERNAL_STORAGE],
                self.on_permissions_result
            )

        # Main layout
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        self.link_input = TextInput(hint_text='Enter YouTube video URL', multiline=False)
        self.download_button = Button(text='Download', disabled=not self.has_permission)  # Set initial state
        self.status_label = Label(text='Status: Waiting for permissions' if not self.has_permission else 'Status: Ready to download')

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
            self.status_label.text = "Status: Permission denied. The app cannot download videos."
            self.show_popup("Permission Required", "Storage permission is required to save videos.")

    def start_download(self, instance):
        url = self.link_input.text.strip()
        if not url:
            self.show_popup("Error", "Please enter a YouTube video URL.")
            return

        self.download_button.disabled = True
        self.status_label.text = "Status: Downloading..."

        # --- FIX: Use the correct method for accessing public Downloads folder ---
        # Get the path to the public Downloads directory.
        # This is the correct way to handle Scoped Storage.
        try:
            download_dir = get_downloads_dir()
            download_path = os.path.join(download_dir, 'YTDownloader')
        except Exception as e:
            # Handle the case where get_downloads_dir() might fail on older Androids,
            # or if the function is not available.
            # Fallback to the old method, which might work on older devices.
            primary_ext = primary_external_storage_path()
            download_path = os.path.join(primary_ext, 'Download', 'YTDownloader')
            print(f"Warning: Falling back to old storage path: {download_path}")
            print(f"Reason: {e}")

        # Run in a thread
        Thread(target=partial(download_video, url, download_path, self.on_download_complete)).start()

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
        # No need for auto-close here, user can close manually.


if __name__ == '__main__':
    DownloaderApp().run()
