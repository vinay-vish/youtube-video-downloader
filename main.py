from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button

# Android-specific imports
try:
    from android.permissions import request_permissions, Permission
except ImportError:
    request_permissions = None
    Permission = None


class PermissionApp(App):
    def on_permission_result(self, permissions, grants):
        """
        Callback after user responds to permission request.
        :param permissions: list of requested permissions
        :param grants: list of booleans (True if granted, False if denied)
        """
        if not grants:
            self.status_label.text = "No permission result received ❌"
            return

        if all(grants):
            self.status_label.text = "Permission granted ✅"
        else:
            self.status_label.text = "Permission denied ❌"

    def request_android_permissions(self):
        """Request storage permission and handle result instantly."""
        if request_permissions:
            request_permissions(
                [Permission.WRITE_EXTERNAL_STORAGE],
                self.on_permission_result  # Callback after user responds
            )
            self.status_label.text = "Requesting permission..."
        else:
            self.status_label.text = "Not running on Android."

    def build(self):
        layout = BoxLayout(orientation='vertical', padding=20, spacing=20)

        self.status_label = Label(text="Click the button to request permission")

        btn_request = Button(text="Request Permission", size_hint=(1, 0.3))
        btn_request.bind(on_press=lambda x: self.request_android_permissions())

        layout.add_widget(self.status_label)
        layout.add_widget(btn_request)

        return layout


if __name__ == "__main__":
    PermissionApp().run()
