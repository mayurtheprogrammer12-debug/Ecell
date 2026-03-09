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
    
    print("Success on port 465!")
    server.quit()
except Exception as e:
    import traceback
    traceback.print_exc()
