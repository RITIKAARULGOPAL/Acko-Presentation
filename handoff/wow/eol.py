# read a file as LF; write it back with the line endings it had
def rd(p):
    raw = open(p, encoding="utf-8", newline="").read()
    return raw.replace("\r\n", "\n"), ("\r\n" if "\r\n" in raw else "\n")
def wr(p, s, nl):
    open(p, "w", encoding="utf-8", newline="").write(s.replace("\r\n", "\n").replace("\n", nl))
