import os
import json
import tempfile
from SublimeLinter.lint import Linter, util
from SublimeLinter.lint.persist import settings


class Golangcilint(Linter):
    cmd = "golangci-lint run --fast --out-format json --enable typecheck"
    regex = r"(?:[^:]+):(?P<line>\d+):(?P<col>\d+):(?:(?P<warning>warning)|(?P<error>error)):(?P<message>.*)"
    defaults = {"selector": "source.go"}
    error_stream = util.STREAM_STDOUT
    multiline = False
