# -*- coding: utf-8 -*-

# This is a simple mailbox polling script for the Sahana Messaging Module
# If there is a need to collect from non-compliant mailers then suggest using the robust Fetchmail to collect & store in a more compliant mailer!
# This script doesn't handle MIME attachments

import sys, socket, email, uuid

# Read-in configuration from Database
settings = db(db.msg_email_settings.id == 1).select(limitby=(0, 1)).first()
host = settings.inbound_mail_server
server_type = settings.inbound_mail_type
ssl = settings.inbound_mail_ssl
port = settings.inbound_mail_port
username = settings.inbound_mail_username
password = settings.inbound_mail_password
delete = settings.inbound_mail_delete

if server_type == "pop3":
    import poplib
    # http://docs.python.org/library/poplib.html
    try:
        if ssl:
            p = poplib.POP3_SSL(host, port)
        else:
            p = poplib.POP3(host, port)
    except socket.error, e:
        error = "Cannot connect: %s" % e
        print error
        # Store status in the DB
        try:
            id = db().select(db.msg_email_inbound_status.id, limitby=(0, 1)).first().id
            db(db.msg_email_inbound_status.id == id).update(status=error)
        except:
            db.msg_email_inbound_status.insert(status=error)
        # Explicitly commit DB operations when running from Cron
        db.commit()
        sys.exit(1)
    try:
        # Attempting APOP authentication...
        p.apop(username, password)
    except poplib.error_proto:
        # Attempting standard authentication...
        try:
            p.user(username)
            p.pass_(password)
        except poplib.error_proto, e:
            print "Login failed:", e
            # Store status in the DB
            try:
                id = db().select(db.msg_email_inbound_status.id, limitby=(0, 1)).first().id
                db(db.msg_email_inbound_status.id == id).update(status="Login failed: %s" % e)
            except:
                db.msg_email_inbound_status.insert(status="Login failed: %s" % e)
            # Explicitly commit DB operations when running from Cron
            db.commit()
            sys.exit(1)
    dellist = []
    mblist = p.list()[1]
    for item in mblist:
        number, octets = item.split(" ")
        # Retrieve the message (storing it in a list of lines)
        lines = p.retr(number)[1]
        # Create an e-mail object representing the message
        msg = email.message_from_string("\n".join(lines))
        # Parse out the 'From' Header
        sender = msg["from"]
        # Parse out the 'Subject' Header
        if "subject" in msg:
            subject = msg["subject"]
        else:
            subject = ""
        # Parse out the 'Body'
        textParts = msg.get_payload()
        body = textParts[0].get_payload()
        # Store in DB
        uuidstamp = uuid.uuid4()
        db.msg_email_inbox.insert(uuid=uuidstamp, sender=sender, subject=subject, body=body)
        if delete:
            # Add it to the list of messages to delete later
            dellist.append(number)
    # Explicitly commit DB operations when running from Cron
    db.commit()
    # Iterate over the list of messages to delete
    for number in dellist:
        p.dele(number)
    p.quit()

elif server_type == "imap":
    import imaplib
    # http://docs.python.org/library/imaplib.html
    try:
        if ssl:
            M = imaplib.IMAP4_SSL(host, port)
        else:
            M = imaplib.IMAP4(host, port)
    except socket.error, e:
        error = "Cannot connect: %s" % e
        print error
        # Store status in the DB
        try:
            id = db().select(db.msg_email_inbound_status.id, limitby=(0, 1)).first().id
            db(db.msg_email_inbound_status.id == id).update(status=error)
        except:
            db.msg_email_inbound_status.insert(status=error)
        # Explicitly commit DB operations when running from Cron
        db.commit()
        sys.exit(1)
    try:
        M.login(username, password)
    except M.error, e:
        error = "Login failed: %s" % e
        print error
        # Store status in the DB
        try:
            id = db().select(db.msg_email_inbound_status.id, limitby=(0, 1)).first().id
            db(db.msg_email_inbound_status.id == id).update(status=error)
        except:
            db.msg_email_inbound_status.insert(status=error)
        # Explicitly commit DB operations when running from Cron
        db.commit()
        sys.exit(1)
    dellist = []
    # Select inbox
    M.select()
    # Search for Messages to Download
    typ, data = M.search(None, "ALL")
    for num in data[0].split():
        typ, msg_data = M.fetch(num, "(RFC822)")
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_string(response_part[1])
                # Parse out the 'From' Header
                sender = msg["from"]
                # Parse out the 'Subject' Header
                if "subject" in msg:
                    subject = msg["subject"]
                else:
                    subject = ""
                # Parse out the 'Body'
                textParts = msg.get_payload()
                body = textParts[0].get_payload()
                # Store in DB
                uuidstamp = uuid.uuid4()
                db.msg_email_inbox.insert(uuid=uuidstamp, sender=sender, subject=subject, body=body)
                if delete:
                    # Add it to the list of messages to delete later
                    dellist.append(num)
    # Explicitly commit DB operations when running from Cron
    db.commit()
    # Iterate over the list of messages to delete
    for number in dellist:
        typ, response = M.store(number, "+FLAGS", r"(\Deleted)")
    M.close()
    M.logout()
