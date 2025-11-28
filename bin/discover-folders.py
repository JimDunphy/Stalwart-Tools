#!/usr/bin/env python3
# List all your IMAP folders and their message counts
import imaplib
import re
import argparse
from email.header import decode_header

def connect_to_imap(username='user@example.com', password='ChangeMe', server='mx.example.com'):
    """Connect to IMAP server and return the connection object."""
    imap = imaplib.IMAP4_SSL(server, 993)
    imap.login(username, password)
    return imap

def list_folders(username='user@example.com', password='ChangeMe', server='mx.example.com'):
    """List all IMAP folders and their message counts."""
    imap = connect_to_imap(username, password, server)

    # List all folders
    status, folders = imap.list()
    print("Your IMAP folders and message counts:")
    print("-" * 60)

    for folder in folders:
        folder_info = folder.decode()

        # Properly extract the folder name from the IMAP LIST response
        # Format is: * LIST (\Attributes) "delimiter" "folder name"
        # Find all quoted strings and take the last one (the folder name)
        matches = re.findall(r'"([^"]*)"', folder_info)
        if len(matches) >= 2:
            folder_name = matches[-1]  # Get the last quoted string (the folder name)
            delimiter = matches[-2]    # Second to last is typically the delimiter
        elif len(matches) == 1:
            folder_name = matches[0]   # If only one quoted string, it might be the folder name
        else:
            # Fallback: extract the last part after splitting
            parts = folder_info.split()
            folder_name = parts[-1] if parts else "Unknown"

        # Count messages in the folder
        try:
            # Use square brackets around folder name to ensure proper quoting if there are special characters
            # Properly handle folder selection with correct quoting
            result = imap.select(f'"{folder_name}"')
            if result[0] == 'OK':
                # Search for all messages
                status, messages = imap.search(None, 'ALL')
                message_count = len(messages[0].split()) if messages[0] and messages[0].strip() else 0

                print(f"{folder_name:<30} : {message_count} messages")
            else:
                print(f"{folder_name:<30} : Unable to select folder")
        except:
            # If the quoted version fails, try the raw version (some servers handle it differently)
            try:
                result = imap.select(folder_name)
                if result[0] == 'OK':
                    # Search for all messages
                    status, messages = imap.search(None, 'ALL')
                    message_count = len(messages[0].split()) if messages[0] and messages[0].strip() else 0

                    print(f"{folder_name:<30} : {message_count} messages")
                else:
                    print(f"{folder_name:<30} : Unable to select folder")
            except Exception as e:
                print(f"{folder_name:<30} : Error - {str(e)}")

    imap.close()
    imap.logout()
    print("-" * 60)
    print("Done.")

