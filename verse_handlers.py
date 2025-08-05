import json
import os
import google.generativeai as genai
import google.api_core.exceptions as g_exceptions
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QLineEdit, QPushButton, QHBoxLayout, QSplitter, QWidget, \
    QLabel, QComboBox, QMessageBox
from PyQt6.QtGui import QFont, QTextCursor, QTextOption
from PyQt6.QtCore import Qt
import sqlite3
import logging
from data_handlers import load_sermon
import datetime

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sermon.log'),
        logging.StreamHandler()
    ]
)

DB_FILE = 'sermon_secrets.db'

# List of distinct colors for Gemini responses
GEMINI_COLORS = ['#2E8B57', '#98FB98', '#3CB371', '#20B2AA', '#66CDAA', '#40E0D0', '#00CED1', '#48D1CC']

def update_verses_list(verses_list, verses, sort_mode='ref'):
    """Update the verses display in a QListWidget, sorted by ref or timestamp."""
    try:
        verses_list.clear()
        # Sort verses based on sort_mode
        if sort_mode == 'time':
            # Sort by timestamp (newest first), with entries lacking timestamp at the end
            sorted_verses = sorted(
                verses,
                key=lambda x: x.get('timestamp', '9999-12-31 23:59:59'),
                reverse=True
            )
        else:
            # Sort by ref field (case-insensitive)
            sorted_verses = sorted(verses, key=lambda x: x.get('ref', '').lower())
        for verse in sorted_verses:
            item_text = f"{verse.get('ref', '')}: {verse.get('text', '')}"
            verses_list.addItem(item_text)
        logging.debug(f"Updated verses list, sorted by {sort_mode}")
    except Exception as e:
        logging.error(f"Error updating verses list: {str(e)}")

def add_verse(parent, sermon, update_callback, get_verse_callback, status_bar):
    """Open SermonNotesDialog to add verses/notes."""
    try:
        dialog = SermonNotesDialog(parent)
        dialog.exec()
        update_callback()
        status_bar.showMessage("Verses/Notes dialog closed.", 3000)
    except Exception as e:
        logging.error(f"Error opening dialog: {str(e)}")
        status_bar.showMessage(f"Error opening dialog: {str(e)}", 5000)

