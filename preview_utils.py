# preview_utils.py

def preview_all(preview_text, sermon):
    # Helper function to format header/footer as HTML, only including non-empty fields
    def format_header_footer(data):
        fields = [
            f"Name: {data['name']}" if data.get('name') else None,
            f"Church: {data['church']}" if data.get('church') else None,
            f"Organization: {data['organization']}" if data.get('organization') else None,
            f"Email: {data['email']}" if data.get('email') else None,
            f"Phone: {data['phone']}" if data.get('phone') else None,
            f"Website: {data['website']}" if data.get('website') else None,
            f"Additional Info: {data['additional']}" if data.get('additional') else None
        ]
        formatted_text = '<br>'.join(field for field in fields if field)
        return formatted_text

    intro_html = sermon['intro'].replace('\n', '<br/>')
    content_html = sermon['content'].replace('\n', '<br/>')
    header_html = format_header_footer(sermon.get('header', {}))
    footer_html = format_header_footer(sermon.get('footer', {}))

    preview = f"<h1>{sermon['title']}</h1>\n"
    preview += f"<h2>Introduction</h2><p>{intro_html}</p>\n"
    preview += f"<h2>Content</h2><p>{content_html}</p>\n"
    preview += "<h2>Verses and Notes</h2>\n"
    for vn in sermon['verses_notes']:
        text_html = vn['text'].replace('\n', '<br/>')
        note_html = vn['note'].replace('\n', '<br/>')
        preview += f"<b>{vn['ref']}:</b> {text_html}<br>Note: {note_html}<br><br>\n"
    if header_html:
        preview += f"<i>Header:<br>{header_html}</i><br>"
    if footer_html:
        preview += f"<i>Footer:<br>{footer_html}</i>"
    preview_text.setHtml(preview)