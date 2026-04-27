"""
Фабрики для создания объектов (Factory Pattern).
"""
import random
import string
import re
from .models import QuizSession


class SessionCodeFactory:
    """Фабрика для генерации уникальных кодов сессий."""

    ALPHABET = string.ascii_uppercase + string.digits
    VALID_PATTERN = re.compile(r'^[A-Z0-9]+$')

    @staticmethod
    def _generate(length: int) -> str:
        """Генерирует случайный код."""
        return ''.join(random.choices(SessionCodeFactory.ALPHABET, k=length))

    @staticmethod
    def _is_unique(code: str) -> bool:
        """Проверяет уникальность кода."""
        return not QuizSession.objects.filter(session_code=code).exists()

    @staticmethod
    def _validate(code: str):
        """Проверяет формат кода."""
        if not SessionCodeFactory.VALID_PATTERN.match(code):
            raise ValueError("Session code must contain only A-Z and 0-9")

    @staticmethod
    def create(length: int = 6) -> str:
        """Создать уникальный код."""
        while True:
            code = SessionCodeFactory._generate(length)

            if SessionCodeFactory._is_unique(code):
                return code

    @staticmethod
    def create_with_prefix(prefix: str, length: int = 6) -> str:
        """Создать код с префиксом."""
        prefix = prefix.upper()

        SessionCodeFactory._validate(prefix)

        while True:
            code = prefix + SessionCodeFactory._generate(length)

            if SessionCodeFactory._is_unique(code):
                return code