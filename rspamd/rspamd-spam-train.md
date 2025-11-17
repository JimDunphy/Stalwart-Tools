# Rspamd Bayes Training Guide

## Overview

This script trains Rspamd's Bayes classifier by connecting to your Stalwart IMAP server and learning from pre-classified messages in your Junk and Inbox folders.

## Features

- ✅ Connects to Stalwart IMAP server
- ✅ Trains from your vetted Junk (spam) and Inbox (ham) folders
- ✅ Tracks which messages have been trained (no duplicates)
- ✅ Can be run multiple times safely
- ✅ Shows progress and statistics
- ✅ Requires minimum 200 spam + 200 ham to activate Bayes

## Prerequisites

### System Requirements

```bash
# Install required Python packages
pip3 install requests --break-system-packages

# Or use a virtual environment
python3 -m venv ~/venv-rspamd-train
source ~/venv-rspamd-train/bin/activate
pip install requests
```

### Before You Train: Vetting Your Messages

**Important**: This script learns from YOUR classifications. You need to prepare clean training data first.

#### The Workflow:

1. **Install and Configure Stalwart Mail Server**
   - Set up Stalwart with rspamd integration
   - Connect your mail client (Thunderbird recommended)

2. **Use Thunderbird to pre-train Messages (Recommended)**

   Why Thunderbird?
   - Has excellent built-in Junk filtering (its own Bayes)
   - Makes it easy to review and reclassify hundreds of messages
   - Future spam/ham is close to 100% effective automatically to build corpus
   - Syncs classifications back to IMAP folders

   The process:
   ```
   a. Let mail accumulate (100-500+ messages)
   b. In Thunderbird, enable Junk Controls (Tools > Account Settings > Junk Settings)
   c. Train Thunderbird's filter on your messages:
      - Mark spam as Junk (J key)
      - Mark ham as Not Junk (Shift+J)
   d. After training, Thunderbird helps identify more spam
   e. Manually review and verify:
      - Check your Junk folder - move any false positives back to Inbox
      - Check your Inbox - move any missed spam to Junk
   f. Repeat until you have clean folders (200+ messages of each)
   ```

3. **Run This Script to Train Rspamd**

   Once your folders are vetted:
   ```bash
   ./rspamd-spam-train.py --train
   ```

   The script sends your vetted messages to rspamd's Bayes classifier.

#### Why This Two-Step Process?

- **Thunderbird's Bayes**: Helps YOU classify messages quickly
- **Rspamd's Bayes**: Learns from your classifications to filter server-side

Think of Thunderbird as your assistant that helps you vet messages, then this script teaches rspamd what you decided.

#### Minimum Training Data

You need at least:
- **200 spam messages** in your Junk folder
- **200 ham messages** in your Inbox

More is better (500-1000 of each is ideal), but quality matters more than quantity. Every message should be correctly classified.

## Installation

```bash
# Download the script
cp /path/to/rspamd-spam-train.py ~/rspamd-spam-train.py
chmod +x ~/rspamd-spam-train.py

# Edit configuration
vi ~/rspamd-spam-train.py
# Update these values in the CONFIG dictionary:
#   'imap_user': 'your_email@your_domain.com'
#   'imap_host': 'localhost' (or your Stalwart server)
```

## Configuration

Edit the `CONFIG` dictionary in the script:

```python
CONFIG = {
    'imap_host': 'localhost',          # Stalwart IMAP server
    'imap_port': 993,                   # IMAP SSL port
    'imap_user': 'user@mx.example.com', # Your email address
    'imap_password': None,              # Will prompt or use env var or CLI
    'rspamd_url': 'http://localhost:11334',  # rspamd API endpoint
    'rspamd_password': 'password_here', # rspamd controller password
    'spam_folder': 'Junk Mail',         # Your spam folder
    'ham_folder': 'INBOX',              # Your ham folder
    'max_messages': 1000,               # Max per run
    'state_file': '/tmp/rspamd-train-state.json',
}
```

**Important Notes:**
- `rspamd_url`: Must point to where rspamd is running (use hostname/IP if rspamd is remote)
- `rspamd_password`: Required for authentication with rspamd's controller API
- `spam_folder`: Use quotes for folders with spaces (default: `'Junk Mail'`)

