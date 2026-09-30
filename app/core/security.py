"""Модуль хеширования и проверки паролей.

Использует Argon2id через pwdlib — рекомендованный OWASP алгоритм для
новых проектов. Argon2id — memory-hard функция, что делает параллельный
подбор на GPU/ASIC существенно дороже, чем bcrypt/scrypt.

Задел на будущее: если через 1-2 года параметры Argon2 устареют
(железо станет быстрее), старые хеши продолжат верифицироваться —
параметры зашиты в саму хеш-строку формата $argon2id$v=19$m=...,t=...,p=...
Новые пароли будут хешироваться с новыми параметрами, а старые —
лениво перехешироваться при следующем логине через `verify_and_update`.
"""

from pwdlib import PasswordHash

# Одна инстанция на процесс. Внутри pwdlib создаёт Argon2Hasher с
# параметрами, рекомендованными на момент релиза библиотеки:
#   time_cost=3, memory_cost=65536 (64 MiB), parallelism=4,
#   hash_len=32, salt_len=16.
# Объект stateless — пересоздавать на каждый вызов нет смысла.
_password_hash = PasswordHash.recommended()


def hash_password(plain_password: str) -> str:
    """Хеширует пароль Argon2id.

    Возвращает строку формата ``$argon2id$v=19$m=65536,t=3,p=4$<salt>$<hash>``,
    пригодную для сохранения в БД (колонка должна быть >= 128 символов,
    у нас в модели — String(255), с запасом).

    Args:
        plain_password: Пароль в открытом виде.

    Returns:
        Хеш пароля в формате Argon2id PHC-строки.
    """
    return _password_hash.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверяет пароль против хеша.

    Сравнение constant-time (внутри argon2-cffi — C-функция argon2_verify).
    Это защищает от timing-атак, при которых атакующий угадывает хеш
    посимвольно по времени ответа.

    Если нужна ленивая миграция хешей при смене параметров Argon2 —
    используй `verify_and_update_password` вместо этой функции.

    Args:
        plain_password: Пароль в открытом виде.
        hashed_password: Хеш из БД.

    Returns:
        True, если пароль совпадает с хешем, иначе False.
    """
    return _password_hash.verify(plain_password, hashed_password)


def verify_and_update_password(
    plain_password: str, hashed_password: str
) -> tuple[bool, str | None]:
    """Проверяет пароль и, если нужно, возвращает новый хеш.

    Атомарная операция: verify + решение о необходимости rehash.
    Используется в `/auth/login` для ленивой миграции устаревших
    хешей при смене параметров Argon2.

    Args:
        plain_password: Пароль в открытом виде.
        hashed_password: Хеш из БД.

    Returns:
        Кортеж ``(is_valid, new_hash)``:

        * ``(True, None)`` — пароль верный, хеш актуален, ничего делать не надо;
        * ``(True, "<новый_хеш>")`` — пароль верный, но параметры устарели:
          надо записать новый хеш в БД;
        * ``(False, None)`` — пароль неверный.
    """
    return _password_hash.verify_and_update(plain_password, hashed_password)
