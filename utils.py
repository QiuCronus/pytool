import base64
import binascii
import bisect
import errno
import hashlib
import math
import os
import random
import shutil
import socket
import stat
import string
import time
import uuid
import zlib
from datetime import datetime, timedelta

codec = "utf8"


def scan_dirs(dirpath: str, limit_count=0, limit_size=0, exclude=None):
    exclude = exclude or [".tmp", ".temp", ".TMP", ".TEMP"]
    paths = set()
    for root, _, names in os.walk(dirpath):
        for name in names:
            pre, ext = os.path.splitext(name)
            abspath = os.path.join(root, name)
            filesize = os.path.getsize(abspath)

            if exclude and ext in exclude:
                continue
            if 0 < limit_size < filesize:
                continue
            if 0 < limit_count < len(paths):
                return list(paths)
            paths.add(abspath)
    return list(paths)


def mkdir(path):
    try:
        os.makedirs(path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
    except OSError as err:
        if err.errno == errno.EEXIST:
            if not os.path.isdir(path):
                raise
        else:
            raise
    finally:
        return path


def rm(path: str):
    if os.path.isfile(path):
        try:
            os.remove(path)
        except OSError as err:
            raise RuntimeError(err)
    elif os.path.isdir(path):
        shutil.rmtree(path, ignore_errors=True)
    else:
        raise RuntimeError(f"rm failed, unknown type: {path}")


def write_file(path, raw, encoding=None):
    mkdir(os.path.split(path)[0])
    mode = "wb" if isinstance(raw, bytes) else "w"
    encoding = None if mode == "wb" else encoding
    with open(path, raw, encoding=encoding) as fd:
        fd.write(raw)


def read_file(path: str, mode="rb", encoding=None):
    encoding = None if mode == "r" else encoding
    with open(path, mode, encoding=encoding) as fd:
        return fd.read()


def iter_read_file(path: str, mode="rb"):
    for line in open(path, mode):
        yield line


def randstr(length: int):
    sample = string.ascii_letters + string.digits
    return "".join([random.choice(sample) for _ in range(length)])


def rgets(container: dict, path: str, default=None):
    def _gets(_container: dict, _path: str):
        _path = _path.strip()
        if _path.count(".") > 0:
            pre, ext = _path.split(".", 1)
            if pre in _container.keys():
                return _gets(_container[pre], ext)
        if _path in _container.keys():
            return _container.get(_path)
        return default

    return _gets(container, path)


def hsize(size: int):
    d = [
        (1024 - 1, "KB"),
        (1024**2 - 1, "MB"),
        (1024**3 - 1, "GB"),
        (1024**4 - 1, "TB"),
    ]
    s = [x[0] for x in d]
    index = bisect.bisect_left(s, size) - 1
    if index == -1:
        return f"{round(size, 2)}B"
    b, u = d[index]
    return f"{round(size / (b + 1), 2)}{u}"


def uid(keep_hyphen=False):
    uid = uuid.uuid4()
    if keep_hyphen:
        return str(uid)
    return uid.hex


def md5(raw):
    if isinstance(raw, str):
        raw = raw.encode(codec)
    m = hashlib.md5()
    m.update(raw)
    return m.hexdigest()


def md5file(path, chunk_size=8192):
    m = hashlib.md5()
    with open(path, "rb") as fd:
        while True:
            chunk = fd.read(chunk_size)
            if not chunk:
                break
            m.update(chunk)
    return m.hexdigest()


def hostname():
    return socket.gethostname()


def compress(raw) -> bytes:
    if isinstance(raw, str):
        raw = raw.encode(codec)
    return zlib.compress(raw)


def decompress(raw) -> bytes:
    if isinstance(raw, str):
        raw = raw.encode(codec)
    return zlib.decompress(raw)


def b64encode(raw, return_str=False):
    if isinstance(raw, str):
        raw = raw.encode(codec)
    r = base64.b64encode(raw)
    if return_str:
        return r.decode(codec)
    return r


def b64decode(raw, return_str=False):
    if isinstance(raw, str):
        raw = raw.encode(codec)
    r = base64.b64decode(raw)
    if return_str:
        return r.decode(codec)
    return r


def b64encode2(raw, return_str=False):
    if isinstance(raw, str):
        raw = raw.encode(codec)
    r = binascii.b2a_base64(raw)
    if return_str:
        return r.decode(codec)
    return r


def b64decode2(raw, return_str=False):
    if isinstance(raw, str):
        raw = raw.encode(codec)
    r = binascii.a2b_base64(raw)
    if return_str:
        return r.decode(codec)
    return r


def timezone():
    offset = time.timezone if (time.localtime().tm_isdst == 0) else time.altzone
    return int(offset / 3600 * -1)


def now(offset_hours: int = 0):
    if offset_hours == 0:
        offset_hours = timezone()

    utc = datetime.utcnow()
    if offset_hours:
        delta = timedelta(hours=offset_hours)
        utc += delta
    return utc


def now_str(fmt: str = "%Y-%m-%d %H:%M:%S", offset_hour: int = 0):
    d = now(offset_hour)
    return d.strftime(fmt).strip()


def timestamp(length: int = 10, offset_hour: int = 0):
    bit = max(length - 10, 0)
    plus = math.pow(10, bit)
    d = now(offset_hour)
    return int(d.timestamp() * plus)


def ts_to_datetime(ts: int, fmt: str = "%Y-%m-%d %H:%M:%S"):
    ts = int(ts)
    d = datetime.utcfromtimestamp(ts)
    return d.strftime(fmt)
