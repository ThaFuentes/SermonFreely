import requests
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton, QWidget, QScrollArea, QMessageBox, QLineEdit
from PyQt6.QtCore import Qt
from bible_utils import BOOK_MAP, REVERSE_BOOK_MAP, BOOK_CHAPTERS, parse_ref, fetch_verse_text
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

class BibleReadDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("Read Bible")
        self.setMinimumSize(800, 600)
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowMinMaxButtonsHint | Qt.WindowType.WindowCloseButtonHint | Qt.WindowType.WindowTitleHint | Qt.WindowType.WindowSystemMenuHint)
        self.setModal(False)
        self.setup_ui()
        self.load_initial_chapter()

    def setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Navigation bar
        nav_layout = QHBoxLayout()
        self.book_combo = QComboBox()
        self.book_combo.addItems(list(BOOK_MAP.keys()))
        self.book_combo.currentTextChanged.connect(self.update_chapter_combo)
        self.book_combo.currentTextChanged.connect(self.load_chapter)
        nav_layout.addWidget(QLabel("Book:"))
        nav_layout.addWidget(self.book_combo)

        self.chapter_combo = QComboBox()
        self.chapter_combo.addItems([str(i) for i in range(1, 2)])  # Placeholder, updated later
        self.chapter_combo.currentTextChanged.connect(self.load_chapter)
        nav_layout.addWidget(QLabel("Chapter:"))
        nav_layout.addWidget(self.chapter_combo)

        self.ref_input = QLineEdit()
        self.ref_input.setPlaceholderText("Enter reference (e.g., John 3:16)")
        self.ref_input.returnPressed.connect(self.jump_to_reference)
        nav_layout.addWidget(self.ref_input)
        layout.addLayout(nav_layout)

        # Verses display
        self.verses_widget = QWidget()
        self.verses_layout = QVBoxLayout()
        self.verses_widget.setLayout(self.verses_layout)

        scroll_area = QScrollArea()
        scroll_area.setWidget(self.verses_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("background-color: #2c2f33; border: 1px solid #444; padding: 10px;")
        layout.addWidget(scroll_area)

        # Navigation buttons
        buttons_layout = QHBoxLayout()
        prev_btn = QPushButton("Previous Chapter")
        prev_btn.setStyleSheet("background-color: #007bff; color: white; border: none; padding: 5px 10px; border-radius: 5px;")
        prev_btn.clicked.connect(lambda: self.navigate_chapter(-1))
        buttons_layout.addWidget(prev_btn)

        next_btn = QPushButton("Next Chapter")
        next_btn.setStyleSheet("background-color: #007bff; color: white; border: none; padding: 5px 10px; border-radius: 5px;")
        next_btn.clicked.connect(lambda: self.navigate_chapter(1))
        buttons_layout.addWidget(next_btn)

        copy_all_btn = QPushButton("Copy All to Notes")
        copy_all_btn.setStyleSheet("background-color: #28a745; color: white; border: none; padding: 5px 10px; border-radius: 5px;")
        copy_all_btn.clicked.connect(self.copy_all_to_notes)
        buttons_layout.addWidget(copy_all_btn)

        layout.addLayout(buttons_layout)

    def update_chapter_combo(self):
        """Update chapter dropdown based on selected book."""
        logging.debug("Updating chapter combo")
        current_book = self.book_combo.currentText()
        max_chapters = BOOK_CHAPTERS.get(current_book, 1)
        self.chapter_combo.blockSignals(True)
        self.chapter_combo.clear()
        self.chapter_combo.addItems([str(i) for i in range(1, max_chapters + 1)])
        self.chapter_combo.blockSignals(False)
        if self.chapter_combo.currentText() == "":
            self.chapter_combo.setCurrentText("1")

    def load_chapter(self):
        """Load and display chapter content."""
        logging.debug("Loading chapter")
        try:
            current_book = self.book_combo.currentText()
            current_chapter_text = self.chapter_combo.currentText()
            if not current_chapter_text or not current_chapter_text.isdigit():
                logging.debug("Invalid chapter text, defaulting to 1")
                current_chapter = 1
                self.chapter_combo.setCurrentText("1")
            else:
                current_chapter = int(current_chapter_text)
            if current_book not in BOOK_MAP or current_chapter < 1 or current_chapter > BOOK_CHAPTERS[current_book]:
                raise ValueError("Invalid book or chapter")
            book_id = BOOK_MAP[current_book]
            translation = self.parent.sermon.get('settings', {}).get('default_translation', 'WEB') if isinstance(self.parent.sermon, dict) else 'WEB'
            url = f"https://bolls.life/get-text/{translation}/{book_id}/{current_chapter}/"
            logging.debug(f"Requesting URL: {url}")
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()

            # Clear existing verses
            while self.verses_layout.count():
                item = self.verses_layout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()

            # Add verses
            for verse in data:
                verse_label = QLabel(f"{verse['verse']}. {verse['text']}")
                verse_label.setStyleSheet("color: #ffffff; margin: 5px 0;")
                verse_label.setWordWrap(True)
                copy_btn = QPushButton("Copy Verse")
                copy_btn.setStyleSheet("background-color: #28a745; color: white; border: none; padding: 2px 5px; border-radius: 3px;")
                copy_btn.clicked.connect(lambda checked, v=verse.copy(): self.copy_to_notes(v, current_book, current_chapter))
                h_layout = QHBoxLayout()
                h_layout.addWidget(verse_label)
                h_layout.addWidget(copy_btn)
                widget = QWidget()
                widget.setLayout(h_layout)
                self.verses_layout.addWidget(widget)
            self.verses_layout.addStretch()
        except requests.RequestException as e:
            logging.error(f"Network error loading chapter: {str(e)}")
            QMessageBox.warning(self, "API Error", f"Network error: {str(e)}")
        except Exception as e:
            logging.error(f"Failed to load chapter: {str(e)}")
            QMessageBox.warning(self, "API Error", f"Failed to fetch chapter: {str(e)}")

    def navigate_chapter(self, direction):
        """Navigate to previous or next chapter."""
        logging.debug("Navigating chapter")
        try:
            current_book = self.book_combo.currentText()
            current_chapter = int(self.chapter_combo.currentText())
            max_chapter = BOOK_CHAPTERS[current_book]
            new_chapter = current_chapter + direction
            if 1 <= new_chapter <= max_chapter:
                self.chapter_combo.setCurrentText(str(new_chapter))
            else:
                books = list(BOOK_MAP.keys())
                book_index = books.index(current_book)
                new_book_index = book_index + direction
                if 0 <= new_book_index < len(books):
                    new_book = books[new_book_index]
                    self.book_combo.setCurrentText(new_book)
                    self.update_chapter_combo()
                    if direction > 0:
                        self.chapter_combo.setCurrentText("1")
                    else:
                        self.chapter_combo.setCurrentText(str(BOOK_CHAPTERS[new_book]))
            self.load_chapter()
        except Exception as e:
            logging.error(f"Navigation error: {str(e)}")
            QMessageBox.warning(self, "Navigation Error", f"Failed to navigate: {str(e)}")

    def jump_to_reference(self):
        """Jump to a specific Bible reference."""
        logging.debug("Jumping to reference")
        try:
            ref = self.ref_input.text().strip()
            book_id, chapter, verse = parse_ref(ref)
            book = REVERSE_BOOK_MAP[book_id]
            self.book_combo.setCurrentText(book)
            self.update_chapter_combo()
            self.chapter_combo.setCurrentText(str(chapter))
            if verse:
                # Clear existing verses
                while self.verses_layout.count():
                    item = self.verses_layout.takeAt(0)
                    widget = item.widget()
                    if widget:
                        widget.deleteLater()
                translation = self.parent.sermon.get('settings', {}).get('default_translation', 'WEB') if isinstance(self.parent.sermon, dict) else 'WEB'
                verse_text = fetch_verse_text(ref, translation)
                verse_label = QLabel(f"{verse}. {verse_text}")
                verse_label.setStyleSheet("color: #ffffff; margin: 5px 0;")
                verse_label.setWordWrap(True)
                copy_btn = QPushButton("Copy Verse")
                copy_btn.setStyleSheet("background-color: #28a745; color: white; border: none; padding: 2px 5px; border-radius: 3px;")
                copy_btn.clicked.connect(lambda checked, v={'verse': str(verse), 'text': verse_text}: self.copy_to_notes(v, book, chapter))
                h_layout = QHBoxLayout()
                h_layout.addWidget(verse_label)
                h_layout.addWidget(copy_btn)
                widget = QWidget()
                widget.setLayout(h_layout)
                self.verses_layout.addWidget(widget)
                self.verses_layout.addStretch()
            else:
                self.load_chapter()
        except Exception as e:
            logging.error(f"Jump to reference error: {str(e)}")
            QMessageBox.warning(self, "Invalid Reference", f"Invalid reference: {str(e)}")

    def copy_to_notes(self, verse, book, chapter):
        """Copy a single verse to sermon notes."""
        logging.debug(f"Starting copy_to_notes with verse: {verse}")
        try:
            if not hasattr(self.parent, 'sermon') or not isinstance(self.parent.sermon, dict):
                logging.warning(f"parent.sermon is not a dict, type: {type(self.parent.sermon) if hasattr(self.parent, 'sermon') else 'None'}, initializing as dict")
                self.parent.sermon = {}
            if 'verses_notes' not in self.parent.sermon:
                self.parent.sermon['verses_notes'] = []
            title = self.parent.sermon.get('title', 'Unknown Title')
            if isinstance(verse, dict) and 'verse' in verse and 'text' in verse:
                verse_num = str(verse['verse'])
                verse_text = str(verse['text'])
                ref = f"{book} {chapter}:{verse_num}"
            else:
                logging.warning(f"Verse is not a valid dict: {type(verse)}, content: {verse}")
                verse_text = str(verse)
                import re
                match = re.match(r'(\d+)\.\s*(.*)', verse_text)
                if match:
                    verse_num = match.group(1)
                    verse_text = match.group(2)
                    ref = f"{book} {chapter}:{verse_num}"
                else:
                    verse_num = 'Unknown'
                    verse_text = verse_text or 'No text available'
                    ref = f"{book} {chapter}:Unknown"
            note_dict = {
                'ref': ref,
                'text': verse_text,
                'note': ''
            }
            self.parent.sermon['verses_notes'].append(note_dict)
            from PyQt6.QtWidgets import QApplication
            clipboard = QApplication.clipboard()
            clipboard.setText(f"{title} - Verse {verse_num}: {verse_text}")
            if hasattr(self.parent, 'verses_list'):
                self.parent.verses_list.blockSignals(True)
                self.parent.update_verses_list()
                self.parent.verses_list.blockSignals(False)
            logging.debug(f"Copied verse to notes: {ref}")
            QMessageBox.information(self, "Success", "Verse copied to notes and clipboard.")
        except Exception as e:
            logging.error(f"Error in copy_to_notes: {str(e)}")
            QMessageBox.critical(self, "Copy Error", f"Failed to copy verse: {str(e)}")

    def copy_all_to_notes(self):
        """Copy all verses in the current chapter to sermon notes."""
        logging.debug("Starting copy_all_to_notes")
        try:
            if not hasattr(self.parent, 'sermon') or not isinstance(self.parent.sermon, dict):
                logging.warning(f"parent.sermon is not a dict, type: {type(self.parent.sermon) if hasattr(self.parent, 'sermon') else 'None'}, initializing as dict")
                self.parent.sermon = {}
            if 'verses_notes' not in self.parent.sermon:
                self.parent.sermon['verses_notes'] = []
            title = self.parent.sermon.get('title', 'Unknown Title')
            current_book = self.book_combo.currentText()
            current_chapter = self.chapter_combo.currentText()
            all_notes = []
            full_text = []
            for i in range(self.verses_layout.count()):
                item = self.verses_layout.itemAt(i)
                if item and item.widget():
                    h_layout = item.widget().layout()
                    if h_layout:
                        label = h_layout.itemAt(0).widget()
                        if isinstance(label, QLabel):
                            label_text = label.text()
                            import re
                            match = re.match(r'(\d+)\.\s*(.*)', label_text)
                            if match:
                                verse_num = match.group(1)
                                verse_text = match.group(2)
                                ref = f"{current_book} {current_chapter}:{verse_num}"
                                note_dict = {
                                    'ref': ref,
                                    'text': verse_text,
                                    'note': ''
                                }
                                all_notes.append(note_dict)
                                full_text.append(label_text)
                            else:
                                logging.warning(f"Failed to parse label text: {label_text}")
            if not all_notes:
                logging.warning("No verses to copy")
                QMessageBox.warning(self, "No Verses", "No verses available to copy.")
                return
            self.parent.sermon['verses_notes'].extend(all_notes)
            from PyQt6.QtWidgets import QApplication
            clipboard = QApplication.clipboard()
            clipboard.setText("\n".join(full_text))
            if hasattr(self.parent, 'verses_list'):
                self.parent.verses_list.blockSignals(True)
                self.parent.update_verses_list()
                self.parent.verses_list.blockSignals(False)
            logging.debug("Copied all verses to notes and clipboard")
            QMessageBox.information(self, "Success", "All verses copied to notes and clipboard as individual entries.")
        except Exception as e:
            logging.error(f"Error in copy_all_to_notes: {str(e)}")
            QMessageBox.critical(self, "Copy Error", f"Failed to copy verses: {str(e)}")

    def load_initial_chapter(self):
        """Load Genesis 1 by default."""
        logging.debug("Setting up initial book and chapter")
        self.book_combo.setCurrentText("Genesis")
        self.update_chapter_combo()
        self.chapter_combo.setCurrentText("1")
        self.load_chapter()