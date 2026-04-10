"""Communication tools: email"""

import os
import smtplib
from email.mime.text import MIMEText

class CommsTools:
    def __init__(self, agent):
        self.agent = agent
    
    def send_email(self, to: str, subject: str, body: str, token: str) -> str:
        """Send an email using SMTP"""
        if not self.agent.broker.validate_and_consume(token, "send_email", to):
            return "Permission denied"
        
        try:
            smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
            smtp_port = int(os.getenv("SMTP_PORT", "587"))
            smtp_user = os.getenv("SMTP_USER")
            smtp_pass = os.getenv("SMTP_PASS")
            
            if not smtp_user or not smtp_pass:
                return "❌ SMTP not configured. Set SMTP_USER and SMTP_PASS in .env"
                
            msg = MIMEText(body)
            msg['Subject'] = subject
            msg['From'] = smtp_user
            msg['To'] = to
            
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)
            
            # Store event in memory
            self.agent.memory.store("email_sent", {"to": to, "subject": subject})
            
            return f"✅ Email sent to {to}"
        except Exception as e:
            return f"❌ Failed to send email: {e}"
