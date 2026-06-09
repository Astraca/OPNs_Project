import unittest

from pydantic import ValidationError

from app.schemas.auth_schema import UserLoginRequest, UserRegisterRequest
from app.utils.security import hash_password, verify_password


class AuthSecurityTestCase(unittest.TestCase):
    def test_hashes_valid_short_password(self) -> None:
        password_hash = hash_password("12345678")

        self.assertTrue(password_hash.startswith("$2b$"))
        self.assertTrue(verify_password("12345678", password_hash))
        self.assertFalse(verify_password("wrong-password", password_hash))

    def test_register_rejects_password_longer_than_bcrypt_limit(self) -> None:
        with self.assertRaises(ValidationError):
            UserRegisterRequest(
                username="longpass",
                email="longpass@example.com",
                password="a" * 73,
            )

    def test_register_rejects_multibyte_password_longer_than_bcrypt_limit(self) -> None:
        with self.assertRaises(ValidationError):
            UserRegisterRequest(
                username="unicodepass",
                email="unicode@example.com",
                password="测" * 25,
            )

    def test_login_accepts_short_random_password_for_authentication(self) -> None:
        payload = UserLoginRequest(username_or_email="ast", password="x")

        self.assertEqual(payload.username_or_email, "ast")
        self.assertEqual(payload.password, "x")


if __name__ == "__main__":
    unittest.main()