**Configuration Priority** (highest to lowest):
1. **Command-line arguments** (`--imap-user`, `--imap-password`)
2. **Environment variables** (`IMAP_PASSWORD`, `RSPAMD_PASSWORD`)
3. **CONFIG dictionary** in the script

## Usage

### Initial Training

```bash
# Option 1: Edit CONFIG in script (one-time setup)
vi ~/rspamd-spam-train.py
# Set imap_user, imap_password, spam_folder, etc.
./rspamd-spam-train.py --train

# Option 2: Use environment variables
export IMAP_PASSWORD="your_password"
./rspamd-spam-train.py --train

# Option 3: Use command-line arguments (best for cron/automation)
./rspamd-spam-train.py --train \
  --imap-user user@example.com \
  --imap-password "your_password"

# Short aliases work too
./rspamd-spam-train.py --train \
  --username user@example.com \
  --password "your_password"

# Override spam folder if needed
./rspamd-spam-train.py --train \
  --spam-folder "Junk Mail" \
  --ham-folder "INBOX"

# For debugging, start with a small number of messages:
./rspamd-spam-train.py --train --max 10
```

### Check Statistics

```bash
./rspamd-spam-train.py --stats
```

Shows:
- How many spam messages trained
- How many ham messages trained
- Whether you've reached the 200 minimum threshold
- Last training run timestamp

### Incremental Training

As you classify more messages in Thunderbird:
- Move spam to Junk folder
- Keep ham in Inbox
- Run training script periodically

```bash
./rspamd-spam-train.py --train
```

The script remembers what it already trained, so it only trains new messages.

### Reset State

If you want to retrain everything:

```bash
./rspamd-spam-train.py --reset
```

**Note**: This only resets the script's memory of what was trained. It doesn't clear rspamd's Bayes database.

## Command Line Options

```bash
./rspamd-spam-train.py --help

Options:
  --train                      Train from new messages in IMAP folders
  --stats                      Show training statistics
  --reset                      Reset training state (retrain on next run)
  --imap-user USER             IMAP username (also: --username)
  --imap-password PASS         IMAP password (also: --password)
  --spam-folder NAME           Override spam folder name (default: Junk Mail)
  --ham-folder NAME            Override ham folder name (default: INBOX)
  --max N                      Max messages to train per run (default: 1000)
```

**New in this version:**
- `--imap-user` / `--username`: Specify IMAP user on command line (perfect for cron/scripts)
- `--imap-password` / `--password`: Specify password on command line (highest priority)

## Example Workflow

### 1. Initial Setup (First Time)

```bash
# Edit script configuration
vi ~/rspamd-spam-train.py
# Update imap_user to your email

# Make executable
chmod 755 ~/rspamd-spam-train.py

# Set password (optional)
export IMAP_PASSWORD="your_password"

# Run initial training
./rspamd-spam-train.py --train
```

Expected output:
```
Rspamd Bayes Training Script
Started at: 2025-11-14 18:30:00
✓ Connected to IMAP server as user@mx.example.com

============================================================
Training SPAM from folder: Junk
============================================================
Found 150 new messages to train (out of 150 total)
  Progress: 10/150 messages trained
  Progress: 20/150 messages trained
  ...
  Progress: 150/150 messages trained
✓ Successfully trained 150/150 spam messages

============================================================
Training HAM from folder: INBOX
============================================================
Found 300 new messages to train (out of 300 total)
  Progress: 10/300 messages trained
  ...
✓ Successfully trained 300/300 ham messages

============================================================
Training Summary
============================================================
Spam messages trained this run: 150
Ham messages trained this run: 300
Total spam trained: 150
Total ham trained: 300

⚠ Need more training data:
  Spam: 50 more needed
  Ham: 0 more needed
```

### 2. Continue Training

```bash
# Move more spam to Junk folder in Thunderbird
# Run training again
./rspamd-spam-train.py --train
```

Output:
```
Found 75 new messages to train (out of 225 total)
✓ Successfully trained 75/75 spam messages
Total spam trained: 225
Total ham trained: 300

✓ Bayes classifier has sufficient training data
```

### 3. Ongoing Maintenance

See the **Automated Training** section below for various automation strategies.

## Understanding Bayes Training

### Minimum Requirements

