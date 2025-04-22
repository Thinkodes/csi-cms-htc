"""
Author: Ansh Mathur
Github: github.com/Fakesum
Repo: github.com/Thinkodes/CMS
"""
def __bootloader():
    import sys, os
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))

__bootloader()

from CMS import main

main()