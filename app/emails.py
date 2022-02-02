import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.encoders import encode_base64
from app.loader import load_enviroment


GMAIL_APPLICATION_CREDENTIALS = os.getenv("GMAIL_APPLICATION_CREDENTIALS", None)
GMAIL_ACCOUNT = os.getenv("GMAIL_ACCOUNT", None)


def mail(to, subject, text, attach):

    msg = MIMEMultipart()

    msg["From"] = GMAIL_ACCOUNT
    realToString = ""
    for s in to:
        realToString = realToString + s + ","
    #    print realToString,to, [gmail_user]+[]+to
    msg["To"] = to  # realToString
    msg["Subject"] = subject

    msg.attach(MIMEText(text))

    # attach each file in the list
    if attach:
        for file in attach:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(open(file, "rb").read())
            encode_base64(part)
            part.add_header(
                "Content-Disposition", 'attachment; filename="%s"' % os.path.basename(file)
            )
            msg.attach(part)

    mailServer = smtplib.SMTP("smtp.gmail.com", 587)
    mailServer.ehlo()
    mailServer.starttls()
    mailServer.ehlo()
    mailServer.login(GMAIL_ACCOUNT, GMAIL_APPLICATION_CREDENTIALS)
    mailServer.sendmail(GMAIL_ACCOUNT, [GMAIL_ACCOUNT] + [] + to, msg.as_string())
    # Should be mailServer.quit(), but that crashes...
    mailServer.close()


if __name__ == "__main__":
    to = "andrade.antonio@gmail.com"
    subject = "Test"
    text = "This is a test"
    attach = None
    mail(to, subject, text, attach)
