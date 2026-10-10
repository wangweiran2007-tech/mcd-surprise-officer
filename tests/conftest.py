# -*- coding: utf-8 -*-
"""让 tests/ 能 import 到 scripts/ 下的被测模块。"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
