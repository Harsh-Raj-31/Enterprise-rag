from app.cache.cache_key import build_cache_key


def test_same_query_role_and_user_produce_same_key():
    key1 = build_cache_key(
        "How many annual leave days do employees receive?",
        "employee",
        "EMP101",
    )

    key2 = build_cache_key(
        "How many annual leave days do employees receive?",
        "employee",
        "EMP101",
    )

    assert key1 == key2


def test_different_roles_produce_different_keys():
    employee_key = build_cache_key(
        "How many annual leave days do employees receive?",
        "employee",
        "EMP101",
    )

    hr_key = build_cache_key(
        "How many annual leave days do employees receive?",
        "hr",
        "HR201",
    )

    assert employee_key != hr_key


def test_different_users_with_same_role_produce_different_keys():
    user1_key = build_cache_key(
        "How many annual leave days do employees receive?",
        "employee",
        "EMP101",
    )

    user2_key = build_cache_key(
        "How many annual leave days do employees receive?",
        "employee",
        "EMP102",
    )

    assert user1_key != user2_key


def test_query_whitespace_is_normalized():
    key1 = build_cache_key(
        "  How many annual leave days do employees receive?  ",
        "employee",
        "EMP101",
    )

    key2 = build_cache_key(
        "How many annual leave days do employees receive?",
        "employee",
        "EMP101",
    )

    assert key1 == key2


def test_role_is_case_insensitive():
    key1 = build_cache_key(
        "How many annual leave days do employees receive?",
        "Employee",
        "EMP101",
    )

    key2 = build_cache_key(
        "How many annual leave days do employees receive?",
        "employee",
        "EMP101",
    )

    assert key1 == key2