Rspamd requires:
- **At least 200 spam messages**
- **At least 200 ham messages**

Until you reach these minimums, the `BAYES_SPAM` and `BAYES_HAM` scores won't appear in message headers.

### What Gets Trained

- **Spam folder (Junk Mail)**: Messages you've manually classified as spam
- **Ham folder (INBOX)**: Messages you've kept as legitimate

### Best Practices

1. **Quality over quantity**: Only train on messages you're 100% sure about
2. **Balanced training**: Try to keep spam and ham counts roughly similar (see below)
3. **Regular updates**: Run training weekly as you classify more messages
4. **Review before training**: Make sure your folders are clean

### Training Quantity Guidelines

**How many messages should you train?**

| Spam Count | Ham Count | Result |
|------------|-----------|--------|
| < 200 | < 200 | Bayes **not active** (minimum not met) |
| 200-500 | 200-500 | Bayes **active** but limited accuracy |
| 1,000-2,000 | 1,000-2,000 | **Good** working classifier |
| 5,000-10,000 | 5,000-10,000 | **Excellent** accuracy and diversity |
| 10,000+ | 10,000+ | Diminishing returns, but not harmful |

**Balance is critical:**
- ✅ Good: 1,000 spam + 1,000 ham (1:1 ratio)
- ✅ Acceptable: 2,000 spam + 1,000 ham (2:1 ratio)
- ❌ Bad: 10,000 spam + 200 ham (50:1 ratio - heavily biased!)

**Key points:**
- **More is better** (up to ~10,000 of each), but quality matters more
- **Keep balanced** - aim for 1:1 ratio, stay within 2:1
- **Diversity helps** - messages from different time periods, senders, topics
- **No maximum** - rspamd handles large training sets well, but benefits plateau after ~10,000

### Does Rspamd Auto-Train?

**No, rspamd does NOT automatically train itself by default.** You must explicitly send messages to the learning API (which this script does).

However, rspamd has an **optional "autolearn" feature** you can enable:

```
# In rspamd config (e.g., /etc/rspamd/local.d/classifier-bayes.conf)
autolearn {
  spam_threshold = 15.0;   # Auto-train as spam if score >= 15
  ham_threshold = -5.0;    # Auto-train as ham if score <= -5
  check_balance = true;    # Keep spam/ham balanced
}
```

**Autolearn pros:**
- Continuously learns from high-confidence classifications
- No manual intervention needed after setup

**Autolearn cons:**
- Risk of feedback loops (classifier reinforces its own mistakes)
- Requires careful threshold tuning
- Can drift over time without oversight
- Not recommended for beginners

**Recommendation:** Start with manual training (this script) until you have 5,000+ of each type and understand your mail patterns. Then consider autolearn as a supplement, not replacement.

### Verifying Bayes is Working

After training 200+ of each:

```bash
# Check a spam email - should see BAYES_SPAM score
./rspamd-ctl.sh --logs | grep BAYES

# Or check headers of incoming spam
# Look for: BAYES_SPAM(x.xx) in X-Spamd-Result header
```

## Troubleshooting

### Connection Refused to Rspamd

**Error**: `Failed to establish a new connection: [Errno 111] Connection refused`

**Cause**: The `rspamd_url` in CONFIG is incorrect or rspamd is not running.

**Fix**:
```bash
# Check if rspamd is running
docker ps | grep rspamd
# or
systemctl status rspamd

# If rspamd is on a different host, update CONFIG:
'rspamd_url': 'http://mx.example.com:11334',  # Use correct hostname/IP

# Test connection manually:
curl http://mx.example.com:11334/stat
```

### HTTP 401 Unauthorized

**Error**: `Warning: HTTP 401 - {"error": "Unauthorized"}`

**Cause**: Missing or incorrect `rspamd_password` in CONFIG.

**Fix**:
```bash
# Find your rspamd password in the config:
cat /opt/stalwart-rspamd/rspamd/local.d/worker-controller.inc

# Update CONFIG in the script:
'rspamd_password': 'your_actual_password',

# Or use environment variable:
export RSPAMD_PASSWORD="your_password"
./rspamd-spam-train.py --train
```

### Successfully Trained 0/X Messages

**Symptom**: Script shows `✓ Successfully trained 0/10 spam messages` even though messages exist.

