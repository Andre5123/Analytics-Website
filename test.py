import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import os
from dotenv import load_dotenv

def send_email(to_email, subject, body):
    # Your email credentials
    from_email = os.getenv("SMTP_EMAIL")
    password = os.getenv("SMTP_PASSWORD")

    # Create message
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    # Connect to SMTP server
    server = smtplib.SMTP("smtp.gmail.com", 587)  # 587 is common for TLS
    server.starttls()  # Secure connection
    server.login(from_email, password)
    server.send_message(msg)
    server.quit()

print("jss do it")
send_email("polarpenguin878@gmail.com", "test", "This is some text")