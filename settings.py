from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QDialogButtonBox, QListWidget, QPushButton, QInputDialog, QHBoxLayout
import sqlite3
import logging

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

class SettingsDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("Settings")
        layout = QVBoxLayout()

        # Bible Translation
        self.translation_combo = QComboBox()
        translations = ['KJV', 'WEB', 'YLT', 'NKJV', 'ASV']
        self.translation_combo.addItems(translations)
        self.translation_combo.setCurrentText(parent.sermon['settings'].get('default_translation', 'WEB'))
        layout.addWidget(QLabel("Default Bible Translation:"))
        layout.addWidget(self.translation_combo)

        # Multiple Gemini API Keys
        layout.addWidget(QLabel("Gemini API Keys (Add multiple for different accounts/models):"))
        self.keys_list = QListWidget()
        self.keys = self.load_api_keys()
        logging.debug(f"Loaded {len(self.keys)} Gemini API keys from DB")
        for key in self.keys:
            self.keys_list.addItem(f"Key {self.keys_list.count() + 1}: {key[:4]}...{key[-4:]}")  # Mask key for display
        layout.addWidget(self.keys_list)

        keys_buttons = QHBoxLayout()
        add_key_btn = QPushButton("Add Key")
        add_key_btn.setStyleSheet("background-color: #007bff; color: white; padding: 5px 10px; border-radius: 5px;")
        add_key_btn.clicked.connect(self.add_key)
        keys_buttons.addWidget(add_key_btn)
        remove_key_btn = QPushButton("Remove Selected")
        remove_key_btn.setStyleSheet("background-color: #dc3545; color: white; padding: 5px 10px; border-radius: 5px;")
        remove_key_btn.clicked.connect(self.remove_key)
        keys_buttons.addWidget(remove_key_btn)
        layout.addLayout(keys_buttons)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept_settings)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.setLayout(layout)
        self.init_db()

    def init_db(self):
        """Initialize the SQLite database if not exists."""
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS gemini_api_keys (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    api_key TEXT NOT NULL
                )
            ''')
            conn.commit()
            conn.close()
            logging.debug("Initialized gemini_api_keys table in DB")
        except Exception as e:
            logging.error(f"Failed to initialize DB: {str(e)}")
            self.parent.statusBar.showMessage(f"Error initializing DB: {str(e)}", 5000)

    def load_api_keys(self):
        """Load API keys from SQLite DB."""
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute('SELECT api_key FROM gemini_api_keys')
            keys = [row[0] for row in cursor.fetchall()]
            conn.close()
            return keys
        except Exception as e:
            logging.error(f"Failed to load API keys from DB: {str(e)}")
            self.parent.statusBar.showMessage(f"Error loading API keys: {str(e)}", 5000)
            return []

    def save_api_keys(self):
        """Save API keys to SQLite DB."""
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM gemini_api_keys')  # Clear existing keys
            for key in self.keys:
                cursor.execute('INSERT INTO gemini_api_keys (api_key) VALUES (?)', (key,))
            conn.commit()
            conn.close()
            logging.debug(f"Saved {len(self.keys)} API keys to DB")
        except Exception as e:
            logging.error(f"Failed to save API keys to DB: {str(e)}")
            self.parent.statusBar.showMessage(f"Error saving API keys: {str(e)}", 5000)

    def add_key(self):
        key, ok = QInputDialog.getText(self, "Add Gemini API Key", "Enter new key:")
        if ok and key.strip():
            self.keys.append(key.strip())
            self.keys_list.addItem(f"Key {self.keys_list.count() + 1}: {key.strip()[:4]}...{key.strip()[-4:]}")
            self.parent.statusBar.showMessage("API key added.", 3000)
            logging.debug(f"Added API key ending in {key[-4:]}")

    def remove_key(self):
        selected = self.keys_list.currentItem()
        if selected:
            index = self.keys_list.currentRow()
            removed_key = self.keys.pop(index)
            self.keys_list.takeItem(index)
            self.parent.statusBar.showMessage("API key removed.", 3000)
            logging.debug(f"Removed API key ending in {removed_key[-4:]}")
            # Update item labels to reflect new numbering
            for i in range(self.keys_list.count()):
                key = self.keys[i]
                self.keys_list.item(i).setText(f"Key {i + 1}: {key[:4]}...{key[-4:]}")

    def accept_settings(self):
        try:
            self.parent.sermon['settings']['default_translation'] = self.translation_combo.currentText()
            self.save_api_keys()
            # Save the sermon to persist any changes like translation
            self.parent.quick_save()  # Assuming quick_save saves the sermon
            self.parent.statusBar.showMessage("Settings saved.", 3000)
            logging.debug(f"Settings saved: translation={self.translation_combo.currentText()}, {len(self.keys)} API keys")
            self.accept()
        except Exception as e:
            logging.error(f"Failed to save settings: {str(e)}")
            self.parent.statusBar.showMessage(f"Error saving settings: {str(e)}", 5000)