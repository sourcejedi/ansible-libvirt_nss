#!/usr/bin/env python3

import unittest
import sys
import os
import re

# Work in bytes, because all significant characters are ASCII.
DATABASE = b"hosts:"
SERVICE = b"libvirt"

def change_line(line):
    if not line.startswith(b"hosts:"):
        return line

    split = re.split(rb"[ \t](dns|resolve)([ \t]|$)", line, maxsplit=1)
    if len(split) == 1:
        raise Exception("hosts: line of nsswitch.conf does not include \"dns\" or \"resolve\"")

    before_dns = split[0]
    if re.search(rb"[ \t]" + SERVICE + rb"([ \t]|$)", before_dns):
        return line  # already done

    # In case someone put SERVICE after dns, remove it.
    # Custom actions for SERVICE are removed.
    line = re.sub(rb"[ \t]" + SERVICE + rb"([ \t]*\[[^]]*\])*" + rb"([ \t]|$)",
                  lambda m: m.group(2),
                  line)

    return re.sub(rb"[ \t](dns|resolve)([ \t]|$)", 
                  lambda m: b" " + SERVICE + m.group(0),
                  line, count=1)

class Test(unittest.TestCase):
    def test(self):
        self.assertEqual(change_line(b""), b"")
        with self.assertRaises(Exception):
            change_line(b"hosts: ")

        self.assertEqual(change_line(b"hosts: dns"),
                         b"hosts: libvirt dns")
        self.assertEqual(change_line(b"hosts: libvirt dns"),
                         b"hosts: libvirt dns")
        self.assertEqual(change_line(b"hosts: dns libvirt"),
                         b"hosts: libvirt dns")
        self.assertEqual(change_line(b"hosts: dns libvirt [SUCCESS=return] [NOTFOUND=return]"),
                         b"hosts: libvirt dns")

        self.assertEqual(change_line(b"hosts: files dns"),
                         b"hosts: files libvirt dns")
        self.assertEqual(change_line(b"hosts: files libvirt dns"),
                         b"hosts: files libvirt dns")

        self.assertEqual(change_line(b"hosts: libvirt mdns4_minimal dns"),
                         b"hosts: libvirt mdns4_minimal dns")

        self.assertEqual(change_line(b"hosts: mymachines resolve [!UNAVAIL=return] myhostname files dns"),
                         b"hosts: mymachines libvirt resolve [!UNAVAIL=return] myhostname files dns")

def main(args):
    if len(args) != 2:
        raise Exception("Wrong number of arguments")

    with open(args[0], "rb") as file_in, \
            open(args[1], "wb") as file_out:
        for line in file_in:
            new_line = change_line(line)
            file_out.write(new_line)

if __name__ == '__main__':
    try:
        main(sys.argv[1:])
    except Exception as e:
        sys.exit(e)
