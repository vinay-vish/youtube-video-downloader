import os
from datetime import datetime

from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.camera import Camera
from kivy.uix.image import Image

# Android-specific imports
try:
    from android.permissions import request_permissions, Permission, check_permission
    from android.storage import primary_external_storage_path
except ImportError:
    request_permissions = None
    Permission = None
    check_permission = None
    primary_external_storage_path = None


class CameraPreviewApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.camera_widget = None
        self.save_button = None
        self.captured_image = None
        self.layout = None

    def on_permission_result(self, permissions, grants):
        """After user responds to permission request."""
        if not grants or not all(grants):
            self.status_label.text = "Camera permission denied"
            return
        self.status_label.text = "Camera permission granted"
        self.start_camera()

    def request_camera_permission(self):
        """Request permission and start camera when granted."""
        if request_permissions:
            request_permissions(
                [Permission.CAMERA, Permission.WRITE_EXTERNAL_STORAGE],
                self.on_permission_result
            )
        else:
            self.status_label.text = "Not running on Android."

    def start_camera(self):
        """Start live camera preview."""
        if self.camera_widget:
            return  # Already running

        self.camera_widget = Camera(play=True)
        self.camera_widget.resolution = (640, 480)
        self.layout.add_widget(self.camera_widget)

        self.save_button = Button(text="Capture Photo", size_hint=(1, 0.15))
        self.save_button.bind(on_press=lambda x: self.capture_photo())
        self.layout.add_widget(self.save_button)

    def capture_photo(self):
        """Capture and save the image, then show preview."""
        if not self.camera_widget:
            self.status_label.text = "Camera not active."
            return

        # Save path
        if primary_external_storage_path:
            save_dir = os.path.join(primary_external_storage_path(), "KivyPhotos")
        else:
            save_dir = os.path.expanduser("~/KivyPhotos")
        os.makedirs(save_dir, exist_ok=True)

        filename = datetime.now().strftime("IMG_%Y%m%d_%H%M%S.png")
        filepath = os.path.join(save_dir, filename)

        self.camera_widget.export_to_png(filepath)
        self.status_label.text = f"Photo saved:\n{filepath}"

        # Show preview
        if self.captured_image:
            self.layout.remove_widget(self.captured_image)
        self.captured_image = Image(source=filepath, size_hint=(1, 0.6))
        self.layout.add_widget(self.captured_image)

    def build(self):
        self.layout = BoxLayout(orientation='vertical', padding=20, spacing=10)

        self.status_label = Label(text="Checking permissions...", size_hint=(1, 0.15))
        self.layout.add_widget(self.status_label)

        btn_request = Button(text="Request Camera Permission", size_hint=(1, 0.15))
        btn_request.bind(on_press=lambda x: self.request_camera_permission())
        self.layout.add_widget(btn_request)

        # Auto-check permission at startup
        if check_permission and check_permission(Permission.CAMERA):
            self.status_label.text = "Permission already granted"
            self.start_camera()
        else:
            self.status_label.text = "Click button to request camera permission"

        return self.layout


if __name__ == "__main__":
    CameraPreviewApp().run()
