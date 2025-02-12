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

def test_account_creation():
    # 1. Empty password
    send_request("create_account", {"username": "test_user", "password": ""}) 

    # 2. Missing username
    send_request("create_account", {"password": "secure123"})

    # Create accounts for test_user, alice, and bob
    send_request("create_account", {"username": "test_user", "password": "secure123"})
    send_request("create_account", {"username": "alice", "password": "1234"})
    send_request("create_account", {"username": "bob", "password": "5678"})

    # 3. Username already exists
    send_request("create_account", {"username": "test_user", "password": "hello123"}) 

def test_login():
    global test_user_response, test_user_socket, alice_response, alice_socket

    # 1. Incorrect username
    send_request("login", {"username": "test_user", "password": "hello123"})

    # 2. Login for test_user and alice
    test_user_response, test_user_socket = send_request("login", {"username": "test_user", "password": "secure123"})
    alice_response, alice_socket = send_request("login", {"username": "alice", "password": "1234"})

def test_messaging():
    global bob_socket

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

def test_logout():
    # test_user logs out
    send_request("logout", {"session_token": test_user_response["data"]["session_token"]})

    # 1. test_user tries to send a message to alice after logging out
    send_request("send_message", {"session_token": test_user_response["data"]["session_token"], "recipient": "alice", "message": "Hello again, Alice!"})

def test_token_expiry():
    # 1. alice sends a message to bob. alice's token has not expired, so the message is sent successfully
    send_request("send_message", {"session_token": alice_response["data"]["session_token"], "recipient": "bob", "message": "Hi, Bob!"})

    time.sleep(7)  # Wait for token to expire

    # 2. alice sends a message to bob. alice's token has expired, so the message is not sent
    send_request("send_message", {"session_token": alice_response["data"]["session_token"], "recipient": "bob", "message": "Hi again, Bob!"})

def test_list_accounts():
    send_request("create_account", {"username": "andy", "password": "andy123"})
    send_request("create_account", {"username": "alex", "password": "alex123"})
    send_request("create_account", {"username": "Andrew", "password": "Andrew123"})
    send_request("create_account", {"username": "bob", "password": "bob123"})
    andy_response, _ = send_request("login", {"username": "andy", "password": "andy123"})
    send_request("list_accounts", {"session_token": andy_response["data"]["session_token"], "pattern": "a*", "page": 1, "page_size": 5})
    send_request("list_accounts", {"session_token": andy_response["data"]["session_token"]})

if __name__ == "__main__":
    # step 4 testing
    # test_account_creation()
    # print("-" * 50)
    # test_login()
    # print("-" * 50)
    # test_messaging()
    # print("-" * 50)
    # test_logout()
    # print("-" * 50)
    # test_token_expiry()

    # step 5 testing
    test_list_accounts()
