#!/data/data/com.termux/files/home/.local/bin/python
import sys

import pysrt

if __name__ == "__main__":
    fn = sys.argv[1]
    amount = int(sys.argv[2].strip())
    srt = pysrt.SubRipFile(fn)
    sub = srt.open(fn, encoding="utf-8")
    sub.shift(amount)
    srt.save(fn, encoding="utf-8")
    print("done")
