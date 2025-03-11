import threading
import time
from datetime import datetime

import speech_recognition as sr
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivymd.app import MDApp
from kivymd.uix.list import MDList, TwoLineListItem
from kivy.uix.scrollview import ScrollView
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField

KV = """
ScreenManager:
    MainScreen:

<MainScreen>:
    name: "main"
    MDBoxLayout:
        orientation: "vertical"
        padding: "10dp"
        spacing: "10dp"

        MDCard:
            size_hint_y: None
            height: "50dp"
            md_bg_color: 0.2, 0.6, 0.8, 1
            radius: [10, 10, 0, 0]
            padding: "10dp"

            MDLabel:
                text: "AI Notes App"
                theme_text_color: "Custom"
                text_color: 1, 1, 1, 1
                font_style: "H6"
                halign: "center"

        MDTextField:
            id: note_input
            hint_text: "Type or use voice input..."
            multiline: True

        MDRaisedButton:
            text: "Record Voice"
            on_release: app.record_voice()

        MDRaisedButton:
            text: "Save Note"
            on_release: app.save_note()

        ScrollView:
            MDList:
                id: notes_list
"""

class MainScreen(Screen):
    pass

class AI_NoteApp(MDApp):
    dialog = None  # To store the dialog instance

    def build(self):
        return Builder.load_string(KV)

    def on_start(self):
        self.load_notes()

    def record_voice(self):
        threading.Thread(target=self._record_in_chunks).start()

    def _record_in_chunks(self):
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            self.update_text("Listening...")
            while True:
                try:
                    audio = recognizer.listen(source, phrase_time_limit=5)
                    text = recognizer.recognize_google(audio)
                    self.update_text(f" {text}")
                except sr.UnknownValueError:
                    pass
                except Exception as e:
                    self.update_text(f"Error: {e}")
                    break
                time.sleep(0.1)

    def update_text(self, text_to_add):
        Clock.schedule_once(lambda dt: self._update_text_main_thread(text_to_add))

    def _update_text_main_thread(self, text_to_add):
        if self.root:
            self.root.get_screen("main").ids.note_input.text += text_to_add

    def save_note(self):
        text = self.root.get_screen("main").ids.note_input.text
        if text:
            try:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                with open("notes.txt", "a", encoding="utf-8") as file:
                    file.write(f"[{timestamp}] {text}\n")
                self.root.get_screen("main").ids.note_input.text = "Note saved!"
                self.load_notes()
            except Exception as e:
                self.root.get_screen("main").ids.note_input.text = f"Error saving note: {e}"

    def load_notes(self):
        try:
            with open("notes.txt", "r", encoding="utf-8") as file:
                notes = file.readlines()
            notes_list = self.root.get_screen("main").ids.notes_list
            notes_list.clear_widgets()
            for i, note in enumerate(reversed(notes), 1):
                try:
                    timestamp, note_text = note.split("]", 1)
                    item = TwoLineListItem(
                        text=f"{i}. {timestamp}]",
                        secondary_text=note_text.strip(),
                        on_release=lambda x, note_index=len(notes) - i: self.show_note_actions(note_index)
                    )
                    notes_list.add_widget(item)
                except ValueError:
                    print(f"Skipping invalid note: {note}")
        except FileNotFoundError:
            pass

    def show_note_actions(self, note_index):
        if not self.dialog:
            self.dialog = MDDialog(
                title="Note Actions",
                buttons=[
                    MDRaisedButton(text="Edit", on_release=lambda x: self.edit_note(note_index)),
                    MDRaisedButton(text="Delete", on_release=lambda x: self.delete_note(note_index)),
                    MDRaisedButton(text="Cancel", on_release=lambda x: self.dialog.dismiss())
                ]
            )
        self.dialog.open()

    def edit_note(self, note_index):
        self.dialog.dismiss()
        try:
            with open("notes.txt", "r", encoding="utf-8") as file:
                notes = file.readlines()
            note = notes[note_index]
            timestamp, note_text = note.split("]", 1)
            text_field = MDTextField(text=note_text.strip(), multiline=True)
            edit_dialog = MDDialog(
                title="Edit Note",
                type="custom",
                content_cls=text_field,
                buttons=[
                    MDRaisedButton(text="Save", on_release=lambda x: self.save_edited_note(note_index, text_field.text)),
                    MDRaisedButton(text="Cancel", on_release=lambda x: edit_dialog.dismiss())
                ]
            )
            edit_dialog.open()
        except Exception as e:
            print(f"Error editing note: {e}")

    def save_edited_note(self, note_index, new_text):
        try:
            with open("notes.txt", "r", encoding="utf-8") as file:
                notes = file.readlines()
            timestamp, _ = notes[note_index].split("]", 1)
            notes[note_index] = f"{timestamp}] {new_text}\n"
            with open("notes.txt", "w", encoding="utf-8") as file:
                file.writelines(notes)
            self.load_notes()
        except Exception as e:
            print(f"Error saving edited note: {e}")
        self.dialog.dismiss()

    def delete_note(self, note_index):
        try:
            with open("notes.txt", "r", encoding="utf-8") as file:
                notes = file.readlines()
            del notes[note_index]
            with open("notes.txt", "w", encoding="utf-8") as file:
                file.writelines(notes)
            self.load_notes()
        except Exception as e:
            print(f"Error deleting note: {e}")
        self.dialog.dismiss()

if __name__ == "__main__":
    AI_NoteApp().run()