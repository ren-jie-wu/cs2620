# PS1 - Chat System

A simple client-server chat application that allows users to send and receive messages over sockets using JSON for communication. The server manages user authentication, message storage, and real-time message delivery.

## 🚀 Features

✅ User Authentication: Create an account, log in, and log out securely.  
✅ Messaging: Send messages instantly if the recipient is online; store them otherwise.  
✅ Session Management: Uses session tokens with expiration handling.  
✅ Message Handling: Read and delete unread messages.  
✅ User Listing: Search for users with wildcard matching.  
✅ GUI Client: User-friendly interface for sending and receiving messages.

## 📂 Project Structure

```
chat-system/                
│── server/                 # Server side code
│   │── tests/              # Test code (for server)
│   │── config.py           # Configuration file (for server)
│   │── utils.py            # Some helper functions
│   │── storage.py          # Data read/write
│   │── request_handler.py  # Process request/response
│   │── server.py           # Server entry code
│── clients/                # Client side code
│   │── tests/              # Test code (for client)
│   │── config.py           # Configuration file (for client)
│   │── network.py          # Process request/response
│   │── gui.py              # Client GUI
│── shared/                 # Shared between server and client
│   │── config.py           # Configuration file (for both)
│   │── protocol.py         # Protocol (for both)
│── test_integration/       # Test code (for integration of server and client)
│── htmlcov/                # Test coverage report
│── requirements.txt        # Python dependencies
│── README.md               # Documentation (this file)
│── engineering_notebook.md # Record of development
```

## 💻 Installation & Setup

### Clone the Repository
``` bash
git clone https://github.com/ren-jie-wu/cs2620
cd cs2620/PS1
```

### Install Dependencies
``` bash
pip install -r requirements.txt
```

### Configure Server & Client
In [`shared/config.py`](shared/config.py), configure the host, port, and protocol to use. This is shared between server and client.

In [`server/config.py`](server/config.py), configure the storage type to use (`"memory"` or `"db"`), buffer size, and token expiry settings.

In [`client/config.py`](client/config.py), configure the buffer size and other display settings.

### Run the Server & Client
First, on one terminal

``` bash
python server/server.py
```

