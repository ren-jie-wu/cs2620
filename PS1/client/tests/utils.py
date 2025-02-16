import tkinter.messagebox
import tkinter.simpledialog
from unittest import mock

def disable_messagebox():
    """Globally disable tkinter.messagebox pop-ups during tests."""
    tkinter.messagebox.showinfo = mock.Mock(return_value=None)
    tkinter.messagebox.showerror = mock.Mock(return_value=None)
    tkinter.messagebox.askyesno = mock.Mock(return_value=True)

def enable_messagebox():
    """Re-enable tkinter.messagebox pop-ups after tests."""
    import tkinter.messagebox as original_messagebox
    tkinter.messagebox.showinfo = original_messagebox.showinfo
    tkinter.messagebox.showerror = original_messagebox.showerror
    tkinter.messagebox.askyesno = original_messagebox.askyesno

def set_askstring(value):
    """Set the return value of tkinter.simpledialog.askstring."""
    tkinter.simpledialog.askstring = mock.Mock(return_value=value)

def setback_askstring():
    """Re-enable tkinter.simpledialog.askstring after tests."""
    import tkinter.simpledialog as original_simpledialog
    tkinter.simpledialog.askstring = original_simpledialog.askstring

def set_askinteger(value):
    """Set the return value of tkinter.simpledialog.askinteger."""
    tkinter.simpledialog.askinteger = mock.Mock(return_value=value)

def setback_askinteger():
    """Re-enable tkinter.simpledialog.askinteger after tests."""
    import tkinter.simpledialog as original_simpledialog
    tkinter.simpledialog.askinteger = original_simpledialog.askinteger