def get_emails_from_folder(folder_name, limit=5, show_uid=False, username='user@example.com', password='ChangeMe', server='mx.example.com'):
    """Get the latest emails from specified folder and display in table format."""
    imap = connect_to_imap(username, password, server)

    try:
        # Select the folder
        result = imap.select(f'"{folder_name}"')
        if result[0] != 'OK':
            print(f"Cannot select folder: {folder_name}")
            imap.logout()
            return

        # Try to use SORT command to get messages in reverse date order (newest first)
        # If SORT is not supported by the server, fall back to basic approach
        try:
            status, msg_ids = imap.sort('REVERSE DATE', 'UTF-8', 'ALL')
            if not msg_ids or status != 'OK':
                # If sort fails, fall back to basic search
                raise Exception("SORT not supported or failed")
            # Ensure msg_ids is properly formatted
            if msg_ids and msg_ids[0]:
                if isinstance(msg_ids[0], bytes):
                    msg_ids = msg_ids[0].decode().split()
                elif isinstance(msg_ids[0], str):
                    msg_ids = msg_ids[0].split()
                else:
                    msg_ids = [str(x) for x in msg_ids[0]]
            else:
                # If sort returns empty, fall back to basic search
                raise Exception("SORT returned empty result")
        except:
            # Fallback: get all messages and use UID search to get most recent emails
            # First, get all message UIDs in ascending order
            status, messages = imap.search(None, 'ALL')
            if not messages[0]:
                print(f"No messages found in folder: {folder_name}")
                imap.logout()
                return
            msg_ids = messages[0].split()
            # Convert to integers, sort in reverse order to get highest numbers first (most recent)
            msg_ids = [x.decode() if isinstance(x, bytes) else x for x in msg_ids]  # Ensure strings
            msg_ids = sorted(msg_ids, key=lambda x: int(x), reverse=True)

        # Take only the first 'limit' messages (which are the newest)
        msg_ids = msg_ids[:limit] if len(msg_ids) >= limit else msg_ids

        # Print table header
        print(f"\nLatest {len(msg_ids)} emails from '{folder_name}':")
        if show_uid:
            print(f"{'UID':<10} {'From':<50} {'Subject':<50} {'X-Spamd-Result':<30}")
            print("-" * 140)
        else:
            print(f"{'From':<60} {'Subject':<50} {'X-Spamd-Result':<30}")
            print("-" * 140)

        # Fetch email headers for each message
        for msg_id in msg_ids:
            # Ensure msg_id is a string for the fetch command
            msg_str = str(msg_id).encode() if isinstance(msg_id, str) else msg_id
            status, msg_data = imap.fetch(msg_str, '(RFC822.HEADER)')
            if status == 'OK':
                header_data = msg_data[0][1]

                # Parse header data
                from_header = ""
                subject_header = ""
                spamd_result = ""

                lines = header_data.decode('utf-8', errors='ignore').split('\r\n')

                # Better approach: parse headers by tracking which header we're currently reading
                current_header = None
                header_content = []

                for line in lines:
                    # Check if this line is a new header field
                    if ':' in line and (line[0] != ' ' and line[0] != '\t'):
                        # Save the previous header if we have one
                        if current_header and header_content:
                            header_value = ' '.join(header_content).strip()
                            if current_header.lower() == 'from':
                                from_header = header_value
                            elif current_header.lower() == 'subject':
                                subject_header = header_value
                            elif current_header.lower() == 'x-spamd-result':
                                spamd_result = header_value

                        # Start a new header
                        colon_pos = line.find(':')
                        current_header = line[:colon_pos].lower()
                        header_content = [line[colon_pos+1:].strip()]
                    else:
                        # This is a continuation of the current header (indented)
                        if current_header:
                            header_content.append(line.strip())

                # Don't forget the last header
                if current_header and header_content:
                    header_value = ' '.join(header_content).strip()
                    if current_header.lower() == 'from':
                        from_header = header_value
                    elif current_header.lower() == 'subject':
                        subject_header = header_value
                    elif current_header.lower() == 'x-spamd-result':
                        spamd_result = header_value

                # Decode headers if needed
                if from_header:
                    from_header = decode_mime_words(from_header)
                if subject_header:
                    subject_header = decode_mime_words(subject_header)

                # Extract the score part from X-Spamd-Result: default: False [9.10 / 1004.00];
                if spamd_result:
                    match = re.search(r'\[([^\]]+)\]', spamd_result)
                    if match:
                        spamd_result = match.group(1)  # Extract content between brackets
                    else:
                        spamd_result = spamd_result  # Use the full value if no brackets found

                # Truncate headers to specified width
                if show_uid:
                    from_display = (from_header[:47] + '...') if from_header and len(from_header) > 50 else (from_header or '')
                    subject_display = (subject_header[:47] + '...') if subject_header and len(subject_header) > 50 else (subject_header or '')
                    spamd_display = (spamd_result[:27] + '...') if spamd_result and len(spamd_result) > 30 else (spamd_result or '')
                    print(f"{msg_id:<10} {from_display:<50} {subject_display:<50} {spamd_display:<30}")
                else:
                    from_display = (from_header[:57] + '...') if from_header and len(from_header) > 60 else (from_header or '')
                    subject_display = (subject_header[:47] + '...') if subject_header and len(subject_header) > 50 else (subject_header or '')
                    spamd_display = (spamd_result[:27] + '...') if spamd_result and len(spamd_result) > 30 else (spamd_result or '')
                    print(f"{from_display:<60} {subject_display:<50} {spamd_display:<30}")

        print("-" * 140)

    except Exception as e:
        print(f"Error accessing folder {folder_name}: {str(e)}")

    finally:
        imap.close()
        imap.logout()

def decode_mime_words(s):
    """Decode MIME encoded words in headers."""
    try:
        decoded_fragments = decode_header(s)
        fragments = []
        for fragment, encoding in decoded_fragments:
            if isinstance(fragment, bytes):
                if encoding:
                    fragments.append(fragment.decode(encoding))
                else:
                    fragments.append(fragment.decode('utf-8', errors='ignore'))
            else:
                fragments.append(fragment)
        return ''.join(fragments)
    except:
        return s

def show_message_headers(folder_name, uid, username='user@example.com', password='ChangeMe', server='mx.example.com'):
    """Display all headers for a specific message UID in raw format."""
    imap = connect_to_imap(username, password, server)

    try:
        # Select the folder
        result = imap.select(f'"{folder_name}"')
        if result[0] != 'OK':
            print(f"Cannot select folder: {folder_name}")
            imap.logout()
            return

        # Fetch the headers for the specified UID
        msg_str = str(uid).encode() if isinstance(uid, int) else str(uid).encode()
        status, msg_data = imap.fetch(msg_str, '(RFC822.HEADER)')

        if status != 'OK' or not msg_data or msg_data[0] is None:
            print(f"Message UID {uid} not found in folder '{folder_name}'")
            imap.logout()
            return

        # Get the raw header data
        header_data = msg_data[0][1]

        print(f"\n{'='*80}")
        print(f"Headers for message UID {uid} in folder '{folder_name}':")
        print(f"{'='*80}\n")

        # Display raw headers
        print(header_data.decode('utf-8', errors='ignore'))

        print(f"\n{'='*80}")

    except Exception as e:
        print(f"Error fetching message {uid} from folder {folder_name}: {str(e)}")

    finally:
        imap.close()
        imap.logout()