**Cause**: This was a bug in earlier versions where HTTP 204 and 208 responses weren't recognized as success.

**Fix**: Make sure you have the latest version of the script that handles these response codes:
- HTTP 200: Success with JSON response
- HTTP 204: Success, no content
- HTTP 208: Already learned (still counts as success)

### Folder Names with Spaces

**Error**: Cannot select folder "Junk Mail"

**Fix**: The script automatically handles spaces, but make sure your config uses the exact folder name:
```python
'spam_folder': 'Junk Mail',  # Include the space
```

### "No spam-db specified" Error

This is normal. It means you haven't trained yet. The database is created automatically when you first train.

### IMAP Connection Failed

Check:
```bash
# Test IMAP connection
openssl s_client -connect localhost:993 -starttls imap

# Verify credentials
# Make sure imap_user and password are correct
```

### Messages Not Training

Check rspamd logs:
```bash
# Docker
docker logs rspamd | grep -i learn

# Or if using rspamd-ctl wrapper:
./rspamd-ctl.sh --logs | grep -i learn
```

### State File Issues

```bash
# Check state file
cat /tmp/rspamd-train-state.json

# Reset if corrupted
./rspamd-spam-train.py --reset
```

### Permission Denied

```bash
# Make sure script is executable
chmod +x ~/rspamd-spam-train.py

# Check state file permissions
ls -la /tmp/rspamd-train-state.json
```

### Debugging Tips

```bash
# Start with a small test run
./rspamd-spam-train.py --train --max 10

# Check what rspamd sees:
curl -X POST \
  -H "Password: your_password" \
  -H "Content-Type: message/rfc822" \
  --data-binary @test.eml \
  http://mx.example.com:11334/learnspam

# Verify state tracking is working
./rspamd-spam-train.py --stats
```

## Advanced Usage

### Train from Different Folders

```bash
# Train from custom folders
./rspamd-spam-train.py --train \
  --spam-folder "INBOX/Spam" \
  --ham-folder "INBOX/NotSpam"
```

### Limit Messages Per Run

```bash
# Only train 100 messages at a time
./rspamd-spam-train.py --train --max 100
```

### Multiple Accounts

Create separate config files:
```bash
cp ~/rspamd-spam-train.py ~/rspamd-train-account1.py
cp ~/rspamd-spam-train.py ~/rspamd-train-account2.py

# Edit each with different imap_user and state_file
vi ~/rspamd-train-account1.py
vi ~/rspamd-train-account2.py
```

## Automated Training Strategies

### Quick Recommendation

- **Personal/Testing:** Start with **Option 1** (Single User)
- **Multi-User Stalwart:** Use **Option 3** (IMAPSieve Auto-Copy) ⭐
- **No Stalwart/Different server:** Use **Option 4** (Central Forward Account)

---

### Option 1: Single User Nightly Training (Simplest)

Perfect for personal mail servers or testing.

**Setup with Cron:**
```bash
# Edit crontab
crontab -e

# Train nightly at 2 AM
0 2 * * * export IMAP_PASSWORD="yourpass" && /home/user/rspamd-spam-train.py --train >> /var/log/rspamd-train.log 2>&1
```

**Setup with Systemd (Recommended):**

Create `/etc/systemd/system/rspamd-train.service`:
```ini
[Unit]
Description=Train Rspamd Bayes Classifier
After=network.target stalwart.service

[Service]
Type=oneshot
User=mail
Environment="IMAP_PASSWORD=your_password"
ExecStart=/usr/local/bin/rspamd-spam-train.py --train
StandardOutput=journal
StandardError=journal
```

Create `/etc/systemd/system/rspamd-train.timer`:
```ini
[Unit]
Description=Train Rspamd Bayes nightly

[Timer]
OnCalendar=02:00
Persistent=true
RandomizedDelaySec=300

[Install]
WantedBy=timers.target
```

Enable:
```bash
sudo systemctl daemon-reload
sudo systemctl enable rspamd-train.timer
sudo systemctl start rspamd-train.timer

# Check status
systemctl status rspamd-train.timer
journalctl -u rspamd-train.service
```

**Pros:** Simple, secure (one password), easy to debug
**Cons:** Only learns from one user's classifications

---

### Option 2: Multi-User Training Loop

