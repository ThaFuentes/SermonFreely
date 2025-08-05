import json
import os
from cryptography.fernet import Fernet
from PyQt6.QtWidgets import QMessageBox
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

JSON_FILE = 'sermon_data.json'

def init_encryption(sermon):
    """Initialize or load the Fernet encryption key."""
    try:
        if 'fernet_key' not in sermon['settings']:
            sermon['settings']['fernet_key'] = Fernet.generate_key().decode()
            logging.debug("Generated new Fernet key")
        return Fernet(sermon['settings']['fernet_key'].encode())
    except Exception as e:
        logging.error(f"Error initializing encryption: {str(e)}")
        raise

def save_sermon(sermon, status_bar):
    """Save sermon to JSON, preserving newlines natively."""
    try:
        data = load_json() if os.path.exists(JSON_FILE) else {}
        data['sermon'] = sermon  # JSON preserves \n natively
        save_json(data)
        status_bar.showMessage("Saved to JSON.", 3000)
        logging.debug("Sermon saved to JSON")
    except Exception as e:
        logging.error(f"Failed to save sermon: {str(e)}")
        status_bar.showMessage(f"Failed to save to JSON: {str(e)}", 5000)

def load_sermon(parent=None):
    """Load the sermon from JSON, preserving newlines."""
    try:
        if not os.path.exists(JSON_FILE):
            logging.debug("No sermon_data.json found, returning default sermon")
            return create_default_sermon()
        data = load_json()
        sermon = data.get('sermon', create_default_sermon())
        logging.debug("Loaded sermon from JSON")
        return sermon
    except Exception as e:
        logging.error(f"Failed to load sermon: {str(e)}")
        if parent:
            parent.statusBar.showMessage(f"Failed to load from JSON: {str(e)}", 5000)
        return create_default_sermon()

def create_default_sermon():
    """Create a default sermon structure."""
    fernet_key = Fernet.generate_key().decode()
    logging.debug("Created default sermon with new Fernet key")
    return {
        'title': '',
        'intro': '',
        'content': '',
        'verses_notes': [],
        'header': {},
        'footer': {},
        'settings': {'default_translation': 'WEB', 'fernet_key': fernet_key}
    }

def clear_sermon_data(parent, sermon):
    """Clear sermon data in memory and JSON."""
    if QMessageBox.question(parent, "Confirm Clear", "Clear all data?") == QMessageBox.StandardButton.Yes:
        sermon.clear()
        sermon.update(create_default_sermon())
        if os.path.exists(JSON_FILE):
            os.remove(JSON_FILE)
            logging.debug("Deleted sermon_data.json")
        parent.refresh_ui()
        parent.statusBar.showMessage("All cleared.", 3000)

def load_json():
    """Load JSON file."""
    try:
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            logging.debug("Loaded JSON file")
            return data
    except Exception as e:
        logging.error(f"Failed to load JSON: {str(e)}")
        raise

def save_json(data):
    """Save JSON file."""
    try:
        with open(JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        logging.debug("Saved JSON file")
    except Exception as e:
        logging.error(f"Failed to save JSON: {str(e)}")
        raise