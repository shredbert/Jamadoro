#!.venv/bin/python3

"""Script to test more complicated DB functions for managing TODOs"""

import sys
from datetime import date
from utils_db import (
    slct_todo_todos,
    insert_jammer,
    insert_pomodoro,
    insert_todo,
    updt_todo_lst_ord,
    delete_all,
)
from werkzeug.security import generate_password_hash

print("Loading test data...")

# Reset test data & load
delete_all()

# Create Jammer record for testing with
email = "test@test.com"
pw = "test"
name = "test"
jammer_id = insert_jammer(
    email=email,
    hashed_password=generate_password_hash(pw),
    username=name,
)
jammer_id = jammer_id[0] if jammer_id else None

# Create TODOs to test with & grab
insert_pomodoro(jammer_id=jammer_id, completed_date=date.today(), duration_secs=900)
insert_pomodoro(jammer_id=jammer_id, completed_date=date.today(), duration_secs=2700)
insert_pomodoro(jammer_id=jammer_id, completed_date=date.today(), duration_secs=1800)
insert_pomodoro(jammer_id=jammer_id, completed_date=date.today(), duration_secs=3600)
insert_todo(jammer_id, "test 1")
insert_todo(jammer_id, "test 2")
insert_todo(jammer_id, "test 3")
insert_todo(jammer_id, "test 4")

# Get & check correct -- just care about description & order for tests
todos = slct_todo_todos(jammer_id)
assert [{k: v for k, v in t.items() if k in ["list_order", "todo_description"]} for t in todos] == [
    {"list_order": 1, "todo_description": "test 1"},
    {"list_order": 2, "todo_description": "test 2"},
    {"list_order": 3, "todo_description": "test 3"},
    {"list_order": 4, "todo_description": "test 4"},
]
print("Initial To Dos populated correctly")

# Check moving 4th item first
updt_todo_lst_ord(jammer_id, todos[3]["todo_id"], "first")
# Check order
todos = slct_todo_todos(jammer_id)
assert [{k: v for k, v in t.items() if k in ["list_order", "todo_description"]} for t in todos] == [
    {"list_order": 1, "todo_description": "test 4"},
    {"list_order": 2, "todo_description": "test 1"},
    {"list_order": 3, "todo_description": "test 2"},
    {"list_order": 4, "todo_description": "test 3"},
]
print("Move to first correct")

# Check moving 4th item up
updt_todo_lst_ord(jammer_id, todos[3]["todo_id"], "up")
todos = slct_todo_todos(jammer_id)
assert [{k: v for k, v in t.items() if k in ["list_order", "todo_description"]} for t in todos] == [
    {"list_order": 1, "todo_description": "test 4"},
    {"list_order": 2, "todo_description": "test 1"},
    {"list_order": 3, "todo_description": "test 3"},
    {"list_order": 4, "todo_description": "test 2"},
]
print("Move up correct")

# Check moving 2nd item down
updt_todo_lst_ord(jammer_id, todos[1]["todo_id"], "down")
# Check order
todos = slct_todo_todos(jammer_id)
assert [{k: v for k, v in t.items() if k in ["list_order", "todo_description"]} for t in todos] == [
    {"list_order": 1, "todo_description": "test 4"},
    {"list_order": 2, "todo_description": "test 3"},
    {"list_order": 3, "todo_description": "test 1"},
    {"list_order": 4, "todo_description": "test 2"},
]
print("Move down correct")

# Check moving 3rd item last
updt_todo_lst_ord(jammer_id, todos[2]["todo_id"], "last")
# Check order
todos = slct_todo_todos(jammer_id)
assert [{k: v for k, v in t.items() if k in ["list_order", "todo_description"]} for t in todos] == [
    {"list_order": 1, "todo_description": "test 4"},
    {"list_order": 2, "todo_description": "test 3"},
    {"list_order": 3, "todo_description": "test 2"},
    {"list_order": 4, "todo_description": "test 1"},
]
print("Move to last correct")

print("Excelsior!!!")
sys.exit(0)
