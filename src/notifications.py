from exponent_server_sdk import (
    PushClient,
    PushMessage,
    PushServerError,
    DeviceNotRegisteredError,
    PushTicketError,
)

def send_push_notification(expo_token, title, message):
    # Create the PushMessage object
    message = PushMessage(
        to=expo_token,
        title=title,
        body=message,
        data={"message": message}
    )

    # Initialize the PushClient
    try:
        response = PushClient().publish(message)
        response.validate_response()
    except DeviceNotRegisteredError:
        # Handle the case where the device is no longer registered
        print("Device is not registered. Could not send the notification.")
    except PushTicketError as exc:
        # Handle specific errors related to the push ticket
        print(f"Push ticket error: {exc}")
    except PushServerError as exc:
        # Handle server errors
        print(f"Push server error: {exc}")
    except Exception as e:
        # Handle other exceptions
        print(f"Failed to send push notification: {e}")