Then, on another terminal (or another computer; then both side should set the `HOST` IP in the `shared/config.py` file as the IP of the computer running `server/server.py`. Refer to [this](https://apple.stackexchange.com/questions/20547/how-do-i-find-my-ip-address-from-the-command-line) to find your IP address.)

``` bash
python client/gui.py
```

## 🔧 API & Wire Protocol

### JSON
The server and client communicate via JSON messages over sockets. Below are the supported actions:

| **Action**         | **Description**                                          | **Request Example** | **Response Example** |
|--------------------|----------------------------------------------------------|---------------------|----------------------|
| `create_account`   | Create a new user account                                | `{"action": "create_account", "data": {"username": "user1", "password": "pass"}}` | `{"action": "create_account", "status": "success"}` |
| `login`            | Log in and receive session token                         | `{"action": "login", "data": {"username": "user1", "password": "pass"}}` | `{"action": "login", "status": "success", "data": {"session_token": "xyz", "unread_message_count": 3}}` |
| `listen`           | Keep a background connection to listen real-time messages| `{"action": "listen", "data": {"username": "user1", "password": "pass"}}` | `{"action": "login", "status": "success", "data": {"session_token": "xyz"}}` |
| `receive_message`  | Receive real-time messages                               | (No need to request) | `{"action": "receive_message", "data": {"sender": sender, "message": message}}`
| `send_message`     | Send a message to a user                                 | `{"action": "send_message", "data": {"session_token": "xyz", "recipient": "user2", "message": "Hello!"}}` | `{"action": "send_message", "status": "success"}` |
| `read_messages`    | Read unread messages                                     | `{"action": "read_messages", "data": {"session_token": "xyz"}}` | `{"action": "read_messages", "status": "success", "data": {"unread_messages": [{"from": "user2", "message": "Hey"}]}}` |
| `list_accounts`    | List all accounts (supports wildcard search)             | `{"action": "list_accounts", "data": {"session_token": "xyz", "pattern": "user*"}}` | `{"action": "list_accounts", "status": "success", "data": ["user1", "user2"]}` |
| `delete_messages`  | Delete unread messages                                   | `{"action": "delete_messages", "data": {"session_token": "xyz", "num_to_delete": 2}}` | `{"action": "delete_messages", "status": "success"}` |
| `delete_account`   | Delete user account                                      | `{"action": "delete_account", "data": {"session_token": "xyz"}}` | `{"action": "delete_account", "status": "success"}` |
| `logout`           | Log out the current user                                 | `{"action": "logout", "data": {"session_token": "xyz"}}` | `{"action": "logout", "status": "success"}` |

### Customized Protocol

Customized protocol is a more compact and efficient binary-like protocol designed to replace standard JSON messaging. Each message follows this structure:
```
[length]:[action][status][error_length]:[error][data]
```
| **Field**  | **Description**	                                        | **Example**           |
|------------|----------------------------------------------------------|-----------------------|
| [length]   | Length of the entire message (excluding itself)	        | "21"                  |
| [action]   | Encoded action (10-19 for known actions, 00 if unknown)	| "12" (list_accounts)  |
| [status]   | "11" = success, "10" = error, "00" = request (no status)	| "11"                  |
| [error]    | Length-prefixed error message ("0" if none)	            | "0" (no error)        |
| [data]	 | JSON-encoded data ("0" if none)	                        | "{\"key\": \"value\"}"|

Supported actions:
| **Action**	    |**Code**   |
|-------------------|-----------|
| create_account	|"10"       |
| login	            |"11"       |
| listen	        |"12"       |
| list_accounts	    |"13"       |
| send_message	    |"14"       |
| receive_message	|"15"       |
| read_messages	    |"16"       |
| delete_messages	|"17"       |
| logout	        |"18"       |
| delete_account	|"19"       |

### Comparison
We tested three different cases:
1.	Login Request (Smallest Message)
    ``` json
    {"action": "login", "data": {"username": "alice", "password": "securepass"}}
    ```
2.	Message Sending (Medium-Sized Data)
    ``` json
    {"action": "send_message", "data": {"recipient": "bob", "message": "Hello, Bob!"}}
    ```
3.	Account Listing Response (Larger Message)
    ```json
    {
        "action": "list_accounts",
        "status": "success",
        "data": {"accounts": ["alice", "bob", "charlie", "dave", "eve"]}
    }
    ```

|Case                     |JSONProtocol (bytes)     |CustomizedProtocol (bytes)    |Reduction (%)       |
|-------------------------|-------------------------|------------------------------|--------------------|
|Login Request            |76                       |55                            |27.6%               |
|Send Message Request     |82                       |54                            |34.1%               |
|List Accounts Response   |114                      |64                            |43.9%               |

The CustomizedProtocol achieves higher efficiency by:
1. Numeric Action Codes. Instead of sending "send_message", we send "14", reducing size significantly.
2. Compact Status Encoding. "success" is "11", "error" is "10", saving bytes.
3. Length-Prefixed Data. No need for JSON parsing overhead; simply read the exact number of bytes.
4. No Extra Quotes & Formatting. Standard JSON requires extra symbols ({}, :) and redundant keys.

This could lead to higher scalability via impacts on bandwidth usage, processing time, multiple messages in stream, storage impact (if logged).

### Some specification

These APIs are called by
``` python
server.request_handler.process_request(request, client_socket)  # server is a ChatServer object
```

1. When sending message, if a user is off-line, the message will be saved by the server, wait until the recipient has logged in and decided to read these unsent messages, and then send them, as well as remove them from the server memory/database. If a user is online, the server will send the message immediately, and the user is supposed to be able to read it in real-time, with a background thread listening to the server and trigger printing the messages when it's delivered.
2. The chat system is not designed for keeping chat history for going through over and over again; users either receive and read them immediately, or choose to log out to stop reading if feeling overwhelmed. So the `deleted_messages` is only for those undelivered (i.e., unread) messages (probably because they feel overwhemed and want to discard those earlier messages and to read those latest).
3. When deleting user account, their undelivered messages will be cleared out as well.

## 🛠 Development Guide

### 📌 Collaboration Workflow
1. Fork the repo and create a feature branch.
2. Make changes and commit with clear messages.
3. Submit a pull request (PR) for review.
4. Discuss & merge changes.

### 📌 Testing
- Run unit tests and view the coverage report by
``` bash
pytest --cov=. --cov-report=html
open htmlcov/index.html
```
- Check server logs for debugging

    Sometimes it reports the port cannot be used or the host is refucing the connection, just change the `PORT` in the `shared/config.py`.

#### Test Coverage Results
| File | statements | missing | excluded | coverage |
| --- | --- | --- | --- | --- |
| \_\_init\_\_.py | 0   | 0   | 0   | 100% |
| client/\_\_init\_\_.py | 0   | 0   | 0   | 100% |
| client/config.py | 8   | 0   | 0   | 100% |
| client/gui.py | 195 | 4   | 0   | 98% |
| client/network.py | 28  | 0   | 0   | 100% |
| client/tests/test\_gui.py | 135 | 0   | 0   | 100% |
| client/tests/test\_network.py | 43  | 0   | 0   | 100% |
| client/tests/utils.py | 22  | 0   | 0   | 100% |
| server/\_\_init\_\_.py | 0   | 0   | 0   | 100% |
| server/config.py | 8   | 0   | 0   | 100% |
| server/request\_handler.py | 108 | 0   | 0   | 100% |
| server/server.py | 57  | 4   | 0   | 93% |
| server/storage.py | 296 | 13  | 0   | 96% |
| server/tests/test\_protocol.py | 21  | 0   | 0   | 100% |
| server/tests/test\_request\_handler.py | 183 | 0   | 0   | 100% |
| server/tests/test\_server.py | 76  | 0   | 0   | 100% |
| server/tests/test\_server\_integration.py | 67  | 0   | 0   | 100% |
| server/tests/test\_storage\_db.py | 36  | 0   | 0   | 100% |
| server/tests/test\_storage\_memory.py | 89  | 0   | 0   | 100% |
| server/tests/test\_storage\_session\_cleanup.py | 27  | 0   | 0   | 100% |
| server/utils.py | 6   | 0   | 0   | 100% |
| shared/\_\_init\_\_.py | 0   | 0   | 0   | 100% |
| shared/config.py | 3   | 0   | 0   | 100% |
| shared/protocol.py | 78  | 5   | 0   | 94% |
| shared/utils.py | 3   | 0   | 0   | 100% |
| Total | 1489 | 26  | 0   | 98% |


## 📄 License
[MIT License](https://mit-license.org/)

## 👥 Contributors
Roger Wu (@ren-jie-wu)
