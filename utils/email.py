import smtplib
import imaplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class Mail:
	def __init__(self, email, password, smtp_server, smtp_port):
		self.email = email
		self.password = password
		self.smtp_server = smtp_server
		self.smtp_port = smtp_port

	def send_email(self, to, subject, body):
		msg = MIMEMultipart()
		msg['From'] = self.email
		msg['To'] = to
		msg['Subject'] = subject
		msg.attach(MIMEText(body, 'plain'))

		try:
			server = smtplib.SMTP(self.smtp_server, self.smtp_port)
			server.starttls()
			server.login(self.email, self.password)
			server.sendmail(self.email, to, msg.as_string())
			server.quit()
			print("Email sent successfully!")
		except Exception as e:
			print("Failed to send email:", str(e))

	def read_emails(self, num_emails=10):
		try:
			server = imaplib.IMAP4_SSL(self.smtp_server)
			server.login(self.email, self.password)
			server.select('INBOX')
			_, data = server.search(None, 'ALL')
			email_ids = data[0].split()

			if num_emails:
				num_emails = min(num_emails, len(email_ids))
			else:
				num_emails =  len(email_ids)

			emails = []

			for i in range(num_emails):
				_, data = server.fetch(email_ids[i], '(FLAGS RFC822)')
				msg_flags = email.message_from_bytes(data[0][0]).get_flags()
				raw_email = data[0][1].decode('utf-8')
				emails.append({'msg_flags':msg_flags, 'raw_email':raw_email})

			server.logout()
			return emails
		except Exception as e:
			raise Exception(f"Failed to read emails: {str(e)}")

 
# mail_client = Mail(email, password, smtp_server, smtp_port)

# # Send an email
# mail_client.send_email('recipient@example.com', 'Test Subject', 'This is the email body.')

# # Read emails
# mail_client.read_emails(num_emails=5)  # Replace 5 with the number of emails to read
