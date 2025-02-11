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

### 2. Some of Core Designs

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
- [ ] Store user data and messages (initially in-memory, later in a database)
- [ ] Implement message sending & retrieval

#### Phase 2: Enhancements

- [ ] Implement wildcard search & pagination for listing accounts
- [ ] Implement batch retrieval of messages
- [ ] Implement deletion logic for messages & accounts
- [ ] Introduce a database backend (SQLite or lightweight key-value store)
- [ ] Improve concurrency with threading or async

#### Phase 3: Finalization

- [ ] Build a basic GUI client
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

### 2. Basic Server-Client Socket Setup and Testing

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

### 3. Update Server with User Authentication

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

