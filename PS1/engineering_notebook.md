## Problem Analysis and Planning

### 1. High-Level Design

#### Components

##### Server
- Manages user accounts and authentication.
- Stores and relays messages.
- Handles concurrent client connections.
- Implements a JSON-based wire protocol and another customized wire protocol.
##### Client
- Provides a GUI interface for interaction.
- Supports account creation, login, and messaging.
- Retrieves and displays messages.

### 2. Some of Design Specification

#### Authentication & Security
- Passwords will be **hashed** before storage (e.g., using bcrypt).
- Authentication should be **stateful**, meaning the server maintains session info.

#### Messaging System
- **Instant** delivery if the recipient is online.
- Offline message **storage** for later retrieval.
- Message **retrieval in batches** (user-specified count).

#### Account Management
- **Wildcard search** & **pagination** when listing accounts.
- Semantics for account deletion:
    - Unread messages should be either deleted? (to be specified)

#### Wire Protocol (JSON over Sockets)
- Define a structured message format such as
``` json
{
  "action": "send_message",
  "sender": "Alice",
  "recipient": "Bob",
  "message": "Hello Bob!",
  "timestamp": "2025-02-10T12:00:00Z"
}
```

### 3. Implementation Plan

#### Phase 1: Core Features

- [x] Determine the protocol definition
- [x] Set up server-client socket communication
- [x] Implement account creation & login with secure password handling
- [x] Store user data and messages (initially in-memory, later in a database)
- [x] Implement message sending & retrieval with user authetication (by session tokens)

#### Phase 2: Enhancements

- [ ] Implement wildcard search & pagination for listing accounts
- [x] Implement batch retrieval of messages
- [ ] Implement deletion logic for messages & accounts
- [ ] Introduce a database backend (SQLite or lightweight key-value store, however it could not be able to support concurrency)
- [x] Improve concurrency with threading or async

#### Phase 3: Finalization

- [ ] Build a basic GUI client
- [ ] Change the JSON wire protocol to an optimized one
- [ ] Implement configuration file support
- [ ] Conduct comprehensive testing & documentation
- [ ] Optimize code for future extensibility
- [ ] Check if all requirements have met


## Development Steps

### 1. JSON Wire Protocol Definition

#### General Structure

Every message exchanged between the client and server follows this structure:

``` json
{
  "action": "<operation_name>",
  "data": { ... },
  "status": "<optional_status>",
  "error": "<optional_error_message>"
}
```

- action: Specifies the operation (e.g., create_account, send_message).
- data: Contains request or response details, varying by action.
- status (optional): Server response status (success, error, etc.).
- error (optional): A human-readable error message if applicable.

#### Create Account

Request
``` json
{
  "action": "create_account",
  "data": {
    "username": "Alice",
    "password": "<hashed_password>"
  }
}
```
Response
``` json
{
  "action": "create_account",
  "status": "success"
}
```
OR (if username already exists)
``` json
{
  "action": "create_account",
  "status": "error",
  "error": "Username already exists"
}
```

#### Log in
Request
``` json
{
  "action": "login",
  "data": {
    "username": "Alice",
    "password": "<hashed_password>"
  }
}
```
Response
``` json
{
  "action": "login",
  "status": "success",
  "data": {
    "unread_messages": 3
  }
}
```
OR (if authentication fails)

``` json
{
  "action": "login",
  "status": "error",
  "error": "Invalid username or password"
}
```

#### List Accounts
Request
``` json
{
  "action": "list_accounts",
  "data": {
    "pattern": "Al*",
    "page": 1, 
    "page_size": 10
  }
}
```
Response
``` json
{
  "action": "list_accounts",
  "status": "success",
  "data": {
    "accounts": ["Alice", "Alex", "Alan"],
    "total_pages": 2
  }
}
```

#### Send Message
Request
``` json
{
  "action": "send_message",
  "data": {
    "sender": "Alice",
    "recipient": "Bob",
    "message": "Hello Bob!",
    "timestamp": "2025-02-10T12:00:00Z"
  }
}
```
Response
``` json
{
  "action": "send_message",
  "status": "success"
}
```

#### Read Messages
Request
``` json
{
  "action": "read_messages",
  "data": {
    "username": "Bob",
    "count": 5
  }
}
```
Response
``` json
{
  "action": "read_messages",
  "status": "success",
  "data": {
    "messages": [
      {
        "sender": "Alice",
        "message": "Hello Bob!",
        "timestamp": "2025-02-10T12:00:00Z"
      }
    ]
  }
}
```

