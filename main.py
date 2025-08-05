import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget, QMessageBox, QStatusBar, QMenuBar, QMenu, QTextEdit, QListWidget
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtCore import Qt, QTimer
from data_handlers import load_sermon, save_sermon, clear_sermon_data, init_encryption
from ui_tabs import create_title_tab, create_intro_tab, create_content_tab, create_verses_tab, create_preview_tab
from verse_handlers import update_verses_list, add_verse, edit_verse, delete_verse, SermonNotesDialog
from bible_utils import fetch_verse_text
from bible_read import BibleReadDialog
from export_utils import set_header, set_footer, save_as_word
from preview_utils import preview_all
from settings import SettingsDialog
from bible_search import BibleSearchDialog
from gemini_chat import GeminiChatDialog
from help_utils import HelpDialog
import sqlite3
import logging
import os

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

def open_bible_reader(parent):
    """Open the BibleReadDialog."""
    logging.debug("Opening BibleReadDialog")
    try:
        dialog = BibleReadDialog(parent)
        dialog.exec()
    except Exception as e:
        logging.error(f"Failed to open BibleReadDialog: {str(e)}")
        QMessageBox.critical(parent, "Dialog Error", f"Failed to open Read Bible: {str(e)}")

class SermonApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sermon Freely")
        self.setGeometry(100, 100, 800, 600)
        try:
            icon_path = 'icon.png'  # Assumes icon.png is in D:\PycharmProjects\SermonFreelyPro\
            # Alternatively, use full path: 'D:/PycharmProjects/SermonFreelyPro/icon.png'
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
                logging.debug(f"Set window icon to {icon_path}")
            else:
                logging.warning(f"Icon file not found: {icon_path}")
        except Exception as e:
            logging.error(f"Error setting window icon: {str(e)}")
        self.sermon = load_sermon(self)
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.sort_mode = 'ref'  # Default sorting mode: 'ref' or 'time'
        self.init_menu()
        self.init_ui()
        self.auto_save_on_close = True
        self.auto_save_timer = QTimer(self)
        self.auto_save_timer.timeout.connect(self.quick_save)
        self.auto_save_timer.start(300000)  # 5 minutes

    def init_menu(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("File")
        file_menu.addAction("Quick Save", self.quick_save)
        file_menu.addAction("Quick Load", self.quick_load)
        file_menu.addAction("Save to Word...", self.save_as_word)
        file_menu.addSeparator()
        file_menu.addAction("Clear All", self.clear_all)
        file_menu.addSeparator()
        file_menu.addAction("Exit", self.close)
        tools_menu = menu_bar.addMenu("Tools")
        tools_menu.addAction("Read Bible", self.read_bible)
        tools_menu.addAction("Bible Search", self.bible_search)
        tools_menu.addAction("Gemini Chat", self.open_gemini_chat)
        tools_menu.addAction("Clear All", self.clear_all)
        settings_menu = menu_bar.addMenu("Settings")
        settings_menu.addAction("Gemini Api and Bible Version", self.open_settings)
        settings_menu.addAction("Set Header", self.set_header)
        settings_menu.addAction("Set Footer", self.set_footer)
        help_menu = menu_bar.addMenu("Help")
        help_menu.addAction("How to Operate the Program", lambda: self.open_help("operate"))
        help_menu.addAction("How to Create a Gemini API Key", lambda: self.open_help("gemini"))
        help_menu.addAction("Help and Support", lambda: self.open_help("support"))

    def init_ui(self):
        tabs = QTabWidget()
        self.setCentralWidget(tabs)
        title_tab, self.title_edit = create_title_tab(self.sermon['title'], self.save_title)
        tabs.addTab(title_tab, "Title")
        intro_tab, self.intro_edit = create_intro_tab(self.sermon['intro'], self.save_intro)
        tabs.addTab(intro_tab, "Intro")
        verses_tab, self.verses_list = create_verses_tab(self.add_verse, self.edit_verse, self.delete_verse, self.copy_to_sermon_content, self.toggle_sort_mode, self.copy_all_to_sermon_content)
        tabs.addTab(verses_tab, "Verses & Notes")
        content_tab, self.content_edit = create_content_tab(self.sermon['content'], self.save_content)
        tabs.addTab(content_tab, "Content")
        preview_tab, self.preview_text = create_preview_tab(self.preview_all)
        tabs.addTab(preview_tab, "Preview")
        self.update_verses_list()
        self.verses_list.mousePressEvent = self.handle_verses_list_mouse_press
        self.verses_list.mouseDoubleClickEvent = self.handle_verses_list_double_click
        self.intro_edit.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.intro_edit.setAcceptRichText(False)
        self.content_edit.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.content_edit.setAcceptRichText(False)

    def toggle_sort_mode(self, sort_button):
        """Toggle between sorting by ref and time, update button text."""
        try:
            self.sort_mode = 'time' if self.sort_mode == 'ref' else 'ref'
            sort_button.setText(f"Sort By: {'Time' if self.sort_mode == 'time' else 'Reference'}")
            self.update_verses_list()
            logging.debug(f"Toggled sort mode to: {self.sort_mode}")
        except Exception as e:
            logging.error(f"Error toggling sort mode: {str(e)}")
            self.statusBar.showMessage(f"Error toggling sort mode: {str(e)}", 5000)

    def handle_verses_list_mouse_press(self, event):
        """Handle single-click events in the verses list to allow selection or add new note."""
        try:
            QListWidget.mousePressEvent(self.verses_list, event)  # Call base class method for selection
            if event.button() == Qt.MouseButton.LeftButton:
                item = self.verses_list.itemAt(event.pos())
                if not item:
                    self.add_verse()
                    logging.debug("Mouse press in verses list: Add dialog opened")
        except Exception as e:
            logging.error(f"Error handling mouse press in verses list: {str(e)}")
            self.statusBar.showMessage(f"Error handling click: {str(e)}", 5000)

    def handle_verses_list_double_click(self, event):
        """Handle double-click events in the verses list to edit existing items."""
        try:
            QListWidget.mouseDoubleClickEvent(self.verses_list, event)  # Call base class method
            if event.button() == Qt.MouseButton.LeftButton:
                item = self.verses_list.itemAt(event.pos())
                if item:
                    self.verses_list.setCurrentItem(item)  # Ensure the clicked item is selected
                    self.edit_verse()
                    logging.debug("Double-click in verses list: Edit dialog opened")
        except Exception as e:
            logging.error(f"Error handling double-click in verses list: {str(e)}")
            self.statusBar.showMessage(f"Error handling double-click: {str(e)}", 5000)

    def save_title(self):
        self.sermon['title'] = self.title_edit.text()
        self.statusBar.showMessage("Title saved.", 3000)

    def save_intro(self):
        self.sermon['intro'] = self.intro_edit.toPlainText().replace('\r\n', '\n').replace('\r', '\n')
        self.statusBar.showMessage("Intro saved.", 3000)

    def save_content(self):
        self.sermon['content'] = self.content_edit.toPlainText().replace('\r\n', '\n').replace('\r', '\n')
        self.statusBar.showMessage("Content saved.", 3000)

    def update_verses_list(self):
        update_verses_list(self.verses_list, self.sermon['verses_notes'], self.sort_mode)

    def add_verse(self):
        add_verse(self, self.sermon, self.update_verses_list, self.get_verse, self.statusBar)

    def edit_verse(self):
        edit_verse(self, self.sermon, self.verses_list, self.update_verses_list, self.get_verse, self.statusBar)

    def delete_verse(self):
        delete_verse(self, self.sermon, self.verses_list, self.update_verses_list, self.statusBar)

    def copy_to_sermon_content(self):
        try:
            selected = self.verses_list.currentItem()
            if not selected:
                self.statusBar.showMessage("No verse/note selected.", 3000)
                return
            index = self.verses_list.currentRow()
            if index < 0 or index >= len(self.sermon['verses_notes']):
                self.statusBar.showMessage("Error: Invalid selection.", 5000)
                return
            text = self.sermon['verses_notes'][index]['text']
            self.sermon['content'] += "\n\n" + text
            self.content_edit.setPlainText(self.sermon['content'])
            self.statusBar.showMessage("Copied to sermon content.", 3000)
        except Exception as e:
            self.statusBar.showMessage(f"Error copying to sermon content: {str(e)}", 5000)

    def copy_all_to_sermon_content(self):
        try:
            if not self.sermon['verses_notes']:
                self.statusBar.showMessage("No verses/notes to copy.", 3000)
                return
            all_text = "\n\n".join(verse['text'] for verse in self.sermon['verses_notes'])
            self.sermon['content'] += "\n\n" + all_text
            self.content_edit.setPlainText(self.sermon['content'])
            self.statusBar.showMessage("All verses/notes copied to sermon content.", 3000)
        except Exception as e:
            logging.error(f"Error copying all verses/notes to sermon content: {str(e)}")
            self.statusBar.showMessage(f"Error copying all verses/notes: {str(e)}", 5000)

    def get_verse(self, ref):
        translation = self.sermon['settings']['default_translation']
        return fetch_verse_text(ref, translation)

    def read_bible(self):
        try:
            open_bible_reader(self)
        except Exception as e:
            QMessageBox.critical(self, "Read Bible Error", f"Failed to open Read Bible: {str(e)}")

    def bible_search(self):
        try:
            dialog = BibleSearchDialog(self)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Bible Search Error", f"Failed to open Bible Search: {str(e)}")

    def open_gemini_chat(self):
        try:
            # Load API keys from SQLite database
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute('SELECT api_key FROM gemini_api_keys')
            api_keys = [row[0] for row in cursor.fetchall()]
            conn.close()
            logging.debug(f"Loaded {len(api_keys)} API keys from {DB_FILE}")

            if not api_keys:
                QMessageBox.warning(self, "No API Key", "Please set your Gemini API key in Settings first.")
                return
            dialog = GeminiChatDialog(self)
            dialog.exec()
        except Exception as e:
            logging.error(f"Failed to open Gemini Chat: {str(e)}")
            QMessageBox.critical(self, "Gemini Chat Error", f"Failed to open Gemini Chat: {str(e)}")

    def open_settings(self):
        dialog = SettingsDialog(self)
        if dialog.exec():
            self.statusBar.showMessage("Settings saved.", 3000)

    def open_help(self, topic):
        try:
            dialog = HelpDialog(self)
            dialog.show_topic(topic)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Help Error", f"Failed to open Help: {str(e)}")

    def preview_all(self):
        preview_all(self.preview_text, self.sermon)

    def set_header(self):
        set_header(self, self.sermon, self.statusBar)

    def set_footer(self):
        set_footer(self, self.sermon, self.statusBar)

    def quick_save(self):
        save_sermon(self.sermon, self.statusBar)
        if self.sender() == self.auto_save_timer:
            self.statusBar.showMessage("Auto-saved to JSON.", 3000)
        else:
            self.statusBar.showMessage("Saved to JSON.", 3000)

    def quick_load(self):
        self.sermon = load_sermon(self)
        self.refresh_ui()
        self.statusBar.showMessage("Quick loaded.", 3000)

    def clear_all(self):
        clear_sermon_data(self, self.sermon)

    def save_as_word(self):
        save_as_word(self, self.sermon, self.statusBar)

    def refresh_ui(self):
        self.title_edit.setText(self.sermon['title'])
        self.intro_edit.setPlainText(self.sermon['intro'].replace('\r\n', '\n').replace('\r', '\n'))
        self.intro_edit.repaint()
        self.content_edit.setPlainText(self.sermon['content'].replace('\r\n', '\n').replace('\r', '\n'))
        self.content_edit.repaint()
        self.update_verses_list()
        self.preview_all()

    def closeEvent(self, event):
        if self.auto_save_on_close and QMessageBox.question(self, "Exit", "Save to JSON before exit?") == QMessageBox.StandardButton.Yes:
            self.sermon['title'] = self.title_edit.text()
            self.sermon['intro'] = self.intro_edit.toPlainText().replace('\r\n', '\n').replace('\r', '\n')
            self.sermon['content'] = self.content_edit.toPlainText().replace('\r\n', '\n').replace('\r', '\n')
            self.quick_save()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SermonApp()
    window.show()
    sys.exit(app.exec())