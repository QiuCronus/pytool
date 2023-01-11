import functools
import time


__all__ = ["retry", "ignore_errors", "profiles", "snapshot"]


def retry(exceptions=Exception, tries=-1, delay=0, max_delay=None):
    def _decorator(func):
        def _wrapper(*args, **kwargs):
            _tries, _delay = tries, delay
            while _tries:
                try:
                    return func(*args, **kwargs)
                except exceptions:
                    _tries -= 1
                    if not _tries:
                        raise
                    time.sleep(_delay)
                    if not max_delay:
                        _delay = min(_delay, max_delay)

        return _wrapper

    return _decorator


def ignore_errors(exceptions=Exception):
    def _decorator(func):
        def _wrapper(*args, **kwargs):
            try:
                func(*args, **kwargs)
            except exceptions:
                pass

        return _wrapper

    return _decorator


def profiles(logger):
    def _decorator(func):
        def _wrapper(*args, **kwargs):
            func_name = func.__name__
            st = time.time() * 1000
            try:
                r = func(*args, **kwargs)
            finally:
                se = time.time() * 1000
                if logger:
                    logger.info("{func} spent {time} ms.".format(func=func_name, time=round(se - st, 4)))

        return _wrapper

    return _decorator


def snapshot():
    pass
