# seleniumfw/thread_context.py
import threading

_thread_data = threading.local()
_thread_locals = threading.local()
