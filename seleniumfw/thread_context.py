# File: seleniumfw/thread_context.py
import threading

# Single thread-local storage
_thread_context = threading.local()

def set_context(key, value):
    setattr(_thread_context, key, value)

def get_context(key, default=None):
    return getattr(_thread_context, key, default)

def has_context(key):
    return hasattr(_thread_context, key)

def clear_context():
    """Clear all attributes for this thread."""
    for attr in dir(_thread_context):
        if not attr.startswith("__"):
            delattr(_thread_context, attr)
