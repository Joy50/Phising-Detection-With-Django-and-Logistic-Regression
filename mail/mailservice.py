import imaplib
import email
import os
from bs4 import BeautifulSoup
import PyPDF2
import docx
import re

# Connect to the email server (Gmail in this case)
def connect_to_email(username, password, mail_server='imap.gmail.com'):
    mail = imaplib.IMAP4_SSL(mail_server)
    mail.login(username, password)
    return mail

# Fetch the emails
def fetch_emails(mail, folder='inbox'):
    mail.select(folder)
    status, messages = mail.search(None, 'ALL')
    email_ids = messages[0].split()
    return email_ids

# Download the attachments and check for embedded links
def process_attachment(part, save_dir):
    file_name = part.get_filename()
    if file_name:
        file_path = os.path.join(save_dir, file_name)
        
        # Save the attachment
        with open(file_path, 'wb') as f:
            f.write(part.get_payload(decode=True))
        
        print(f"Attachment {file_name} saved to {file_path}")
        
        # Check file type and process
        if file_name.endswith('.pdf'):
            return check_links_in_pdf(file_path)
        elif file_name.endswith('.docx'):
            return check_links_in_docx(file_path)
        # You can add more file types here (e.g., .xlsx for Excel)
    
    return []

# Extract links from PDF files
def check_links_in_pdf(file_path):
    links = []
    with open(file_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text = page.extract_text()
            links.extend(extract_links_from_text(text))
    return links

# Extract links from Word (docx) files
def check_links_in_docx(file_path):
    links = []
    doc = docx.Document(file_path)
    for para in doc.paragraphs:
        links.extend(extract_links_from_text(para.text))
    return links

# Helper function to find links in text using regex
def extract_links_from_text(text):
    # Regex pattern to find URLs
    url_pattern = r'(https?://\S+)'
    return re.findall(url_pattern, text)

# Parse the email and look for attachments
def extract_attachments_and_check_links(raw_email, save_dir):
    email_message = email.message_from_bytes(raw_email)
    all_links = []
    
    for part in email_message.walk():
        if part.get_content_disposition() == 'attachment':
            links_in_attachment = process_attachment(part, save_dir)
            if links_in_attachment:
                print(f"Links found in attachment: {links_in_attachment}")
                all_links.extend(links_in_attachment)
    
    return all_links

# Main function to process all emails
def process_emails(username, password, save_dir='attachments'):
    # Create a directory to save attachments if it doesn't exist
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    mail = connect_to_email(username, password)
    email_ids = fetch_emails(mail)

    for e_id in email_ids:
        status, email_data = mail.fetch(e_id, '(RFC822)')
        for response_part in email_data:
            if isinstance(response_part, tuple):
                raw_email = response_part[1]
                links = extract_attachments_and_check_links(raw_email, save_dir)
                if links:
                    print(f"Found links in email attachments: {links}")
    
    mail.logout()

# Example usage
username = 'your-email@gmail.com'
password = 'your-password'
process_emails(username, password)
