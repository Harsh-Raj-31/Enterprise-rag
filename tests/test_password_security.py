from app.security.password import hash_password, verify_password


def test_password_hashing():
    password = "employee123"

    password_hash = hash_password(password)

    assert password_hash != password
    assert password_hash.startswith("$2")


def test_correct_password_verifies():
    password = "employee123"
    password_hash = hash_password(password)

    assert verify_password(password, password_hash) is True


def test_wrong_password_fails():
    password = "employee123"
    password_hash = hash_password(password)

    assert verify_password("wrong-password", password_hash) is False


def test_same_password_gets_different_hashes():
    password = "employee123"

    hash_one = hash_password(password)
    hash_two = hash_password(password)

    assert hash_one != hash_two
    assert verify_password(password, hash_one) is True
    assert verify_password(password, hash_two) is True