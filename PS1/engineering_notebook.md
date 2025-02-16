## Problem Analysis and Planning

## Plans

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

- [x] Implement wildcard search & pagination for listing accounts
- [x] Implement batch retrieval of messages
- [x] Implement deletion logic for messages & accounts
- [x] Introduce a database backend (SQLite or lightweight key-value store)
- [x] Improve concurrency with threading or async

#### Phase 3: Finalization

- [x] Build a basic GUI client
- [x] Test if it runs on two machines
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
  "action": "delete_messages",
  "data": {
    "username": "Bob",
    "message_id": "12345"
  }
}
```
Response
``` json
{
  "action": "delete_messages",
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
- [x] Retrieve messages when the user requests them, with number of messages designated by the user *(positive number ~ reading from latest; negative number ~ reading from earliest)*
- [x] Maintain a session list to validate if a request is coming from a logged-in user
- [x] Add session token expiry with a background thread cleaning-up tokens to improve security.

#### Issues
- [x] In the line `data = client_socket.recv(1024).decode("utf-8")`, the server seems not to keep waiting for the requests from client; rather it just goes to the break statement and disconnect the client. This will prevent from sending a message to the recipient immediately if online, since the connection does not exist anymore. [Solved: This is actually because the socket object in the client side is dead outside of the function. The solution is to maintain that object]
- [x] Even if the above issue is solved, or say the server has the connection to send messages to the recipient, the recipient does not keep receiving messages from the server to display. [Currently manually fetch the message has been changed to a background thread constantly listening to the server]

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

### 6. Message Deletion and Account Deletion

#### Specification

- This chat system is designed for immediately reading messages rather than browsing over and over again. Once the message is read it will no longer exist in any place in the system, except in the client's brain. There is neither chat history designed to record everything having happened. Therefore, the only message records that can be manipulated are **unread** messages.
- The user can (and must, to avoid unintentional deletion) specify the number `n` of messages to delete, in a 'FIFO' manner. That is, the earliest `n` messages will be deleted, since the user may be overwhelmed with too many unread messages otherwise, and typically would prefer to read from the latest ones and ignore the earliest ones.
- If an account is deleted, their unread messages also need not storing and should be deleted, for the sake of memory saving.

#### Key Features
- [x] Deleted top `n` earliest unread messages with authentication
- [x] Delete account and its unread messages stored in the server with authentication
- [x] Remove user session and close their connection just as logging out when deleting account
- [x] (Patch) There could be multiple sessions and connections associated with the same user. All of them need deleting.

#### Testing

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

[NEW CONNECTION] ('127.0.0.1', 57464) connected.
[REQUEST FROM ('127.0.0.1', 57464)] {'action': 'create_account', 'data': {'username': 'alice', 'password': '1234'}}

[DISCONNECTED] ('127.0.0.1', 57464) disconnected.

[NEW CONNECTION] ('127.0.0.1', 57465) connected.
[REQUEST FROM ('127.0.0.1', 57465)] {'action': 'create_account', 'data': {'username': 'bob', 'password': '5678'}}

[DISCONNECTED] ('127.0.0.1', 57465) disconnected.

[NEW CONNECTION] ('127.0.0.1', 57466) connected.
[REQUEST FROM ('127.0.0.1', 57466)] {'action': 'login', 'data': {'username': 'alice', 'password': '1234'}}

[NEW CONNECTION] ('127.0.0.1', 57467) connected.
[REQUEST FROM ('127.0.0.1', 57467)] {'action': 'send_message', 'data': {'session_token': 'd168f64c-4283-4a56-a17b-9d0c2ce5aac2', 'recipient': 'bob', 'message': 'The first day missing bob.'}}

[DISCONNECTED] ('127.0.0.1', 57467) disconnected.

[NEW CONNECTION] ('127.0.0.1', 57468) connected.
[REQUEST FROM ('127.0.0.1', 57468)] {'action': 'send_message', 'data': {'session_token': 'd168f64c-4283-4a56-a17b-9d0c2ce5aac2', 'recipient': 'bob', 'message': 'The second day missing bob.'}}

[DISCONNECTED] ('127.0.0.1', 57468) disconnected.

[NEW CONNECTION] ('127.0.0.1', 57469) connected.
[REQUEST FROM ('127.0.0.1', 57469)] {'action': 'delete_messages', 'data': {'username': 'bob', 'num_to_delete': 1}}

[DISCONNECTED] ('127.0.0.1', 57469) disconnected.

[NEW CONNECTION] ('127.0.0.1', 57470) connected.
[REQUEST FROM ('127.0.0.1', 57470)] {'action': 'login', 'data': {'username': 'bob', 'password': '5678'}}

[DISCONNECTED] ('127.0.0.1', 57466) disconnected.

[NEW CONNECTION] ('127.0.0.1', 57471) connected.
[REQUEST FROM ('127.0.0.1', 57471)] {'action': 'delete_messages', 'data': {'session_token': 'c464ea82-d67e-4f51-a385-1b72c747a8f2', 'num_to_delete': 1}}

[DISCONNECTED] ('127.0.0.1', 57471) disconnected.

[NEW CONNECTION] ('127.0.0.1', 57472) connected.
[REQUEST FROM ('127.0.0.1', 57472)] {'action': 'read_messages', 'data': {'session_token': 'c464ea82-d67e-4f51-a385-1b72c747a8f2'}}

[DISCONNECTED] ('127.0.0.1', 57472) disconnected.

[DISCONNECTED] ('127.0.0.1', 57470) disconnected.

[NEW CONNECTION] ('127.0.0.1', 57473) connected.
[REQUEST FROM ('127.0.0.1', 57473)] {'action': 'create_account', 'data': {'username': 'alice', 'password': '1234'}}

[DISCONNECTED] ('127.0.0.1', 57473) disconnected.

[NEW CONNECTION] ('127.0.0.1', 57474) connected.
[REQUEST FROM ('127.0.0.1', 57474)] {'action': 'create_account', 'data': {'username': 'bob', 'password': '5678'}}

[DISCONNECTED] ('127.0.0.1', 57474) disconnected.

[NEW CONNECTION] ('127.0.0.1', 57475) connected.
[REQUEST FROM ('127.0.0.1', 57475)] {'action': 'login', 'data': {'username': 'bob', 'password': '5678'}}

[NEW CONNECTION] ('127.0.0.1', 57476) connected.
[REQUEST FROM ('127.0.0.1', 57476)] {'action': 'list_accounts', 'data': {'session_token': '1b7ffa8b-572f-4068-92b9-454d931e326c'}}

[DISCONNECTED] ('127.0.0.1', 57476) disconnected.

[NEW CONNECTION] ('127.0.0.1', 57477) connected.
[REQUEST FROM ('127.0.0.1', 57477)] {'action': 'delete_account', 'data': {'username': 'alice'}}

[DISCONNECTED] ('127.0.0.1', 57477) disconnected.

[NEW CONNECTION] ('127.0.0.1', 57478) connected.
[REQUEST FROM ('127.0.0.1', 57478)] {'action': 'login', 'data': {'username': 'alice', 'password': '1234'}}

[DISCONNECTED] ('127.0.0.1', 57475) disconnected.

[NEW CONNECTION] ('127.0.0.1', 57479) connected.
[REQUEST FROM ('127.0.0.1', 57479)] {'action': 'delete_account', 'data': {'session_token': 'c5c6a6c4-73c2-466e-8125-69e2a8c2c79b'}}

[DISCONNECTED] ('127.0.0.1', 57478) disconnected.

[DISCONNECTED] ('127.0.0.1', 57479) disconnected.

[NEW CONNECTION] ('127.0.0.1', 57480) connected.
[REQUEST FROM ('127.0.0.1', 57480)] {'action': 'list_accounts', 'data': {'session_token': '1b7ffa8b-572f-4068-92b9-454d931e326c'}}

[DISCONNECTED] ('127.0.0.1', 57480) disconnected.
```

Expected Output on the client:
```
[SERVER RESPONSE TO ('127.0.0.1', 57464)] {'action': 'create_account', 'status': 'success'}

[SERVER RESPONSE TO ('127.0.0.1', 57465)] {'action': 'create_account', 'status': 'success'}

[SERVER RESPONSE TO ('127.0.0.1', 57466)] {'action': 'login', 'status': 'success', 'data': {'session_token': 'd168f64c-4283-4a56-a17b-9d0c2ce5aac2', 'unread_message_count': 0}}

[SERVER RESPONSE TO ('127.0.0.1', 57467)] {'action': 'send_message', 'status': 'success'}

[SERVER RESPONSE TO ('127.0.0.1', 57468)] {'action': 'send_message', 'status': 'success'}

[SERVER RESPONSE TO ('127.0.0.1', 57469)] {'action': 'delete_messages', 'status': 'error', 'error': 'Invalid session'}

[SERVER RESPONSE TO ('127.0.0.1', 57470)] {'action': 'login', 'status': 'success', 'data': {'session_token': 'c464ea82-d67e-4f51-a385-1b72c747a8f2', 'unread_message_count': 2}}

[SERVER RESPONSE TO ('127.0.0.1', 57471)] {'action': 'delete_messages', 'status': 'success', 'data': {'num_messages_deleted': 1}}

[SERVER RESPONSE TO ('127.0.0.1', 57472)] {'action': 'read_messages', 'status': 'success', 'data': {'unread_messages': [{'from': 'alice', 'message': 'The second day missing bob.'}], 'remaining_unread_count': 0}}

[SERVER RESPONSE TO ('127.0.0.1', 57473)] {'action': 'create_account', 'status': 'error', 'error': 'Username already exists'}

[SERVER RESPONSE TO ('127.0.0.1', 57474)] {'action': 'create_account', 'status': 'error', 'error': 'Username already exists'}

[SERVER RESPONSE TO ('127.0.0.1', 57475)] {'action': 'login', 'status': 'success', 'data': {'session_token': '1b7ffa8b-572f-4068-92b9-454d931e326c', 'unread_message_count': 0}}

[SERVER RESPONSE TO ('127.0.0.1', 57476)] {'action': 'list_accounts', 'status': 'success', 'data': {'accounts': ['alice', 'bob'], 'page': 1, 'total_pages': 1}}

[SERVER RESPONSE TO ('127.0.0.1', 57477)] {'action': 'delete_account', 'status': 'error', 'error': 'Invalid session'}

[SERVER RESPONSE TO ('127.0.0.1', 57478)] {'action': 'login', 'status': 'success', 'data': {'session_token': 'c5c6a6c4-73c2-466e-8125-69e2a8c2c79b', 'unread_message_count': 0}}

[SERVER RESPONSE TO ('127.0.0.1', 57479)] {'action': 'delete_account', 'status': 'success'}

[SERVER RESPONSE TO ('127.0.0.1', 57480)] {'action': 'list_accounts', 'status': 'success', 'data': {'accounts': ['bob'], 'page': 1, 'total_pages': 1}}
```

### * Patch: Addition of a Background Thread to Listen to the Delivered Messages

This is implemented through a `ChatClient.listen_for_messages` function in the `gui.py`. The function check the `self.running` status, which will be open when logging-in and closed when logging-out or account deleting. If it should be running, it will constantly listening to the server and print the received messages in the chat display box.

### 7. GUI

#### Key Features

- [x] Login & Account Creation Screen
- [x] Main Chat Window with Chat Display
  - [x] Accounts Listing UI
  - [x] Message Sending UI
  - [x] Message Reading UI
  - [x] Message Deleting UI
  - [x] Account Deleting UI
  - [x] Logout UI
- [ ] Polishing UI Layout
- [x] (Patch) the account list window is now fixed

### 8. Restructuring the Codes as a Better Design

#### Improvement
- [x] Modularization & Encapsulation – Move each functionality into separate classes/modules.
  - Isolated configuration, utilities, protocol details, data storage, request handling, and server operations into separate modules on the server side. The Storage class encapsulates all data access and modification. The Protocol abstraction makes it easy to switch from JSON to another protocol later.
  - Decoupled network communication and GUI logic for the client side. This will make it easier for separate testing.
- [x] Persistence Support – Migrate information from memory to database
  - Instead of connecting to database for each request in each thread, we'd connect for only once. This would not incur the "database is lock" issue, and the database itself will handle the read/write in different thread that may be concurrent.

### * Patch: Solving that the client gui often breaks down

It's observed that the client gui often breaks down, and it should have nothing to do with the server side, since from the server output we can see that the requests and responses are correctly delivered, but the gui just got stuck. After removing the background thread checking coming-in messages it won't get stuck. Probably this needs to be optimized.

- [x] Optimize background thread

This is probably because the same connection is used in the two thread: the main thread for GUI uses this connection to send all the proactive request to the client and receive corresponding responses; while the background thread also uses this connection to constantly listen to the server for the real-time delivered messages. This is solved by adding another connection when logged in for the background thread.

This involves the addition of `ChatClient.background_connection` in the client gui, as well as a new API `listen` in the server side, so that the connection in the main thread will never receive the real-time messages (response with action of `receive_message`). If we don't separate the two APIs (`listen` and `login`) the main thread is still possible to receive the messages and then the socket can sometimes receive two or more response dictionaries at the same time, resulting in json decoding error.

Another problem is that if there are a lot of in-coming messages at the same time, it's possible that the decoded bytes are a stream of dicts, and the `json.load` would fail to parse it. This will need an advanced parser.

### 9. Testing with `unittest`

#### Testing Components
First test the components in isolation, then their integration functionality. 
- server side
  - [x] protocol.py (test_protocol.py)
  - [x] storage.py (test_storage_memory.py, test_storage_db.py, test_storage_session_cleanup.py)
  - [x] request_handler.py (test_request_handler.py)
  - [x] server.py (test_server.py)
  - [x] integration of the server side (test_server_integration.py)
- [x] client side
- [ ] integration of server and client


#### Testing command
Change the directory to `PS1/` and make sure `server/`, `client/` and `shared/` are in the folder. Make sure `pytest-cov` has been installed.
``` bash
pytest --cov=server --cov=client --cov=shared --cov-report=html
```

This will generate a html report, which can be reached by
``` bash
open htmlcov/index.html
```

### 10. Customized Protocol

Specified in [`README.md`](README.md).

When converting dict to str, do not use `str` or `repr` directly - this will introduce bug in `json.loads` in the future. (json.decoder.JSONDecodeError: Expecting property name enclosed in double quotes: line 1 column 2 (char 1))

### Comments on the Two Protocols

See [`README.md`](README.md).