#### Delete Message
Request
``` json
{
  "action": "delete_message",
  "data": {
    "username": "Bob",
    "message_id": "12345"
  }
}
```
Response
``` json
{
  "action": "delete_message",
  "status": "success"
}
```

#### Delete Account
Request
``` json
{
  "action": "delete_account",
  "data": {
    "username": "Alice"
  }
}
```
Response
``` json
{
  "action": "delete_account",
  "status": "success"
}
```

### 2. Basic Server-Client Socket Setup

#### Key Features of Server
- [x] Accepts multiple client connections.
- [x] Listens for incoming JSON requests.
- [x] Parses and responds to client requests (at least in a dummy way).

#### Key Features of Client
- [x] Connects to the server.
- [x] Sends JSON requests and receives responses.

#### Testing

Start the server in one terminal:
``` sh
python server.py
```

Run the client in another terminal (or multiple terminals, to simulate concurrent requests):
``` sh
python client.py
```

Expected output on the server:
```
[SERVER STARTED] Listening on 127.0.0.1:54400

[NEW CONNECTION] ('127.0.0.1', 53578) connected.
[REQUEST FROM ('127.0.0.1', 53578)] {'action': 'ping', 'data': {}}
```
Expected output on the client:
```
[SERVER RESPONSE] {'action': 'ping', 'status': 'success', 'message': 'Pong!'}
```
If we have multiple client running at the same time, the requests can be concurrently (well, at least it looks like so when using `time.sleep` to simulate processing) processed since multi-threading is used.

### 3. Update Server with User Account Management

#### Key Additions
- [x] Account Creation: Store username-password pairs securely.
- [x] Login Handling: Authenticate users correctly.
- [x] Basic In-Memory User Store (to be replaced with persistent storage later).

#### Testing
Run the server in one terminal:
``` sh
python server.py
```

Run the client in another terminal:
``` sh
python client.py
```

Expected Output on the client:
```
[SERVER RESPONSE] {'action': 'create_account', 'status': 'error', 'error': 'Missing username or password'}
[SERVER RESPONSE] {'action': 'create_account', 'status': 'error', 'error': 'Missing username or password'}
[SERVER RESPONSE] {'action': 'create_account', 'status': 'success', 'message': 'Account created successfully'}
[SERVER RESPONSE] {'action': 'create_account', 'status': 'error', 'error': 'Username already exists'}
[SERVER RESPONSE] {'action': 'login', 'status': 'error', 'error': 'Incorrect password'}
[SERVER RESPONSE] {'action': 'login', 'status': 'success', 'message': 'Login successful'}
```

### 4. Update Server with Messaging Functionality and User Session Tracking

#### Key Additions
- [x] Send a message to an online or offline user.
- [x] Store undelivered messages until the recipient logs in.
- [x] Retrieve messages when the user requests them, with number of messages designated by the user (positive number ~ reading from latest; negative number ~ reading from earliest)
- [x] Maintain a session list to validate if a request is coming from a logged-in user
- [x] Add session token expiry with a background thread cleaning-up tokens to improve security.

