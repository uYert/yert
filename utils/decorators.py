"""
MIT License

Copyright (c) 2020 - Sudosnok, AbstractUmbra, Nickofolas, Saphielle-Akiyama

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

from asyncio import get_event_loop
from functools import wraps as funct_wraps
from functools import partial as funct_partial


def to_run_in_executor(loop=None, executor=None):
    """Decorates a sync function that will be ran into an executor"""
    def decorator(func):
        @funct_wraps(func)
        def wrapper(*args, **kwargs):
            partial = funct_partial(func, *args, **kwargs)
            loop = loop or get_event_loop()
            return loop.run_in_executor(executor, partial)
        return wrapper
    return decorator