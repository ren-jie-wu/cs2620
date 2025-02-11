import socket
import json

HOST = "127.0.0.1"
PORT = 54400

def send_request(action, data=None):
    """Sends a request to the server and prints the response."""
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((HOST, PORT))

    request = {"action": action, "data": data or {}}
    client.send(json.dumps(request).encode("utf-8"))

    response = json.loads(client.recv(1024).decode("utf-8"))
    print(f"[SERVER RESPONSE] {response}")

    if action == "login" and response.get("status") == "success":
        pass
    else:
        client.close()
    return response

if __name__ == "__main__":
    # Test account creation
    send_request("create_account", {"username": "test_user", "password": ""}) # Empty password
    send_request("create_account", {"password": "secure123"}) # Missing username
    send_request("create_account", {"username": "test_user", "password": "secure123"})
    send_request("create_account", {"username": "alice", "password": "1234"})
    send_request("create_account", {"username": "bob", "password": "5678"})
    send_request("create_account", {"username": "test_user", "password": "hello123"}) # Existing username
    
    # Test login
    print("-" * 50)
    send_request("login", {"username": "test_user", "password": "hello123"}) # Incorrect password
    test_user_response = send_request("login", {"username": "test_user", "password": "secure123"})
    alice_response = send_request("login", {"username": "alice", "password": "1234"})

    # Test sending/receiving messages
    print("-" * 50)
    # 1. test_user sends a message to alice. Since alice is online, alice can immediately receive the message
    send_request("send_message", {"session_token": test_user_response["data"]["session_token"], "recipient": "alice", "message": "Hello, Alice!"})
    # 2. test_user sends a message to bob. Since bob is offline, the message is stored
    send_request("send_message", {"session_token": test_user_response["data"]["session_token"], "recipient": "bob", "message": "Hello, Bob!"})
    # 3. bob logs in and chooses to read his messages
    bob_response = send_request("login", {"username": "bob", "password": "5678"})
    send_request("read_messages", {"session_token": bob_response["data"]["session_token"]})
    # 4. test_user sends a message to carol. Since carol does not exist, an error is returned
    send_request("send_message", {"session_token": test_user_response["data"]["session_token"], "recipient": "carol", "message": "Hello, Carol!"})
    # 5. Suppose there is a malicious user who tries to send/read messages without verifying the session token
    send_request("send_message", {"session_token": "invalid_token", "username": "alice", "recipient": "bob", "message": "Hello, Bob!"})
    send_request("read_messages", {"session_token": "invalid_token", "username": "bob"})

    # Test logout
    print("-" * 50)
    send_request("logout", {"session_token": test_user_response["data"]["session_token"]})
    send_request("send_message", {"session_token": test_user_response["data"]["session_token"], "recipient": "alice", "message": "Hello again, Alice!"}) # This should fail