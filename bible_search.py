import requests
import logging
import sqlite3
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QListWidget, QTextEdit, \
    QMessageBox, QInputDialog
from PyQt6.QtCore import Qt
from bible_utils import REVERSE_BOOK_MAP, parse_ref, fetch_verse_text
import difflib
import re

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

BOOK_VARIANTS = {
    'Genesis': ['Gen', 'Ge', 'Gn'],
    'Exodus': ['Exod', 'Ex'],
    'Leviticus': ['Lev', 'Lv', 'Le'],
    'Numbers': ['Num', 'Nm', 'Nu'],
    'Deuteronomy': ['Deut', 'Dt', 'De', 'Du'],
    'Joshua': ['Josh', 'Jos', 'Jo'],
    'Judges': ['Judg', 'Jdg', 'Jgs'],
    'Ruth': ['Ruth', 'Ru'],
    '1 Samuel': ['1 Sam', '1 Sm', '1 Sa', '1Sam', '1Sa', '1S'],
    '2 Samuel': ['2 Sam', '2 Sm', '2 Sa', '2Sam', '2Sa', '2S'],
    '1 Kings': ['1 Kgs', '1 Kg', '1 Ki', '1Kgs', '1Kin', '1Ki', '1K'],
    '2 Kings': ['2 Kgs', '2 Kg', '2 Ki', '2Kgs', '2Kin', '2Ki', '2K'],
    '1 Chronicles': ['1 Chr', '1 Ch', '1Chron', '1Chr', '1Ch'],
    '2 Chronicles': ['2 Chr', '2 Ch', '2Chron', '2Chr', '2Ch'],
    'Ezra': ['Ezra', 'Ezr', 'Ez'],
    'Nehemiah': ['Neh', 'Ne'],
    'Esther': ['Esth', 'Est', 'Es'],
    'Job': ['Job', 'Jb'],
    'Psalms': ['Ps', 'Pss', 'Pslm', 'Psa', 'Psm'],
    'Proverbs': ['Prov', 'Prv', 'Pr'],
    'Ecclesiastes': ['Eccl', 'Eccles', 'Ec', 'Qoh'],
    'Song of Solomon': ['Song', 'Ss', 'So', 'Sg', 'Cant', 'Can'],
    'Isaiah': ['Isa', 'Is'],
    'Jeremiah': ['Jer', 'Je', 'Jr'],
    'Lamentations': ['Lam', 'La'],
    'Ezekiel': ['Ezek', 'Ezk', 'Ez'],
    'Daniel': ['Dan', 'Dn', 'Da'],
    'Hosea': ['Hos', 'Ho'],
    'Joel': ['Joel', 'Jl'],
    'Amos': ['Amos', 'Am'],
    'Obadiah': ['Obad', 'Ob'],
    'Jonah': ['Jonah', 'Jnh', 'Jon'],
    'Micah': ['Mic', 'Mc'],
    'Nahum': ['Nah', 'Na'],
    'Habakkuk': ['Hab', 'Hb'],
    'Zephaniah': ['Zeph', 'Zep', 'Zp'],
    'Haggai': ['Hag', 'Hg'],
    'Zechariah': ['Zech', 'Zec', 'Zc'],
    'Malachi': ['Mal', 'Ml'],
    'Matthew': ['Matt', 'Mt'],
    'Mark': ['Mark', 'Mrk', 'Mar', 'Mk', 'Mr'],
    'Luke': ['Luke', 'Lk'],
    'John': ['John', 'Jhn', 'Jn', 'Joh'],
    'Acts': ['Acts', 'Act', 'Ac'],
    'Romans': ['Rom', 'Ro', 'Rm'],
    '1 Corinthians': ['1 Cor', '1 Co', '1Cor', '1Co'],
    '2 Corinthians': ['2 Cor', '2 Co', '2Cor', '2Co'],
    'Galatians': ['Gal', 'Ga'],
    'Ephesians': ['Eph', 'Ephes'],
    'Philippians': ['Phil', 'Php', 'Pp'],
    'Colossians': ['Col', 'Co'],
    '1 Thessalonians': ['1 Thess', '1 Thes', '1 Th', '1Thess', '1Thes', '1Th'],
    '2 Thessalonians': ['2 Thess', '2 Thes', '2 Th', '2Thess', '2Thes', '2Th'],
    '1 Timothy': ['1 Tim', '1 Tm', '1 Ti', '1T'],
    '2 Timothy': ['2 Tim', '2 Tm', '2 Ti', '2T'],
    'Titus': ['Titus', 'Tit', 'Ti'],
    'Philemon': ['Phlm', 'Phm'],
    'Hebrews': ['Heb', 'He'],
    'James': ['Jas', 'Ja'],
    '1 Peter': ['1 Pet', '1 Pt', '1P'],
    '2 Peter': ['2 Pet', '2 Pt', '2P'],
    '1 John': ['1 John', '1 Jn', '1 Jo', '1J', '1John', '1Jn', '1Jo'],
    '2 John': ['2 John', '2 Jn', '2 Jo', '2J'],
    '3 John': ['3 John', '3 Jn', '3 Jo', '3J'],
    'Jude': ['Jude', 'Ju'],
    'Revelation': ['Rev', 'Re', 'Rv']
}