def show_full_message(folder_name, uid, username='user@example.com', password='ChangeMe', server='mx.example.com'):
    """Display complete raw message (headers + body) for a specific UID."""
    imap = connect_to_imap(username, password, server)

    try:
        # Select the folder
        result = imap.select(f'"{folder_name}"')
        if result[0] != 'OK':
            print(f"Cannot select folder: {folder_name}")
            imap.logout()
            return

        # Fetch the complete message for the specified UID
        msg_str = str(uid).encode() if isinstance(uid, int) else str(uid).encode()
        status, msg_data = imap.fetch(msg_str, '(RFC822)')

        if status != 'OK' or not msg_data or msg_data[0] is None:
            print(f"Message UID {uid} not found in folder '{folder_name}'")
            imap.logout()
            return

        # Get the raw message data (headers + body)
        message_data = msg_data[0][1]

        print(f"\n{'='*80}")
        print(f"Complete message UID {uid} in folder '{folder_name}':")
        print(f"{'='*80}\n")

        # Display raw message
        print(message_data.decode('utf-8', errors='ignore'))

        print(f"\n{'='*80}")

    except Exception as e:
        print(f"Error fetching message {uid} from folder {folder_name}: {str(e)}")

    finally:
        imap.close()
        imap.logout()

def main():
    parser = argparse.ArgumentParser(
        description='IMAP folder and email utility for monitoring spam classification',
        epilog='''
Examples:
  %(prog)s                              List all folders and message counts
  %(prog)s --ham                        Show latest 5 emails from INBOX
  %(prog)s --spam                       Show latest 5 emails from Junk Mail
  %(prog)s --folder "Sent"              Show latest 5 emails from any folder
  %(prog)s --ham --uid                  Show INBOX with UID column
  %(prog)s --ham --limit 10             Show latest 10 emails from INBOX
  %(prog)s --spam --headers 1234        Show all headers for message UID 1234 in Junk Mail
  %(prog)s --spam --message 1234        Show complete raw message (headers+body) for UID 1234
  %(prog)s --user user2@example.com --password ChangeMe --ham
                                        Use different account credentials
  %(prog)s --server mx.example.com --ham
                                        Use different IMAP server

Workflow for debugging spam classification:
  1. %(prog)s --spam --uid              Find message UID in Junk Mail
  2. %(prog)s --spam --headers 657      Check headers to see Rspamd scores
  3. %(prog)s --spam --message 657      Get full message to test in Rspamd
  4. Use Rspamd web interface to analyze symbols and rules
        ''',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Authentication options
    parser.add_argument('--user', default='user@example.com',
                        help='IMAP username (default: user@example.com)')
    parser.add_argument('--password', default='ChangeMe',
                        help='IMAP password (default: ChangeMe)')
    parser.add_argument('--server', default='mx.example.com',
                        help='IMAP server hostname (default: mx.example.com)')

    # Folder selection options
    parser.add_argument('--ham', action='store_true',
                        help='Display emails from INBOX folder')
    parser.add_argument('--spam', action='store_true',
                        help='Display emails from Junk Mail folder')
    parser.add_argument('--folder', type=str,
                        help='Display emails from specified folder')
    parser.add_argument('--list', action='store_true',
                        help='List all folders and their message counts (default if no other option)')

    # Display options
    parser.add_argument('--limit', type=int, default=5,
                        help='Number of messages to display (default: 5)')
    parser.add_argument('--uid', action='store_true',
                        help='Show UID column in message table')
    parser.add_argument('--headers', type=int, metavar='UID',
                        help='Display all headers for message with specified UID')
    parser.add_argument('--message', type=int, metavar='UID',
                        help='Display complete raw message (headers + body) for specified UID')

    args = parser.parse_args()

    # Determine which folder to use
    folder = None
    if args.ham:
        folder = 'INBOX'
    elif args.spam:
        folder = 'Junk Mail'
    elif args.folder:
        folder = args.folder

    # Execute the appropriate action
    if args.headers:
        if not folder:
            # Default to INBOX if showing headers without specifying folder
            folder = 'INBOX'
        show_message_headers(folder, args.headers, args.user, args.password, args.server)
    elif args.message:
        if not folder:
            # Default to INBOX if showing message without specifying folder
            folder = 'INBOX'
        show_full_message(folder, args.message, args.user, args.password, args.server)
    elif folder:
        get_emails_from_folder(folder, args.limit, args.uid, args.user, args.password, args.server)
    else:
        list_folders(args.user, args.password, args.server)

if __name__ == '__main__':
    main()
