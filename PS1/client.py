import socket
import json
import time
from utils import HOST, PORT

def send_request(action, data=None):
    """Sends a request to the server and prints the response."""

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((HOST, PORT))

    request = {"action": action, "data": data or {}}
    client.send(json.dumps(request).encode("utf-8"))

    response = json.loads(client.recv(4096).decode("utf-8"))
    print(f"[SERVER RESPONSE] {response}")

    if action == "login" and response.get("status") == "success":
        return response, client
    else:
        client.close()
        return response, None

if __name__ == "__main__":
    # Test account creation
    send_request("create_account", {"username": "test_user", "password": ""}) # Empty password
    send_request("create_account", {"password": "secure123"}) # Missing username
    send_request("create_account", {"username": "test_user", "password": "secure123"})
    send_request("create_account", {"username": "alice", "password": "1234"})
    send_request("create_account", {"username": "bob", "password": "5678"})
    send_request("create_account", {"username": "test_user", "password": "hello123"}) # Existing username

    print("-" * 50)
    
    # Test login
    send_request("login", {"username": "test_user", "password": "hello123"}) # Incorrect password
    test_user_response, test_user_socket = send_request("login", {"username": "test_user", "password": "secure123"})
    alice_response, alice_socket = send_request("login", {"username": "alice", "password": "1234"})

    print("-" * 50)

    # Test sending/receiving messages
    # 1. test_user sends a message to alice. Since alice is online, alice can immediately receive the message
    send_request("send_message", {"session_token": test_user_response["data"]["session_token"], "recipient": "alice", "message": "Hello, Alice!"})
    alice_message = json.loads(alice_socket.recv(4096).decode("utf-8"))
    print(f"[MANUALLY FETCHED MESSAGE] {alice_message}")  # Alice receives the message
    # 2. test_user sends a message to bob. Since bob is offline, the message is stored
    send_request("send_message", {"session_token": test_user_response["data"]["session_token"], "recipient": "bob", "message": "Hello, Bob!"})
    # 3. bob logs in and chooses to read his messages
    bob_response, bob_socket = send_request("login", {"username": "bob", "password": "5678"})
    send_request("read_messages", {"session_token": bob_response["data"]["session_token"]})
    # 4. test_user sends a message to carol. Since carol does not exist, an error is returned
    send_request("send_message", {"session_token": test_user_response["data"]["session_token"], "recipient": "carol", "message": "Hello, Carol!"})
    # 5. Suppose there is a malicious user who tries to send/read messages without verifying the session token
    send_request("send_message", {"session_token": "invalid_token", "username": "alice", "recipient": "bob", "message": "Hello, Bob!"})
    send_request("read_messages", {"session_token": "invalid_token", "username": "bob"})

    print("-" * 50)

    # Test logout
    send_request("logout", {"session_token": test_user_response["data"]["session_token"]})
    send_request("send_message", {"session_token": test_user_response["data"]["session_token"], "recipient": "alice", "message": "Hello again, Alice!"}) # This should fail
    
    # Test Token Expiry
    send_request("send_message", {"session_token": alice_response["data"]["session_token"], "recipient": "bob", "message": "Hi, Bob!"})
    time.sleep(7)  # Wait for token to expire
    send_request("send_message", {"session_token": alice_response["data"]["session_token"], "recipient": "bob", "message": "Hi again, Bob!"})  # This should fail

    # Disconnect sockets
    test_user_socket.close()
    alice_socket.close()
    bob_socket.close()
