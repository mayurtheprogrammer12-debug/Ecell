import smtplib
from dotenv import load_dotenv
import os

load_dotenv('.env')

EMAIL_HOST = 'mail.ennovatex26.in'
EMAIL_PORT = 465
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')

try:
    print(f"Connecting to {EMAIL_HOST} on port {EMAIL_PORT} with SSL...")
    server = smtplib.SMTP_SSL(EMAIL_HOST, EMAIL_PORT, timeout=10)
    server.set_debuglevel(1)
    
    print("Logging in...")
    server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
    
    print("Success on port 465! Now sending test email...")
    
    from email.mime.text import MIMEText
    msg = MIMEText("This is a live test email from the ECell Website.")
    msg['Subject'] = 'Live SMTP Test Successful'
    msg['From'] = EMAIL_HOST_USER
    msg['To'] = EMAIL_HOST_USER
    
    server.send_message(msg)
    print(f"Test email sent to {EMAIL_HOST_USER}!")
    server.quit()
except Exception as e:
    import traceback
    traceback.print_exc()
