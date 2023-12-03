import yagmail

OFFICIAL_SENDER = "cedric.kuang2002@gmail.com"
USER_EMAIL = "kuang5005@163.com"

# sender secret is required, please ask any group member for it
def send_user_notification(content = "Testing", subject = "Testing"):
    yag = yagmail.SMTP(OFFICIAL_SENDER, oauth2_file="./client_secret.json")
    contents = ['Testing AIPet functionality. By receiving this email it means that it is connected successfully']
    yag.send(USER_EMAIL, 'AIPet: ' + subject, contents)
    return True


if __name__ == "__main__":
    send_user_notification()