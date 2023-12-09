import smtplib
import ssl

def send_simple_email(to, subject, body):
    #Your SMTP server
    host = "smtp.gmail.com"
    port = 465

    #Your credentials
    login = "seaweedtest@gmail.com"
    password = "ysjw yjli vgpm khat"

    #Build your email
    context = ssl.create_default_context()

    email = f"""Subject: {subject}
To: {to}
From: {login}
{body}"""

    #Send email
    with smtplib.SMTP_SSL(host, port, context=context) as server:
        server.login(login, password)
        server.sendmail(login, to, email)
        
#send_simple_email("zhenbruin20@g.ucla.edu","Hello there","How are you doing?")
