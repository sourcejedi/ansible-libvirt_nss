#!/usr/bin/env python3

import unittest
import os
import re

NAME = "/etc/nsswitch.conf"
NAME_TMP = NAME + ".tmp"

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

    # In case someone put SERVICE after dns, remove it
    line = re.sub(rb"[ \t]" + SERVICE + rb"([ \t]|$)", 
                  lambda m: m.group(1),
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

        self.assertEqual(change_line(b"hosts: files dns"),
                         b"hosts: files libvirt dns")
        self.assertEqual(change_line(b"hosts: files libvirt dns"),
                         b"hosts: files libvirt dns")

        self.assertEqual(change_line(b"hosts: libvirt mdns4_minimal dns"),
                         b"hosts: libvirt mdns4_minimal dns")

        self.assertEqual(change_line(b"hosts: mymachines resolve [!UNAVAIL=return] myhostname files dns"),
                         b"hosts: mymachines libvirt resolve [!UNAVAIL=return] myhostname files dns")

if __name__ == '__main__':
    file_old = open(NAME, "rb")
    file_tmp = open(NAME_TMP, "wb")
    os.chmod(NAME_TMP, 0o644)  # u+rw,a+r

    changed = False
    for line in file_old:
        new_line = change_line(line)
        if new_line != line:
            changed = True
        file_tmp.write(new_line)

    file_tmp.close()
    file_old.close()
    if changed:
        os.rename(NAME_TMP, NAME)
        print("changed\n")
    else:
        os.unlink(NAME_TMP)
