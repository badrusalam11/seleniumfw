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

def delete_context(key):
    if hasattr(_thread_context, key):
        delattr(_thread_context, key)

def clear_context():
    for key in list(vars(_thread_context).keys()):
        delattr(_thread_context, key)
