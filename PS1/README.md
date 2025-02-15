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

### 1️⃣ Clone the Repository
``` bash
git clone https://github.com/ren-jie-wu/cs2620
cd cs2620/PS1
```

### 2️⃣ Install Dependencies
``` bash
pip install -r requirements.txt
```

### 3️⃣ Run the Server
On one terminal

``` bash
python server/server.py
```

### 4️⃣ Run the Client
On another terminal (or another computer; then both side should set the `HOST` IP in the `shared/config.py` file as the IP of the computer running `server/server.py`. Refer to [this](https://apple.stackexchange.com/questions/20547/how-do-i-find-my-ip-address-from-the-command-line) to find your IP address.)

``` bash
python client/gui.py
```

## 🔧 API & Wire Protocol (JSON)
The server and client communicate via JSON messages over sockets. Below are the supported actions:

| **Action**         | **Description**                                          | **Request Example** | **Response Example** |
|--------------------|----------------------------------------------------------|---------------------|----------------------|
| `create_account`   | Create a new user account                                | `{"action": "create_account", "data": {"username": "user1", "password": "pass"}}` | `{"action": "create_account", "status": "success"}` |
| `login`            | Log in and receive session token                         | `{"action": "login", "data": {"username": "user1", "password": "pass"}}` | `{"action": "login", "status": "success", "data": {"session_token": "xyz"}}` |
| `send_message`     | Send a message to a user                                 | `{"action": "send_message", "data": {"session_token": "xyz", "recipient": "user2", "message": "Hello!"}}` | `{"action": "send_message", "status": "success"}` |
| `read_messages`    | Read unread messages                                     | `{"action": "read_messages", "data": {"session_token": "xyz"}}` | `{"action": "read_messages", "status": "success", "data": {"unread_messages": [{"from": "user2", "message": "Hey"}]}}` |
| `list_accounts`    | List all accounts (supports wildcard search)             | `{"action": "list_accounts", "data": {"session_token": "xyz", "pattern": "user*"}}` | `{"action": "list_accounts", "status": "success", "data": ["user1", "user2"]}` |
| `delete_messages`  | Delete unread messages                                   | `{"action": "delete_messages", "data": {"session_token": "xyz", "num_to_delete": 2}}` | `{"action": "delete_messages", "status": "success"}` |
| `delete_account`   | Delete user account                                      | `{"action": "delete_account", "data": {"session_token": "xyz"}}` | `{"action": "delete_account", "status": "success"}` |
| `logout`           | Log out the current user                                 | `{"action": "logout", "data": {"session_token": "xyz"}}` | `{"action": "logout", "status": "success"}` |

They are called by
``` python
server.request_handler.process_request(request, client_socket)  # server is a ChatServer object
```

### Some specification

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
- Check server logs for debugging.

### 📌 To-Do & Future Enhancements
- [ ] Fix client GUI bug (current GUI sometimes get stuck, probably due to the background thread adding task to the GUI loop (`display_messages` called in `listen_for_messages`))
- [ ] Report test coverage (client & integration left)
- [ ] Design and implement a second protocol other than JSON
- [ ] Analyze the two protocols (efficiency, scalability)
- [ ] Finalize Documentation (this readme file, requirements, engineering notebook content, code comment&docstrings)

## 📄 License
[MIT License](https://mit-license.org/)

## 👥 Contributors
Roger Wu (@ren-jie-wu)
