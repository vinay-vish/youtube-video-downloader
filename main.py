import os
import shutil
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.clock import Clock
from pytubefix import YouTube
from threading import Thread

# Android specific imports for permission and file management
from android.permissions import request_permissions, Permission
from android.storage import app_storage_path

# Use pyjnius for Android API calls
from jnius import autoclass

# Define the necessary Java classes
PythonActivity = autoclass('org.kivy.android.PythonActivity')
Environment = autoclass('android.os.Environment')
ContentValues = autoclass('android.content.ContentValues')
MimeTypeMap = autoclass('android.webkit.MimeTypeMap')
MediaStore = autoclass('android.provider.MediaStore')

def download_video(url, temp_path, callback):
    """Download the YouTube video to a temporary location."""
    try:
        yt = YouTube(url)
        video = yt.streams.get_highest_resolution()
        
        # Download to a temporary location within the app's internal storage
        downloaded_file_path = video.download(output_path=temp_path)
        
        # Now, save the file to the public Downloads folder
        success = save_file_to_downloads(downloaded_file_path)

        if success:
            os.remove(downloaded_file_path)
            callback("Download complete!", True)
        else:
            callback("Error: Could not save file to Downloads.", False)
    except Exception as e:
        callback(f"Error during download: {e}", False)

def save_file_to_downloads(file_path):
    """
    Saves a file to the user's public Downloads directory using a Content Resolver.
    This is the correct way to handle file saving on Android API 29+.
    """
    try:
        context = PythonActivity.mActivity
        resolver = context.getContentResolver()
        
        file_name = os.path.basename(file_path)
        extension = file_name.split('.')[-1]
        mime_type = MimeTypeMap.getSingleton().getMimeTypeFromExtension(extension)

        values = ContentValues()
        values.put(MediaStore.Downloads.DISPLAY_NAME, file_name)
        values.put(MediaStore.Downloads.MIME_TYPE, mime_type)
        values.put(MediaStore.Downloads.RELATIVE_PATH, Environment.DIRECTORY_DOWNLOADS + "/YTDownloader")

        uri = resolver.insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, values)

        if uri:
            output_stream = resolver.openOutputStream(uri)
            with open(file_path, 'rb') as input_stream:
                shutil.copyfileobj(input_stream, output_stream)
            output_stream.close()
            return True
        else:
            return False

    except Exception as e:
        print(f"Error in save_file_to_downloads: {e}")
        return False

class DownloaderApp(App):
    def build(self):
        self.has_permission = False
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        self.link_input = TextInput(hint_text='Enter YouTube video URL', multiline=False)
        self.download_button = Button(text='Download', disabled=True)
        self.status_label = Label(text='Status: Awaiting start')
        self.download_button.bind(on_press=self.start_download)
        
        layout.add_widget(self.link_input)
        layout.add_widget(self.download_button)
        layout.add_widget(self.status_label)
        return layout

    def on_start(self):
        self.status_label.text = "Status: Waiting for permissions"
        request_permissions(
            [Permission.WRITE_EXTERNAL_STORAGE, Permission.READ_EXTERNAL_STORAGE],
            self.on_permissions_result
        )

    def on_permissions_result(self, permissions, grants):
        if all(grants):
            self.has_permission = True
            self.status_label.text = "Status: Ready to download"
            self.download_button.disabled = False
        else:
            self.has_permission = False
            self.status_label.text = "Status: Permission denied. App cannot save files."
            self.download_button.disabled = True

    def start_download(self, instance):
        url = self.link_input.text.strip()
        if not url:
            self.show_popup("Error", "Please enter a YouTube video URL.")
            return

        if not self.has_permission:
            self.show_popup("Permission Error", "Permissions were denied. Cannot save files.")
            return

        self.download_button.disabled = True
        self.status_label.text = "Status: Downloading..."

        temp_path = app_storage_path()
        os.makedirs(temp_path, exist_ok=True)
        
        Thread(target=download_video, args=(url, temp_path, self.on_download_complete)).start()

    def on_download_complete(self, message, success):
        Clock.schedule_once(lambda dt: self.update_ui_after_download(message, success))

    def update_ui_after_download(self, message, success):
        self.status_label.text = f"Status: {message}"
        self.download_button.disabled = False
        self.show_popup("Success" if success else "Error", message)

    def show_popup(self, title, message):
        popup = Popup(title=title, content=Label(text=message), size_hint=(0.8, 0.4))
        popup.open()
        Clock.schedule_once(lambda dt: popup.dismiss(), 2)

if __name__ == '__main__':
    DownloaderApp().run()
