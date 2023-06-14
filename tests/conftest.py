import io
import os
import sys
import threading
import time
from collections import deque
from dataclasses import dataclass

import pandas as pd
import pytest


def nop(*arg):
    pass


@pytest.hookimpl(trylast=True)
def pytest_configure(config):
    pytest.stdout_copy = io.StringIO()
    tr = config.pluginmanager.getplugin("terminalreporter")
    tr_write = tr.write

    def write(s, *args, **kwargs):
        tr_write(s, *args, **kwargs)
        pytest.stdout_copy.write(s)
