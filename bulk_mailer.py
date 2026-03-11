import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# -------- EMAIL CONFIG --------
sender_email = input("Enter your Gmail: ")
password = input("Enter your Gmail App Password: ")

subject = input("Enter Email Subject: ")
body = input("Enter Email Body: ")

# -------- FILE INPUT --------
# file_path = input("Enter Excel file path: ")

# Load Excel
df = pd.read_excel("C:\\Projects\\New folder\\marketnow_backend\\Email_Template (7).xlsx")

print("\nColumns in the Excel sheet:")
for i, col in enumerate(df.columns):
    print(f"{i} : {col}")

# Ask for column number
col_number = int(input("\nEnter the column number containing emails: "))

email_list = df.iloc[:, col_number].dropna().tolist()

print(f"\nTotal Emails Found: {len(email_list)}")

# -------- SMTP SETUP --------
server = smtplib.SMTP("smtp.gmail.com", 587)
server.starttls()
server.login(sender_email, password)

# -------- SEND EMAIL --------
for email in email_list:
    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = email
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'plain'))

        server.sendmail(sender_email, email, msg.as_string())

        print(f"Email sent to {email}")

    except Exception as e:
        print(f"Failed to send to {email}: {e}")

server.quit()

print("\nAll emails processed.")