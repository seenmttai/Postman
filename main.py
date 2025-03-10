import os
import csv
import smtplib
import argparse
import getpass
import time
import random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from string import Template
import logging
import json
from datetime import datetime

class ClubEmailSender:
    def __init__(self, config_file=None):
        self.config = {
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "from_email": "",
            "rate_limit": 20,
            "delay_range": [30, 90],
            "log_file": "email_log.txt"
        }
        
        if config_file and os.path.exists(config_file):
            self.load_config(config_file)
            
        logging.basicConfig(
            filename=self.config["log_file"],
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger("ClubEmailSender")
        
        self.sent_count = 0
        self.start_time = datetime.now()
    
    def load_config(self, config_file):
        try:
            with open(config_file, 'r') as f:
                user_config = json.load(f)
                self.config.update(user_config)
            print(f"Loaded configuration from {config_file}")
        except Exception as e:
            print(f"Error loading config file: {e}")
    
    def save_config(self, config_file):
        try:
            save_config = {k: v for k, v in self.config.items() if k != 'password'}
            with open(config_file, 'w') as f:
                json.dump(save_config, f, indent=2)
            print(f"Configuration saved to {config_file}")
        except Exception as e:
            print(f"Error saving config file: {e}")
    
    def read_csv_data(self, csv_file):
        recipients = []
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    recipients.append(row)
            print(f"Loaded {len(recipients)} recipients from {csv_file}")
            return recipients
        except Exception as e:
            self.logger.error(f"Error reading CSV file: {e}")
            print(f"Error reading CSV file: {e}")
            return []
    
    def load_template(self, template_file):
        try:
            with open(template_file, 'r', encoding='utf-8') as f:
                return Template(f.read())
        except Exception as e:
            self.logger.error(f"Error loading template file: {e}")
            print(f"Error loading template file: {e}")
            return None
    
    def personalize_email(self, template, recipient_data):
        try:
            return template.substitute(**recipient_data)
        except KeyError as e:
            self.logger.warning(f"Missing field in data: {e}")
            print(f"Warning: Missing field in recipient data: {e}")
            return template.safe_substitute(**recipient_data)
    
    def create_email(self, recipient, subject, content, attachments=None):
        msg = MIMEMultipart()
        msg['From'] = self.config['from_email']
        msg['To'] = recipient['email']
        msg['Subject'] = subject
        
        msg.attach(MIMEText(content, 'html'))
        
        if attachments:
            for file_path in attachments:
                try:
                    with open(file_path, 'rb') as file:
                        attachment = MIMEApplication(file.read(), Name=os.path.basename(file_path))
                    attachment['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
                    msg.attach(attachment)
                except Exception as e:
                    self.logger.error(f"Error attaching file {file_path}: {e}")
                    print(f"Error attaching file {file_path}: {e}")
        
        return msg
    
    def rate_limit_check(self):
        current_time = datetime.now()
        elapsed_hours = (current_time - self.start_time).total_seconds() / 3600
        
        if elapsed_hours > 0 and self.sent_count / elapsed_hours > self.config['rate_limit']:
            wait_time = 30 #3600 / self.config['rate_limit']
            print(f"Rate limit reached. Waiting {wait_time:.1f} seconds...")
            self.logger.info(f"Rate limit reached. Waiting {wait_time:.1f} seconds")
            time.sleep(wait_time)
        
        delay = random.randint(self.config['delay_range'][0], self.config['delay_range'][1])
        time.sleep(delay)
    
    def send_emails(self, recipients, subject_template, email_template, test_mode=False, 
                   attachments=None, limit=None, skip=0):
        if not recipients:
            print("No recipients to email")
            return

        server = None
        if not test_mode:
            try:
                server = smtplib.SMTP(self.config['smtp_server'], self.config['smtp_port'])
                server.starttls()
                server.login(self.config['from_email'], self.config['password'])
                self.logger.info(f"Connected to {self.config['smtp_server']}")
            except Exception as e:
                self.logger.error(f"SMTP connection error: {e}")
                print(f"SMTP connection error: {e}")
                return
        
        success_count = 0
        error_count = 0
        
        if limit is None:
            limit = len(recipients)
        process_recipients = recipients[skip:skip+limit]
        
        subject_tmpl = Template(subject_template)
        email_tmpl = self.load_template(email_template) if os.path.isfile(email_template) else Template(email_template)
        
        if not email_tmpl:
            if server:
                server.quit()
            return
        
        try:
            for idx, recipient in enumerate(process_recipients, 1):
                try:
                    subject = subject_tmpl.safe_substitute(**recipient)
                    content = self.personalize_email(email_tmpl, recipient)
                    
                    msg = self.create_email(recipient, subject, content, attachments)
                    
                    if test_mode:
                        print(f"\nTEST MODE - Would send to: {recipient['email']}")
                        print(f"Subject: {subject}")
                        print(f"Content preview (first 300 chars):\n{content[:300]}...\n")
                        success_count += 1
                    else:
                        self.rate_limit_check()
                        
                        server.send_message(msg)
                        self.sent_count += 1
                        success_count += 1
                        
                        self.logger.info(f"Sent email to {recipient['email']}")
                        print(f"Sent email {idx}/{len(process_recipients)} to {recipient['email']}")
                
                except Exception as e:
                    error_count += 1
                    self.logger.error(f"Error sending email to {recipient.get('email', 'unknown')}: {e}")
                    print(f"Error sending to {recipient.get('email', 'unknown')}: {e}")
                
                if idx % 10 == 0 or idx == len(process_recipients):
                    print(f"Progress: {idx}/{len(process_recipients)} emails processed")
        
        finally:
            if server:
                server.quit()
            print(f"\nEmail sending completed: {success_count} successful, {error_count} failed")
            self.logger.info(f"Session completed: {success_count} successful, {error_count} failed")

def main():
    parser = argparse.ArgumentParser(description="Club Email Sender")
    parser.add_argument("--csv", help="CSV file with recipient data", required=True)
    parser.add_argument("--template", help="Email template file (HTML)", required=True)
    parser.add_argument("--subject", help="Email subject line (can include template variables)", required=True)
    parser.add_argument("--config", help="Configuration file (JSON)", default="email_config.json")
    parser.add_argument("--attachments", help="Comma-separated list of files to attach", default="")
    parser.add_argument("--test", help="Test mode - don't actually send emails", action="store_true")
    parser.add_argument("--limit", help="Limit number of emails to send", type=int)
    parser.add_argument("--skip", help="Skip first N recipients", type=int, default=0)
    parser.add_argument("--smtp", help="SMTP server", default=None)
    parser.add_argument("--port", help="SMTP port", type=int, default=None)
    parser.add_argument("--email", help="Sender email address", default=None)
    parser.add_argument("--delay", help="Delay range in seconds (min,max)", default=None)
    parser.add_argument("--rate", help="Maximum emails per hour", type=int, default=None)
    
    args = parser.parse_args()
    
    sender = ClubEmailSender(args.config)
    
    if args.smtp:
        sender.config["smtp_server"] = args.smtp
    if args.port:
        sender.config["smtp_port"] = args.port
    if args.email:
        sender.config["from_email"] = args.email
    if args.rate:
        sender.config["rate_limit"] = args.rate
    if args.delay:
        try:
            min_delay, max_delay = map(int, args.delay.split(','))
            sender.config["delay_range"] = [min_delay, max_delay]
        except:
            print("Invalid delay format. Use min,max (e.g., 30,90)")
    
    if not sender.config.get("from_email"):
        sender.config["from_email"] = input("Sender email: ")
    
    if not args.test:
        sender.config["password"] = input(f"Password for {sender.config['from_email']}: ")
    
    recipients = sender.read_csv_data(args.csv)
    
    attachments = [f.strip() for f in args.attachments.split(',')] if args.attachments else []
    attachments = [f for f in attachments if f and os.path.exists(f)]
    
    if attachments:
        print(f"Will attach {len(attachments)} files: {', '.join(os.path.basename(f) for f in attachments)}")
    
    if not args.test and recipients:
        confirm = input(f"Ready to send {len(recipients) if not args.limit else min(args.limit, len(recipients))} emails. Proceed? (y/n): ")
        if confirm.lower() != 'y':
            print("Operation cancelled")
            return
    
    sender.send_emails(
        recipients=recipients,
        subject_template=args.subject,
        email_template=args.template,
        test_mode=args.test,
        attachments=attachments,
        limit=args.limit,
        skip=args.skip
    )
    
    sender.save_config(args.config)

if __name__ == "__main__":
    main()