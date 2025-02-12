import socket
import threading
import json
import time  # noqa: F401
import fnmatch
from utils import hash_password, generate_token, cleanup_expired_sessions, HOST, PORT, TOKEN_EXPIRY_TIME

# Server State (in-memory storage)
users = {}  # Stores {username: password_hash}
messages = {}  # Stores {recipient: [unread_message1, unread_message2, ...]}
clients = {}  # Stores {logged_in_username: client_socket}
sessions = {}  # Stores {session_token: {username, expiry_time}}

def handle_client(client_socket, address):
    """Handles communication with a single client."""
    print(f"\n[NEW CONNECTION] {address} connected.")

    try:
        while True:
            # If the client-side socket is dead or closed, it will enter the break block and then disconnect
            # If the server-side socket is closed, it will throw "Bad file descriptor" error, and then disconnect
            data = client_socket.recv(1024).decode("utf-8")
            if not data:
                break

            request = json.loads(data)
            print(f"[REQUEST FROM {address}] {request}")

            response = process_request(request, client_socket)
            client_socket.send(json.dumps(response).encode("utf-8"))
    except OSError:
        pass  # Ignore "Bad file descriptor" error, which occurs when the socket has been closed
    except Exception as e:
        print(f"[ERROR] {e.__class__.__name__} {e} occurred for {address}")
    finally:
        client_socket.close()
        print(f"\n[DISCONNECTED] {address} disconnected.")

def process_request(request, client_socket):
    """Processes the client's request and returns a response."""
    action = request.get("action")
    data = request.get("data", {})

    if action == "create_account":
        username, password = data.get("username"), data.get("password")

        if not username or not password:
            return {"action": "create_account", "status": "error", "error": "Missing username or password"}
        
        if username in users:
            return {"action": "create_account", "status": "error", "error": "Username already exists"}
        
        users[username] = hash_password(password)
        messages[username] = [] # Initialize an empty list for the user's messages
        return {"action": "create_account", "status": "success"}
    
    elif action == "login":
        username, password = data.get("username"), data.get("password")

        if username not in users:
            return {"action": "login", "status": "error", "error": "User does not exist"}
        
        if users[username] != hash_password(password):
            return {"action": "login", "status": "error", "error": "Incorrect password"}
        
        clients[username] = client_socket
        session_token = generate_token()
        sessions[session_token] = {"username": username, "expiry_time": time.time() + TOKEN_EXPIRY_TIME}
        unread_count = len(messages.get(username, []))
        return {"action": "login", "status": "success", "data": {"session_token": session_token, "unread_message_count": unread_count}}
    
    elif action == "list_accounts":
        session_token = data.get("session_token")

        if not session_token:
            return {"action": "list_accounts", "status": "error", "error": "Invalid session"}
        
        pattern = data.get("pattern", "*")
        page = data.get("page", 1)
        page_size = data.get("page_size", 10)
        try:
            page = int(page)
            page_size = int(page_size)
            assert page > 0 and page_size > 0
        except Exception:
            return {"action": "list_accounts", "status": "error", "error": "Invalid page or page size"}

        matched_users = sorted(fnmatch.filter(users.keys(), pattern))
        
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        paginated_users = matched_users[start_index:end_index]

        return {"action": "list_accounts", "status": "success", "data": {"accounts": paginated_users, "page": page, "total_pages": (len(matched_users) - 1) // page_size + 1}}

    elif action == "send_message":
        session_token = data.get("session_token")
        sender = sessions.get(session_token, {}).get("username")  # Validate session token
        recipient, message = data.get("recipient"), data.get("message")

        if not sender:
            return {"action": "send_message", "status": "error", "error": "Invalid session"}
        
        if not recipient or not message:
            return {"action": "send_message", "status": "error", "error": "Missing recipient or message"}

        if recipient not in users:
            return {"action": "send_message", "status": "error", "error": "Recipient does not exist"}

        if recipient in clients and clients[recipient].fileno() != -1:  # Check if recipient is online
            clients[recipient].send(json.dumps({"action": "receive_message", "data": {"sender": sender, "message": message}}).encode("utf-8"))
        else:
            messages[recipient].append({"from": sender, "message": message})  # Store if offline

        return {"action": "send_message", "status": "success"}

    elif action == "read_messages":
        session_token = data.get("session_token")
        username = sessions.get(session_token, {}).get("username")  # Validate session token

        num_to_read = data.get("num_to_read", 1)  # if num_to_read is positive, read from the latest message; if negative, read from the oldest message
        try:
            num_to_read = int(num_to_read)
        except Exception:
            return {"action": "read_messages", "status": "error", "error": "Invalid number of messages to read"}

        if not username:
            return {"action": "read_messages", "status": "error", "error": "Invalid session"}
        
        if num_to_read < 0:
            user_messages = messages.get(username, [])[:-num_to_read]
            messages[username] = messages.get(username, [])[-num_to_read:]  # Remove read messages
        else:
            user_messages = messages.get(username, [])[-num_to_read:]
            messages[username] = messages.get(username, [])[:-num_to_read]  # Remove read messages
        return {"action": "read_messages", "status": "success", "data": {"unread_messages": user_messages}}
    
    elif action == "logout":
        session_token = data.get("session_token")
        username = sessions.get(session_token, {}).get("username")  # Validate session token

        if not username:
            return {"action": "logout", "status": "error", "error": "Invalid session"}

        clients[username].close()
        del clients[username]
        del sessions[session_token]
        return {"action": "logout", "status": "success"}
    
    return {"action": action, "status": "error", "error": "Invalid request"}

def start_server():
    """Starts the server and listens for incoming connections."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind((HOST, PORT))
        server.listen(5)
        print(f"[SERVER STARTED] Listening on {HOST}:{PORT}")

        while True:
            try:
                client_socket, addr = server.accept()
            except KeyboardInterrupt:
                print("\n[SERVER STOPPED] Exiting...")
                break
            client_thread = threading.Thread(target=handle_client, args=(client_socket, addr))
            client_thread.start()
    return

if __name__ == "__main__":
    threading.Thread(target=cleanup_expired_sessions, args=(sessions, clients), daemon=True).start()
    start_server()

# TODO list: 
# Must have:
# Implement another wire protocol other than JSON (e.g., Protocol Buffers like)

# Nice to have:
# Implement thread safety for managing concurrent clients (e.g., using locks)
# Implement a database for storing user data