Train from multiple users' folders every night. Similar to how organizations with multiple users contribute to training.

**Create a wrapper script** (`/usr/local/bin/rspamd-train-all.sh`):
```bash
#!/bin/bash

# List of users to train from
USERS=(
    "user1@domain.com:password1"
    "user2@domain.com:password2"
    "admin@domain.com:password3"
)

SCRIPT="/usr/local/bin/rspamd-spam-train.py"
LOG="/var/log/rspamd-train-all.log"

echo "=== Rspamd Training Started: $(date) ===" | tee -a "$LOG"

for user_pass in "${USERS[@]}"; do
    user="${user_pass%%:*}"
    pass="${user_pass#*:}"

    echo "Training from $user..." | tee -a "$LOG"

    # Create temp config for this user
    STATE_FILE="/tmp/rspamd-train-state-${user//[@.]/-}.json"

    # Use environment variables to override config
    export IMAP_PASSWORD="$pass"

    # Call script with user-specific settings
    # (You'll need to modify the script to accept --imap-user flag)
    # For now, you can create per-user scripts or modify CONFIG on the fly

    python3 "$SCRIPT" --train --max 1000 2>&1 | tee -a "$LOG"

    echo "" | tee -a "$LOG"
done

echo "=== Rspamd Training Completed: $(date) ===" | tee -a "$LOG"
```

**Cron entry:**
```bash
0 2 * * * /usr/local/bin/rspamd-train-all.sh
```

**Pros:** Learns from multiple users, distributed classification effort
**Cons:** Need to store multiple passwords, more complex

---

### Option 3: IMAPSieve Auto-Copy (Best for Stalwart!) ⭐

**Your users' workflow stays exactly the same** - they just move messages to Junk or back to Inbox. Stalwart automatically copies these to training accounts behind the scenes using IMAPSieve.

#### Why This is the Best Approach:

- ✅ **No user passwords needed** - Admin doesn't need access to user accounts
- ✅ **No user training required** - Users work normally in their mail client
- ✅ **Automatic** - Happens server-side, no client configuration
- ✅ **Collaborative** - All users contribute to training
- ✅ **Privacy-friendly** - Users' original messages stay in their folders

#### How It Works:

```
User moves message to Junk folder
         ↓
IMAPSieve triggers (RFC 6785 - Stalwart supports this!)
         ↓
Sieve script copies message to spam@domain.com
         ↓
Original stays in user's Junk folder (untouched)
         ↓
Nightly: Training script processes spam@domain.com
         ↓
After training: Script deletes messages from training account
```

#### Implementation:

**Step 1: Create Training Accounts**

```bash
# In Stalwart admin interface or CLI, create:
# - spam@yourdomain.com (collects spam copies)
# - ham@yourdomain.com (collects false positive copies)
```

**Step 2: Configure IMAPSieve Scripts**

Stalwart supports IMAPSieve globally. Create a Sieve script that triggers on IMAP folder moves:

**For spam collection** (`/etc/stalwart/sieve/global-spam-copy.sieve`):
```sieve
require ["imap4flags", "vnd.stalwart.expressions", "copy", "environment", "variables"];

# Trigger when user moves message TO Junk folder
if environment "imap.mailbox" "Junk" {
    redirect :copy "spam@yourdomain.com";
}

# Alternative: Also trigger on explicit spam flag
if hasflag "\\Junk" {
    redirect :copy "spam@yourdomain.com";
}
```

**For ham (false positive) collection** (`/etc/stalwart/sieve/global-ham-copy.sieve`):
```sieve
require ["imap4flags", "vnd.stalwart.expressions", "copy", "environment", "variables"];

# Trigger when user moves message FROM Junk back to INBOX
# This indicates a false positive
if allof(
    environment "imap.mailbox-from" "Junk",
    environment "imap.mailbox" "INBOX"
) {
    redirect :copy "ham@yourdomain.com";
}

# Or when user explicitly removes spam flag
if not hasflag "\\Junk" {
    # Check if previously in Junk
    if environment "imap.mailbox-from" "Junk" {
        redirect :copy "ham@yourdomain.com";
    }
}
```

**Step 3: Configure Stalwart to Use IMAPSieve**

In your Stalwart configuration file:

