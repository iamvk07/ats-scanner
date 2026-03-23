#!/usr/bin/env python3
"""
ATS Scanner — Resume vs Job Description Analyzer
Author: Vedant Kadam
GitHub: github.com/iamvk07
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ats_scanner.cli import main

if __name__ == "__main__":
    main()
