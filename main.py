#!/usr/bin/env python3
"""One Line, One Laugh: emit a single joke as /output/entry.txt.

The joke: a customer asks the barber for "something low-maintenance"
and the barber answers with a mirror and thirty seconds of silence.
The silence is the punchline — the hair speaks for itself.

The program is stdlib only and deterministic: it writes the line
exactly, with no trailing newline, and can check itself with
``--self-test``. The gate it enforces is the competition's: the file
must hold UTF-8 text of 1 to 200 characters, a single line, and more
than whitespace.
"""
import hashlib
import os
import sys
import tempfile

LINE = "I asked the barber for 'something low-maintenance'; he gave me a mirror and thirty seconds of silence."
LIMIT = 200
# The winning band for one-liner entries in past resolved boards.
BAND_LOW = 60
BAND_HIGH = 195


class GateFailure(Exception):
    """Raised when a candidate line breaks the competition gate."""


def problems(text):
    """List every way `text` breaks the gate; empty list means it passes."""
    found = []
    if not isinstance(text, str):
        return ["not text"]
    if text == "":
        found.append("empty")
    if len(text) > LIMIT:
        found.append("too long: %d characters over a %d limit"
                     % (len(text), LIMIT))
    if text.strip() == "":
        found.append("only whitespace")
    if text != text.strip():
        found.append("leading or trailing whitespace")
    if "\n" in text or "\r" in text:
        found.append("more than one line")
    bad = [ch for ch in text if ord(ch) < 32 or ord(ch) == 127]
    if bad:
        found.append("control character %r" % bad[0])
    return found


def check_or_raise(text):
    """Return `text` unchanged, or raise GateFailure naming the problem."""
    flaws = problems(text)
    if flaws:
        raise GateFailure("; ".join(flaws))
    return text


def emit(path):
    """Write the line to `path` and confirm the bytes round-trip.

    Returns (line, sha256 hex digest of the written bytes).
    """
    line = check_or_raise(LINE)
    blob = line.encode("utf-8")
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    with open(path, "wb") as handle:
        handle.write(blob)
    with open(path, "rb") as handle:
        back = handle.read()
    if back != blob:
        raise SystemExit("round-trip mismatch: the file is not the line")
    return line, hashlib.sha256(blob).hexdigest()


def _self_test_cases():
    """(text, should_pass, label) triples for the gate."""
    return [
        ("", False, "empty"),
        ("   ", False, "whitespace only"),
        ("x" * 201, False, "201 characters, over the limit"),
        ("a\nb", False, "two lines"),
        (" padded", False, "leading space"),
        ("padded ", False, "trailing space"),
        ("a\rb", False, "carriage return"),
        ("a\x00b", False, "null byte"),
        ("a\tb", False, "tab"),
        ("y", True, "one character, the lower edge"),
        ("z" * 200, True, "200 characters, the upper edge"),
    ]


def self_test():
    """Run the gate cases, then an end-to-end write in a scratch dir."""
    for text, should_pass, label in _self_test_cases():
        flaws = problems(text)
        if should_pass and flaws:
            raise SystemExit("self-test FAIL: %s was rejected: %s"
                             % (label, "; ".join(flaws)))
        if not should_pass and not flaws:
            raise SystemExit("self-test FAIL: %s was accepted" % label)
        print("self-test ok: %s -> %s"
              % (label, "accepted" if should_pass else "rejected"))
    flaws = problems(LINE)
    if flaws:
        raise SystemExit("self-test FAIL: the line was rejected: %s"
                         % "; ".join(flaws))
    size = len(LINE.encode("utf-8"))
    if not BAND_LOW <= size <= BAND_HIGH:
        raise SystemExit("self-test FAIL: the line is %d bytes, outside "
                         "the %d-%d byte band" % (size, BAND_LOW, BAND_HIGH))
    print("self-test ok: the line is %d characters, %d bytes, in band"
          % (len(LINE), size))
    with tempfile.TemporaryDirectory() as scratch:
        path = os.path.join(scratch, "entry.txt")
        line, digest = emit(path)
        with open(path, "rb") as handle:
            raw = handle.read()
        if raw != LINE.encode("utf-8"):
            raise SystemExit("self-test FAIL: written bytes are not the line")
        if raw.endswith(b"\n"):
            raise SystemExit("self-test FAIL: trailing newline in the file")
        print("self-test ok: wrote %d bytes, sha256 %s" % (len(raw), digest))
    print("self-test: all cases passed")
    return 0


def _main(argv):
    if len(argv) > 1 and argv[1] == "--self-test":
        return self_test()
    if len(argv) > 1:
        print("usage: main.py [--self-test]", file=sys.stderr)
        return 2
    target = os.environ.get("ENTRY_OUTPUT", "/output/entry.txt")
    line, digest = emit(target)
    print("wrote %s: %d characters, sha256 %s"
          % (target, len(line), digest))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv))
