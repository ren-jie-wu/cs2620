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
- [ ] Introduce a database backend (SQLite or lightweight key-value store)
- [ ] Improve concurrency with threading or async

#### Phase 3: Finalization

- [ ] Build a basic GUI client
- [ ] Change the JSON wire protocol to an optimized one
- [ ] Implement configuration file support
- [ ] Conduct comprehensive testing & documentation
- [ ] Optimize code for future extensibility


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
- [x] Retrieve messages when the user requests them.
- [x] Maintain a session list to validate if a request is coming from a logged-in user

#### Unsolved Issues
- [ ] In the line `data = client_socket.recv(1024).decode("utf-8")`, the server seems not to keep waiting for the requests from client; rather it just goes to the break statement and disconnect the client. This will prevent from sending a message to the recipient immediately if online, since the connection does not exist anymore.
- [ ] Even if the above issue is solved, or say the server has the connection to send messages to the recipient, the recipient does not keep receiving messages from the server to display.

#### Testing
Run the server in one terminal:
``` sh
python server.py
```

Run the client in another terminal:
``` sh
python client.py
```

Expected Output on the server (the client side output are just simply those outputs which starts from `[RESPONSE TO ...]` on the server side):
```
[SERVER STARTED] Listening on 127.0.0.1:54400

[NEW CONNECTION] ('127.0.0.1', 55982) connected.
[REQUEST FROM ('127.0.0.1', 55982)] {'action': 'create_account', 'data': {'username': 'test_user', 'password': ''}}
[RESPONSE TO ('127.0.0.1', 55982)] {'action': 'create_account', 'status': 'error', 'error': 'Missing username or password'}
[DISCONNECTED] ('127.0.0.1', 55982) disconnected.

[NEW CONNECTION] ('127.0.0.1', 55983) connected.
[REQUEST FROM ('127.0.0.1', 55983)] {'action': 'create_account', 'data': {'password': 'secure123'}}
[RESPONSE TO ('127.0.0.1', 55983)] {'action': 'create_account', 'status': 'error', 'error': 'Missing username or password'}
[DISCONNECTED] ('127.0.0.1', 55983) disconnected.

[NEW CONNECTION] ('127.0.0.1', 55984) connected.
[REQUEST FROM ('127.0.0.1', 55984)] {'action': 'create_account', 'data': {'username': 'test_user', 'password': 'secure123'}}
[RESPONSE TO ('127.0.0.1', 55984)] {'action': 'create_account', 'status': 'success'}
[DISCONNECTED] ('127.0.0.1', 55984) disconnected.

[NEW CONNECTION] ('127.0.0.1', 55985) connected.
[REQUEST FROM ('127.0.0.1', 55985)] {'action': 'create_account', 'data': {'username': 'alice', 'password': '1234'}}
[RESPONSE TO ('127.0.0.1', 55985)] {'action': 'create_account', 'status': 'success'}
[DISCONNECTED] ('127.0.0.1', 55985) disconnected.

[NEW CONNECTION] ('127.0.0.1', 55986) connected.
[REQUEST FROM ('127.0.0.1', 55986)] {'action': 'create_account', 'data': {'username': 'bob', 'password': '5678'}}
[RESPONSE TO ('127.0.0.1', 55986)] {'action': 'create_account', 'status': 'success'}
[DISCONNECTED] ('127.0.0.1', 55986) disconnected.

[NEW CONNECTION] ('127.0.0.1', 55987) connected.
[REQUEST FROM ('127.0.0.1', 55987)] {'action': 'create_account', 'data': {'username': 'test_user', 'password': 'hello123'}}
[RESPONSE TO ('127.0.0.1', 55987)] {'action': 'create_account', 'status': 'error', 'error': 'Username already exists'}
[DISCONNECTED] ('127.0.0.1', 55987) disconnected.

[NEW CONNECTION] ('127.0.0.1', 55988) connected.
[REQUEST FROM ('127.0.0.1', 55988)] {'action': 'login', 'data': {'username': 'test_user', 'password': 'hello123'}}
[RESPONSE TO ('127.0.0.1', 55988)] {'action': 'login', 'status': 'error', 'error': 'Incorrect password'}
[DISCONNECTED] ('127.0.0.1', 55988) disconnected.

[NEW CONNECTION] ('127.0.0.1', 55989) connected.
[REQUEST FROM ('127.0.0.1', 55989)] {'action': 'login', 'data': {'username': 'test_user', 'password': 'secure123'}}
[RESPONSE TO ('127.0.0.1', 55989)] {'action': 'login', 'status': 'success', 'data': {'session_token': '284c24a4-8243-441c-bf51-07a4721d5a2d', 'unread_message_count': 0}}
[DISCONNECTED] ('127.0.0.1', 55989) disconnected.

[NEW CONNECTION] ('127.0.0.1', 55990) connected.
[REQUEST FROM ('127.0.0.1', 55990)] {'action': 'login', 'data': {'username': 'alice', 'password': '1234'}}
[RESPONSE TO ('127.0.0.1', 55990)] {'action': 'login', 'status': 'success', 'data': {'session_token': '2611dc40-3494-403b-85a9-81694f376aa6', 'unread_message_count': 0}}
[DISCONNECTED] ('127.0.0.1', 55990) disconnected.

[NEW CONNECTION] ('127.0.0.1', 55991) connected.
[REQUEST FROM ('127.0.0.1', 55991)] {'action': 'send_message', 'data': {'session_token': '284c24a4-8243-441c-bf51-07a4721d5a2d', 'recipient': 'alice', 'message': 'Hello, Alice!'}}
[RESPONSE TO ('127.0.0.1', 55991)] {'action': 'send_message', 'status': 'success'}
[DISCONNECTED] ('127.0.0.1', 55991) disconnected.

[NEW CONNECTION] ('127.0.0.1', 55992) connected.
[REQUEST FROM ('127.0.0.1', 55992)] {'action': 'send_message', 'data': {'session_token': '284c24a4-8243-441c-bf51-07a4721d5a2d', 'recipient': 'bob', 'message': 'Hello, Bob!'}}
[RESPONSE TO ('127.0.0.1', 55992)] {'action': 'send_message', 'status': 'success'}
[DISCONNECTED] ('127.0.0.1', 55992) disconnected.

[NEW CONNECTION] ('127.0.0.1', 55993) connected.
[REQUEST FROM ('127.0.0.1', 55993)] {'action': 'login', 'data': {'username': 'bob', 'password': '5678'}}
[RESPONSE TO ('127.0.0.1', 55993)] {'action': 'login', 'status': 'success', 'data': {'session_token': 'f9bf6859-1c27-4f48-bbb6-90f8711c8561', 'unread_message_count': 1}}
[DISCONNECTED] ('127.0.0.1', 55993) disconnected.

[NEW CONNECTION] ('127.0.0.1', 55994) connected.
[REQUEST FROM ('127.0.0.1', 55994)] {'action': 'read_messages', 'data': {'session_token': 'f9bf6859-1c27-4f48-bbb6-90f8711c8561'}}
[RESPONSE TO ('127.0.0.1', 55994)] {'action': 'read_messages', 'status': 'success', 'data': {'unread_messages': [{'from': 'test_user', 'message': 'Hello, Bob!'}]}}
[DISCONNECTED] ('127.0.0.1', 55994) disconnected.

[NEW CONNECTION] ('127.0.0.1', 55995) connected.
[REQUEST FROM ('127.0.0.1', 55995)] {'action': 'send_message', 'data': {'session_token': '284c24a4-8243-441c-bf51-07a4721d5a2d', 'recipient': 'carol', 'message': 'Hello, Carol!'}}
[RESPONSE TO ('127.0.0.1', 55995)] {'action': 'send_message', 'status': 'error', 'error': 'Recipient does not exist'}
[DISCONNECTED] ('127.0.0.1', 55995) disconnected.

[NEW CONNECTION] ('127.0.0.1', 55996) connected.
[REQUEST FROM ('127.0.0.1', 55996)] {'action': 'send_message', 'data': {'session_token': 'invalid_token', 'username': 'alice', 'recipient': 'bob', 'message': 'Hello, Bob!'}}
[RESPONSE TO ('127.0.0.1', 55996)] {'action': 'send_message', 'status': 'error', 'error': 'Invalid session'}
[DISCONNECTED] ('127.0.0.1', 55996) disconnected.

[NEW CONNECTION] ('127.0.0.1', 55997) connected.
[REQUEST FROM ('127.0.0.1', 55997)] {'action': 'read_messages', 'data': {'session_token': 'invalid_token', 'username': 'bob'}}
[RESPONSE TO ('127.0.0.1', 55997)] {'action': 'read_messages', 'status': 'error', 'error': 'Invalid session'}
[DISCONNECTED] ('127.0.0.1', 55997) disconnected.

[NEW CONNECTION] ('127.0.0.1', 55998) connected.
[REQUEST FROM ('127.0.0.1', 55998)] {'action': 'logout', 'data': {'session_token': '284c24a4-8243-441c-bf51-07a4721d5a2d'}}
[RESPONSE TO ('127.0.0.1', 55998)] {'action': 'logout', 'status': 'success'}
[DISCONNECTED] ('127.0.0.1', 55998) disconnected.

[NEW CONNECTION] ('127.0.0.1', 55999) connected.
[REQUEST FROM ('127.0.0.1', 55999)] {'action': 'send_message', 'data': {'session_token': '284c24a4-8243-441c-bf51-07a4721d5a2d', 'recipient': 'alice', 'message': 'Hello again, Alice!'}}
[RESPONSE TO ('127.0.0.1', 55999)] {'action': 'send_message', 'status': 'error', 'error': 'Invalid session'}
[DISCONNECTED] ('127.0.0.1', 55999) disconnected.
```