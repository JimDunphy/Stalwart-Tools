# IMAP Folder Discovery and Spam Classification Debugging Tool

## Overview

`discover-folders.py` is a Python script for monitoring and debugging spam classification in a Stalwart + Rspamd email system. It provides IMAP folder inspection, message listing with spam scores, and raw message/header extraction for debugging.

### Why This Tool Exists

When integrating Rspamd as a milter with Stalwart Mail Server, you need to verify that spam classification and folder delivery are working correctly **without interference from email clients (MUAs)** that might automatically move messages between folders.

This tool allows you to:

1. **Inspect messages directly on the server** via IMAP without using an email client
2. **Verify Rspamd's spam scores** by examining X-Spamd-Result headers
3. **Confirm Stalwart's folder placement** based on Rspamd's X-Spam header
4. **Cross-reference with Rspamd's web GUI history** to match real-time classification with delivered results
5. **Debug misclassifications** by extracting complete messages for re-testing in Rspamd

### The Stalwart + Rspamd Integration

In this configuration:

- **Rspamd runs as a milter** and classifies email during SMTP delivery
- **Rspamd adds headers** (X-Spam, X-Spam-Status, X-Spamd-Result) to messages
- **Stalwart reads the X-Spam header** during ingestion and moves spam to the Junk folder
- **Stalwart's built-in spam filter is disabled** to avoid double classification

This is achieved with the following Stalwart configuration:

```toml
# Enable spam filter globally (required for ingestion-phase header check)
spam-filter.enable = true

# Check Rspamd's X-Spam header during ingestion
spam-filter.header.status.name = "X-Spam"
spam-filter.header.status.enable = false

# Disable Stalwart's SMTP-phase spam filter (no double classification!)
session.data.spam-filter = false

# Disable account-specific Bayes at ingestion (optional, for extra safety)
spam-filter.bayes.account.enable = false
```

