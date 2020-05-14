"""
MIT License

Copyright (c) 2020 - Sudosnok, AbstractUmbra, Saphielle-Akiyama

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

from asyncio import AbstractEventLoop, get_event_loop
from asyncio import sleep as async_sleep
from collections import namedtuple
from collections.abc import Hashable, MutableMapping
from types import MappingProxyType, SimpleNamespace
from typing import Any, Union
from datetime import timedelta, datetime, timezone

class TimedCache(MutableMapping):
    """
    A dictionary that delete it's own keys 
    a certain amount of time after being inserted
    
    The timer is reset / updated if an item is inserted in the same slot
    """
    def _convert_delay(self, delay: Union[timedelta, datetime, int, None]):
        """converts a delay into seconds"""
        if isinstance(delay, timedelta):
            return delay.total_seconds()
        if isinstance(delay, datetime):
            return (datetime.now(tz=timezone.utc) - delay).total_seconds()
        
        return delay or self.timeout
    
    def __init__(self, *, timeout: Union[timedelta, datetime, int] = 600, loop: AbstractEventLoop = None):
        self.timeout = self._convert_delay(timeout)
        self.loop = loop or get_event_loop()
        self.storage = {}
    
    async def _timed_del(self, key: Hashable, timeout: int = None) -> None:
        """Deletes the item and the task associated with it"""
        self.storage.pop(await async_sleep(timeout or self.timeout, result=key))

    def __setitem__(self, key: Hashable, value: Any, *, timeout: int = None) -> None:
        if old_val := self.storage.pop(key, None): 
            old_val[1].cancel()
            
        task = self._timed_del(key, timeout=self._convert_delay(timeout))
        self.storage[key] = (value, self.loop.create_task(task))
        
    def __delitem__(self, key: Hashable) -> None:
        self.storage[key][1].cancel()
        del self.storage[key]
        
    def get(self, key: Hashable, default: Any = None) -> Any:
        value = self.storage.get(key, default)
        return value[0] if value else default

    def set(self, key: Hashable, value: Any, timeout: Union[timedelta, datetime, int] = None) -> Any:
        self.__setitem__(key, value, timeout=self._convert_delay(timeout))
        return value
    
    def __getitem__(self, key: Hashable) -> Any: return self.storage[key][0]
    def __iter__(self) -> iter: return iter({k: v[0] for k, v in self.storage.items()})
    def __len__(self) -> int: return len(self.storage)
    def __repr__(self) -> repr: return repr(self.storage)
    def __str__(self) -> str: return str(self.storage)

        
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
        for k, v in attrs.items():
            if isinstance(v, dict):
                attrs[k] = self.__class__(**v)
            if isinstance(v, list):
                v = [self.__class__(**item) for item in v]
        return attrs

    def __repr__(self) -> repr:
        attrs = ' '.join(f'{k}={v}' for k, v in self.__dict__.items() if not k.startswith('_'))
        return f'<{self.__class__.__name__} {attrs}>'

    def to_dict(self) -> MappingProxyType:
        return MappingProxyType(self.__attrs)


def get_index(indexable, index: int, default=None) -> Any:
    """Tries to get an item using it's index, returns the default is not found"""
    try:
        return indexable[index]
    except IndexError:
        return default
