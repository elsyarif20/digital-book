# models.py

from typing import Any, Dict

class UserModel:
    def __init__(self, username: str, email: str):
        """
        Inisialisasi UserModel.

        Args:
        - username (str): Nama pengguna.
        - email (str): Alamat email.
        """
        self.username = username
        self.email = email

    def to_dict(self) -> Dict[str, Any]:
        """
        Konversi UserModel ke dictionary.

        Returns:
        - Dict[str, Any]: Dictionary yang mewakili UserModel.
        """
        return {
            "username": self.username,
            "email": self.email
        }

class SettingsModel:
    def __init__(self, theme: str, language: str):
        """
        Inisialisasi SettingsModel.

        Args:
        - theme (str): Tema aplikasi.
        - language (str): Bahasa aplikasi.
        """
        self.theme = theme
        self.language = language

    def to_dict(self) -> Dict[str, Any]:
        """
        Konversi SettingsModel ke dictionary.

        Returns:
        - Dict[str, Any]: Dictionary yang mewakili SettingsModel.
        """
        return {
            "theme": self.theme,
            "language": self.language
        }