# bible_utils.py
# Contains Bible data structures and utility functions for parsing and fetching verses.

import requests
import re
import logging
import sys

# Set up logging to console and file
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sermon.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

BOOK_MAP = {
    "Genesis": 1,
    "Exodus": 2,
    "Leviticus": 3,
    "Numbers": 4,
    "Deuteronomy": 5,
    "Joshua": 6,
    "Judges": 7,
    "Ruth": 8,
    "1 Samuel": 9,
    "2 Samuel": 10,
    "1 Kings": 11,
    "2 Kings": 12,
    "1 Chronicles": 13,
    "2 Chronicles": 14,
    "Ezra": 15,
    "Nehemiah": 16,
    "Esther": 17,
    "Job": 18,
    "Psalms": 19,
    "Proverbs": 20,
    "Ecclesiastes": 21,
    "Song of Solomon": 22,
    "Isaiah": 23,
    "Jeremiah": 24,
    "Lamentations": 25,
    "Ezekiel": 26,
    "Daniel": 27,
    "Hosea": 28,
    "Joel": 29,
    "Amos": 30,
    "Obadiah": 31,
    "Jonah": 32,
    "Micah": 33,
    "Nahum": 34,
    "Habakkuk": 35,
    "Zephaniah": 36,
    "Haggai": 37,
    "Zechariah": 38,
    "Malachi": 39,
    "Matthew": 40,
    "Mark": 41,
    "Luke": 42,
    "John": 43,
    "Acts": 44,
    "Romans": 45,
    "1 Corinthians": 46,
    "2 Corinthians": 47,
    "Galatians": 48,
    "Ephesians": 49,
    "Philippians": 50,
    "Colossions": 51,
    "1 Thessalonians": 52,
    "2 Thessalonians": 53,
    "1 Timothy": 54,
    "2 Timothy": 55,
    "Titus": 56,
    "Philemon": 57,
    "Hebrews": 58,
    "James": 59,
    "1 Peter": 60,
    "2 Peter": 61,
    "1 John": 62,
    "2 John": 63,
    "3 John": 64,
    "Jude": 65,
    "Revelation": 66
}

REVERSE_BOOK_MAP = {v: k for k, v in BOOK_MAP.items()}

BOOK_CHAPTERS = {
    "Genesis": 50,
    "Exodus": 40,
    "Leviticus": 27,
    "Numbers": 36,
    "Deuteronomy": 34,
    "Joshua": 24,
    "Judges": 21,
    "Ruth": 4,
    "1 Samuel": 31,
    "2 Samuel": 24,
    "1 Kings": 22,
    "2 Kings": 25,
    "1 Chronicles": 29,
    "2 Chronicles": 36,
    "Ezra": 10,
    "Nehemiah": 13,
    "Esther": 10,
    "Job": 42,
    "Psalms": 150,
    "Proverbs": 31,
    "Ecclesiastes": 12,
    "Song of Solomon": 8,
    "Isaiah": 66,
    "Jeremiah": 52,
    "Lamentations": 5,
    "Ezekiel": 48,
    "Daniel": 12,
    "Hosea": 14,
    "Joel": 3,
    "Amos": 9,
    "Obadiah": 1,
    "Jonah": 4,
    "Micah": 7,
    "Nahum": 3,
    "Habakkuk": 3,
    "Zephaniah": 3,
    "Haggai": 2,
    "Zechariah": 14,
    "Malachi": 4,
    "Matthew": 28,
    "Mark": 16,
    "Luke": 24,
    "John": 21,
    "Acts": 28,
    "Romans": 16,
    "1 Corinthians": 16,
    "2 Corinthians": 13,
    "Galatians": 6,
    "Ephesians": 6,
    "Philippians": 4,
    "Colossions": 4,
    "1 Thessalonians": 5,
    "2 Thessalonians": 3,
    "1 Timothy": 6,
    "2 Timothy": 4,
    "Titus": 3,
    "Philemon": 1,
    "Hebrews": 13,
    "James": 5,
    "1 Peter": 5,
    "2 Peter": 3,
    "1 John": 5,
    "2 John": 1,
    "3 John": 1,
    "Jude": 1,
    "Revelation": 22
}

def parse_ref(ref):
    ref = ref.strip()
    match = re.match(r'(\d*\s*[a-zA-Z ]+) (\d+)(:(\d+))?', ref, re.I)
    if not match:
        raise ValueError("Invalid reference. Use e.g., John 3 or John 3:16")
    book_str = match.group(1).strip().title()
    chapter = int(match.group(2))
    verse = int(match.group(4)) if match.group(4) else None
    if book_str in BOOK_MAP:
        book_id = BOOK_MAP[book_str]
    else:
        match_num = re.match(r'(\d)(\w+)', book_str)
        if match_num:
            book_str = match_num.group(1) + ' ' + match_num.group(2)
            book_str = book_str.title()
        book_id = BOOK_MAP.get(book_str)
    if not book_id:
        raise ValueError("Unknown book name.")
    return book_id, chapter, verse

def fetch_verse_text(ref, translation):
    try:
        logging.debug(f"Fetching verse text for {ref} with translation {translation}")
        book_id, chapter, verse = parse_ref(ref)
        url = f"https://bolls.life/get-text/{translation}/{book_id}/{chapter}/"
        logging.debug(f"Requesting URL: {url}")
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        if verse is None:
            text = '\n'.join(f"{v['verse']}. {v['text']}" for v in data)
        else:
            text = None
            for v in data:
                if v['verse'] == verse:
                    text = v['text']
                    break
            if text is None:
                text = "Verse not found in chapter."
        logging.debug(f"Successfully fetched text: {text[:50]}...")
        return text
    except requests.RequestException as e:
        logging.error(f"Network error fetching verse text: {str(e)}")
        return f"Network error: {str(e)}"
    except Exception as e:
        logging.error(f"Error fetching verse text: {str(e)}")
        return f"Error fetching: {str(e)}"