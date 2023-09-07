import os
from datetime import datetime
import win32com.client  # pywin32
from dotenv import load_dotenv
from monday_utils import MondayManager
from file_utils import append_text_to_file, get_last_run_time, save_last_run_time, delete_files, load_file_contents
from llm_utils import analyze_email, extract_data_from_response, log_token_usage
import yaml
import argparse
import logging

logging.basicConfig(level=logging.INFO)
load_dotenv()
# Load config
with open("config.yml", 'r') as ymlfile:
    config = yaml.safe_load(ymlfile)


def readable_date(input_dt, frmat="%A, %B %d, %Y %H:%M:%S"):
    return datetime(*input_dt.timetuple()[:-2]).strftime(frmat)


def check_item_exists_in_memory(content, keywords):
    return all(keyword in content for keyword in keywords)


class EmailAIAssistant:
    def __init__(self, reset_items, monday_com):
        self.config = yaml.safe_load(open("config.yml"))
        self.TARGET_MAILBOX_NAME = self.config['TARGET_MAILBOX_NAME']
        self.TARGET_DOMAIN = self.config['TARGET_DOMAIN']
        self.TARGET_RECEIVER = self.config['TARGET_RECEIVER']
        self.SMTP_ADDRESS_MARKER = self.config['SMTP_ADDRESS_MARKER']

        self.todos_content = load_file_contents("todos.txt")
        self.summary_content = load_file_contents("summary.txt")

        self.monday_com = monday_com

        if monday_com:
            self.manager = MondayManager(os.environ["MONDAY_TOKEN"])
            self.board_id = self.manager.get_board_id_by_name(self.config['MONDAY_BOARD'])
            self.group_id = self.manager.get_group_id_by_name(self.board_id, self.config['MONDAY_GROUP'])

        if reset_items:
            delete_files()

        self.outlook = win32com.client.Dispatch('outlook.application')
        self.mapi = self.outlook.GetNamespace("MAPI")

    def format(self, message, email_sender, llm_email_response):
        return f"Email from {email_sender} - Received on: {readable_date(message.ReceivedTime)} - {message.Subject}\nSummary: {llm_email_response['Notes']}\n\n"

    def perform_action_for_email(self, llm_email_response, message, email_sender):
        if llm_email_response['action_type'] == 'action':
            keys_to_extract = ["Notes", "Due Date"]
            extracted_data = {key: llm_email_response[key] for key in keys_to_extract if key in llm_email_response}
            extracted_data['Notes'] += f"\nEmail from {email_sender} - Subject: {message.Subject} - Received on: {readable_date(message.ReceivedTime)}"

            if self.monday_com:
                self.manager.create_item(board_id=self.board_id, group_id=self.group_id,
                                         item_name=f"{llm_email_response['item_name']} - from {email_sender}",
                                         column_values=extracted_data)

            print(f"Creating to do - {llm_email_response['item_name']} - {llm_email_response['Notes']}")
            append_text_to_file("todos.txt", self.format(message, email_sender, llm_email_response))
        else:
            print(f"Creating informed item - {llm_email_response['Notes']}")
            append_text_to_file("summary.txt", self.format(message, email_sender, llm_email_response))

    def process_single_email(self, message, email_sender):
        unique_keywords = [email_sender, message.Subject, readable_date(message.ReceivedTime)]
        if check_item_exists_in_memory(self.todos_content, unique_keywords) or \
                check_item_exists_in_memory(self.summary_content, unique_keywords):
            print(f"Item already exists for email from {email_sender} with subject {message.Subject}. Skipping.")
            return
        response = analyze_email(message, self.TARGET_RECEIVER)
        data = extract_data_from_response(response)

        log_token_usage(response)

        self.perform_action_for_email(data, message, email_sender)

    def get_smtp_address(self, message):
        try:
            return message.Sender.GetExchangeUser().PrimarySmtpAddress
        except Exception as e:
            print(
                f"Failed to process mail from {message.SenderName}. Error: {e}.  "
                f"Class: {message.MessageClass} Subject: {message.Subject}")
            append_text_to_file("errors.txt",
                                f"Failed to process mail from {message.SenderName}. Error: {e}.  "
                                f"Class: {message.MessageClass} Subject: {message.Subject}\n{message.body}\n"
                                f"-----------------------------End of "
                                f"MAIL------------------------------------------------")
            return None

    def filter_messages(self, all_messages, target_sender_domain):
        filtered_messages = []

        for message in list(all_messages):
            if self.SMTP_ADDRESS_MARKER in message.SenderEmailAddress:  # Check if it's in X.500 format
                smtp_address = self.get_smtp_address(message)
                if not smtp_address:
                    continue
                sender_email = smtp_address
            else:
                sender_email = message.SenderEmailAddress

            if target_sender_domain in sender_email:
                filtered_messages.append(message)
                self.process_single_email(message, sender_email)

        return filtered_messages

    def process_inbox(self):
        last_run_time = get_last_run_time()
        append_text_to_file("summary.txt", f"\nRun On {datetime.now()} - Run From: {last_run_time}")
        append_text_to_file("todos.txt", f"\nRun On {datetime.now()} - Run From: {last_run_time}")
        append_text_to_file("errors.txt", f"\nRun On {datetime.now()} - Run From: {last_run_time}")

        for account in self.mapi.Accounts:
            print("Finding mailbox")
            if account.DeliveryStore.DisplayName == self.TARGET_MAILBOX_NAME:
                inbox = account.DeliveryStore.GetDefaultFolder(6)
                messages = inbox.Items
                messages = messages.Restrict("[ReceivedTime] >= '" + last_run_time.strftime('%m/%d/%Y %H:%M %p') + "'")
                # messages = messages.Restrict("@SQL=""urn:schemas:httpmail:senderemail"" LIKE '%/O=EXCHANGELABS%'")
                print("Processing new mail")
                processed_messages = self.filter_messages(messages, self.TARGET_DOMAIN)

                # Save the current time to a file to be used as last run time for next execution
                print("Saving updated run date/time")
                save_last_run_time(datetime.now())
                return processed_messages


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Email AI Assistant")
    parser.add_argument("-r", "--reset_items", default=False, help="Reset existing item files")
    parser.add_argument("-m", "--monday_com", default=False, help="Upload To Do Items to Monday.com")
    # parser.add_argument("-v", "--verbose", default=True, help="Provide verbose console logging")

    args = parser.parse_args()

    reset_items = True if str(args.reset_items).lower() in ["t", "true"] else False
    monday_com = True if str(args.monday_com).lower() in ["t", "true"] else False

    assistant = EmailAIAssistant(reset_items, monday_com)
    msg = assistant.process_inbox()
    print(
        'Finished processing email.  Todos can be found in todos.txt.  \nInformed items can be found in summary.txt.  '
        'Errors can be found in errors.txt\nToken usage can be found in token_usage.txt')
