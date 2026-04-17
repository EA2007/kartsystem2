import multiprocessing

# Bind to Unix socket (Nginx will proxy to it)
bind = "unix:/tmp/kartsystem.sock"

# Workers: (2 × CPU cores) + 1 is a common rule
workers = multiprocessing.cpu_count() * 2 + 1

# Use gevent for better concurrency (optional, install gevent if needed)
# worker_class = "gevent"

# Timeouts
timeout = 60
keepalive = 5

# Logging
accesslog = "-"     # stdout
errorlog  = "-"     # stderr
loglevel  = "info"

# Process naming
proc_name = "kartsystem"

# Restart workers after this many requests (prevents memory leaks)
max_requests = 1000
max_requests_jitter = 100