```toml
[sieve]
# Enable IMAPSieve
imap.enabled = true

# Global scripts that run for all users on IMAP events
imap.global-scripts = [
    "/etc/stalwart/sieve/global-spam-copy.sieve",
    "/etc/stalwart/sieve/global-ham-copy.sieve"
]

# Or per-user if preferred
# imap.user-scripts = true
```

**Step 4: Training Script with Auto-Cleanup**

Create `/usr/local/bin/rspamd-train-autoclean.sh`:

```bash
#!/bin/bash

SCRIPT="/usr/local/bin/rspamd-spam-train.py"
LOG="/var/log/rspamd-train-auto.log"

echo "=== Auto-Training Started: $(date) ===" | tee -a "$LOG"

# Train from spam@ account
echo "Training spam from spam@yourdomain.com..." | tee -a "$LOG"
export IMAP_PASSWORD="spam_account_password"
export IMAP_USER="spam@yourdomain.com"

python3 "$SCRIPT" --train --spam-folder "INBOX" --ham-folder "NonExistent" 2>&1 | tee -a "$LOG"

# Clean up trained spam messages (optional - delete after 7 days)
# python3 -c "
# import imaplib, os, time
# imap = imaplib.IMAP4_SSL('localhost', 993)
# imap.login('spam@yourdomain.com', os.getenv('IMAP_PASSWORD'))
# imap.select('INBOX')
# # Delete messages older than 7 days
# date = (time.time() - 7*24*3600)
# typ, data = imap.search(None, 'BEFORE', time.strftime('%d-%b-%Y', time.localtime(date)))
# for num in data[0].split():
#     imap.store(num, '+FLAGS', '\\Deleted')
# imap.expunge()
# imap.logout()
# "

# Train from ham@ account (false positives)
echo "Training ham from ham@yourdomain.com..." | tee -a "$LOG"
export IMAP_PASSWORD="ham_account_password"
export IMAP_USER="ham@yourdomain.com"

python3 "$SCRIPT" --train --spam-folder "NonExistent" --ham-folder "INBOX" 2>&1 | tee -a "$LOG"

echo "=== Auto-Training Complete ===" | tee -a "$LOG"
```

Make executable:
```bash
chmod +x /usr/local/bin/rspamd-train-autoclean.sh
```

**Step 5: Schedule Nightly Training**

```bash
# Cron - runs at 3 AM
crontab -e
0 3 * * * /usr/local/bin/rspamd-train-autoclean.sh
```

Or with systemd (create service + timer as shown in Option 1).

#### Advantages Over Manual Forwarding:

| Feature | IMAPSieve Auto-Copy | Manual Forward |
|---------|---------------------|----------------|
| User effort | None (automatic) | Must remember to forward |
| Password security | No user passwords needed | Users share passwords |
| Adoption rate | 100% (automatic) | Depends on user compliance |
| Privacy | Original stays with user | User sends copy |
| Configuration | Admin sets up once | Every user configures |

#### Monitoring:

```bash
# Check how many messages were auto-collected today
echo "Spam collected:"
curl -u spam@yourdomain.com:password https://localhost:993/... # Use IMAP status

# Check training logs
tail -f /var/log/rspamd-train-auto.log

# See training stats
./rspamd-spam-train.py --stats
```

#### Notes:

- **Stalwart's IMAPSieve** support (RFC 6785) makes this possible
- **No user intervention** required after initial setup
- **Scales automatically** as you add users
- **Privacy-preserving** - copies only, originals stay in user folders
- Consider **retention policy** - delete training messages after X days
- **Test first** with a single user account before rolling out globally

---

### Option 4: Central Spam Account (User Forwards)

Alternative to IMAPSieve if you prefer users to actively forward spam (simpler but requires user action).

Users forward spam/ham to dedicated training accounts, script pulls from there.

**Setup:**

1. **Create training accounts:**
   ```
   spam@yourdomain.com   (for spam reports)
   ham@yourdomain.com    (for false positives)
   ```

2. **Configure Sieve rules** (in Stalwart) to auto-file messages:

   For `spam@yourdomain.com`:
   ```sieve
   # Auto-file all incoming to Junk folder
   require "fileinto";
   fileinto "Junk";
   ```

   For `ham@yourdomain.com`:
   ```sieve
   # Keep all in INBOX
   keep;
   ```

