"""
Gunicorn configuration file for high concurrency.

This configuration is optimized for production environments with moderate to high traffic.
"""
import multiprocessing
import os

# Server socket
bind = "unix:/home/ec2-user/appcitas/gunicorn.sock"
backlog = 2048

# Worker processes
# Formula: (2 x $num_cores) + 1
# For a 2-core machine: (2 x 2) + 1 = 5 workers
# For a 4-core machine: (2 x 4) + 1 = 9 workers
workers = multiprocessing.cpu_count() * 2 + 1

# Worker class - use sync for compatibility with Django DB connections
# gevent causes thread sharing issues with Django's database connections
# sync workers are more stable for Django applications
worker_class = 'sync'  # Default, works well with Django
# worker_connections only applies to async workers like gevent/eventlet
# worker_connections = 1000

# Worker timeout
# 60 seconds para soportar operaciones más largas como reportes
# Aumentado de 30s para evitar timeouts en exportaciones CSV y queries complejas
timeout = 60
graceful_timeout = 30
keepalive = 2

# Logging
accesslog = '-'  # Log to stdout
errorlog = '-'   # Log to stderr
loglevel = 'info'  # Use 'debug' for development, 'warning' or 'error' for production
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = 'gunicorn_citas'

# Server mechanics
daemon = False  # Don't run as daemon (systemd handles this)
pidfile = None  # systemd handles PID management
user = None     # systemd sets the user
group = None    # systemd sets the group
tmp_upload_dir = None

# Preload app for better memory usage (workers share code)
preload_app = True

# Max requests a worker will process before restarting
# This helps prevent memory leaks
max_requests = 1000
max_requests_jitter = 50  # Randomize restart to avoid all workers restarting at once

# SSL (uncomment if using HTTPS directly with gunicorn)
# keyfile = '/path/to/keyfile'
# certfile = '/path/to/certfile'

def when_ready(server):
    """Called just after the server is started."""
    print("Server is ready. Spawning workers")

def worker_int(worker):
    """Called when a worker receives the INT or QUIT signal."""
    print(f"Worker received INT or QUIT signal: {worker.pid}")

def on_exit(server):
    """Called just before exiting gunicorn."""
    print("Gunicorn server is exiting")