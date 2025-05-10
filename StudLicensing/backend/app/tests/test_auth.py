import pytest
#Monkey patch for models to work
import collections
import collections.abc
if not hasattr(collections, "Iterator"):
    collections.Iterator = collections.abc.Iterator
from app.auth import validate_password_policy


def test_validate_password_policy():
    # Test valid password (should not raise exception)
    assert validate_password_policy("Valid123!") is None  # Should pass silently
    # Test invalid password (too short)
    with pytest.raises(ValueError, match="Password must be at least 7 characters long."):
        validate_password_policy("Short1")
    # Test invalid password (no number)
    with pytest.raises(ValueError, match="Password must contain at least one number."):
        validate_password_policy("NoNumber!")
    # Test invalid password (no uppercase letter)
    with pytest.raises(ValueError, match="Password must contain at least one uppercase letter."):
        validate_password_policy("nouppercase1!")


