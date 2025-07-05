import hashlib

notification_type = "p2p-incoming"
operation_id = "1234567890"
amount = "100.00"
currency = "643"
datetime_ = "2025-07-05T16:31:28Z"
sender = "4100111222333444"
codepro = "false"
YOOMONEY_SECRET = "PaxJwRSvpeZ+3cUaVYAaFL33"
label = "245243773"

hash_string = f"{notification_type}&{operation_id}&{amount}&{currency}&{datetime_}&{sender}&{codepro}&{YOOMONEY_SECRET}&{label}"
print("String to hash:", hash_string)

calculated_hash = hashlib.sha1(hash_string.encode('utf-8')).hexdigest()
print("Calculated sha1 hash:", calculated_hash)
