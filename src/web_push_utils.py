from pywebpush import webpush, WebPushException
import os, json

VAPID_PRIVATE_KEY = os.getenv("VAPID_PRIVATE_KEY")
VAPID_CLAIMS = {"sub": "mailto:youremail@example.com"}

async def send_web_push(subscription_info: dict, message_body: str):
    try:
        webpush(
            subscription_info=subscription_info,
            data=json.dumps({"message": message_body}),
            vapid_private_key=VAPID_PRIVATE_KEY,
            vapid_claims=VAPID_CLAIMS
        )
    except WebPushException as e:
        print(f"Error sending push notification: {e}")
