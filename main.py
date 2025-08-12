import os
import shutil  # Import shutil for file operations
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
from android.activity import get_activity

# Define the necessary Java classes
Environment = autoclass('android.os.Environment')
Intent = autoclass('android.content.Intent')
Uri = autoclass('android.net.Uri')
PythonActivity = autoclass('org.kivy.android.PythonActivity')

def save_file_to_downloads(file_path):
    """
    Saves a file to the user's public Downloads directory using a Content Resolver.
    This is the correct way to handle file saving on Android API 29+.
    """
    try:
        # Get the context and content resolver
        context = get_activity().getApplicationContext()
        resolver = context.getContentResolver()

        # Get the file name
        file_name = os.path.basename(file_path)

        # Get the MIME type (e.g., 'video/mp4')
        MimeTypeMap = autoclass('android.webkit.MimeTypeMap')
        extension = file_name.split('.')[-1]
        mime_type = MimeTypeMap.getSingleton().getMimeTypeFromExtension(extension)

        # Create the ContentValues object with file details
        ContentValues = autoclass('android.content.ContentValues')
        values = ContentValues()
        values.put('_display_name', file_name)
        values.put('mime_type', mime_type)
        values.put('relative_path', Environment.DIRECTORY_DOWNLOADS)

        # Insert a new record into the MediaStore and get the URI
        uri = resolver.insert(
            Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_DOWNLOADS).toURI(),
            values
        )

        if uri:
            # Open an output stream to the URI
            output_stream = resolver.openOutputStream(uri)
            with open(file_path, 'rb') as input_stream:
                shutil.copyfileobj(input_stream, output_stream)
            output_stream.close()
            return True
        else:
            return False

    except Exception as e:
        # Log the error for debugging
        print(f"Error saving file via ContentResolver: {e}")
        return False


def download_video(url, temp_path, callback):
    """Download the YouTube video and call callback after completion."""
    try:
        yt = YouTube(url)
        video = yt.streams.get_highest_resolution()
        
        # Download to a temporary location within the app's internal storage
        # This is the directory we can always write to
        downloaded_file = video.download(output_path=temp_path)
        
        # Now, use the Android API to save the file to the public Downloads folder
        success = save_file_to_downloads(downloaded_file)

        if success:
            # Clean up the temporary file
            os.remove(downloaded_file)
            callback("Download complete!", True)
        else:
            callback("Error: Could not save file to Downloads.", False)

    except Exception as e:
        callback(f"Error: {e}", False)


class DownloaderApp(App):
    def build(self):
        request_permissions(
            [Permission.WRITE_EXTERNAL_STORAGE, Permission.READ_EXTERNAL_STORAGE],
            self.on_permissions_result
        )

        self.has_permission = False

        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        self.link_input = TextInput(hint_text='Enter YouTube video URL', multiline=False)
        self.download_button = Button(text='Download', disabled=True)
        self.status_label = Label(text='Status: Waiting for permissions')
        self.download_button.bind(on_press=self.start_download)
        
        layout.add_widget(self.link_input)
        layout.add_widget(self.download_button)
        layout.add_widget(self.status_label)
        return layout

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

        # Temporary path within the app's internal storage
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