See the [Stalwart documentation on Rspamd integration](https://github.com/stalwartlabs/stalwart/discussions/2159#discussioncomment-15067611) for complete details.

### Workflow: Verifying the Integration

1. Send or receive a test email
2. Check Rspamd's web GUI → History to see the classification in real-time
3. Use this tool to verify:
   - The message landed in the correct folder (INBOX or Junk Mail)
   - The X-Spamd-Result header matches what Rspamd's GUI shows
   - The X-Spam header is present (or absent) as expected
4. Extract problematic messages for re-testing if needed

## ⚠️ Quick Start Warning

**Before running this script, you MUST customize the default values for your environment!**

The script contains example credentials and server settings that will not work on your system. See the [Configuration](#-important-customize-defaults-before-use) section below for details on how to customize the defaults or use command-line arguments.

## Features

- **List all IMAP folders** with message counts
- **Display recent messages** from any folder with spam scores
- **Show UID column** to identify specific messages
- **Extract raw headers** for spam analysis
- **Extract complete messages** for Rspamd testing
- **Flexible authentication** with command-line overrides
- **Customizable limits** for message display

## Requirements

```bash
python3
imaplib (standard library)
email (standard library)
```

No external dependencies required.

## Configuration

### ⚠️ IMPORTANT: Customize Defaults Before Use

**The script contains example defaults that MUST be changed for your environment.**

Running the script without customization will result in connection errors:
```
socket.gaierror: [Errno -2] Name or service not known
```

**You have two options:**

#### Option 1: Edit the Script Defaults (Recommended for Regular Use)

Edit `discover-folders.py` and change the default values in the function signatures:

```python
def connect_to_imap(username='YOUR_EMAIL@YOUR_DOMAIN.com',
                   password='YOUR_PASSWORD',
                   server='YOUR_IMAP_SERVER.com'):
```

Change these in all function definitions:
- Line 8: `connect_to_imap()`
- Line 14: `list_folders()`
- Line 73: `get_emails_from_folder()`
- Line 231: `show_message_headers()`
- Line 271: `show_full_message()`
- Lines 337-342: Argument parser defaults

#### Option 2: Always Use Command-Line Arguments

Always specify your server, username, and password when running:

```bash
./discover-folders.py --server YOUR_SERVER.com --user YOUR_EMAIL@DOMAIN.com --password YOUR_PASSWORD
```

### Default Settings

The script ships with example defaults that must be customized:

- **IMAP Server:** `mx.example.com:993` (SSL) - **CHANGE THIS**
- **Username:** `user@example.com` - **CHANGE THIS**
- **Password:** `ChangeMe` - **CHANGE THIS**
- **Default limit:** 5 messages

### Override Defaults

All defaults can be overridden via command-line arguments:

```bash
--server <hostname>     # Use different IMAP server
--user <email>          # Use different account
--password <pass>       # Use different password
--limit <n>             # Show more/fewer messages
```

## Usage

### Basic Commands

#### List All Folders
```bash
./discover-folders.py
./discover-folders.py --list
```

**Output:**
```
Your IMAP folders and message counts:
------------------------------------------------------------
INBOX                          : 145 messages
Junk Mail                      : 23 messages
Sent                           : 89 messages
Drafts                         : 2 messages
------------------------------------------------------------
```

#### Show Recent Messages from INBOX
```bash
./discover-folders.py --ham
./discover-folders.py --ham --limit 10
```

**Output:**
```
Latest 5 emails from 'INBOX':
From                                                         Subject                                            X-Spamd-Result
--------------------------------------------------------------------------------------------------------------------------------------------
ChatGPT <noreply@email.openai.com>                           Ask anything – really                              3.34 / 1004.00
Node Weekly <node@cooperpress.com>                           Guess who's back, back again? Shai-Hulud.          2.54 / 1004.00
"Bloomberg" <noreply@news.bloomberg.com>                     Mixed messages                                     1.13 / 1004.00
```

#### Show Recent Messages from Junk Mail
```bash
./discover-folders.py --spam
./discover-folders.py --spam --limit 10
```

#### Show Messages from Any Folder
```bash
./discover-folders.py --folder "Sent"
./discover-folders.py --folder "Drafts" --limit 20
```

### Advanced Commands

#### Show UID Column
```bash
./discover-folders.py --spam --uid
```

**Output:**
```
Latest 5 emails from 'Junk Mail':
UID        From                                               Subject                                            X-Spamd-Result
--------------------------------------------------------------------------------------------------------------------------------------------
657        100% Natural Pain Relief <vlkm@vlkm.my>            The real reason behind tingling, burning...        14.83 / 1004.00
656        "Empty Your Bowels" <support@glucont.shop>         Empty Your Bowels 2X FASTER...                     21.20 / 1004.00
653        "Alzheimer's brain" <support@hlthsfit.shop>        Harvard's leaked 'Memory Revival Tonic'...         31.65 / 1004.00
```

#### Extract Message Headers
```bash
./discover-folders.py --spam --headers 657
```

**Output:**
```
================================================================================
Headers for message UID 657 in folder 'Junk Mail':
================================================================================

Delivered-To: user@mx.example.com
X-Spam: Yes
X-Spam-Status: Yes, score=14.83
X-Spamd-Result: default: False [14.83 / 1004.00];
	R_BAD_CTE_7BIT(3.50)[7bit];
	RCVD_IN_IVMSIP(3.00)[34.31.231.79:received];
	RCVD_UNAUTH_PBL(2.00)[];
	RBL_SPAMHAUS_PBL(2.00)[34.31.231.79:from];
	...

================================================================================
```

#### Extract Complete Message
```bash
./discover-folders.py --spam --message 657
./discover-folders.py --ham --message 2513 > message.eml
```

**Output:**
Raw RFC822 message (headers + body) suitable for:
- Piping to rspamd-client
- Testing in Rspamd web interface
- Manual analysis

### Authentication Options

#### Use Different Account
```bash
./discover-folders.py --user user2@example.com --password ChangeMe --ham
```

#### Use Different Server
```bash
./discover-folders.py --server mx.example.com --ham
./discover-folders.py --server mail.example.com --user admin@example.com --password secret --spam
```

#### Works with All Commands
```bash
./discover-folders.py --user admin@example.com --password secret --spam --uid
```

## Command-Line Options Reference

### Folder Selection
| Option | Description |
|--------|-------------|
| `--ham` | Display emails from INBOX folder |
| `--spam` | Display emails from Junk Mail folder |
| `--folder <name>` | Display emails from specified folder |
| `--list` | List all folders and their message counts (default) |

### Display Options
| Option | Description |
|--------|-------------|
| `--limit <n>` | Number of messages to display (default: 5) |
| `--uid` | Show UID column in message table |
| `--headers <UID>` | Display all headers for message with specified UID |
| `--message <UID>` | Display complete raw message (headers+body) for UID |

### Authentication Options
| Option | Description |
|--------|-------------|
| `--server <hostname>` | IMAP server hostname (default: mx.example.com) |
| `--user <email>` | IMAP username (default: user@example.com) |
| `--password <pass>` | IMAP password (default: ChangeMe) |

### Help
| Option | Description |
|--------|-------------|
| `-h, --help` | Show help message with examples |

## Workflow: Debugging Spam Classification

### Problem: Message in Wrong Folder

**Scenario:** Legitimate email went to Junk, or spam stayed in INBOX.

**Steps:**

1. **Find the message and its UID:**
   ```bash
   ./discover-folders.py --spam --uid
   # or
   ./discover-folders.py --ham --uid
   ```

2. **Check the headers to see Rspamd scores:**
   ```bash
   ./discover-folders.py --spam --headers 657
   ```

   Look for:
   - `X-Spam-Status: Yes, score=14.83`
   - `X-Spamd-Result:` with detailed symbol scores

3. **Extract the full message for Rspamd testing:**
   ```bash
   ./discover-folders.py --spam --message 657 > test-message.eml
   ```

4. **Analyze in Rspamd web interface:**
   - Go to Rspamd web UI → History
   - Or use: `rspamd-client < test-message.eml`
   - Check which symbols fired and their scores

5. **Verify Stalwart folder delivery:**
   - If `X-Spam: Yes` → should be in Junk Mail
   - If no `X-Spam: Yes` → should be in INBOX

### Problem: Understanding Why Rules Fired

**Scenario:** Need to understand why specific Rspamd rules triggered.

**Steps:**

1. **Get message UID:**
   ```bash
   ./discover-folders.py --spam --uid
   ```

2. **Extract full headers:**
   ```bash
   ./discover-folders.py --spam --headers 657
   ```

3. **Look for X-Spamd-Result header:**
   ```
   X-Spamd-Result: default: False [14.83 / 1004.00];
       R_BAD_CTE_7BIT(3.50)[7bit];
       RCVD_IN_IVMSIP(3.00)[34.31.231.79:received];
       RBL_SPAMHAUS_PBL(2.00)[34.31.231.79:from];
   ```

4. **Cross-reference with Rspamd web interface:**
   - History tab shows all symbols
   - Can see why each symbol fired
   - Can test rule changes

### Problem: Verifying Configuration Changes

**Scenario:** Changed Rspamd or Stalwart config, need to verify it works.

**Steps:**

1. **Send test message**

2. **Check where it landed:**
   ```bash
   ./discover-folders.py --ham --uid --limit 1
   ./discover-folders.py --spam --uid --limit 1
   ```

3. **Verify headers:**
   ```bash
   ./discover-folders.py --spam --headers <UID>
   ```

4. **Check critical headers:**
   - `X-Spam: Yes` or absent
   - `X-Spam-Status: Yes, score=...`
   - `X-Spamd-Result:` with expected symbols

## Integration with Rspamd Web Interface

### Real-Time Verification Workflow

The key advantage of this tool is verifying that **what Rspamd classified during SMTP delivery** matches **what Stalwart delivered to folders**.

1. **Watch Rspamd classify in real-time:**
   - Open Rspamd web GUI → History tab
   - Send or receive a test email
   - Note the spam score and symbols that fired

2. **Verify folder delivery with this tool:**
   ```bash
   # Check if spam landed in Junk Mail
   ./discover-folders.py --spam --uid --limit 5

   # Check if ham stayed in INBOX
   ./discover-folders.py --ham --uid --limit 5
   ```

3. **Compare headers with Rspamd's classification:**
   ```bash
   # Extract headers for specific message
   ./discover-folders.py --spam --headers 657
   ```

   Look for:
   - `X-Spamd-Result:` - Should match Rspamd GUI scores
   - `X-Spam: Yes` - Indicates Rspamd marked it as spam
   - Folder location - Should be Junk Mail if X-Spam: Yes

4. **Debug misclassifications:**
   ```bash
   # Extract complete message for re-testing
   ./discover-folders.py --spam --message 657 > test-message.eml

   # Re-test in Rspamd
   rspamd-client < test-message.eml
   ```

### What to Look For

**In discover-folders.py output:**
- `X-Spamd-Result:` header with score and symbols - should match Rspamd GUI
- `X-Spam: Yes` header - indicates Rspamd classified as spam
- Folder location:
  - **Junk Mail** if X-Spam: Yes present
  - **INBOX** if X-Spam: Yes absent
- Envelope addresses and authentication results

**In Rspamd web interface History:**
- Same message (match by Message-ID, From, Subject, or timestamp)
- Symbol breakdown with individual scores
- Why each symbol fired
- Total score calculation
- Compare this with the X-Spamd-Result header from discover-folders.py

### Common Verification Scenarios

**Scenario 1: Message in wrong folder**
1. Find message UID: `./discover-folders.py --ham --uid` (if spam in INBOX)
2. Check headers: `./discover-folders.py --ham --headers <UID>`
3. Look for X-Spam header:
   - If present but in INBOX → Stalwart configuration issue
   - If absent but should be spam → Rspamd rules need tuning

**Scenario 2: Scores don't match Rspamd GUI**
1. Extract headers: `./discover-folders.py --spam --headers <UID>`
2. Compare X-Spamd-Result with Rspamd GUI History
3. If different → Check timestamps (may be different messages)
4. Extract and re-test: `./discover-folders.py --spam --message <UID> > test.eml && rspamd-client < test.eml`

## Troubleshooting

### Connection Errors

**Problem:** `Cannot connect to IMAP server`

**Solution:**
- Check server name: default is `mx.example.com:993`
- Use `--server` to specify different server if needed
- Verify SSL/TLS is working
- Test credentials manually

```bash
./discover-folders.py --server mx.example.com --ham
```

### Authentication Failed

**Problem:** `Login failed`

**Solution:**
```bash
./discover-folders.py --user correct@email.com --password correctpass
```

### Message Not Found

**Problem:** `Message UID 1234 not found`

**Solution:**
- UIDs change when messages are deleted
- Get fresh UID list: `./discover-folders.py --spam --uid`
- UIDs are per-folder, not global

### Folder Not Found

**Problem:** `Cannot select folder: FolderName`

**Solution:**
- List all folders: `./discover-folders.py --list`
- Use exact folder name with quotes if it has spaces
- Folder names are case-sensitive

## Tips and Best Practices

### 1. Always Use --uid for Message Operations

```bash
# Good workflow
./discover-folders.py --spam --uid          # Get UID
./discover-folders.py --spam --headers 657  # Use UID
```

### 2. Pipe Messages to Files for Analysis

```bash
./discover-folders.py --spam --message 657 > spam-sample.eml
./discover-folders.py --ham --message 2513 > ham-sample.eml
```

### 3. Use --limit to Find Recent Issues

```bash
./discover-folders.py --spam --limit 20 --uid
```

### 4. Check Both Folders When Debugging

```bash
./discover-folders.py --ham --uid | grep -i "suspicious"
./discover-folders.py --spam --uid | grep -i "legitimate"
```

### 5. Regular Monitoring

```bash
# Check spam folder daily
./discover-folders.py --spam --limit 10

# Verify recent ham
./discover-folders.py --ham --limit 10
```

## Examples

### Example 1: Daily Spam Check

```bash
#!/bin/bash
# daily-spam-check.sh

echo "=== Checking Recent Spam ==="
./discover-folders.py --spam --limit 10

echo ""
echo "=== Checking Recent Ham ==="
./discover-folders.py --ham --limit 10
```

### Example 2: Debug Misclassified Message

```bash
# Found false positive in Junk Mail
./discover-folders.py --spam --uid | grep "Legitimate"
# UID 658

# Check headers
./discover-folders.py --spam --headers 658 | grep -E "X-Spam|X-Spamd-Result"

# Extract for testing
./discover-folders.py --spam --message 658 > false-positive.eml

# Analyze in Rspamd
rspamd-client < false-positive.eml
```

### Example 3: Verify Stalwart Configuration

```bash
# Check that spam with X-Spam: Yes is in Junk
./discover-folders.py --spam --headers 657 | grep "X-Spam:"
# Should show: X-Spam: Yes

# Check that ham without X-Spam: Yes is in INBOX
./discover-folders.py --ham --headers 2513 | grep "X-Spam:"
# Should show no X-Spam: Yes header
```

### Example 4: Multiple Accounts

```bash
# Check main account
./discover-folders.py --spam --uid

# Check secondary account
./discover-folders.py --user user2@example.com --password ChangeMe --spam --uid
```

## Technical Details

### Message Retrieval

- Uses IMAP `RFC822.HEADER` for headers only
- Uses IMAP `RFC822` for complete messages
- Sorts by date (newest first) using IMAP SORT or fallback
- UIDs are stable until messages are expunged

### Header Parsing

- MIME-encoded headers are decoded
- Multi-line headers are properly assembled
- X-Spamd-Result score is extracted from `[score / threshold]` format

### Output Formatting

- Table widths adjust based on `--uid` flag
- Headers are truncated with `...` to fit columns
- Raw output (--headers, --message) is unmodified

## Related Documentation

- [Stalwart Spam Classification Flow](stalwart_spam_classification_flow.md)
- [Rspamd Rule Writing Guide](../rspamd/rspamd-docs/rspamd_rule_writing_guide.md)
- [Rspamd RBL Guide](../rspamd/rspamd-docs/rspamd_rbl_guide.md)

## Version History

- **v2.0** - Added UID column, message extraction, flexible authentication, improved help
- **v1.0** - Initial version with folder listing and basic message display

---

**Author:** Jim Dunphy
**Last Updated:** 2025-11-25
**License:** Use freely for email system management
