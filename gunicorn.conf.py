import os
import dotenv

dotenv.load_dotenv()
is_prod = os.environ.get("PY_ENV") == "production"

# Logging settings
if is_prod:
    accesslog = "/home/shredbert/CS50-Final-Project/log/jamadoro.access.log"
    errorlog = "/home/shredbert/CS50-Final-Project/log/jamadoro.error.log"
else:
    accesslog = "./log/jamadoro.access.log"
    errorlog = "./log/jamadoro.error.log"

capture_output = True
loglevel = "debug"

# Non-logging settings
if is_prod:
    bind = "unix:jamadoro.sock"
    workers = 3
