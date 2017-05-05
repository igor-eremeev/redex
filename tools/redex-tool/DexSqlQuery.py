#!/usr/bin/env python3

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import sqlite3
import sys
import readline
from os.path import expanduser
import re

PAT_ANON_CLASS = re.compile(".*\$[0-9]+;")

HISTORY_FILE = expanduser("~/.dexsql.history")

OPCODES = dict()
OPCODES[0x1a] = "const-string"
OPCODES[0x1b] = "const-string/jumbo"
OPCODES[0x1c] = "const-class"
OPCODES[0x1f] = "check-cast"
OPCODES[0x20] = "instance-of"
OPCODES[0x22] = "new-instance"
OPCODES[0x52] = "iget"
OPCODES[0x53] = "iget/wide"
OPCODES[0x54] = "iget-object"
OPCODES[0x55] = "iget-boolean"
OPCODES[0x56] = "iget-byte"
OPCODES[0x57] = "iget-char"
OPCODES[0x58] = "iget-short"
OPCODES[0x59] = "iput"
OPCODES[0x5a] = "iput/wide"
OPCODES[0x5b] = "iput-object"
OPCODES[0x5c] = "iput-boolean"
OPCODES[0x5d] = "iput-byte"
OPCODES[0x5e] = "iput-char"
OPCODES[0x5f] = "iput-short"
OPCODES[0x60] = "sget"
OPCODES[0x61] = "sget/wide"
OPCODES[0x62] = "sget-object"
OPCODES[0x63] = "sget-boolean"
OPCODES[0x64] = "sget-byte"
OPCODES[0x65] = "sget-char"
OPCODES[0x66] = "sget-short"
OPCODES[0x67] = "sput"
OPCODES[0x68] = "sput/wide"
OPCODES[0x69] = "sput-object"
OPCODES[0x6a] = "sput-boolean"
OPCODES[0x6b] = "sput-byte"
OPCODES[0x6c] = "sput-char"
OPCODES[0x6d] = "sput-short"
OPCODES[0x6e] = "invoke-virtual"
OPCODES[0x6f] = "invoke-super"
OPCODES[0x70] = "invoke-direct"
OPCODES[0x71] = "invoke-static"
OPCODES[0x72] = "invoke-interface"
OPCODES[0x74] = "invoke-virtual/range"
OPCODES[0x75] = "invoke-super/range"
OPCODES[0x76] = "invoke-direct/range"
OPCODES[0x77] = "invoke-static/range"
OPCODES[0x78] = "invoke-interface/range"

# operates on classes.name column
# return the first n levels of the package: PKG("com/foo/bar", 2) => "com/foo"
def udf_pkg_2arg(text, n):
    groups = text.split('/')
    if (n >= (len(groups) - 1)):
        n = len(groups) - 1
    return '/'.join(groups[:n])

def udf_pkg_1arg(text):
    return udf_pkg_2arg(text, 9999)

# operates on access column
def udf_is_interface(access):
    return access & 0x00000200

# operates on access column
def udf_is_static(access):
    return access & 0x00000008

# operates on access column
def udf_is_final(access):
    return access & 0x00000010

# operates on access column
def udf_is_native(access):
    return access & 0x00000100

# operates on access column
def udf_is_abstract(access):
    return access & 0x00000400

# operates on access column
def udf_is_synthetic(access):
    return access & 0x00001000

# operates on access column
def udf_is_annotation(access):
    return access & 0x00002000

# operates on access column
def udf_is_enum(access):
    return access & 0x00004000

# operates on access column
def udf_is_constructor(access):
    return access & 0x00010000

# operates on dex column
def udf_is_voltron_dex(dex_id):
    return not dex_id.startswith("dex/")

# operates on classes.name
def udf_is_inner_class(name):
    return "$" in name

# operates on classes.name
def udf_is_anon_class(name):
    return PAT_ANON_CLASS.match(name) is not None

# convert a numerical opcode to its name
def udf_opcode(opcode):
    return OPCODES.get(opcode, opcode)

# operates on dex column
def udf_is_coldstart(dex_id):
    return dex_id == "dex/0" or dex_id == "dex/1" or dex_id == "dex/2"

conn = sqlite3.connect(sys.argv[1])
conn.create_function("PKG", 2, udf_pkg_2arg)
conn.create_function("PKG", 1, udf_pkg_1arg)
conn.create_function("IS_INTERFACE", 1, udf_is_interface)
conn.create_function("IS_STATIC", 1, udf_is_static)
conn.create_function("IS_FINAL", 1, udf_is_final)
conn.create_function("IS_NATIVE", 1, udf_is_native)
conn.create_function("IS_ABSTRACT", 1, udf_is_abstract)
conn.create_function("IS_SYNTHETIC", 1, udf_is_synthetic)
conn.create_function("IS_ANNOTATION", 1, udf_is_annotation)
conn.create_function("IS_ENUM", 1, udf_is_enum)
conn.create_function("IS_CONSTRUCTOR", 1, udf_is_constructor)
conn.create_function("IS_VOLTRON_DEX", 1, udf_is_voltron_dex)
conn.create_function("IS_INNER_CLASS", 1, udf_is_inner_class)
conn.create_function("IS_ANON_CLASS", 1, udf_is_anon_class)
conn.create_function("OPCODE", 1, udf_opcode)
conn.create_function("IS_COLDSTART", 1, udf_is_coldstart)

cursor = conn.cursor()

open(HISTORY_FILE, 'a')
readline.read_history_file(HISTORY_FILE)
readline.set_history_length(1000)
while True:
    line = input("> ")
    readline.write_history_file(HISTORY_FILE)
    try:
        rows = 0
        cursor.execute(line)
        for row in cursor.fetchall():
            print(str(row))
            rows += 1
        print("%d rows returned by query" % (rows))
    except sqlite3.OperationalError as e:
        print("Query caused exception: %s" % str(e))

cursor.close()
conn.close()