3. **Train from these accounts:**

   Create `/usr/local/bin/rspamd-train-central.sh`:
   ```bash
   #!/bin/bash

   # Train from spam reports
   export IMAP_PASSWORD="spam_account_password"
   python3 /usr/local/bin/rspamd-spam-train.py \
       --train \
       --spam-folder "Junk" \
       --ham-folder "INBOX" \
       --max 5000 \
       2>&1 | logger -t rspamd-train
   ```

   Modify the script CONFIG or use a separate config:
   ```python
   CONFIG = {
       'imap_user': 'spam@yourdomain.com',
       'imap_password': os.getenv('IMAP_PASSWORD'),
       'spam_folder': 'Junk',
       'ham_folder': 'INBOX',  # ham@ forwards go here
       # ... rest of config
   }
   ```

4. **User workflow:**
   - Got spam in inbox? Forward to `spam@yourdomain.com`
   - Got false positive in junk? Forward to `ham@yourdomain.com`
   - Script runs nightly and trains rspamd

**Cron:**
```bash
0 3 * * * /usr/local/bin/rspamd-train-central.sh
```

**Pros:** Easy for users (just forward), centralized, no password management
**Cons:** Requires users to remember to forward, extra mailboxes

---

### Option 5: Shared IMAP Folders

Users contribute to shared Junk/Ham folders, script trains from there.

**Setup:**

1. **Create shared folders** in Stalwart:
   ```
   Shared/TrainSpam
   Shared/TrainHam
   ```

2. **Give all users access** (ACL in Stalwart)

3. **User workflow:**
   - Found spam? Move/copy to Shared/TrainSpam
   - Found false positive? Move to Shared/TrainHam

4. **Training script config:**
   ```python
   CONFIG = {
       'imap_user': 'trainer@yourdomain.com',  # Account with folder access
       'spam_folder': 'Shared/TrainSpam',
       'ham_folder': 'Shared/TrainHam',
       # ...
   }
   ```

5. **Nightly training:**
   ```bash
   0 2 * * * /usr/local/bin/rspamd-spam-train.py --train
   ```

**Optional - Auto-cleanup:**
```bash
# After training, delete old trained messages
# (Modify script to track and delete, or use IMAP expunge)
```

**Pros:** Collaborative, single password, easy auditing
**Cons:** Requires shared folder support, users need training

---

### Option 6: Hybrid Approach (Maximum Accuracy)

Combine multiple strategies for best results.

**Setup:**

1. **Personal training:** Key users (admins) have nightly training from their own folders
2. **Central reporting:** All users can forward to spam@/ham@ addresses
3. **Shared folders:** Optional for power users

**Implementation:**

Create `/usr/local/bin/rspamd-train-hybrid.sh`:
```bash
#!/bin/bash

LOG="/var/log/rspamd-train.log"

echo "=== Hybrid Training: $(date) ===" >> "$LOG"

# 1. Train from admin's personal folders
export IMAP_PASSWORD="admin_pass"
python3 /usr/local/bin/rspamd-spam-train.py --train 2>&1 | tee -a "$LOG"

# 2. Train from central spam@ account
export IMAP_PASSWORD="spam_account_pass"
python3 /usr/local/bin/rspamd-spam-train-central.py --train 2>&1 | tee -a "$LOG"

# 3. Optional: Train from shared folders
# ... additional training ...

echo "=== Training Complete ===" >> "$LOG"
```

---

### Comparison Table

| Strategy | Complexity | User Effort | Password Access | Best For |
|----------|------------|-------------|-----------------|----------|
| Single User | Low | Low | One user only | Personal servers, testing |
| Multi-User Loop | Medium | Low | Need all passwords | Small teams, trusted users |
| **IMAPSieve Auto-Copy** ⭐ | **Medium** | **None** | **No user passwords!** | **Multi-user Stalwart servers** |
| Central Account (Forward) | Medium | Medium | Central account only | Medium orgs, forwarding culture |
| Shared Folders | Medium | Medium | Shared account only | Collaborative teams |
| Hybrid | High | Variable | Multiple accounts | Large orgs, best accuracy |

---

### Best Practices for Automation

1. **Start small:** Begin with single-user training, expand later

