import tkinter as tk
from tkinter import messagebox, simpledialog
import socket
import json
import threading
from utils import HOST, PORT

class ChatClient:
    def __init__(self, root):
        self.root = root
        self.root.title("Chat System")

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((HOST, PORT))

        self.session_token = None  # Store session after login

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

    def build_chat_screen(self):  #TODO: Design a better UI
        """Create the main chat UI after login."""
        for widget in self.root.winfo_children():
            widget.destroy()

        self.chat_display = tk.Text(self.root, height=15, width=50, state=tk.DISABLED)
        self.chat_display.pack()

        self.message_entry = tk.Entry(self.root, width=40)
        self.message_entry.pack()

        tk.Button(self.root, text="Send", command=self.send_message).pack()
        tk.Button(self.root, text="View Unread Messages", command=self.read_messages).pack()
        tk.Button(self.root, text="Delete Unread Messages", command=self.delete_messages).pack()
        tk.Button(self.root, text="List Accounts", command=self.list_accounts).pack()
        tk.Button(self.root, text="Delete Account", command=self.delete_account).pack()
        tk.Button(self.root, text="Log Out", command=self.logout).pack()

        # Add a background listener to read messages
        self.running = True
        self.listener_thread = threading.Thread(target=self.listen_for_messages, daemon=True)
        self.listener_thread.start()
    
    def listen_for_messages(self):
        while self.running:
            try:
                data = self.socket.recv(1024).decode("utf-8")
                if not data:
                    break
                response = json.loads(data)

                if response.get("action") == "receive_message":
                    sender = response.get("data", {}).get("sender")
                    message = response.get("data", {}).get("message")
                    self.chat_display.config(state=tk.NORMAL)
                    self.chat_display.insert(tk.END, f"[NEW] {sender} -> You: {message}\n")
                    self.chat_display.config(state=tk.DISABLED)
            except OSError:
                break
            except Exception as e:
                print(f"[ERROR] Listener thread: {e}")
        
    def send_request(self, action, data):
        """Helper function to send JSON requests to server."""
        self.socket.send(json.dumps({"action": action, "data": data}).encode("utf-8"))
        response = json.loads(self.socket.recv(1024).decode("utf-8"))
        return response

    def create_account(self):
        """Handle account creation."""
        username = self.username_entry.get()
        password = self.password_entry.get()
        response = self.send_request("create_account", {"username": username, "password": password})

        if response.get("status") == "success":
            messagebox.showinfo("Success", "Account created. Please log in.")
        else:
            messagebox.showerror("Error", response.get("error"))

    def login(self):
        """Handle user login."""
        username = self.username_entry.get()
        password = self.password_entry.get()
        response = self.send_request("login", {"username": username, "password": password})

        if response.get("status") == "success":
            self.session_token = response.get("data", {}).get("session_token")
            messagebox.showinfo("Success", f"Logged in! {response.get("data", {}).get("unread_message_count")} unread messages.")
            self.build_chat_screen()
        else:
            messagebox.showerror("Error", response.get("error"))

    def list_accounts(self):
        """Prompt user for search pattern and display paginated list of accounts."""
        pattern = simpledialog.askstring("List Accounts", "Enter search pattern (* for all):", initialvalue="*")
        
        if pattern is not None:
            self.account_search_pattern = pattern
            self.account_page = 1  # Reset to first page
            self.fetch_accounts()

    def fetch_accounts(self):
        """Fetch and display a page of account listings."""
        response = self.send_request("list_accounts", {"session_token": self.session_token, 
                                                       "pattern": self.account_search_pattern, 
                                                       "page": self.account_page, "page_size": 10})  #TODO: allow user to configure for once

        if response["status"] == "success":
            accounts = response["data"]["accounts"]
            page = response["data"]["page"]
            total_pages = response["data"]["total_pages"]

            result_text = f"Page {page}/{total_pages}\n" + "\n".join(accounts) if accounts else "No accounts found."

            account_window = tk.Toplevel(self.root)
            account_window.title("Account List")

            tk.Label(account_window, text=result_text, justify=tk.LEFT).pack()

            # Pagination Controls
            if page > 1:
                tk.Button(account_window, text="Previous", command=lambda: self.change_account_page(-1, account_window)).pack(side=tk.LEFT)
            if page < total_pages:
                tk.Button(account_window, text="Next", command=lambda: self.change_account_page(1, account_window)).pack(side=tk.RIGHT)
        else:
            messagebox.showerror("Error", response["error"])

    def change_account_page(self, direction, window):
        """Navigate through paginated account results."""
        self.account_page += direction
        window.destroy()
        self.fetch_accounts()

    def send_message(self):
        """Send a message to a recipient."""
        recipient = simpledialog.askstring("Recipient", "Enter recipient username:")
        message = self.message_entry.get()

        if recipient and message:
            response = self.send_request("send_message", {"session_token": self.session_token, "recipient": recipient, "message": message})

            if response.get("status") == "success":
                self.chat_display.config(state=tk.NORMAL)
                self.chat_display.insert(tk.END, f"You -> {recipient}: {message}\n")
                self.chat_display.config(state=tk.DISABLED)
                self.message_entry.delete(0, tk.END)
            else:
                messagebox.showerror("Error", response.get("error"))

    def read_messages(self):
        """Retrieve unread messages."""
        response = self.send_request("read_messages", {"session_token": self.session_token, "num_to_read": 5})  #TODO: allow user to configure for once

        if response.get("status") == "success":
            unread_messages = response.get("data", {}).get("unread_messages")
            if unread_messages:
                self.chat_display.config(state=tk.NORMAL)
                for msg in unread_messages:
                    self.chat_display.insert(tk.END, f"{msg['from']} -> You: {msg['message']}\n")
                self.chat_display.config(state=tk.DISABLED)
            else:
                messagebox.showinfo("No Messages", "No new messages.")
        else:
            messagebox.showerror("Error", response.get("error"))

    def delete_messages(self):
        """Prompt user for the number of unread messages to delete and send request to the server."""
        num_to_delete = simpledialog.askinteger("Delete Messages", "Enter number of unread messages to delete (positive number to delete from earliest and negative for latest):", minvalue=1)

        if num_to_delete is not None:
            response = self.send_request("delete_messages", {"session_token": self.session_token, "num_to_delete": num_to_delete})

            if response["status"] == "success":
                num_deleted = response["data"]["num_messages_deleted"]
                messagebox.showinfo("Success", f"Deleted {num_deleted} unread messages.")
            else:
                messagebox.showerror("Error", response["error"])

    def delete_account(self):
        """Delete the logged-in user's account and return to login screen."""
        if messagebox.askyesno("Confirm", "Are you sure you want to delete your account?"):
            self.running = False  # Stop listener thread
            response = self.send_request("delete_account", {"session_token": self.session_token})

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
            response = self.send_request("logout", {"session_token": self.session_token})

            if response.get("status") == "success":
                self.session_token = None  # Clear session
                messagebox.showinfo("Logged Out", "You have been logged out.")
                self.build_login_screen()  # Return to login screen
            else:
                messagebox.showerror("Error", response.get("error"))

if __name__ == "__main__":
    root = tk.Tk()
    client = ChatClient(root)
    root.mainloop()
