SermonFreely
SermonFreely is a free, open-source desktop application designed to assist pastors and ministers in preparing sermons. Built with PyQt6, it provides tools for Bible verse lookup, note-taking, sermon organization, and AI-assisted sermon preparation using the Gemini API. The application allows users to create, save, and export sermons to Word documents, with a focus on ease of use and theological accuracy.
Features

Bible Search: Look up Bible verses by reference (e.g., "John 3:16") or keyword, with support for fuzzy matching of book names and multiple translations (e.g., KJV, WEB, NKJV). Verses can be copied to sermon notes.
Bible Reading: Browse and read Bible chapters, with navigation by book and chapter, and copy verses to notes.
Sermon Management: Organize sermons with dedicated tabs for title, introduction, content, and verses/notes. Save sermons to a local JSON file (sermon_data.json).
Gemini AI Integration: Use the Gemini API to generate sermon ideas, verse suggestions, or thematic insights. Supports multiple API keys for flexibility.
Export to Word: Export sermons to .docx files with customizable headers and footers, including fields like name, church, and email.
Notes and Verses: Add, edit, and sort verses or custom notes, with options to copy them to sermon content.
Settings: Configure default Bible translations and manage Gemini API keys stored in an encrypted SQLite database (sermon_secrets.db).
Help and Support: Access built-in help for operation, Gemini API setup, and troubleshooting, including the MIT License details.

Installation
Prerequisites

Python 3.8+: Download from python.org.
Git: Install from git-scm.com to clone the repository.
Dependencies: Listed in requirements.txt (see below).

Steps

Clone the Repository:
git clone https://github.com/ThaFuentes/SermonFreely.git
cd SermonFreely


Install Dependencies:Create a virtual environment and install required packages:
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

Required packages:

PyQt6
requests
python-docx
cryptography
google-generativeai


Obtain a Gemini API Key:

Go to Google AI Studio, sign in, and generate an API key.
In the application, go to Settings > Gemini API and Bible Version, and add your key.


Run the Application:
python main.py



Usage

Launch the Application:Run python main.py to open the SermonFreely window.

Create a Sermon:

Title Tab: Enter and save the sermon title.
Intro Tab: Write and save the introduction.
Content Tab: Draft the main sermon content.
Verses & Notes Tab: Add verses via Bible Search or manually, edit/delete notes, and copy to content.
Preview Tab: View a formatted preview of the sermon.


Bible Features:

Read Bible (Tools > Read Bible): Browse books and chapters, copy verses to notes.
Bible Search (Tools > Bible Search): Search by reference (e.g., "jhn 3 16") or keyword (e.g., "love"), and copy results to notes.


Gemini AI Assistance:

Go to Tools > Gemini Chat or use the Quick Gemini Research in the Verses/Notes dialog.
Enter queries (e.g., "Suggest verses on faith") to get AI-generated suggestions.


Export and Save:

Save sermons to sermon_data.json via File > Quick Save.
Export to Word via File > Save to Word....
Set headers/footers via Settings > Set Header/Set Footer.


Settings:

Choose a default Bible translation (e.g., WEB, KJV).
Add/remove Gemini API keys in Settings > Gemini API and Bible Version.


Help:

Access Help > How to Operate, Create Gemini API Key, or Help and Support for guidance.



Security Notes

Gemini API Keys: Stored in sermon_secrets.db (encrypted SQLite database). Keep this file secure and never share it publicly.
Sensitive Data: Ensure sermon_secrets.db and sermon_data.json are excluded from version control. The provided .gitignore already includes these files.
API Key Safety: If a Gemini API key is exposed, revoke it immediately via Google Cloud and generate a new one.

Troubleshooting

App Crashes: Check sermon.log in the project directory for error details.
Bible Search Fails: Verify internet connectivity and try a different translation in Settings.
Gemini Chat Errors: Ensure a valid API key is set in Settings. Check Google AI Studio for API issues.
Database Issues: If saves/loads fail, delete sermon_secrets.db and restart the app to reinitialize.

License
SermonFreely is free software provided under the MIT License with an additional non-commercial clause. You may use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the software, but you may not charge others for the program or its use. The software is provided "as is," without warranty of any kind.
MIT License with Non-Commercial Clause
Copyright (c) 2025 ThaFuentes
Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The Software may not be sold, nor may it be used in a commercial product or service where a fee is charged for the use of the Software itself.
The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
Support
For issues or inquiries:

Check sermon.log for error details.
Visit Google AI Studio for Gemini API support.
Contact community forums or support channels listed at Google AI Studio.
