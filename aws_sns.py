# sns_notifier.py
import boto3
from datetime import datetime
from typing import Optional


class SNSNotifier:
    def __init__(self):
        # Initialize a boto3 session with a specific profile "dy-admin"
        session = boto3.Session(profile_name="dy-admin")
        self.client = session.client("sns", region_name="us-west-2")

    def send_deal_alert(
        self,
        phone_number: str,
        title: str,
        price: str,
        url: str,
        list_price: Optional[str] = None,
    ) -> bool:
        """
        Send a clean SMS alert when item is back in stock
        Returns True if sent successfully
        """
        short_title = (title[:70] + "...") if len(title) > 70 else title
        now = datetime.now().strftime("%b %d, %Y %H:%M")

        message_lines = [
            "IN STOCK – Amazon.ca Deal!",
            short_title,
            price,
        ]
        if list_price and list_price != price:
            message_lines.append(f"Was {list_price}")

        message_lines.extend([url, f"Sent: {now}"])

        message = "\n".join(message_lines)

        # SMS max length is ~1600, but we keep it short and sweet
        if len(message) > 1600:
            message = message[:1595] + "..."

        try:
            response = self.client.publish(
                PhoneNumber=phone_number,
                Message=message,
                MessageAttributes={
                    "AWS.SNS.SMS.SenderID": {
                        "DataType": "String",
                        "StringValue": "DealAlert",
                    },
                    "AWS.SNS.SMS.SMSType": {
                        "DataType": "String",
                        "StringValue": "Transactional",
                    },
                },
            )
            print(f"SMS sent successfully! MessageId: {response['MessageId']}")
            return True
        except Exception as e:
            print(f"Failed to send SMS: {e}")
            return False
