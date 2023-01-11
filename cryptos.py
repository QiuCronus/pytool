import base64
import copy
import ctypes
import functools
import os
import sys

__all__ = ["encrypt", "decrypt"]

_library = None
codec = "utf8"

VERSION = (1, 0)

if VERSION <= (1, 0):

    def load_library(caller):
        @functools.wraps(caller)
        def load(*args, **kwargs):
            global _library

            if _library is None:
                suffix = "dll" if sys.platform.lower().startswith("win") else "so"
                path = os.path.join(os.path.dirname(__file__), f"c.{suffix}")
                _library = ctypes.CDLL(path)
                _library.init()

            return caller(*args, **kwargs)

        return load

    @load_library
    def encrypt_string(raw, encoding="utf8"):
        raw_ = raw.encode(encoding)
        len_ = int(len(raw_) * 2 + 1)
        buf = ctypes.create_string_buffer(len_)
        r = _library.doEncryptString(raw_, len_, buf)
        return buf.value.decode(encoding) if r == 0 else None

    @load_library
    def decrypt_string(raw: str, encoding="utf8"):
        raw_ = raw.encode(encoding)
        len_ = int(len(raw_) * 2 + 1)
        buf = ctypes.create_string_buffer(len_)
        r = _library.doDecryptString(raw_, len_, buf)
        return buf.value.decode(codec) if r == 0 else None

    @load_library
    def encrypt(raw: bytes):
        raw_ = copy.copy(raw)
        length = len(raw_)
        r = _library.doEncryptBytes(raw_, length)
        return raw_ if r == 0 else None

    decrypt = encrypt

else:

    def load_library(caller):
        @functools.wraps(caller)
        def load(*args, **kwargs):
            global _library

            if _library is None:
                suffix = "dll" if sys.platform.lower().startswith("win") else "so"
                path = os.path.join(os.path.dirname(__file__), f"c.{suffix}")
                _library = ctypes.CDLL(path)

            return caller(*args, **kwargs)

        return load

    @load_library
    def _invoke_raw_api(func, raw):
        return func(raw, len(raw))

    @load_library
    def _invoke_file_api(func, src, dst):
        return func(src, dst)

    def encrypt(raw: bytes) -> bytes:
        func = _library.EncryptBytes
        func.argtypes = [ctypes.c_char_p, ctypes.c_int]
        func.restype = ctypes.c_char_p
        #
        enc_base64 = _invoke_raw_api(func, raw)
        return base64.b64decode(enc_base64)

    def decrypt(raw: bytes) -> bytes:
        func = _library.DecryptBytes
        func.argtypes = [ctypes.c_char_p, ctypes.c_int]
        func.restype = ctypes.c_char_p
        #
        enc_base64 = _invoke_raw_api(func, raw)
        return base64.b64decode(enc_base64)

    def encrypt_string(raw: str, encoding="utf8") -> str:
        raw_ = raw.encode(encoding)
        r = encrypt(raw_)
        return r.decode(encoding)

    def decrypt_string(raw: str, encoding="utf8") -> str:
        raw_ = raw.encode(encoding)
        r = decrypt(raw_)
        return r.decode(encoding)

    def encrypt_small_file(src: str, dst: str) -> int:
        func = _library.EncryptFile
        func.decrypts_file.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
        func.decrypts_file.restype = ctypes.c_int
        #
        bsrc, bdst = src.encode(), dst.encode()
        return _invoke_file_api(func, bsrc, bdst)

    def decrypt_small_file(src: str, dst: str) -> int:
        func = _library.DecryptFile
        func.decrypts_file.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
        func.decrypts_file.restype = ctypes.c_int
        #
        bsrc, bdst = src.encode(), dst.encode()
        return _invoke_file_api(func, bsrc, bdst)