VARIANT_TO_FULL = {}
for full, abbrevs in BOOK_VARIANTS.items():
    VARIANT_TO_FULL[full.lower()] = full
    for ab in abbrevs:
        VARIANT_TO_FULL[ab.lower()] = full

class HistoryDialog(QDialog):
    def __init__(self, parent=None, queries=[]):
        super().__init__(parent)
        self.setWindowTitle("Search History")
        self.setMinimumSize(400, 300)
        layout = QVBoxLayout()

        self.history_list = QListWidget()
        for query_id, query, timestamp in queries:
            self.history_list.addItem(f"{query} ({timestamp})")
            self.history_list.item(self.history_list.count() - 1).setData(Qt.ItemDataRole.UserRole, query_id)
        layout.addWidget(self.history_list)

        buttons_layout = QHBoxLayout()
        select_btn = QPushButton("Select")
        select_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(select_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)

        layout.addLayout(buttons_layout)
        self.setLayout(layout)

    def selected_query(self):
        selected_item = self.history_list.currentItem()
        if selected_item:
            return selected_item.text().split(" (")[0]  # Extract query without timestamp
        return None

class BibleSearchDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("Bible Search")
        self.setMinimumSize(600, 400)
        self.init_db()  # Initialize the database
        layout = QVBoxLayout()

        # Search input
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Keyword or Ref (e.g., jhn 3 16, mathew 1 15)")
        self.search_input.setStyleSheet("padding: 5px; font-size: 14px;")
        search_layout.addWidget(QLabel("Search:"))
        search_layout.addWidget(self.search_input)
        search_btn = QPushButton("Search")
        search_btn.setStyleSheet(
            "background-color: #007bff; color: white; border: none; padding: 5px 10px; border-radius: 5px;")
        search_btn.clicked.connect(self.perform_search)
        search_layout.addWidget(search_btn)
        layout.addLayout(search_layout)

        # Search history button
        history_btn = QPushButton("Show Search History")
        history_btn.setStyleSheet(
            "background-color: #28a745; color: white; border: none; padding: 5px 10px; border-radius: 5px;")
        history_btn.clicked.connect(self.show_history)
        layout.addWidget(history_btn)

        # Results list
        self.results_list = QListWidget()
        self.results_list.setStyleSheet("background-color: #2c2f33; color: #ffffff; border: 1px solid #444;")
        layout.addWidget(self.results_list)

        # Verse text display
        self.verse_text = QTextEdit()
        self.verse_text.setReadOnly(True)
        self.verse_text.setStyleSheet(
            "background-color: #2c2f33; color: #ffffff; border: 1px solid #444; padding: 10px;")
        layout.addWidget(self.verse_text)

        # Copy button
        copy_btn = QPushButton("Copy to Verses/Notes")
        copy_btn.setStyleSheet(
            "background-color: #28a745; color: white; border: none; padding: 5px 10px; border-radius: 5px;")
        copy_btn.clicked.connect(self.copy_to_notes)
        layout.addWidget(copy_btn)

        self.setLayout(layout)
        self.results = []
        self.selected_ref = None
        self.selected_text = None
        self.results_list.itemClicked.connect(self.display_verse)

    def init_db(self):
        """Initialize the SQLite database for search history."""
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS search_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
            conn.close()
            logging.debug("Initialized search_history table in DB")
        except Exception as e:
            logging.error(f"Failed to initialize DB: {str(e)}")
            QMessageBox.critical(self, "Database Error", f"Failed to initialize database: {str(e)}")

    def perform_search(self):
        """Handle search input, prioritizing Bible reference parsing, then keyword search."""
        input_text = self.search_input.text().strip()
        if not input_text:
            QMessageBox.warning(self, "Empty Input", "Please enter a reference or keyword.")
            return

        # Save to search history
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute('INSERT INTO search_history (query) VALUES (?)', (input_text,))
            cursor.execute(
                'DELETE FROM search_history WHERE id NOT IN (SELECT id FROM search_history ORDER BY timestamp DESC '
                'LIMIT 10)')
            conn.commit()
            conn.close()
            logging.debug(f"Saved search query to history: {input_text}")
        except Exception as e:
            logging.error(f"Failed to save search history: {str(e)}")
            QMessageBox.critical(self, "Database Error", f"Failed to save search history: {str(e)}")

        translation = self.parent.sermon['settings']['default_translation']
        logging.debug(f"Performing search for: {input_text}, translation: {translation}")

        # Try parsing as a Bible reference first
        try:
            book_id, chapter, verse = parse_ref(input_text)
            ref = f"{REVERSE_BOOK_MAP[book_id]} {chapter}"
            if verse:
                ref += f":{verse}"
            logging.debug(f"Parsed reference: {ref} (book_id: {book_id}, chapter: {chapter}, verse: {verse})")

            # Fetch verse or chapter text
            text = fetch_verse_text(ref, translation)
            if text.startswith("Error") or text == "Verse not found in chapter.":
                logging.warning(f"Failed to fetch text for {ref}: {text}")
                QMessageBox.warning(self, "Fetch Error", f"Could not fetch {ref}: {text}")
                return

            # Display single result
            self.results_list.clear()
            self.results_list.addItem(ref)
            self.results = [{'book': book_id, 'chapter': chapter, 'verse': verse or 1, 'text': text}]
            self.verse_text.setText(text)
            self.selected_ref = ref
            self.selected_text = text
            logging.debug(f"Successfully fetched and displayed: {ref}")
            return
        except ValueError as e:
            logging.debug(f"Input not a valid reference: {e}, attempting fuzzy match")

        # Attempt fuzzy matching for possible misspelled book name
        text = re.sub(r'[^\w\s:]', '', input_text.lower()).strip()
        parts = text.split()
        if parts:
            ref_start = None
            for j in range(len(parts)):
                if re.sub(r'[:\-]', '', parts[j]).isdigit():
                    ref_start = j
                    break
            if ref_start is not None:
                book_cand = ' '.join(parts[:ref_start])
                ref_part = ' '.join(parts[ref_start:])
                chapter = None
                verse = None
                if ':' in ref_part:
                    ch_v = ref_part.split(':', 1)
                    chapter = ch_v[0].strip()
                    verse_str = ch_v[1].strip()
                    if '-' in verse_str:
                        verse = verse_str.split('-')[0]
                    else:
                        verse = verse_str
                else:
                    chapter = ref_part.strip()
                if book_cand and chapter:
                    closest = difflib.get_close_matches(book_cand, list(VARIANT_TO_FULL.keys()), n=1, cutoff=0.6)
                    if closest:
                        corrected_book = VARIANT_TO_FULL[closest[0]]
                        corrected_input = f"{corrected_book} {chapter}"
                        if verse:
                            corrected_input += f":{verse}"
                        logging.debug(f"Attempting corrected reference: {corrected_input}")
                        try:
                            book_id, chapter, verse = parse_ref(corrected_input)
                            ref = f"{REVERSE_BOOK_MAP[book_id]} {chapter}"
                            if verse:
                                ref += f":{verse}"
                            text = fetch_verse_text(ref, translation)
                            if text.startswith("Error") or text == "Verse not found in chapter.":
                                raise ValueError("Fetch failed")
                            self.results_list.clear()
                            self.results_list.addItem(ref)
                            self.results = [{'book': book_id, 'chapter': chapter, 'verse': verse or 1, 'text': text}]
                            self.verse_text.setText(text)
                            self.selected_ref = ref
                            self.selected_text = text
                            logging.debug(f"Successfully used corrected ref: {corrected_input}")
                            return
                        except Exception as ex:
                            logging.debug(f"Corrected parse failed: {ex}")

        # Keyword search
        url = f"https://bolls.life/v2/find/{translation}?search={input_text}&match_case=false&match_whole=false&limit=50"
        try:
            logging.debug(f"Sending keyword search request: {url}")
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()
            self.results = data['results']
            self.results_list.clear()
            for r in self.results:
                book_name = REVERSE_BOOK_MAP.get(r['book'], 'Unknown')
                ref = f"{book_name} {r['chapter']}:{r['verse']}"
                self.results_list.addItem(ref)
            if not self.results:
                QMessageBox.information(self, "No Results", f"No verses found for '{input_text}'.")
            logging.debug(f"Keyword search returned {len(self.results)} results")
        except requests.RequestException as e:
            logging.error(f"Network error during keyword search: {str(e)}")
            QMessageBox.warning(self, "Network Error", f"Failed to search: {str(e)}")
        except Exception as e:
            logging.error(f"Unexpected error during keyword search: {str(e)}")
            QMessageBox.warning(self, "Error", f"Search failed: {str(e)}")

    def display_verse(self, item):
        """Display selected verse text."""
        index = self.results_list.row(item)
        r = self.results[index]
        self.verse_text.setText(r['text'])
        self.selected_ref = item.text()
        self.selected_text = r['text']
        logging.debug(f"Displaying verse: {self.selected_ref}")

    def copy_to_notes(self):
        """Copy selected verse to sermon['verses_notes'] and refresh main GUI."""
        if not self.selected_text or not self.selected_ref:
            QMessageBox.warning(self, "No Selection", "Please select a verse to copy.")
            return

        try:
            if 'verses_notes' not in self.parent.sermon:
                self.parent.sermon['verses_notes'] = []
            note_dict = {
                'ref': self.selected_ref,
                'text': self.selected_text,
                'note': ''
            }
            self.parent.sermon['verses_notes'].append(note_dict)
            self.parent.update_verses_list()
            self.parent.statusBar.showMessage(f"Copied {self.selected_ref} to Verses/Notes.", 3000)
            QMessageBox.information(self, "Copied", f"Copied {self.selected_ref} to Verses/Notes.")
            logging.debug(f"Copied to verses_notes: {self.selected_ref}")
        except Exception as e:
            logging.error(f"Error copying to verses/notes: {str(e)}")
            QMessageBox.critical(self, "Copy Error", f"Failed to copy: {str(e)}")

    def show_history(self):
        """Show recent search queries and allow reuse."""
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute('SELECT id, query, timestamp FROM search_history ORDER BY timestamp DESC LIMIT 10')
            queries = cursor.fetchall()
            conn.close()
            if not queries:
                QMessageBox.information(self, "History", "No search history available.")
                return
            dialog = HistoryDialog(self, queries)
            if dialog.exec():
                selected_query = dialog.selected_query()
                if selected_query:
                    self.search_input.setText(selected_query)
                    self.perform_search()
                    logging.debug(f"Reused search query from history: {selected_query}")
        except Exception as e:
            logging.error(f"Failed to show search history: {str(e)}")
            QMessageBox.critical(self, "History Error", f"Failed to load search history: {str(e)}")