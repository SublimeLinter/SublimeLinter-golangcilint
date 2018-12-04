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

    def run(self, cmd, code):
        dir = os.path.dirname(self.filename)
        if not dir:
            print("golangcilint: skipped linting of unsaved file")
            return
        if settings.get("lint_mode") == "background":
            return self._live_lint(cmd, code)
        else:
            return self._in_place_lint(cmd)
