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

    def finalize_cmd(self, cmd, context, at_value='', auto_append=False):
        """prevents SublimeLinter to append filename at the end of cmd"""
        return cmd

    def _live_lint(self, cmd, code):
        dir = os.path.dirname(self.filename)
        files = [file for file in os.listdir(dir) if file.endswith(".go")]
        if len(files) > 100:
            print("golangcilint: too many files ({}), live linting skipped".format(len(files)))
            return ""
        return self.tmpdir(cmd, dir, files, self.filename, code)

    def _in_place_lint(self, cmd):
        return self.execute(cmd)

    def tmpdir(self, cmd, dir, files, filename, code):
        """Run an external executable using a temp dir filled with files and return its output."""
        try:
            with tempfile.TemporaryDirectory(dir=dir, prefix=".golangcilint-") as tmpdir:
                for filepath in files:
                    target = os.path.join(tmpdir, filepath)
                    filepath = os.path.join(dir, filepath)
                    if os.path.basename(target) != os.path.basename(filename):
                        os.link(filepath, target)
                        continue
                    # source file hasn't been saved since change
                    # so update it from our live buffer for now
                    with open(target, 'wb') as w:
                        if isinstance(code, str):
                            code = code.encode('utf8')
                        w.write(code)
                return self.execute(cmd + [tmpdir])
        except FileNotFoundError:
            print("golangcilint file not found error on `{}`".format(dir))
            return ""
        except PermissionError:
            print("golangcilint permission error on `{}`".format(dir))
            return ""

    def execute(self, cmd):
        lines = []
        output = self.communicate(cmd)
        report = json.loads(output)
        currnt = os.path.basename(self.filename)

        """format issues into formal pattern"""
        for issue in report["Issues"]:
            name = issue["Pos"]["Filename"]
            mark = name.rfind("/")
            mark = 0 if mark == -1 else mark+1
            issue["Pos"]["Shortname"] = name[mark:]
            """skip issues from unrelated files"""
            if issue["Pos"]["Shortname"] != currnt:
                continue
            lines.append(
                "{}:{}:{}:{}:{}".format(
                    issue["Pos"]["Shortname"],
                    issue["Pos"]["Line"],
                    issue["Pos"]["Column"],
                    issue["Level"],
                    issue["Text"]
                )
            )

        return "\n".join(lines)
