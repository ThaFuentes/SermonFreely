import json
import os
import datetime
import google.generativeai as genai
import google.api_core.exceptions as g_exceptions
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QLineEdit, QPushButton, QHBoxLayout, QLabel, QListWidget, QComboBox, QSplitter, QWidget, QMenu, QInputDialog
from PyQt6.QtGui import QFont, QTextCursor, QAction
from PyQt6.QtCore import Qt
import sqlite3
import logging
from data_handlers import load_sermon

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sermon.log'),
        logging.StreamHandler()
    ]
)

CHAT_HISTORY_DIR = 'chat_histories'
DB_FILE = 'sermon_secrets.db'

# List of distinct colors for Gemini responses
GEMINI_COLORS = ['#2E8B57', '#98FB98', '#3CB371', '#20B2AA', '#66CDAA', '#40E0D0', '#00CED1', '#48D1CC']

class GeminiChatDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("Gemini Chat Assistant")
        self.model = None
        self.chat = None
        self.history = []
        self.conversation_label = None
        self.saved_conversations = self.load_saved_conversations()
        self.color_index = 0  # Track color index for unique Gemini responses

        self.setMinimumSize(600, 400)
        self.resize(800, 600)
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowMinMaxButtonsHint | Qt.WindowType.WindowCloseButtonHint)

        layout = QVBoxLayout()
        self.setLayout(layout)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)

        left_widget = QVBoxLayout()
        left_label = QLabel("Previous Conversations")
        left_label.setStyleSheet("color: #b9bbbe;")
        left_widget.addWidget(left_label)
        self.convo_list = QListWidget()
        self.convo_list.setStyleSheet("background-color: #2c2f33; color: #ffffff; border: 1px solid #444;")
        self.convo_list.itemClicked.connect(self.load_conversation)
        self.convo_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.convo_list.customContextMenuRequested.connect(self.show_context_menu)
        self.update_convo_list()
        left_widget.addWidget(self.convo_list)
        left_container = QWidget()
        left_container.setLayout(left_widget)
        splitter.addWidget(left_container)

        right_widget = QVBoxLayout()
        self.convo_text = QTextEdit()
        self.convo_text.setReadOnly(True)
        self.convo_text.setFont(QFont("Arial", 12))
        self.convo_text.setStyleSheet("""
            background-color: #2c2f33;
            border: 1px solid #444;
            padding: 10px;
            color: #ffffff;
        """)
        right_widget.addWidget(self.convo_text)

        input_layout = QHBoxLayout()
        self.input_edit = QLineEdit()
        self.input_edit.setPlaceholderText("Type your message here...")
        self.input_edit.setStyleSheet("background-color: #40444b; color: #ffffff; border: 1px solid #444; padding: 5px; border-radius: 5px;")
        self.input_edit.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.input_edit)

        send_btn = QPushButton("Send")
        send_btn.setStyleSheet("background-color: #007bff; color: white; border: none; padding: 5px 10px; border-radius: 5px;")
        send_btn.clicked.connect(self.send_message)
        input_layout.addWidget(send_btn)

        right_widget.addLayout(input_layout)

        controls_layout = QHBoxLayout()
        save_btn = QPushButton("Save Conversation")
        save_btn.setStyleSheet("background-color: #28a745; color: white; border: none; padding: 5px 10px; border-radius: 5px;")
        save_btn.clicked.connect(self.save_conversation)
        controls_layout.addWidget(save_btn)

        clear_btn = QPushButton("Clear History")
        clear_btn.setStyleSheet("background-color: #dc3545; color: white; border: none; padding: 5px 10px; border-radius: 5px;")
        clear_btn.clicked.connect(self.clear_history)
        controls_layout.addWidget(clear_btn)

        reference_label = QLabel("Short Log: Up to 100 messages kept for reference")
        reference_label.setStyleSheet("color: #b9bbbe;")
        controls_layout.addWidget(reference_label)

        right_widget.addLayout(controls_layout)

        right_container = QWidget()
        right_container.setLayout(right_widget)
        splitter.addWidget(right_container)

        try:
            self.api_keys = self.load_api_keys()
            logging.debug(f"Loaded {len(self.api_keys)} API keys from {DB_FILE}")
            if not self.api_keys:
                self.append_message("Error", "No Gemini API Key. Please visit the Help section to make one.", "#ff4040")
            else:
                key_layout = QHBoxLayout()
                key_label = QLabel("Select Gemini Key:")
                key_layout.addWidget(key_label)
                self.key_combo = QComboBox()
                self.key_combo.addItems([f"Key {i+1}" for i in range(len(self.api_keys))])
                self.key_combo.currentIndexChanged.connect(self.switch_key)
                key_layout.addWidget(self.key_combo)
                layout.addLayout(key_layout)
                self.current_key_index = 0
                self.api_key = self.api_keys[0]
            self.model_name = self.parent.sermon.get('settings', {}).get('gemini_model', 'gemini-1.5-flash')
            logging.debug(f"Using Gemini model: {self.model_name}")
        except Exception as e:
            logging.error(f"Error initializing API keys: {str(e)}")
            self.append_message("Error", f"Failed to initialize API keys: {str(e)}", "#ff4040")

    def load_api_keys(self):
        """Load API keys from SQLite DB."""
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute('SELECT api_key FROM gemini_api_keys')
            keys = [row[0] for row in cursor.fetchall()]
            conn.close()
            logging.debug(f"Successfully loaded {len(keys)} API keys from gemini_api_keys table")
            return keys
        except Exception as e:
            logging.error(f"Failed to load API keys from {DB_FILE}: {str(e)}")
            raise

    def send_message(self):
        msg = self.input_edit.text().strip()
        if not msg:
            return

        if not self.api_keys:
            self.append_message("Error", "No Gemini API Key. Please visit the Help section to make one.", "#ff4040")
            return

        self.history.append({'role': 'user', 'text': msg})
        self.append_message("User", msg, "#00bfff")

        if not self.model or not self.chat:
            self._init_gemini()

        ai_text = self._try_send_message(msg)
        if ai_text is None:
            return

        self.history.append({'role': 'ai', 'text': ai_text})
        # Assign a unique color for each new Gemini response
        self.color_index = (self.color_index + 1) % len(GEMINI_COLORS)
        self.append_message("Gemini", ai_text, GEMINI_COLORS[self.color_index])

        self.input_edit.clear()
        self.trim_history()
        self.auto_label_conversation()

    def _try_send_message(self, msg):
        retries = len(self.api_keys)
        while retries > 0:
            try:
                response = self.chat.send_message(msg)
                return response.text
            except g_exceptions.ResourceExhausted as e:
                self.append_message("Error", f"Quota exceeded for current key: {str(e)}", "#ff4040")
                self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
                self.api_key = self.api_keys[self.current_key_index]
                self.key_combo.setCurrentIndex(self.current_key_index)
                self._init_gemini()
                self.append_message("System", f"Switched to Key {self.current_key_index + 1}", "#b9bbbe")
                retries -= 1
            except g_exceptions.GoogleAPICallError as e:
                self.append_message("Error", f"Gemini API call failed: {str(e)}", "#ff4040")
                return None
            except Exception as e:
                self.append_message("Error", f"Unexpected error with Gemini: {str(e)}", "#ff4040")
                return None
        self.append_message("Error", "All API keys exhausted.", "#ff4040")
        return None

    def append_message(self, role, text, color):
        # Append new text without forcing scroll, allowing natural view
        try:
            html = f"<p style='color: {color}; margin: 5px 0;'><b>{role}:</b> {text.replace('\n', '<br>')}</p>"
            self.convo_text.append(html)
            logging.debug(f"Appended message for {role} with length {len(text)} and color {color}")
        except Exception as e:
            logging.error(f"Error appending message: {str(e)}")

    def trim_history(self):
        if len(self.history) > 100:
            self.history = self.history[-100:]

    def clear_history(self):
        self.history = []
        self.convo_text.clear()
        self.chat = None
        self.color_index = 0  # Reset color index on clear

    def save_conversation(self):
        if not self.history:
            QMessageBox.warning(self, "No History", "No conversation history to save.")
            return

        if not self.conversation_label:
            self.auto_label_conversation()
        label = self.conversation_label or f"Conversation - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        if not os.path.exists(CHAT_HISTORY_DIR):
            os.makedirs(CHAT_HISTORY_DIR)

        filename = os.path.join(CHAT_HISTORY_DIR, f"{label.replace(' ', '_')}.json")
        try:
            with open(filename, 'w') as f:
                json.dump(self.history, f, indent=4)
            self.saved_conversations[label] = filename
            self.update_convo_list()
            QMessageBox.information(self, "Saved", f"Conversation saved as {label}")
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save conversation: {str(e)}")

    def load_conversation(self, item):
        label = item.text()
        filename = self.saved_conversations.get(label)
        if filename:
            try:
                with open(filename, 'r') as f:
                    self.history = json.load(f)
                self.convo_text.clear()
                self.color_index = 0  # Reset color index for loaded conversation
                for entry in self.history:
                    color = "#00bfff" if entry['role'] == 'user' else GEMINI_COLORS[self.color_index % len(GEMINI_COLORS)]
                    self.append_message(entry['role'].capitalize(), entry['text'], color)
                    if entry['role'] == 'ai':
                        self.color_index += 1  # Increment for each Gemini response
                self.conversation_label = label
            except Exception as e:
                QMessageBox.critical(self, "Load Error", f"Failed to load conversation: {str(e)}")

    def load_saved_conversations(self):
        saved = {}
        if os.path.exists(CHAT_HISTORY_DIR):
            for file in os.listdir(CHAT_HISTORY_DIR):
                if file.endswith('.json'):
                    label = file.replace('.json', '').replace('_', ' ')
                    saved[label] = os.path.join(CHAT_HISTORY_DIR, file)
        return saved

    def update_convo_list(self):
        self.convo_list.clear()
        for label in sorted(self.saved_conversations.keys()):
            self.convo_list.addItem(label)

    def auto_label_conversation(self):
        if self.history:
            first_msg = self.history[0]['text'][:50]
            date_str = datetime.datetime.now().strftime('%Y-%m-%d')
            self.conversation_label = f"{date_str} - {first_msg}..."

    def show_context_menu(self, pos):
        item = self.convo_list.itemAt(pos)
        if item:
            menu = QMenu(self)
            edit_action = QAction("Edit Name", self)
            edit_action.triggered.connect(lambda: self.edit_convo_name(item))
            menu.addAction(edit_action)
            delete_action = QAction("Delete", self)
            delete_action.triggered.connect(lambda: self.delete_convo(item))
            menu.addAction(delete_action)
            menu.exec(self.convo_list.viewport().mapToGlobal(pos))

    def edit_convo_name(self, item):
        old_label = item.text()
        new_label, ok = QInputDialog.getText(self, "Edit Conversation Name", "New name:", text=old_label)
        if ok and new_label and new_label != old_label:
            old_filename = self.saved_conversations[old_label]
            new_filename = os.path.join(CHAT_HISTORY_DIR, f"{new_label.replace(' ', '_')}.json")
            try:
                os.rename(old_filename, new_filename)
                del self.saved_conversations[old_label]
                self.saved_conversations[new_label] = new_filename
                self.update_convo_list()
                QMessageBox.information(self, "Edited", f"Conversation name changed to {new_label}")
            except Exception as e:
                QMessageBox.critical(self, "Edit Error", f"Failed to edit name: {str(e)}")

    def delete_convo(self, item):
        label = item.text()
        reply = QMessageBox.question(self, "Delete Confirmation", f"Are you sure you want to delete '{label}'?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            filename = self.saved_conversations[label]
            try:
                os.remove(filename)
                del self.saved_conversations[label]
                self.update_convo_list()
                if self.conversation_label == label:
                    self.clear_history()
                QMessageBox.information(self, "Deleted", f"Conversation '{label}' deleted.")
            except Exception as e:
                QMessageBox.critical(self, "Delete Error", f"Failed to delete: {str(e)}")

    def switch_key(self, index):
        if 0 <= index < len(self.api_keys):
            self.current_key_index = index
            self.api_key = self.api_keys[index]
            self.chat = None
            self.append_message("System", f"Switched to Key {index+1}", "#b9bbbe")

    def _init_gemini(self):
        """Initialize Gemini if not already."""
        try:
            model_name = self.parent.sermon.get('settings', {}).get('gemini_model', 'gemini-1.5-flash')
            logging.debug(f"Initializing Gemini with model: {model_name}")
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(
                model_name=model_name,
                system_instruction="You are a sermon assistant designed to assist pastors and ministers in preparing "
                                   "sermons, with a focus on biblical teachings and spiritual guidance. Recognize "
                                   "that sermon perspectives may vary, including non-mainstream views, and respect "
                                   "the user’s preferences while maintaining theological accuracy where applicable. "
                                   "If a user’s request includes a perspective not widely accepted in biblical "
                                   "scholarship, acknowledge this politely with a brief note (e.g., “This view may "
                                   "not be widely accepted in mainstream theology”) and proceed to provide relevant "
                                   "assistance without obstruction.\n\nRespond exclusively with content relevant to "
                                   "sermon preparation, such as biblical verse suggestions, thematic insights, "
                                   "sermon outline ideas, or spiritual reflections. Do not generate full sermons; "
                                   "instead, provide tools like outlines, key points, or verse references to support "
                                   "the user’s creative process. Avoid any content that is sexual, off-topic, "
                                   "or uses inappropriate language. If a request is unclear or deviates from "
                                   "sermon-related topics, politely redirect to relevant sermon preparation content ("
                                   "e.g., “Could you clarify how this relates to your sermon? I can suggest relevant "
                                   "verses or themes.”).\n\nWhen providing Bible verses, include the full reference ("
                                   "e.g., “John 3:16”) and the verse text, ensuring each verse is separated by a "
                                   "blank line for clarity and readability. Verify that all responses are concise, "
                                   "actionable, and aligned with the user’s intent for sermon development. Log any "
                                   "unclear or non-biblical requests for review, but prioritize fulfilling the user’s "
                                   "sermon-related needs."
            )
            self.chat = self.model.start_chat(history=[])
        except Exception as e:
            logging.error(f"Failed to initialize Gemini: {str(e)}")
            self.append_message("Error", f"Failed to initialize Gemini: {str(e)}", "#ff4040")

    def reject(self):
        super().reject()