2. **Monitor logs:**
   ```bash
   # Check last training run
   journalctl -u rspamd-train.service -n 50

   # Watch training in real-time
   tail -f /var/log/rspamd-train.log
   ```

3. **Alert on failures:**
   ```bash
   # Add to cron script
   if ! /usr/local/bin/rspamd-spam-train.py --train; then
       echo "Training failed!" | mail -s "Rspamd Training Failed" admin@domain.com
   fi
   ```

4. **Rate limiting:** Don't train too often (once daily is plenty)

5. **State file management:**
   - Keep separate state files per user/source
   - Backup state files occasionally
   ```bash
   # In your training script
   cp /tmp/rspamd-train-state.json /var/backups/rspamd-train-state.json.$(date +%Y%m%d)
   ```

6. **Incremental training:** The script's built-in state tracking means you only train new messages

7. **Statistics tracking:**
   ```bash
   # Weekly stats email
   0 8 * * 1 /usr/local/bin/rspamd-spam-train.py --stats | mail -s "Weekly Bayes Stats" admin@domain.com
   ```

---

### Security Considerations

**Password Storage:**

Option 1 - Environment file (better):
```bash
# Create /etc/rspamd-train-env
export IMAP_PASSWORD="secret"
export RSPAMD_PASSWORD="secret"

# Make it secure
chmod 600 /etc/rspamd-train-env

# Source in systemd service
EnvironmentFile=/etc/rspamd-train-env
```

Option 2 - Use systemd credentials (best):
```bash
# Store password securely
systemd-creds encrypt --name=imap_password - imap_password.cred
# Enter password when prompted

# In service file:
LoadCredential=imap_password:/path/to/imap_password.cred
```

Option 3 - App-specific passwords (if supported)

**File Permissions:**
```bash
chmod 700 /usr/local/bin/rspamd-train-*.sh
chmod 600 /var/log/rspamd-train.log
chown mail:mail /var/log/rspamd-train.log
```

## Comparison with Stalwart's Built-in Training

| Feature | Rspamd | Stalwart Built-in |
|---------|--------|-------------------|
| Training Method | HTTP API | Parse message bodies |
| Complexity | Simple POST request | Extract and parse content |
| State Tracking | This script | This script |
| Per-user Bayes | No (global) | Yes (per account) |
| Minimum messages | 200 each | Configurable |

## Integration with Your Existing Workflow

### The Complete Picture

```
┌─────────────────┐
│  Stalwart Mail  │  ← Your mail server (with rspamd)
└────────┬────────┘
         │ IMAP
         ↓
┌─────────────────┐
│  Thunderbird    │  ← YOU classify messages here
│  (Junk Filter)  │     - Thunderbird's Bayes helps you
└────────┬────────┘     - You review and correct
         │              - Messages sorted into folders
         ↓
┌─────────────────┐
│  This Script    │  ← Trains rspamd from your classifications
│  (rspamd train) │     - Reads Junk & Inbox via IMAP
└────────┬────────┘     - Sends to rspamd's learning API
         │
         ↓
┌─────────────────┐
│ Rspamd Bayes DB │  ← Now filters future mail server-side
└─────────────────┘
```

### For Existing Users

If you already have:
- ✅ Thunderbird connected to Stalwart
- ✅ Vetted Junk and Inbox folders (hundreds of messages)
- ✅ Experience with mail training

This script:
- Uses the same IMAP connection you're familiar with
- Works with your existing folder structure
- Leverages the work you already did in Thunderbird
- Much simpler than parsing message bodies
- Can run on the same schedule as your old Stalwart training

### Ongoing Workflow

Once trained:
1. New mail arrives → rspamd filters it (using Bayes + other rules)
2. Check your mail in Thunderbird
3. Correct any mistakes (move misclassified messages)
4. Run training script weekly/monthly to learn from corrections
5. Rspamd gets smarter over time

## See Also

- [Rspamd Bayes Documentation](https://rspamd.com/doc/configuration/statistic.html)
- [Rspamd Learning API](https://rspamd.com/doc/modules/neural.html)
- Your original: [stalwart-spam-train.md](https://github.com/JimDunphy/Stalwart-Tools/blob/main/bin/stalwart-spam-train.md)

## License

MIT License (same as your original stalwart-spam-train.py)
