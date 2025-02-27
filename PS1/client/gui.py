# client/gui.py
import time
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import tkinter as tk
from tkinter import messagebox, simpledialog
import threading
from client.network import ChatNetwork
from client.config import PAGE_SIZE, MSG_NUM, REFRESH_INTERVAL


class ChatClient:
    def __init__(self, root, network=ChatNetwork):
        """
        Initialize a new ChatClient instance.

        :param root: The Tk root window to contain the chat UI.
        :param network: The network class to use for communication with the server.
        """
        self.root = root
        self.root.title("Chat System") 
        self.network = network       
        self.connection = network()
        self.background_connection = None
        self.session_token = None
        self.background_session_token = None
        self.running = False

        self.build_login_screen()

    def build_login_screen(self):
        """Create the login & account creation UI."""
        for widget in self.root.winfo_children():
            widget.destroy()

        tk.Label(self.root, text="Username:").pack()
        self.username_entry = tk.Entry(self.root)
        self.username_entry.pack()

        tk.Label(self.root, text="Password:").pack()
        self.password_entry = tk.Entry(self.root, show="*")
        self.password_entry.pack()

        tk.Button(self.root, text="Log In", command=self.login).pack()
        tk.Button(self.root, text="Create Account", command=self.create_account).pack()

    def build_chat_screen(self, background=True):
        """Create the main chat UI after login."""
        username = self.username_entry.get()
        password = self.password_entry.get()

        for widget in self.root.winfo_children():
            widget.destroy()

        self.chat_display = tk.Text(self.root, height=15, width=50, state=tk.DISABLED)
        self.chat_display.pack(pady=10)

        # Message entry and send button
        message_frame = tk.Frame(self.root)
        message_frame.pack(fill=tk.X, padx=10)
        self.message_entry = tk.Entry(message_frame, width=40)
        self.message_entry.pack(side=tk.LEFT, expand=True, fill=tk.X)
        tk.Button(message_frame, text="Send", command=self.send_message).pack(side=tk.RIGHT)

        # Unread messages buttons
        unread_frame = tk.Frame(self.root)
        unread_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(unread_frame, text="Unread Messages:").pack(side=tk.LEFT)
        tk.Button(unread_frame, text="View", command=self.read_messages).pack(side=tk.LEFT, padx=5)
        tk.Button(unread_frame, text="Delete", command=self.delete_messages).pack(side=tk.LEFT)

        # Account buttons
        account_frame = tk.Frame(self.root)
        account_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(account_frame, text="Account:").pack(side=tk.LEFT)
        tk.Button(account_frame, text="Search", command=self.list_accounts).pack(side=tk.LEFT, padx=5)
        tk.Button(account_frame, text="Delete", command=self.delete_account).pack(side=tk.LEFT)

        # Logout button
        tk.Button(self.root, text="Log Out", command=self.logout).pack(pady=10)

        if background:
            self.running = True
            self.background_connection = self.network()
            self.listener_thread = threading.Thread(target=self.listen_for_messages, args=(username, password), daemon=True)
            self.listener_thread.start()

    def listen_for_messages(self, username, password, refresh_interval=REFRESH_INTERVAL):
        """Background thread that listens for incoming messages."""
        # Create a new connection for background thread
        # This can successfully solve the problem of getting stuck for no reason (probably 
        # due to hearing with the same socket in the main thread and the background)
        
        response = self.background_connection.send_request("listen", {"username": username, "password": password})
        if response["status"] == "success":
            self.background_session_token = response["data"]["session_token"]
        else:
            messagebox.showerror("Error", response["error"])
            self.running = False
            return
        while self.running:
            responses = self.background_connection.receive_message()
            for response in responses:
                if response and response.get("action") == "receive_message":
                    sender = response["data"]["sender"]
                    message = response["data"]["message"]
                    self.display_messages([f"[NEW] {sender} -> You: {message}\n"])
            time.sleep(refresh_interval)

    def display_messages(self, messages, append=False):
        """Update the chat display with new messages (from latest to earliest)."""
        self.chat_display.config(state=tk.NORMAL)
        if append:
            for message in messages:
                self.chat_display.insert(tk.END, message)
            self.chat_display.insert(tk.END, "-"*50 + "\n")
        else:
            self.chat_display.insert("1.0", "-"*50 + "\n")
            for message in messages[::-1]:
                self.chat_display.insert("1.0", message)
        
        self.chat_display.config(state=tk.DISABLED)

    def create_account(self):
        """Handle account creation."""
        username = self.username_entry.get()
        password = self.password_entry.get()
        response = self.connection.send_request("create_account", {"username": username, "password": password})

        if response["status"] == "success":
            messagebox.showinfo("Success", "Account created. Please log in.")
        else:
            messagebox.showerror("Error", response["error"])

    def login(self):
        """Handle user login."""
        username = self.username_entry.get()
        password = self.password_entry.get()
        response = self.connection.send_request("login", {"username": username, "password": password})

        if response["status"] == "success":
            self.session_token = response["data"]["session_token"]
            unread_count = response["data"]["unread_message_count"]
            messagebox.showinfo("Success", f"Logged in! {unread_count} unread messages.")
            self.build_chat_screen()
        else:
            messagebox.showerror("Error", response["error"])
    
    def list_accounts(self):
        """Prompt user for search pattern and display paginated list of accounts."""
        pattern = simpledialog.askstring("List Accounts", "Enter search pattern (* for all):", initialvalue="*")
        
        if pattern is not None:
            self.account_search_pattern = pattern
            self.account_page = 1  # Reset to first page
            self.fetch_accounts()
    
    def fetch_accounts(self, x=None, y=None):
        """Fetch and display a page of account listings."""
        response = self.connection.send_request("list_accounts", {"session_token": self.session_token, 
                                                       "pattern": self.account_search_pattern, 
                                                       "page": self.account_page, "page_size": PAGE_SIZE})

        if response["status"] == "success":
            accounts = response["data"]["accounts"]
            page = response["data"]["page"]
            total_pages = response["data"]["total_pages"]

            result_text = "\n".join(accounts) if accounts else "No accounts found."
            _ = self.create_account_window(result_text, page, total_pages, x, y)
        else:
            messagebox.showerror("Error", response["error"])
    

    def create_account_window(self, result_text, page, total_pages, x=None, y=None):
        """Create a toplevel window for displaying paginated account listings."""
        account_window = tk.Toplevel(self.root)
        account_window.title("Account List")
        account_window.geometry(f"300x250+{x}+{y}" if x and y else "300x250")  # Set a fixed size for the window
        account_window.resizable(False, False)  # Make the window non-resizable

        # Create a main frame to hold content
        main_frame = tk.Frame(account_window)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Create a text widget for the account list
        text_widget = tk.Text(main_frame, wrap=tk.WORD, width=40, height=10)
        text_widget.insert(tk.END, result_text)
        text_widget.config(state=tk.DISABLED)  # Make it read-only
        text_widget.pack(fill=tk.BOTH, expand=True)

        # Add a scrollbar
        scrollbar = tk.Scrollbar(main_frame, orient=tk.VERTICAL, command=text_widget.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text_widget.config(yscrollcommand=scrollbar.set)

        # Button frame for pagination controls
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        # Pagination Controls
        if page > 1:
            prev_button = tk.Button(button_frame, text="Previous", 
                                    command=lambda: self.change_account_page(-1, account_window))
            prev_button.pack(side=tk.LEFT)

        if page < total_pages:
            next_button = tk.Button(button_frame, text="Next", 
                                    command=lambda: self.change_account_page(1, account_window))
            next_button.pack(side=tk.RIGHT)

        # Page indicator
        page_label = tk.Label(button_frame, text=f"Page {page} of {total_pages}")
        page_label.pack(side=tk.TOP)

        return account_window

    def change_account_page(self, direction, window):
        """Navigate through paginated account results."""
        x = window.winfo_x()
        y = window.winfo_y()
        self.account_page += direction
        window.destroy()
        self.fetch_accounts(x, y)
    
    def send_message(self):
        """Send a message to a recipient."""
        recipient = simpledialog.askstring("Recipient", "Enter recipient username:")
        message = self.message_entry.get()
        if recipient and message:
            response = self.connection.send_request("send_message", {"session_token": self.session_token, "recipient": recipient, "message": message})

            if response.get("status") == "success":
                self.display_messages([f"You -> {recipient}: {message}\n"])
                self.message_entry.delete(0, tk.END)
            else:
                messagebox.showerror("Error", response.get("error"))

    def read_messages(self):
        """Retrieve unread messages."""
        response = self.connection.send_request("read_messages", {"session_token": self.session_token, "num_to_read": MSG_NUM})

        if response.get("status") == "success":
            unread_messages = response.get("data", {}).get("unread_messages")
            if unread_messages:
                self.display_messages([f"{msg["sender"]} -> You: {msg['message']}\n" for msg in unread_messages], append=True)
            else:
                messagebox.showinfo("No Messages", "No new messages.")
        else:
            messagebox.showerror("Error", response.get("error"))

    def delete_messages(self):
        """Prompt user for the number of unread messages to delete and send request to the server."""
        num_to_delete = simpledialog.askinteger("Delete Messages", "Enter number of unread messages to delete (positive number to delete from earliest and negative for latest):", minvalue=1)

        if num_to_delete is not None:
            response = self.connection.send_request("delete_messages", {"session_token": self.session_token, "num_to_delete": num_to_delete})

            if response["status"] == "success":
                num_deleted = response["data"]["num_messages_deleted"]
                messagebox.showinfo("Success", f"Deleted {num_deleted} unread messages.")
            else:
                messagebox.showerror("Error", response["error"])

    def delete_account(self):
        """Delete the logged-in user's account and return to login screen."""
        if messagebox.askyesno("Confirm", "Are you sure you want to delete your account?"):
            self.running = False  # Stop listener thread
            response = self.connection.send_request("delete_account", {"session_token": self.session_token})

            if response.get("status") == "success":
                self.session_token = None  # Clear session
                messagebox.showinfo("Deleted", "Account deleted successfully.")
                self.build_login_screen()  # Return to login screen
            else:
                messagebox.showerror("Error", response.get("error"))

    def logout(self):
        """Log out the user and return to login screen."""
        if messagebox.askyesno("Confirm", "Are you sure you want to log out?"):
            self.running = False  # Stop listener thread
            response1 = self.connection.send_request("logout", {"session_token": self.session_token})
            response2 = self.background_connection.send_request("logout", {"session_token": self.background_session_token})

            if response1["status"] == "success" and response2["status"] == "success":
                self.session_token = None
                messagebox.showinfo("Logged Out", "You have been logged out.")
                self.build_login_screen()
            else:
                messagebox.showerror("Error", response1["error"] or response2["error"])

if __name__ == "__main__":
    root = tk.Tk()
    client = ChatClient(root)
    root.mainloop()
