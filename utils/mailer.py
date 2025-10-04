import os
import smtplib
from email.message import EmailMessage
from typing import Optional


def send_email(to_email: str, subject: str, body_text: str, body_html: Optional[str] = None) -> bool:
    """Send an email using SMTP configuration from environment variables.

    Environment variables expected:
      SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, FROM_EMAIL

    Returns True on success, False on error (prints the error).
    """
    host = os.environ.get('SMTP_HOST')
    port = os.environ.get('SMTP_PORT')
    user = os.environ.get('SMTP_USER')
    password = os.environ.get('SMTP_PASS')
    from_email = os.environ.get('FROM_EMAIL') or user

    if not host or not port:
        print('SMTP not configured (SMTP_HOST/SMTP_PORT missing). Email would be:' )
        print('To:', to_email)
        print('Subject:', subject)
        print('Body:', body_text)
        return False

    try:
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = from_email
        msg['To'] = to_email
        msg.set_content(body_text)
        if body_html:
            msg.add_alternative(body_html, subtype='html')

        port_int = int(port)
        # Use SSL if port is 465, otherwise try STARTTLS
        if port_int == 465:
            with smtplib.SMTP_SSL(host, port_int) as smtp:
                if user and password:
                    smtp.login(user, password)
                smtp.send_message(msg)
        else:
            with smtplib.SMTP(host, port_int) as smtp:
                smtp.ehlo()
                try:
                    smtp.starttls()
                except Exception:
                    pass
                if user and password:
                    smtp.login(user, password)
                smtp.send_message(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False
