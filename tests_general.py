#!.venv/bin/python3
from utils_general import is_valid_password

print("Testing passwords...")

# PWs must have 1 caps, 1 lower, 1 num, 1 symbol, & be 8-30 chars

# Valid PWs
assert is_valid_password("1Test_2!"), "Valid PW not accepted"
assert is_valid_password("1Test_2!tttttttttttttttttttttt"), "Valid PW not accepted"
assert is_valid_password("Test_12@"), "Valid PW not accepted"
assert is_valid_password("~Test_1 2"), "Valid PW not accepted"
assert is_valid_password("Test 012`"), "Valid PW not accepted"
assert is_valid_password("Test_012345789!@#'\""), "Valid PW not accepted"

# Invalid PWs
assert not is_valid_password("Test1!"), "Invalid PW with not enough characters accepted"
assert not is_valid_password("Test1!ttttttttttttttttttttttttt"), "Invalid PW with too many characters accepted"
assert not is_valid_password("test123!"), "Invalid PW with no caps accepted"
assert not is_valid_password("Testonetwothree!"), "Invalid PW with no nums accepted"
assert not is_valid_password("TEST1234!"), "Invalid PW with no lowers accepted"
assert not is_valid_password("Test1234"), "Invalid PW with no symbols accepted"

print("Tests pass")
