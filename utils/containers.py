"""
MIT License

Copyright (c) 2021 - µYert

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from asyncio import AbstractEventLoop, Task, get_event_loop
from asyncio import sleep as async_sleep
from collections.abc import Hashable, MutableMapping
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from types import MappingProxyType, SimpleNamespace
from typing import Any, Iterator, Tuple, Union

from humanize import naturaldelta
import numpy as np


@dataclass
class TimedValue:
    value: Any
    expires: datetime
    task: Task


class TimedCache(MutableMapping):
    """
    A dictionary that delete it's own keys
    a certain amount of time after being inserted

    The timer is reset / updated if an item is inserted in the same slot
    """

    def _make_delays(
        self, delay: Union[timedelta, datetime, int, None]
    ) -> Tuple[int, datetime]:
        """converts a delay into seconds"""

        dt_now = datetime.now(tz=timezone.utc)

        if isinstance(delay, timedelta):
            return delay.total_seconds(), (dt_now + delay)

        elif isinstance(delay, datetime):
            delta = dt_now - delay.replace(tzinfo=timezone.utc)
            return delta.total_seconds(), delay

        elif isinstance(delay, int):
            final_delay = delay or self.timeout
            return final_delay, (dt_now + timedelta(seconds=final_delay))

        elif delay is None:
            return self.timeout

        else:  # hardcoding ? don't know about what you mean
            raise TypeError(
                f"Expected (timedelta, datetime, int, None), got {delay.__class__.__name__}"
            )

    def __init__(
        self,
        *,
        timeout: Union[timedelta, datetime, int] = 600,
        loop: AbstractEventLoop = None,
    ):
        self.timeout = timeout  # funky way to use the default timeout in the init
        self.timeout, _ = self._make_delays(timeout)
        self.loop = loop or get_event_loop()
        self.storage = {}

    async def _timed_del(self, key: Hashable, timeout: int) -> None:
        """Deletes the item and the task associated with it"""
        self.storage.pop(await async_sleep(timeout or self.timeout, result=key))

    def __setitem__(self, key: Hashable, value: Any, *, timeout: int = None) -> None:
        if old_val := self.storage.pop(key, None):
            old_val.task.cancel()

        timeout, final_time = self._make_delays(timeout)
        coro = self._timed_del(key, timeout=timeout)
        task = self.loop.create_task(coro, name="Timed deletion")

        self.storage[key] = TimedValue(value=value, expires=final_time, task=task)

    def __delitem__(self, key: Hashable) -> None:
        self.storage[key].task.cancel()
        del self.storage[key]

    def get(self, key: Hashable, default: Any = None) -> Any:
        """ Get a value from TimedCache. """
        timed_value = self.storage.get(key, default)
        return getattr(timed_value, "value", default)

    def set(
        self, key: Hashable, value: Any, timeout: Union[timedelta, datetime, int] = None
    ) -> Any:
        """ Set's the value into TimedCache. """
        self.__setitem__(key, value, timeout=timeout)
        return value

    def __getitem__(self, key: Hashable) -> Any:
        return self.storage[key].value

    def __iter__(self) -> iter:
        return iter(self.storage)

    def __len__(self) -> int:
        return len(self.storage)

    def _clean_data(self) -> Iterator[Tuple[Hashable, Tuple[Any, str]]]:
        dt_now = datetime.now(tz=timezone.utc)
        for key, timedvalue in self.storage.items():
            yield key, (
                timedvalue.value,
                f"Expires in {naturaldelta(dt_now - timedvalue.expires)}",
            )

    def __repr__(self) -> repr:
        return repr(self.storage)

    def __str__(self) -> str:
        return str({k: v for k, v in self._clean_data()})

    def __eq__(self, value):
        return self.storage == value

    def __bool__(self):
        return bool(self.storage)

    def __del__(self):
        for key in self.storage.keys():
            del self.storage[key]


class NestedNamespace(SimpleNamespace):  # Thanks, cy
    """
    A class that transforms a dictionnary into an object with the same attributes
    Pretty useful for jsons
    """

    def __init__(self, **attrs):
        self.__attrs = attrs
        new_attrs = self._prepare_(**attrs)
        super().__init__(**new_attrs)

    def _prepare_(self, **attrs) -> dict:
        for key, value in attrs.items():
            if isinstance(value, dict):
                attrs[key] = self.__class__(**value)
            if isinstance(value, list):
                counter = 1
                for item in value:
                    if isinstance(item, dict):
                        if counter == 1:
                            _k = list(item.keys())[0]
                            _v = list(item.values())[0]
                            attrs[key] = self.__class__(**{str(_k): str(_v)})
                            counter += 1
                        else:
                            _k = list(item.keys())[0]
                            _v = list(item.values())[0]
                            setattr(attrs[key], _k, _v)
        _attrs = (
            attrs  # do this to avoid changing the size of the dict whilst iterating
        )
        return _attrs

    def __repr__(self) -> str:
        attrs = " ".join(
            f"{k}={v}" for k, v in self.__dict__.items() if not k.startswith("_")
        )
        return f"<{self.__class__.__name__} {attrs}>"

    def to_dict(self) -> MappingProxyType:
        """ Returns to a dict type. """
        return MappingProxyType(self.__attrs)

class DieEval:
    value = 0
    average = 0

    def __init__(self, num, die, op, mod):
        self.ops = {'-': lambda l, r: l - r, '+': lambda l, r: l + r}
        self.num = int(num)
        self.die = int(die)
        self.op = op
        self.mod = int(mod)
        self.eval()

    def eval(self):
        self.rolls = [np.random.randint(1, self.die) for _ in range(self.num)]
        self.averate = sum(self.rolls) / len(self.rolls)
        self.total = self.ops[self.op](sum(self.rolls), self.mod)

    @classmethod
    def generate(cls, **kwargs):
        """Makes a random die object, but you can pass each param as a kwarg if you want"""
        num_min = kwargs.pop('num_min', None) or 1
        num_max = kwargs.pop('num_max', None) or 20
        num_min, num_max = min(num_min, num_max), max(num_min, num_max) #sanity checks

        size_min = kwargs.pop('size_min', None) or 2
        size_max = kwargs.pop('size_max', None) or 20
        size_min, size_max = min(size_min, size_max), max(size_min, size_max)

        op = kwargs.pop('op', None) or np.random.choice(['+', '-'])

        mod_min = kwargs.pop('mod_min', None) or 0
        mod_max = kwargs.pop('mod_max', None) or 10
        mod_min, mod_max = min(mod_min, mod_max), max(mod_min, mod_max)

        num = np.random.randint(num_min, num_max)
        size = np.random.choice(np.arange(size_min, size_max, 2))
        mod = np.random.randint(mod_min, mod_max)

        return cls(num, size, op, mod)

    def __str__(self):
        if self.mod != 0:
            return f"{self.num}d{self.die}{self.op}{self.mod}"
        return f"{self.num}d{self.die}"

    def __repr__(self):
        num = self.num
        die = self.die
        op = self.op
        mod = self.mod
        if mod != 0:
            return f"<class DieEval; total={self.total}, {num}d{die}{op}{mod}>"
        return f"<class DieEval; total={self.total}, {num}d{die}>"

    def __int__(self): return self.total

    def __add__(self, other):
        return self.total + int(other)

    def __sub__(self, other):
        return self.total - int(other)

    def print(self):
        out = f"{self} -> {self.total}\nRolls: "
        out += ', '.join(map(str, sorted(self.rolls, reverse=True)))
        out += f"\nAverage roll: {self.average:.2f}"
        return out
