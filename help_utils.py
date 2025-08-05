from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit, QLabel
from PyQt6.QtCore import Qt
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


class HelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sermon Freely Help")
        self.setMinimumSize(600, 400)
        layout = QVBoxLayout()

        # Instruction label
        layout.addWidget(QLabel("Select a help topic:"))

        # Buttons for topics
        btn_layout = QHBoxLayout()
        ops_btn = QPushButton("How to Operate")
        ops_btn.clicked.connect(lambda: self.show_topic("operate"))
        btn_layout.addWidget(ops_btn)
        gemini_btn = QPushButton("Create Gemini API Key")
        gemini_btn.clicked.connect(lambda: self.show_topic("gemini"))
        btn_layout.addWidget(gemini_btn)
        support_btn = QPushButton("Help and Support")
        support_btn.clicked.connect(lambda: self.show_topic("support"))
        btn_layout.addWidget(support_btn)
        layout.addLayout(btn_layout)

        # Text display
        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)
        self.text_display.setStyleSheet(
            "background-color: #2c2f33; color: #ffffff; border: 1px solid #444; padding: 10px;")
        layout.addWidget(self.text_display)

        self.setLayout(layout)
        self.show_topic("operate")  # Show operation instructions by default

    def show_topic(self, topic):
        """Display help content for the selected topic."""
        logging.debug(f"Displaying help topic: {topic}")
        if topic == "operate":
            content = """
            <h1>How to Operate Sermon Freely</h1>
            <p><b>Overview:</b> Sermon Freely is a tool for creating and managing sermons, with features for Bible verse lookup, note-taking, and AI assistance via Gemini.</p>
            <h2>Key Features</h2>
            <ul>
                <li><b>Title, Intro, Content Tabs:</b> Enter your sermon title, introduction, and main content in the respective tabs. Click "Save" buttons to update the sermon data.</li>
                <li><b>Verses & Notes Tab:</b>
                    <ul>
                        <li>Add verses or notes manually or via Bible Search.</li>
                        <li>Edit or delete selected verses/notes using the buttons.</li>
                        <li>Copy verses to sermon content for inclusion in your sermon.</li>
                    </ul>
                </li>
                <li><b>Bible Search (Tools > Bible Search):</b>
                    <ul>
                        <li>Enter a reference (e.g., "jhn 3 16" or "John 3:16") or keyword (e.g., "love").</li>
                        <li>Select a result and click "Copy to Verses/Notes" to add it to your sermon.</li>
                    </ul>
                </li>
                <li><b>Read Bible (Tools > Read Bible):</b> Browse Bible books and chapters, copy verses to notes.</li>
                <li><b>Gemini Chat (Tools > Gemini Chat):</b> Use AI to generate sermon ideas or verse suggestions (requires API key).</li>
                <li><b>Settings:</b> Set default Bible translation (e.g., WEB, KJV) and Gemini API key.</li>
                <li><b>Quick Save/Load:</b> Save your sermon to the database with File > Quick Save. Load the last saved sermon with File > Quick Load.</li>
                <li><b>Clear All:</b> Reset all sermon data to empty (File > Clear All).</li>
                <li><b>Save to Word:</b> Export your sermon to a Word document (File > Export to Word...).</li>
            </ul>
            <h2>Usage Tips</h2>
            <ul>
                <li>Save frequently using Quick Save to preserve your work.</li>
                <li>Use Bible Search for quick verse lookup with flexible references (e.g., "mathew 1 15").</li>
                <li>Ensure a valid Gemini API key for AI features.</li>
            </ul>
            """
        elif topic == "gemini":
            content = """
            <h1>How to Create a Gemini API Key</h1>
            <p>Sermon Freely uses the Gemini AI model for sermon assistance. You need a Gemini API key to use the Gemini Chat feature.</p>
            <h2>Steps to Obtain a Gemini API Key</h2>
            <ol>
                <li>Visit the <a href='https://ai.google.dev/'>Google AI Studio</a>[](https://ai.google.dev/).</li>
                <li>Sign in with your Google account or create one if you don't have an account.</li>
                <li>In Google AI Studio, navigate to the API key section (usually under "Get API key" or similar).</li>
                <li>Click "Create API Key" or follow prompts to generate a key for the Gemini model.</li>
                <li>Copy the generated API key (a long string of characters).</li>
                <li>In Sermon Freely, go to Settings > Open Settings.</li>
                <li>Paste the API key into the "Gemini API Key" field and click OK.</li>
            </ol>
            <h2>Notes</h2>
            <ul>
                <li>Keep your API key secure; do not share it publicly.</li>
                <li>Check your Google Cloud project for API usage limits or billing requirements.</li>
                <li>If you encounter issues, ensure the key is valid and not expired. Visit https://ai.google.dev/ for troubleshooting.</li>
            </ul>
            """
        else:  # support
            content = """
            <h1>Help and Support</h1>
            <p>If you encounter issues with Sermon Freely, use the following resources:</p>
            <h2>License and Usage</h2>
            <p><b>Sermon Freely is free software and not for resale.</b> It is provided at no cost for personal and non-commercial use under the MIT License.</p>
            <h3>MIT License</h3>
            <p>Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:</p>
            <p>The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.</p>
            <p>THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.</p>
            <h2>Troubleshooting</h2>
            <ul>
                <li><b>App Crashes:</b> Check sermon.log in the application directory for error details.</li>
                <li><b>Bible Search Fails:</b> Ensure internet connectivity and try a different translation in Settings.</li>
                <li><b>Gemini Chat Errors:</b> Verify your API key in Settings and ensure it’s valid (see "Create Gemini API Key").</li>
                <li><b>Database Issues:</b> If saves/loads fail, delete sermon_secrets.db and restart the app to reinitialize.</li>
            </ul>
            <h2>Contact Support</h2>
            <ul>
                <li><b>Google AI Support:</b> For Gemini API issues, visit https://ai.google.dev/ or check Google Cloud support.</li>
                <li><b>General Inquiries:</b> Use community forums or support channels listed at https://ai.google.dev/.</li>
            </ul>
            <h2>Additional Resources</h2>
            <ul>
                <li>Visit https://ai.google.dev/ for Gemini API documentation and updates.</li>
                <li>Review sermon.log for detailed error messages.</li>
            </ul>
            """
        self.text_display.setHtml(content)
        logging.debug(f"Displayed help content for {topic}")