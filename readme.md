# Postman

A Python tool for sending personalized mass emails, with a lot of flexibility.

## Features

- Send personalized HTML emails using template variables
- CSV data integration for recipient information
- Rate limiting to prevent sending too many emails too quickly
- Random delays between emails to appear more natural
- File attachments support
- Test mode to preview emails without sending
- Detailed logging of all email activity
- Configurable SMTP settings

## Requirements

- Python 3.6+
- CSV file with recipient data (must include an "email" column)
- HTML email template file (optional, can use inline template)

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/seenmttai/postman.git
   cd postman
   ```

2. No additional dependencies are required as the script uses only Python standard library modules.

## Configuration

You can configure the tool in three ways:

1. **JSON configuration file** (recommended for repeated use)
2. **Command-line arguments** (override config file settings)
3. **Interactive prompts** during execution

### Sample Configuration File (email_config.json)

```json
{
  "smtp_server": "smtp.gmail.com",
  "smtp_port": 587,
  "from_email": "your.email@gmail.com",
  "rate_limit": 20,
  "delay_range": [30, 90],
  "log_file": "email_log.txt"
}
```

## CSV File Format

Your CSV file must include an "email" column and any other fields you want to use in your template. Example:

```csv
name,email,membership_id,status
John Doe,john.doe@example.com,12345,active
Jane Smith,jane.smith@example.com,67890,pending
```

## Email Template

Create an HTML template file with placeholders for personalization using Python's string Template syntax (`$variable_name`):

```html
<html>
<body>
  <h1>Hello, $name!</h1>
  <p>Your membership ID is: $membership_id</p>
  <p>Your current status is: $status</p>
</body>
</html>
```

## Usage

Basic usage:

```bash
python main.py --csv members.csv --template email_template.html --subject "Club Update for $name"
```

With additional options:

```bash
python main.py --csv members.csv --template email_template.html --subject "Important Notice" \
  --config my_config.json --attachments "document1.pdf,document2.pdf" \
  --limit 50 --skip 20 --test --rate 15 --delay "45,120"
```

### Command-Line Arguments

| Argument | Description | Required |
|----------|-------------|----------|
| `--csv` | CSV file with recipient data | Yes |
| `--template` | Email template file (HTML) | Yes |
| `--subject` | Email subject line (can include template variables) | Yes |
| `--config` | Configuration file (JSON) | No (default: "email_config.json") |
| `--attachments` | Comma-separated list of files to attach | No |
| `--test` | Test mode - don't actually send emails | No |
| `--limit` | Limit number of emails to send | No |
| `--skip` | Skip first N recipients | No (default: 0) |
| `--smtp` | SMTP server | No (overrides config) |
| `--port` | SMTP port | No (overrides config) |
| `--email` | Sender email address | No (overrides config) |
| `--delay` | Delay range in seconds (min,max) | No (overrides config) |
| `--rate` | Maximum emails per hour | No (overrides config) |

## Security Notes

- The script will prompt for your email password at runtime
- Passwords are never saved to the configuration file
- Consider using an app-specific password if using Gmail or similar services

## Logging

All email sending activities are logged to the file specified in your configuration (default: "email_log.txt"). This includes:
- Successfully sent emails
- Errors and exceptions
- Rate limiting events

## Examples

### Basic Usage
Send emails to all members in the CSV file:

```bash
python main.py --csv members.csv --template welcome_email.html --subject "Welcome to the Club, $name"
```

### Test Mode
Preview emails without sending them:

```bash
python main.py --csv members.csv --template newsletter.html --subject "Monthly Newsletter" --test
```

### With Attachments
Send emails with PDF attachments:

```bash
python main.py --csv members.csv --template invoice.html --subject "Your Invoice" --attachments "invoice.pdf,terms.pdf"
```

### Rate Limiting
Control the sending rate to avoid triggering spam filters:

```bash
python main.py --csv large_list.csv --template announcement.html --subject "Important Announcement" --rate 10 --delay "60,180"
```

## Troubleshooting

- If using Gmail, you may need to enable "Less secure app access" or use an app password
- Check the log file for detailed error messages if emails fail to send
- Ensure your CSV file includes all fields referenced in your template
- Make sure attachments exist and are readable