#### Issues
- [x] In the line `data = client_socket.recv(1024).decode("utf-8")`, the server seems not to keep waiting for the requests from client; rather it just goes to the break statement and disconnect the client. This will prevent from sending a message to the recipient immediately if online, since the connection does not exist anymore. [Solved: This is actually because the socket object in the client side is dead outside of the function. The solution is to maintain that object]
- [ ] Even if the above issue is solved, or say the server has the connection to send messages to the recipient, the recipient does not keep receiving messages from the server to display. [For now let's just manually fetch the message; later it will be changed into multi-threading.]

#### Testing
Run the server in one terminal:
``` sh
python server.py
```

Run the client in another terminal:
``` sh
python client.py
```

Expected Output on the server:
```
[SERVER STARTED] Listening on 127.0.0.1:54400

[NEW CONNECTION] ('127.0.0.1', 59928) connected.
[REQUEST FROM ('127.0.0.1', 59928)] {'action': 'create_account', 'data': {'username': 'test_user', 'password': ''}}

[DISCONNECTED] ('127.0.0.1', 59928) disconnected.

[NEW CONNECTION] ('127.0.0.1', 59929) connected.
[REQUEST FROM ('127.0.0.1', 59929)] {'action': 'create_account', 'data': {'password': 'secure123'}}

[DISCONNECTED] ('127.0.0.1', 59929) disconnected.

[NEW CONNECTION] ('127.0.0.1', 59930) connected.
[REQUEST FROM ('127.0.0.1', 59930)] {'action': 'create_account', 'data': {'username': 'test_user', 'password': 'secure123'}}

[DISCONNECTED] ('127.0.0.1', 59930) disconnected.

[NEW CONNECTION] ('127.0.0.1', 59931) connected.
[REQUEST FROM ('127.0.0.1', 59931)] {'action': 'create_account', 'data': {'username': 'alice', 'password': '1234'}}

[DISCONNECTED] ('127.0.0.1', 59931) disconnected.

[NEW CONNECTION] ('127.0.0.1', 59932) connected.
[REQUEST FROM ('127.0.0.1', 59932)] {'action': 'create_account', 'data': {'username': 'bob', 'password': '5678'}}

[DISCONNECTED] ('127.0.0.1', 59932) disconnected.

[NEW CONNECTION] ('127.0.0.1', 59933) connected.
[REQUEST FROM ('127.0.0.1', 59933)] {'action': 'create_account', 'data': {'username': 'test_user', 'password': 'hello123'}}

[DISCONNECTED] ('127.0.0.1', 59933) disconnected.

[NEW CONNECTION] ('127.0.0.1', 59934) connected.
[REQUEST FROM ('127.0.0.1', 59934)] {'action': 'login', 'data': {'username': 'test_user', 'password': 'hello123'}}

[DISCONNECTED] ('127.0.0.1', 59934) disconnected.

[NEW CONNECTION] ('127.0.0.1', 59935) connected.
[REQUEST FROM ('127.0.0.1', 59935)] {'action': 'login', 'data': {'username': 'test_user', 'password': 'secure123'}}

[NEW CONNECTION] ('127.0.0.1', 59936) connected.
[REQUEST FROM ('127.0.0.1', 59936)] {'action': 'login', 'data': {'username': 'alice', 'password': '1234'}}

[NEW CONNECTION] ('127.0.0.1', 59937) connected.
[REQUEST FROM ('127.0.0.1', 59937)] {'action': 'send_message', 'data': {'session_token': '7f969921-6a31-473c-b43d-73f8644b2d0c', 'recipient': 'alice', 'message': 'Hello, Alice!'}}

[DISCONNECTED] ('127.0.0.1', 59937) disconnected.

[NEW CONNECTION] ('127.0.0.1', 59938) connected.
[REQUEST FROM ('127.0.0.1', 59938)] {'action': 'send_message', 'data': {'session_token': '7f969921-6a31-473c-b43d-73f8644b2d0c', 'recipient': 'bob', 'message': 'Hello, Bob!'}}

[DISCONNECTED] ('127.0.0.1', 59938) disconnected.

[NEW CONNECTION] ('127.0.0.1', 59939) connected.
[REQUEST FROM ('127.0.0.1', 59939)] {'action': 'login', 'data': {'username': 'bob', 'password': '5678'}}

[NEW CONNECTION] ('127.0.0.1', 59940) connected.
[REQUEST FROM ('127.0.0.1', 59940)] {'action': 'read_messages', 'data': {'session_token': '210f31fd-cdcd-4dd9-beb8-1ffd167ebd12'}}

[DISCONNECTED] ('127.0.0.1', 59940) disconnected.

[NEW CONNECTION] ('127.0.0.1', 59941) connected.
[REQUEST FROM ('127.0.0.1', 59941)] {'action': 'send_message', 'data': {'session_token': '7f969921-6a31-473c-b43d-73f8644b2d0c', 'recipient': 'carol', 'message': 'Hello, Carol!'}}

[DISCONNECTED] ('127.0.0.1', 59941) disconnected.

[NEW CONNECTION] ('127.0.0.1', 59942) connected.
[REQUEST FROM ('127.0.0.1', 59942)] {'action': 'send_message', 'data': {'session_token': 'invalid_token', 'username': 'alice', 'recipient': 'bob', 'message': 'Hello, Bob!'}}

[DISCONNECTED] ('127.0.0.1', 59942) disconnected.

[NEW CONNECTION] ('127.0.0.1', 59943) connected.
[REQUEST FROM ('127.0.0.1', 59943)] {'action': 'read_messages', 'data': {'session_token': 'invalid_token', 'username': 'bob'}}

[DISCONNECTED] ('127.0.0.1', 59943) disconnected.

[NEW CONNECTION] ('127.0.0.1', 59944) connected.
[REQUEST FROM ('127.0.0.1', 59944)] {'action': 'logout', 'data': {'session_token': '7f969921-6a31-473c-b43d-73f8644b2d0c'}}

[DISCONNECTED] ('127.0.0.1', 59935) disconnected.

[DISCONNECTED] ('127.0.0.1', 59944) disconnected.

[NEW CONNECTION] ('127.0.0.1', 59945) connected.
[REQUEST FROM ('127.0.0.1', 59945)] {'action': 'send_message', 'data': {'session_token': '7f969921-6a31-473c-b43d-73f8644b2d0c', 'recipient': 'alice', 'message': 'Hello again, Alice!'}}

[DISCONNECTED] ('127.0.0.1', 59945) disconnected.

[NEW CONNECTION] ('127.0.0.1', 59946) connected.
[REQUEST FROM ('127.0.0.1', 59946)] {'action': 'send_message', 'data': {'session_token': 'a2bb7f61-ac84-43f1-972d-0397a390f65f', 'recipient': 'bob', 'message': 'Hi, Bob!'}}

[DISCONNECTED] ('127.0.0.1', 59946) disconnected.

[DISCONNECTED] ('127.0.0.1', 59936) disconnected.

[DISCONNECTED] ('127.0.0.1', 59939) disconnected.

[NEW CONNECTION] ('127.0.0.1', 60032) connected.
[REQUEST FROM ('127.0.0.1', 60032)] {'action': 'send_message', 'data': {'session_token': 'a2bb7f61-ac84-43f1-972d-0397a390f65f', 'recipient': 'bob', 'message': 'Hi again, Bob!'}}

[DISCONNECTED] ('127.0.0.1', 60032) disconnected.
```

Expected Output on the client:
```
[SERVER RESPONSE] {'action': 'create_account', 'status': 'error', 'error': 'Missing username or password'}
[SERVER RESPONSE] {'action': 'create_account', 'status': 'error', 'error': 'Missing username or password'}
[SERVER RESPONSE] {'action': 'create_account', 'status': 'success'}
[SERVER RESPONSE] {'action': 'create_account', 'status': 'success'}
[SERVER RESPONSE] {'action': 'create_account', 'status': 'success'}
[SERVER RESPONSE] {'action': 'create_account', 'status': 'error', 'error': 'Username already exists'}
--------------------------------------------------
[SERVER RESPONSE] {'action': 'login', 'status': 'error', 'error': 'Incorrect password'}
[SERVER RESPONSE] {'action': 'login', 'status': 'success', 'data': {'session_token': '7f969921-6a31-473c-b43d-73f8644b2d0c', 'unread_message_count': 0}}
[SERVER RESPONSE] {'action': 'login', 'status': 'success', 'data': {'session_token': 'a2bb7f61-ac84-43f1-972d-0397a390f65f', 'unread_message_count': 0}}
--------------------------------------------------
[SERVER RESPONSE] {'action': 'send_message', 'status': 'success'}
[MANUALLY FETCHED MESSAGE] {'action': 'receive_message', 'data': {'sender': 'test_user', 'message': 'Hello, Alice!'}}
[SERVER RESPONSE] {'action': 'send_message', 'status': 'success'}
[SERVER RESPONSE] {'action': 'login', 'status': 'success', 'data': {'session_token': '210f31fd-cdcd-4dd9-beb8-1ffd167ebd12', 'unread_message_count': 1}}
[SERVER RESPONSE] {'action': 'read_messages', 'status': 'success', 'data': {'unread_messages': [{'from': 'test_user', 'message': 'Hello, Bob!'}]}}
[SERVER RESPONSE] {'action': 'send_message', 'status': 'error', 'error': 'Recipient does not exist'}
[SERVER RESPONSE] {'action': 'send_message', 'status': 'error', 'error': 'Invalid session'}
[SERVER RESPONSE] {'action': 'read_messages', 'status': 'error', 'error': 'Invalid session'}
--------------------------------------------------
[SERVER RESPONSE] {'action': 'logout', 'status': 'success'}
[SERVER RESPONSE] {'action': 'send_message', 'status': 'error', 'error': 'Invalid session'}
[SERVER RESPONSE] {'action': 'send_message', 'status': 'success'}
[SERVER RESPONSE] {'action': 'send_message', 'status': 'error', 'error': 'Invalid session'}
```

### * Migrate the In-Memory Dictionary Storage to Database Storage

This seem to cause error "database is locked", probably resulting from that we are using multi-threading and SQLite does not support high concurrency by default. This issue hasn't been solved yet.

### 5. List Accounts with Wildcard Search

#### Key Fetures

- [x] List all usernames if no wildcard is provided.
- [x] Support wildcard search using * (e.g., a* matches alice, andy but not bob).
- [x] Require authentication similarly.
- [x] Paginate results to avoid sending too many usernames at once.

#### Testing
Run the server in one terminal:
``` sh
python server.py
```

Run the client in another terminal:
``` sh
python client.py
```

Expected Output on the server:
```
[SERVER STARTED] Listening on 127.0.0.1:54400

[NEW CONNECTION] ('127.0.0.1', 56429) connected.
[REQUEST FROM ('127.0.0.1', 56429)] {'action': 'create_account', 'data': {'username': 'andy', 'password': 'andy123'}}

[DISCONNECTED] ('127.0.0.1', 56429) disconnected.

[NEW CONNECTION] ('127.0.0.1', 56430) connected.
[REQUEST FROM ('127.0.0.1', 56430)] {'action': 'create_account', 'data': {'username': 'alex', 'password': 'alex123'}}

[DISCONNECTED] ('127.0.0.1', 56430) disconnected.

[NEW CONNECTION] ('127.0.0.1', 56431) connected.
[REQUEST FROM ('127.0.0.1', 56431)] {'action': 'create_account', 'data': {'username': 'Andrew', 'password': 'Andrew123'}}

[DISCONNECTED] ('127.0.0.1', 56431) disconnected.

[NEW CONNECTION] ('127.0.0.1', 56432) connected.
[REQUEST FROM ('127.0.0.1', 56432)] {'action': 'create_account', 'data': {'username': 'bob', 'password': 'bob123'}}

[DISCONNECTED] ('127.0.0.1', 56432) disconnected.

[NEW CONNECTION] ('127.0.0.1', 56433) connected.
[REQUEST FROM ('127.0.0.1', 56433)] {'action': 'login', 'data': {'username': 'andy', 'password': 'andy123'}}

[NEW CONNECTION] ('127.0.0.1', 56434) connected.
[REQUEST FROM ('127.0.0.1', 56434)] {'action': 'list_accounts', 'data': {'session_token': '4e0d42fb-da68-451f-b397-162b87dc5691', 'pattern': 'a*', 'page': 1, 'page_size': 5}}

[DISCONNECTED] ('127.0.0.1', 56434) disconnected.

[NEW CONNECTION] ('127.0.0.1', 56435) connected.
[REQUEST FROM ('127.0.0.1', 56435)] {'action': 'list_accounts', 'data': {'session_token': '4e0d42fb-da68-451f-b397-162b87dc5691'}}

[DISCONNECTED] ('127.0.0.1', 56435) disconnected.

[DISCONNECTED] ('127.0.0.1', 56433) disconnected.
```

Expected Output on the client:
```
[SERVER RESPONSE] {'action': 'create_account', 'status': 'success'}
[SERVER RESPONSE] {'action': 'create_account', 'status': 'success'}
[SERVER RESPONSE] {'action': 'create_account', 'status': 'success'}
[SERVER RESPONSE] {'action': 'create_account', 'status': 'success'}
[SERVER RESPONSE] {'action': 'login', 'status': 'success', 'data': {'session_token': '4e0d42fb-da68-451f-b397-162b87dc5691', 'unread_message_count': 0}}
[SERVER RESPONSE] {'action': 'list_accounts', 'status': 'success', 'data': {'accounts': ['alex', 'andy'], 'page': 1, 'total_pages': 1}}
[SERVER RESPONSE] {'action': 'list_accounts', 'status': 'success', 'data': {'accounts': ['Andrew', 'alex', 'andy', 'bob'], 'page': 1, 'total_pages': 1}}
```

