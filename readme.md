# Email AI Assistant

This project uses Python and AI to summarize and automate actions from emails.

## Overview

The code connects to an email inbox, sends emails to an AI API (OpenAI or Azure), and processes the summaries and actions returned. Useful for automating parts of email workflow.

Key features:

- Summarizes email content with AI
- Extracts action items into TODOs
- Saves summaries for searchability  
- Optionally, creates tasks in Monday.com from emails
- Handles some errors 
- Avoids processing duplicate emails
- Tracks AI token usage

## Setup

1. Clone this repo
2. Obtain API keys for OpenAI/Azure and add to `.env` 
3. Configure settings in `config.yml` like email account
4. Run `pip install -r requirements.txt`
5. Schedule `main.py` to run, like with cron

## Usage

- Set `reset_items=True` initially to clear existing files 
- View output summaries in `summary.txt`
- View extracted actions in `todos.txt`
- Errors are logged to `errors.txt`
- Token usage tracked in `token_usage.txt`
### Optional parameters to run
- `-r True` or `-r False` to reset all files. We use files for looking for duplicates, cheap, easy. Default is `False` 
because we do not want to process duplicate emails.  If files are reset, they are deleted.
- `-m True` or `-m False` to save To Do's to Monday.com.  Default is `False`

## Configuration

Key settings in `config.yml`:

- `TARGET_MAILBOX_NAME`: Name of the mailbox folder to scan in your Outlook (in case of multiple mailboxes)
- `TARGET_DOMAIN`: Only process emails from this domain
- `TARGET_RECEIVER`: Who the assistant is processing mail for
- `SMTP_ADDRESS_MARKER`: Used to parse complex Outlook address formats, and help ensure we're only processing internal emails
- `MONDAY_BOARD`: Name of the Monday.com Board to save To-Dos to
- `MONDAY_GROUP`: Name of Group within Monday.com Boars to
- Note: This only processes the inbox, not folders.

See code comments for additional config options.
## Environment Variables in `.env`
Use azure or open_ai to control which endpoint to use
- `API_TYPE` Set to 'azure' or 'openai' to direct which API to hit.

Environment Variables For Azure OpenAI Endpoint.  Use with `azure` above. Given Microsofts LLM approach, can only
call 1 API endpoint for one model, no need to specify model name
- `AZURE_OPENAI_API_BASE`
- `AZURE_OPENAI_API_KEY`
- `AZURE_OPENAI_API_DEPLOYMENT_NAME`
- `AZURE_OPENAI_API_VERSION`

Environment Variables for using OpenAI's ChatCompletion Endpoint.  Use with `openai` above.  With OpenAI's API
You must specify the chat model to use
- `OPENAI_API_KEY`
- `CHAT_MODEL`

Monday.com token
- `MONDAY_TOKEN`

## Contributing

Pull requests welcome!

## License

MIT