def edit_verse(parent, sermon, verses_list, update_callback, get_verse_callback, status_bar):
    """Edit a verse in sermon['verses_notes'] using SermonNotesDialog."""
    try:
        if not verses_list.count():
            status_bar.showMessage("No verses/notes available to edit.", 3000)
            return
        selected = verses_list.currentItem()
        if not selected:
            status_bar.showMessage("No verse/note selected.", 3000)
            return
        index = verses_list.currentRow()
        if index < 0 or index >= len(sermon.get('verses_notes', [])):
            status_bar.showMessage("Error: Invalid selection.", 5000)
            return
        current_ref = sermon['verses_notes'][index].get('ref', 'Note')
        current_text = sermon['verses_notes'][index].get('text', '')
        dialog = SermonNotesDialog(parent, edit_mode=True, edit_index=index, initial_text=current_text, initial_ref=current_ref)
        if dialog.exec():
            new_text = dialog.notes_text.toPlainText().replace('\r\n', '\n').replace('\r', '\n')
            new_ref = dialog.ref_input.text().strip() or 'Note'
            if new_text:
                sermon['verses_notes'][index] = {
                    'ref': new_ref,
                    'text': new_text,
                    'note': sermon['verses_notes'][index].get('note', ''),
                    'timestamp': sermon['verses_notes'][index].get('timestamp', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                }
                update_callback()
                status_bar.showMessage("Verse/Note edited.", 3000)
            else:
                status_bar.showMessage("Edit canceled: No text provided.", 3000)
        else:
            status_bar.showMessage("Edit canceled.", 3000)
    except IndexError:
        logging.error("Error editing verse: Index out of range")
        status_bar.showMessage("Error editing verse: Index out of range", 5000)
    except Exception as e:
        logging.error(f"Error editing verse: {str(e)}")
        status_bar.showMessage(f"Error editing verse: {str(e)}", 5000)

def delete_verse(parent, sermon, verses_list, update_callback, status_bar):
    """Delete a verse from sermon['verses_notes']."""
    try:
        selected = verses_list.currentItem()
        if not selected:
            status_bar.showMessage("No verse selected.", 3000)
            return
        index = verses_list.currentRow()
        sermon['verses_notes'].pop(index)
        update_callback()
        status_bar.showMessage("Verse deleted.", 3000)
    except Exception as e:
        logging.error(f"Error deleting verse: {str(e)}")
        status_bar.showMessage(f"Error deleting verse: {str(e)}", 5000)

class SermonNotesDialog(QDialog):
    def __init__(self, parent=None, edit_mode=False, edit_index=None, initial_text='', initial_ref='Note'):
        super().__init__(parent)
        self.parent = parent
        self.edit_mode = edit_mode
        self.edit_index = edit_index
        self.setWindowTitle("Edit Verse/Note" if edit_mode else "Sermon Notes and Verses")
        self.model = None
        self.chat = None
        self.notes = ""
        self.verses = self.parent.sermon.get('verses_notes', []) if self.parent and hasattr(self.parent, 'sermon') else []
        self.suggestions = ""
        self.color_index = 0  # Track color index for unique Gemini responses

        self.setMinimumSize(600, 600)
        self.resize(800, 800)

        layout = QVBoxLayout()
        self.setLayout(layout)

        splitter = QSplitter(Qt.Orientation.Vertical)
        layout.addWidget(splitter)

        notes_widget = QWidget()
        notes_layout = QVBoxLayout()
        notes_label = QLabel("Input Notes / Verses")
        notes_label.setStyleSheet("color: #b9bbbe;")
        notes_layout.addWidget(notes_label)

        # Add reference input for both add and edit modes
        ref_layout = QHBoxLayout()
        ref_label = QLabel("Reference:")
        ref_label.setStyleSheet("color: #b9bbbe;")
        self.ref_input = QLineEdit(initial_ref)
        self.ref_input.setStyleSheet("background-color: #40444b; color: #ffffff; border: 1px solid #444; padding: 5px; border-radius: 5px;")
        self.ref_input.setPlaceholderText("Enter tag (e.g., Verses, Notes, or custom like John 3:16)")
        ref_layout.addWidget(ref_label)
        ref_layout.addWidget(self.ref_input)
        notes_layout.addLayout(ref_layout)

        self.notes_text = QTextEdit()
        self.notes_text.setFont(QFont("Arial", 14))
        self.notes_text.setStyleSheet("""
            background-color: #2c2f33;
            border: 1px solid #444;
            padding: 10px;
            color: #ffffff;
        """)
        self.notes_text.setAcceptRichText(False)
        self.notes_text.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.notes_text.setWordWrapMode(QTextOption.WrapMode.WordWrap)
        self.notes_text.setPlainText(initial_text)
        notes_layout.addWidget(self.notes_text)
        notes_widget.setLayout(notes_layout)
        splitter.addWidget(notes_widget)

        research_widget = QWidget()
        research_layout = QVBoxLayout()
        research_label = QLabel("Quick Gemini Research")
        research_label.setStyleSheet("color: #b9bbbe;")
        research_layout.addWidget(research_label)

        query_layout = QHBoxLayout()
        self.research_edit = QLineEdit()
        self.research_edit.setPlaceholderText("Enter Gemini query (optional, e.g., 'Suggest verses on faith')")
        self.research_edit.setStyleSheet(
            "background-color: #40444b; color: #ffffff; border: 1px solid #444; padding: 5px; border-radius: 5px;")
        self.research_edit.returnPressed.connect(self.send_gemini_research)
        query_layout.addWidget(self.research_edit)

        send_btn = QPushButton("Send")
        send_btn.setStyleSheet(
            "background-color: #007bff; color: white; border: none; padding: 5px 10px; border-radius: 5px;")
        send_btn.clicked.connect(self.send_gemini_research)
        query_layout.addWidget(send_btn)
        research_layout.addLayout(query_layout)

        self.research_text = QTextEdit()
        self.research_text.setReadOnly(True)
        self.research_text.setFont(QFont("Arial", 14))
        self.research_text.setStyleSheet("""
            background-color: #2c2f33;
            border: 1px solid #444;
            padding: 10px;
            color: #ffffff;
        """)
        self.research_text.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.research_text.setWordWrapMode(QTextOption.WrapMode.WordWrap)
        research_layout.addWidget(self.research_text)
        research_widget.setLayout(research_layout)
        splitter.addWidget(research_widget)

        buttons_layout = QHBoxLayout()
        add_notes_btn = QPushButton("Save Changes" if edit_mode else "Add Notes")
        add_notes_btn.setStyleSheet(
            "background-color: #007bff; color: white; border: none; padding: 5px 10px; border-radius: 5px;")
        add_notes_btn.clicked.connect(self.add_notes)
        buttons_layout.addWidget(add_notes_btn)

        search_notes_btn = QPushButton("Search Notes")
        search_notes_btn.setStyleSheet(
            "background-color: #28a745; color: white; border: none; padding: 5px 10px; border-radius: 5px;")
        search_notes_btn.clicked.connect(self.search_notes)
        buttons_layout.addWidget(search_notes_btn)

        add_suggestions_btn = QPushButton("Add Suggestions")
        add_suggestions_btn.setStyleSheet(
            "background-color: #28a745; color: white; border: none; padding: 5px 10px; border-radius: 5px;")
        add_suggestions_btn.clicked.connect(self.add_suggestions)
        buttons_layout.addWidget(add_suggestions_btn)

        layout.addLayout(buttons_layout)

        try:
            self.api_keys = self.load_api_keys()
            logging.debug(f"Loaded {len(self.api_keys)} API keys from {DB_FILE}")
            if not self.api_keys:
                self.append_research("Error", "No Gemini API Key. Please visit the Help section to make one.",
                                     "#ff4040")
            else:
                key_layout = QHBoxLayout()
                key_label = QLabel("Select Gemini Key:")
                key_layout.addWidget(key_label)
                self.key_combo = QComboBox()
                self.key_combo.addItems([f"Key {i + 1}" for i in range(len(self.api_keys))])
                self.key_combo.currentIndexChanged.connect(self.switch_key)
                key_layout.addWidget(self.key_combo)
                research_layout.addLayout(key_layout)
                self.current_key_index = 0
                self.api_key = self.api_keys[0]
            self.model_name = self.parent.sermon.get('settings', {}).get('gemini_model', 'gemini-1.5-flash')
            logging.debug(f"Using Gemini model: {self.model_name}")
        except Exception as e:
            logging.error(f"Error initializing API keys: {str(e)}")
            self.append_research("Error", f"Failed to initialize API keys: {str(e)}", "#ff4040")

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

    def add_notes(self):
        """Add or update the input from top section as a note to sermon['verses_notes']."""
        try:
            input_text = self.notes_text.toPlainText().replace('\r\n', '\n').replace('\r', '\n')
            if not input_text:
                QMessageBox.warning(self, "No Input", "Please enter some notes or a verse reference.")
                return
            note_dict = {
                'ref': self.ref_input.text().strip() or 'Note',
                'text': input_text,
                'note': '',
                'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            if not hasattr(self.parent, 'sermon') or not isinstance(self.parent.sermon, dict):
                logging.error("Parent sermon is not properly initialized")
                QMessageBox.critical(self, "Error", "Sermon data is not properly initialized.")
                return
            if 'verses_notes' not in self.parent.sermon:
                self.parent.sermon['verses_notes'] = []
            if self.edit_mode and self.edit_index is not None:
                note_dict['timestamp'] = self.parent.sermon['verses_notes'][self.edit_index].get('timestamp', note_dict['timestamp'])
                self.parent.sermon['verses_notes'][self.edit_index] = note_dict
                self.parent.statusBar.showMessage("Verse/Note edited.", 3000)
                QMessageBox.information(self, "Edited", "Verse/Note edited successfully.")
            else:
                self.parent.sermon['verses_notes'].append(note_dict)
                self.parent.statusBar.showMessage("Note added.", 3000)
                QMessageBox.information(self, "Added", "Note added successfully.")
            self.notes_text.clear()
            self.ref_input.clear()
            if self.edit_mode:
                self.accept()  # Close dialog after editing
            if self.parent and hasattr(self.parent, 'update_verses_list'):
                self.parent.update_verses_list()
            logging.debug("Note added or edited successfully")
        except Exception as e:
            logging.error(f"Error adding or editing note: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to add or edit note: {str(e)}")

    def search_notes(self):
        """Send the notes to Gemini for suggestions, display in bottom."""
        try:
            input_text = self.notes_text.toPlainText().replace('\r\n', '\n').replace('\r', '\n')
            if not input_text:
                QMessageBox.warning(self, "No Input", "Please enter some notes to search.")
                return
            if not self.api_key:
                self.append_research("Error", "No Gemini API Key. Please visit the Help section to make one.", "#ff4040")
                return
            self._init_gemini()
            if not self.model or not self.chat:
                return
            prompt = f"Based on these sermon notes: '{input_text}', suggest relevant Bible verses with references and brief explanations."
            self._try_send_gemini_prompt(prompt, "Suggestions")
        except Exception as e:
            logging.error(f"Error searching notes: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to search notes: {str(e)}")

    def add_suggestions(self):
        """Add the entire suggestions from Gemini to the notes/verses section as a single entry."""
        try:
            if not self.suggestions:
                QMessageBox.warning(self, "No Suggestions", "Please generate suggestions first.")
                return
            note_dict = {
                'ref': 'Suggestions',
                'text': self.suggestions,
                'note': '',
                'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            if not hasattr(self.parent, 'sermon') or not isinstance(self.parent.sermon, dict):
                logging.error("Parent sermon is not properly initialized")
                QMessageBox.critical(self, "Error", "Sermon data is not properly initialized.")
                return
            if 'verses_notes' not in self.parent.sermon:
                self.parent.sermon['verses_notes'] = []
            self.parent.sermon['verses_notes'].append(note_dict)
            self.research_text.clear()
            self.suggestions = ""
            if self.parent and hasattr(self.parent, 'update_verses_list'):
                self.parent.update_verses_list()
                self.parent.statusBar.showMessage("Suggestions added.", 3000)
            QMessageBox.information(self, "Added", "Suggestions added successfully.")
            logging.debug("Suggestions added successfully")
        except Exception as e:
            logging.error(f"Error adding suggestions: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to add suggestions: {str(e)}")

    def send_gemini_research(self):
        """Send quick Gemini research query from bottom section."""
        try:
            query = self.research_edit.text().strip()
            if not query:
                QMessageBox.warning(self, "No Query", "Please enter a Gemini query.")
                return
            if not self.api_key:
                self.append_research("Error", "No Gemini API Key. Please visit the Help section to make one.", "#ff4040")
                return
            self._init_gemini()
            if not self.model or not self.chat:
                return
            self._try_send_gemini_prompt(query, "Research")
        except Exception as e:
            logging.error(f"Error sending Gemini research: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to send Gemini research: {str(e)}")

    def switch_key(self, index):
        """Switch the active Gemini API key."""
        try:
            if 0 <= index < len(self.api_keys):
                self.current_key_index = index
                self.api_key = self.api_keys[index]
                self.chat = None
                self.append_research("System", f"Switched to Key {index + 1}", "#b9bbbe")
                logging.debug(f"Switched to API key index {index}")
        except Exception as e:
            logging.error(f"Error switching API key: {str(e)}")
            self.append_research("Error", f"Failed to switch API key: {str(e)}", "#ff4040")

    def _init_gemini(self):
        """Initialize Gemini if not already."""
        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction="You are a sermon assistant designed to assist pastors and ministers in preparing sermons, with a focus on biblical teachings and spiritual guidance. Recognize that sermon perspectives may vary, including non-mainstream views, and respect the user’s preferences while maintaining theological accuracy where applicable. If a user’s request includes a perspective not widely accepted in biblical scholarship, acknowledge this politely with a brief note (e.g., “This view may not be widely accepted in mainstream theology”) and proceed to provide relevant assistance without obstruction.\n\nRespond exclusively with content relevant to sermon preparation, such as biblical verse suggestions, thematic insights, sermon outline ideas, or spiritual reflections. Do not generate full sermons; instead, provide tools like outlines, key points, or verse references to support the user’s creative process. Avoid any content that is sexual, off-topic, or uses inappropriate language. If a request is unclear or deviates from sermon-related topics, politely redirect to relevant sermon preparation content (e.g., “Could you clarify how this relates to your sermon? I can suggest relevant verses or themes.”).\n\nWhen providing Bible verses, include the full reference (e.g., “John 3:16”) and the verse text, ensuring each verse is separated by a blank line for clarity and readability. Verify that all responses are concise, actionable, and aligned with the user’s intent for sermon development. Log any unclear or non-biblical requests for review, but prioritize fulfilling the user’s sermon-related needs."
            )
            self.chat = self.model.start_chat(history=[])
        except Exception as e:
            logging.error(f"Failed to initialize Gemini: {str(e)}")
            self.append_research("Error", f"Failed to initialize Gemini: {str(e)}", "#ff4040")
            self.reject()

    def _try_send_gemini_prompt(self, prompt, role):
        """Send prompt to Gemini with fallback on quota error."""
        retries = len(self.api_keys)
        while retries > 0:
            try:
                response = self.chat.send_message(prompt)
                text = response.text
                # Assign a unique color for each new Gemini response
                self.color_index = (self.color_index + 1) % len(GEMINI_COLORS)
                self.append_research(role, text, GEMINI_COLORS[self.color_index])
                if role == "Suggestions":
                    self.suggestions = text
                return
            except g_exceptions.ResourceExhausted as e:
                self.append_research("Error", f"Quota exceeded for current key: {str(e)}", "#ff4040")
                self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
                self.api_key = self.api_keys[self.current_key_index]
                self.key_combo.setCurrentIndex(self.current_key_index)
                self._init_gemini()
                self.append_research("System", f"Switched to Key {self.current_key_index + 1}", "#b9bbbe")
                retries -= 1
            except g_exceptions.GoogleAPICallError as e:
                self.append_research("Error", f"Gemini API call failed: {str(e)}", "#ff4040")
                return
            except Exception as e:
                self.append_research("Error", f"Unexpected error with Gemini: {str(e)}", "#ff4040")
                return
        self.append_research("Error", "All API keys exhausted.", "#ff4040")

    def append_research(self, role, text, color):
        """Append new text without forcing scroll, allowing natural view."""
        try:
            html = f"<p style='color: {color}; margin: 5px 0;'><b>{role}:</b> {text.replace('\n', '<br>')}</p>"
            self.research_text.append(html)
            logging.debug(f"Appended research for {role} with length {len(text)} and color {color}")
        except Exception as e:
            logging.error(f"Error appending research: {str(e)}")