import os
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

# Load explicitly to be sure
load_dotenv('.env')

EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')

print(f"User: {EMAIL_HOST_USER}")

try:
    print("Connecting to SMTP server...")
    server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT, timeout=10)
    server.set_debuglevel(1)
    
    print("Starting TLS...")
    server.starttls()
    
    print("Logging in...")
    server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
    
    print("Sending test email...")
    msg = MIMEText("This is a test email")
    msg['Subject'] = 'Test Email Direct SMTP'
    msg['From'] = EMAIL_HOST_USER
    msg['To'] = EMAIL_HOST_USER
    
    server.send_message(msg)
    server.quit()
    print("Email sent successfully using direct SMTP!")
except Exception as e:
    import traceback
    traceback.print_exc()
