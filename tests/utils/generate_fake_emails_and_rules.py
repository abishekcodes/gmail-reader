"""
This is just a script that I used to generate dummy emails
Keeping it here just for reference
No need to run this
but if you want to run you need to install faker library -> pip install faker
note that if you regenerate this, you have to rewrite the test cases
"""

# import base64
# import csv
# import email
# import email.utils
# import json

# from faker import Faker

# from .paths import EMAIL_FILE, RULES_FILE

# NUM_EMAILS = 1000

# Faker.seed(12345)
# fake = Faker()


# def generate_fake_emails():

#     rows = []

#     for i in range(1, NUM_EMAILS + 1):
#         sender = fake.email()
#         recipient = fake.email()
#         subject = fake.sentence(nb_words=6)
#         date = fake.date_time_between(start_date="-1y", end_date="now")
#         date_str = date.strftime("%a, %d %b %Y %H:%M:%S +0530")
#         body = fake.paragraph(nb_sentences=3)

#         raw = (
#             f"From: {sender}\r\n"
#             f"To: {recipient}\r\n"
#             f"Subject: {subject}\r\n"
#             f"Date: {date_str}\r\n\r\n{body}"
#         )

#         raw_b64 = base64.urlsafe_b64encode(raw.encode("utf-8")).decode("ascii")

#         rows.append({
#             "id": f"test-email-{i}",
#             "raw": raw_b64,
#             "from_email": sender,
#             "subject": subject,
#             "date": date_str,
#             "body": body
#         })

#     return rows


# def write_as_csv(rows):
#     with EMAIL_FILE.open('w') as f:
#         writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
#         writer.writeheader()
#         writer.writerows(rows)


# def load_msg(raw_b64: str):
#     raw_bytes = base64.urlsafe_b64decode(raw_b64)
#     return email.message_from_bytes(raw_bytes)


# def build_rules(rows: list):
#     rules = []
#     msg1 = load_msg(rows[0]['raw'])
#     from1 = msg1["From"]
#     rules.append(
#         {
#             "name": f"Move messages from {from1}",
#             "conditions": {
#                 "operator": "ALL",
#                 "rules": [
#                     {"field": "from_email", "predicate": "Equals", "value": from1}
#                 ]
#             },
#             "actions": [{"type": "move_message", "folder": "SPAM"}],
#         }
#     )

#     # Rule 2: Mark as read any message whose Subject contains the first word of the 2nd email’s subject
#     msg2 = load_msg(rows[1]['raw'])
#     first2 = msg2["Subject"].split()[0].strip(".,!?")
#     rules.append(
#         {
#             "name": f"Mark messages with '{first2}' in subject as read",
#             "conditions": {
#                 "operator": "ALL",
#                 "rules": [
#                     {"field": "subject", "predicate": "Contains", "value": first2}
#                 ]
#             },
#             "actions": [
#                 {"type": "mark_as_read"}
#             ],
#         }
#     )

#     # Rule 3: Archive any email older than the 3rd email’s date
#     msg3 = load_msg(rows[2]['raw'])
#     dt3 = email.utils.parsedate_to_datetime(msg3["Date"]).isoformat()
#     rules.append(
#         {
#             "name": f"Archive messages before {dt3}",
#             "conditions": {
#                 "operator": "ALL", "rules": [{"field": "date", "predicate": "LessThan", "value": dt3}]
#             },
#             "actions": [
#                 {"type": "move_message", "folder": "TRASH"}
#             ],
#         }
#     )

#     # Rule 4: Mark unread if from the same domain as sender #4 or if body contains its first word
#     msg4 = load_msg(rows[3]['raw'])
#     dom4 = msg4["From"].split("@", 1)[1]
#     first4 = msg4.get_payload().split()[0].strip(".,!?")
#     rules.append(
#         {
#             "name": f"Flag from '{dom4}' or containing '{first4}'",
#             "conditions": {
#                 "operator": "ANY",
#                 "rules": [
#                     {"field": "from_email", "predicate": "Contains", "value": dom4},
#                     {"field": "body", "predicate": "Contains", "value": first4},
#                 ],
#             },
#             "actions": [
#                 {"type": "mark_as_unread"}
#             ],
#         }
#     )

#     with RULES_FILE.open('w') as f:
#         json.dump({"rules": rules}, f, indent=2)

#     print(f"Generated {len(rules)} rules to {RULES_FILE.absolute().as_posix()}")


# if __name__ == "__main__":
#     rows = generate_fake_emails()
#     write_as_csv(rows)
#     build_rules(rows)
