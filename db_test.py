import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email(to_email, subject, body):
    sender_email = "polarpenguin878@gmail.com"
    app_password = "hslskxtigfyibpjh"  # 16-digit password from Google

    # Create message
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    # Send email
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()  # secure the connection
        server.login(sender_email, app_password)
        server.sendmail(sender_email, to_email, msg.as_string())

# Example use:
send_email("polarpenguin878@gmail.com", "Test Email", "This is a test!")