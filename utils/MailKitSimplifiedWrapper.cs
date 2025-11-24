using System;
using System.IO;
using System.Threading.Tasks;
using MailKit;
using MailKit.Net.Imap;
using MailKit.Net.Smtp;
using MailKit.Security;

namespace MailKitSimplified
{
    public class MailClient
    {
        private readonly string _email;
        private readonly string _password;
        private readonly string _smtpServer;
        private readonly int _smtpPort;
        private readonly string _imapServer;
        private readonly int _imapPort;

        public MailClient(string email, string password, string smtpServer, int smtpPort, string imapServer, int imapPort)
        {
            _email = email;
            _password = password;
            _smtpServer = smtpServer;
            _smtpPort = smtpPort;
            _imapServer = imapServer;
            _imapPort = imapPort;
        }

        public async Task SendEmailAsync(string to, string subject, string body)
        {
            using var client = new SmtpClient();
            client.ServerCertificateValidationCallback = (s, c, h, e) => true;
            await client.ConnectAsync(_smtpServer, _smtpPort, SecureSocketOptions.Auto);
            await client.AuthenticateAsync(_email, _password);
            var message = new MimeMessage();
            message.From.Add(new MailboxAddress(_email));
            message.To.Add(new MailboxAddress(to));
            message.Subject = subject;
            message.Body = new TextPart("plain")
            {
                Text = body
            };
            await client.SendAsync(message);
            await client.DisconnectAsync(true);
        }

        public async Task<string> GetEmailAsync(int numEmails)
        {
            using var client = new ImapClient();
            client.ServerCertificateValidationCallback = (s, c, h, e) => true;
            await client.ConnectAsync(_imapServer, _imapPort, SecureSocketOptions.Auto);
            await client.AuthenticateAsync(_email, _password);
            var inbox = client.Inbox;
            await inbox.OpenAsync(FolderAccess.ReadOnly);
            var messages = await inbox.FetchAsync(0, numEmails - 1, MessageSummaryItems.UniqueId | MessageSummaryItems.BodyStructure);
            var result = "";
            foreach (var message in messages)
            {
                var body = await inbox.GetBodyPartAsync(message.UniqueId, message.TextBody);
                result += body.Text;
            }
            await client.DisconnectAsync(true);
            return result;
        }
    }
}
