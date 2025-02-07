import smtplib
import ssl
from email.message import EmailMessage
import mimetypes
import os

# Add SSL ( of security)
context = ssl.create_default_context()


def send_email(email_details, subject, body, image_path=None, is_html=False):
    em = EmailMessage()

    em['From'] = email_details["email_sender"]
    em['To'] = email_details["email_receiver"]
    em['Subject'] = subject

    if is_html:
        em.add_alternative(body, subtype='html')

    else:
        email_body = ""
        for line in body:
            email_body += f"{line}\n\n"
        em.set_content(email_body)

    # Attach PDF if provided
    if image_path:
        # Guess the MIME type and subtype
        mime_type, _ = mimetypes.guess_type(image_path)
        mime_type, mime_subtype = mime_type.split('/')

        with open(image_path, 'rb') as pdf_file:
            em.add_attachment(pdf_file.read(),
                              maintype=mime_type,
                              subtype=mime_subtype,
                              filename=os.path.basename(image_path))

    # Log in and send the email
    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
        smtp.login(email_details["email_sender"], email_details["email_password"])
        smtp.sendmail(email_details["email_sender"], email_details["email_receiver"], em.as_string())
