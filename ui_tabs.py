from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QTextEdit, QPushButton, QListWidget, QHBoxLayout
from PyQt6.QtGui import QTextOption
from PyQt6.QtCore import Qt


def create_title_tab(initial_text, save_callback):
    tab = QWidget()
    layout = QVBoxLayout()
    title_label = QLabel(f"Sermon Title: {initial_text}")
    title_label.setStyleSheet("font-weight: bold; font-size: 16px;")
    layout.addWidget(title_label)
    edit_layout = QHBoxLayout()
    edit_layout.addWidget(QLabel("Edit Title:"))
    edit = QLineEdit(initial_text)
    edit.setStyleSheet("font-size: 14px; padding: 5px;")
    edit_layout.addWidget(edit)
    layout.addLayout(edit_layout)
    btn = QPushButton("Save Title")
    btn.setStyleSheet(
        "background-color: #007bff; color: white; border: none; padding: 4px 8px; border-radius: 4px; font-size: 12px;")
    btn.clicked.connect(lambda: save_and_update_label(edit.text().strip(), save_callback, title_label))
    layout.addWidget(btn)
    tab.setLayout(layout)
    return tab, edit


def save_and_update_label(new_text, save_callback, label):
    save_callback()
    label.setText(f"Sermon Title: {new_text}")


def create_intro_tab(initial_text, save_callback):
    tab = QWidget()
    layout = QVBoxLayout()
    edit = QTextEdit()
    edit.setPlainText(initial_text.replace('\r\n', '\n').replace('\r', '\n'))  # Normalize line endings
    edit.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
    edit.setWordWrapMode(QTextOption.WrapMode.WordWrap)
    edit.setAcceptRichText(False)
    edit.setStyleSheet(
        "font-size: 14px; padding: 5px; background-color: #2c2f33; color: #ffffff; border: 1px solid #444;")
    layout.addWidget(QLabel("Introduction:"))
    layout.addWidget(edit)
    btn = QPushButton("Save Intro")
    btn.setStyleSheet(
        "background-color: #007bff; color: white; border: none; padding: 4px 8px; border-radius: 4px; font-size: 12px;")
    btn.clicked.connect(save_callback)
    layout.addWidget(btn)
    tab.setLayout(layout)
    return tab, edit


def create_content_tab(initial_text, save_callback):
    tab = QWidget()
    layout = QVBoxLayout()
    edit = QTextEdit()
    edit.setPlainText(initial_text.replace('\r\n', '\n').replace('\r', '\n'))  # Normalize line endings
    edit.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
    edit.setWordWrapMode(QTextOption.WrapMode.WordWrap)
    edit.setAcceptRichText(False)
    edit.setStyleSheet(
        "font-size: 14px; padding: 5px; background-color: #2c2f33; color: #ffffff; border: 1px solid #444;")
    layout.addWidget(QLabel("Sermon Content:"))
    layout.addWidget(edit)
    btn = QPushButton("Save Content")
    btn.setStyleSheet(
        "background-color: #007bff; color: white; border: none; padding: 4px 8px; border-radius: 4px; font-size: 12px;")
    btn.clicked.connect(save_callback)
    layout.addWidget(btn)
    tab.setLayout(layout)
    return tab, edit


def create_verses_tab(add_callback, edit_callback, delete_callback, copy_to_sermon_callback, sort_callback,
                      copy_all_callback):
    tab = QWidget()
    layout = QVBoxLayout()
    verses_list = QListWidget()
    layout.addWidget(QLabel("Bible Verses and Notes:"))
    layout.addWidget(verses_list)

    # Create two rows of buttons
    buttons_row1 = QHBoxLayout()
    buttons_row2 = QHBoxLayout()

    add_btn = QPushButton("Add Verse/Note")
    add_btn.setStyleSheet(
        "background-color: #007bff; color: white; border: none; padding: 4px 8px; border-radius: 4px; font-size: 12px;")
    add_btn.clicked.connect(add_callback)
    buttons_row1.addWidget(add_btn)

    edit_btn = QPushButton("Edit")
    edit_btn.setStyleSheet(
        "background-color: #007bff; color: white; border: none; padding: 4px 8px; border-radius: 4px; font-size: 12px;")
    edit_btn.clicked.connect(edit_callback)
    buttons_row1.addWidget(edit_btn)

    delete_btn = QPushButton("Delete")
    delete_btn.setStyleSheet(
        "background-color: #dc3545; color: white; border: none; padding: 4px 8px; border-radius: 4px; font-size: 12px;")
    delete_btn.clicked.connect(delete_callback)
    buttons_row1.addWidget(delete_btn)

    copy_all_btn = QPushButton("Copy All Notes/Verses to Sermon Content")
    copy_all_btn.setStyleSheet(
        "background-color: #007bff; color: white; border: none; padding: 4px 8px; border-radius: 4px; font-size: 12px;")
    copy_all_btn.clicked.connect(copy_all_callback)
    buttons_row2.addWidget(copy_all_btn)

    copy_selected_btn = QPushButton("Copy Selected")
    copy_selected_btn.setStyleSheet(
        "background-color: #007bff; color: white; border: none; padding: 4px 8px; border-radius: 4px; font-size: 12px;")
    copy_selected_btn.clicked.connect(copy_to_sermon_callback)
    buttons_row2.addWidget(copy_selected_btn)

    sort_btn = QPushButton("Sort By: Reference")
    sort_btn.setStyleSheet(
        "background-color: #17a2b8; color: white; border: none; padding: 4px 8px; border-radius: 4px; font-size: 12px;")
    sort_btn.clicked.connect(lambda: sort_callback(sort_btn))
    buttons_row2.addWidget(sort_btn)

    layout.addLayout(buttons_row1)
    layout.addLayout(buttons_row2)
    tab.setLayout(layout)
    return tab, verses_list


def create_preview_tab(refresh_callback):
    tab = QWidget()
    layout = QVBoxLayout()
    text_edit = QTextEdit()
    text_edit.setReadOnly(True)
    text_edit.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
    text_edit.setWordWrapMode(QTextOption.WrapMode.WordWrap)
    text_edit.setStyleSheet(
        "font-size: 14px; padding: 5px; background-color: #2c2f33; color: #ffffff; border: 1px solid #444;")
    layout.addWidget(text_edit)
    btn = QPushButton("Refresh Preview")
    btn.setStyleSheet(
        "background-color: #007bff; color: white; border: none; padding: 4px 8px; border-radius: 4px; font-size: 12px;")
    btn.clicked.connect(refresh_callback)
    layout.addWidget(btn)
    tab.setLayout(layout)
    return tab, text_edit