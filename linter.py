import os
import json
import logging
import tempfile
from SublimeLinter.lint import NodeLinter, util
from SublimeLinter.lint.linter import LintMatch
from SublimeLinter.lint.persist import settings

logger = logging.getLogger('SublimeLinter.plugin.golangcilint')


class Golangcilint(NodeLinter):
    # Here are the statistics of how fast the plugin reports the warnings and
    # errors via golangci-lint when all the helpers are disabled and only the
    # specified linter is enabled. In total, when all of them are enabled, it
    # takes an average of 1.6111 secs in a project with seventy-four (74) Go
    # files, 6043 lines (4620 code + 509 comments + 914 blanks).
    #
    # | Seconds | Linter      |
    # |---------|-------------|
    # | 0.7040s | goconst     |
    # | 0.7085s | nakedret    |
    # | 0.7172s | gocyclo     |
    # | 0.7337s | prealloc    |
    # | 0.7431s | scopelint   |
    # | 0.7479s | ineffassign |
    # | 0.7553s | golint      |
    # | 0.7729s | misspell    |
    # | 0.7733s | gofmt       |
    # | 0.7854s | dupl        |
    # | 1.2574s | varcheck    |
    # | 1.2653s | errcheck    |
    # | 1.3052s | gocritic    |
    # | 1.3078s | typecheck   |
    # | 1.3131s | structcheck |
    # | 1.3140s | maligned    |
    # | 1.3159s | unconvert   |
    # | 1.3598s | depguard    |
    # | 1.3678s | deadcode    |
    # | 1.3942s | govet       |
    # | 1.4565s | gosec       |
    cmd = "golangci-lint run --fast --out-format json"
    defaults = {"selector": "source.go"}
    error_stream = util.STREAM_STDOUT
    line_col_base = (1, 1)

    def run(self, cmd, code):
        if not os.path.dirname(self.filename):
            logger.warning("cannot lint unsaved Go (golang) files")
            self.notify_failure()
            return ""

        # If the user has configured SublimeLinter to run in background mode,
        # the linter will be unable to show warnings or errors in the current
        # buffer until the user saves the changes. To solve this problem, the
        # plugin will create a temporary directory, then will create symbolic
        # links of all the files in the current folder, then will write the
        # buffer into a file, and finally will execute the linter inside this
        # directory.
        #
        # Note: The idea to execute the Foreground linter “on_load” even if
        # “lint_mode” is set to “background” cannot be taken in consideration
        # because of the following scenario:
        #
        # - User makes changes to a file
        # - The editor suddently closes
        # - Buffer is saved for recovery
        # - User opens the editor again
        # - Editor loads the unsaved file
        # - Linter runs in an unsaved file
        if settings.get("lint_mode") == "background":
            return self._background_lint(cmd, code)
        else:
            return self._foreground_lint(cmd)

    """match regex against the command output"""
    def find_errors(self, output):
        current = os.path.basename(self.filename)
        exclude = False

        try:
            data = json.loads(output)
        except Exception as e:
            logger.warning(e)
            self.notify_failure()

        """merge possible stderr with issues"""
        if (data
            and "Report" in data
            and "Error" in data["Report"]):
            for line in data["Report"]["Error"].splitlines():
                if line.count(":") < 3:
                    continue
                parts = line.split(":")
                data["Issues"].append({
                    "FromLinter": "typecheck",
                    "Text": parts[3].strip(),
                    "Pos": {
                        "Filename": parts[0],
                        "Line": parts[1],
                        "Column": parts[2],
                    }
                })

        """find relevant issues and yield a LintMatch"""
        if data and "Issues" in data:
            for issue in data["Issues"]:
                """detect broken canonical imports"""
                if ("code in directory" in issue["Text"]
                    and "expects import" in issue["Text"]):
                    issue = self._canonical(issue)
                    yield self._lintissue(issue)
                    exclude = True
                    continue

                """ignore false positive warnings"""
                if (exclude
                    and "could not import" in issue["Text"]
                    and "missing package:" in issue["Text"]):
                    continue

                """issues found in the current file are relevant"""
                if self._shortname(issue) != current:
                    continue

                yield self._lintissue(issue)

    def finalize_cmd(self, cmd, context, at_value='', auto_append=False):
        """prevents SublimeLinter from appending an unnecessary file"""
        return cmd

    def _foreground_lint(self, cmd):
        return self.communicate(cmd)

    def _background_lint(self, cmd, code):
        folder = os.path.dirname(self.filename)
        things = [f for f in os.listdir(folder) if f.endswith(".go")]
        maxsee = settings.get("delay") * 1000
        nfiles = len(things)

        if nfiles > maxsee:
            # Due to performance issues in golangci-lint, the linter will not
            # attempt to lint more than one-hundred (100) files considering a
            # delay of 100ms and lint_mode equal to “background”. If the user
            # increases the delay, the tool will have more time to scan more
            # files and analyze them.
            logger.warning("too many Go (golang) files ({})".format(nfiles))
            self.notify_failure()
            return ""

        try:
            """create temporary folder to store the code from the buffer"""
            with tempfile.TemporaryDirectory(dir=folder, prefix=".golangcilint-") as tmpdir:
                for filepath in things:
                    target = os.path.join(tmpdir, filepath)
                    filepath = os.path.join(folder, filepath)
                    """create symbolic links to non-modified files"""
                    if os.path.basename(target) != os.path.basename(self.filename):
                        os.link(filepath, target)
                        continue
                    """write the buffer into a file on disk"""
                    with open(target, 'wb') as w:
                        if isinstance(code, str):
                            code = code.encode('utf8')
                        w.write(code)
                """point command to the temporary folder"""
                return self.communicate(cmd + [tmpdir])
        except FileNotFoundError:
            logger.warning("cannot lint non-existent folder “{}”".format(folder))
            self.notify_failure()
            return ""
        except PermissionError:
            logger.warning("cannot lint private folder “{}”".format(folder))
            self.notify_failure()
            return ""

    def _shortname(self, issue):
        """find and return short filename"""
        return os.path.basename(issue["Pos"]["Filename"])

    def _severity(self, issue):
        """consider /dev/stderr as errors and /dev/stdout as warnings"""
        return "error" if issue["FromLinter"] == "typecheck" else "warning"

    def _canonical(self, issue):
        mark = issue["Text"].rfind("/")
        package = issue["Text"][mark+1:-1]
        # Go 1.4 introduces an annotation for package clauses in Go source that
        # identify a canonical import path for the package. If an import is
        # attempted using a path that is not canonical, the go command will
        # refuse to compile the importing package.
        #
        # When the linter runs, it creates a temporary directory, for example,
        # “.golangcilint-foobar”, then creates a symbolic link for all relevant
        # files, and writes the content of the current buffer in the correct
        # file. Unfortunately, canonical imports break this flow because the
        # temporary directory differs from the expected location.
        #
        # The only way to deal with this for now is to detect the error, which
        # may as well be a false positive, and then ignore all the warnings
        # about missing packages in the current file. Hopefully, the user has
        # “goimports” which will automatically resolve the dependencies for
        # them. Also, if the false positives are not, the programmer will know
        # about the missing packages during the compilation phase, so it’s not
        # a bad idea to ignore these warnings for now.
        #
        # See: https://golang.org/doc/go1.4#canonicalimports
        return {
            "FromLinter": "typecheck",
            "Text": "cannot lint package “{}” due to canonical import path".format(package),
            "Replacement": issue["Replacement"],
            "SourceLines": issue["SourceLines"],
            "Level": "error",
            "Pos": {
                "Filename": self.filename,
                "Offset": 0,
                "Column": 0,
                "Line": 1
            }
        }

    def _lintissue(self, issue):
        return LintMatch(
            match=issue,
            message=issue["Text"],
            error_type=self._severity(issue),
            line=issue["Pos"]["Line"] - self.line_col_base[0],
            col=issue["Pos"]["Column"] - self.line_col_base[1],
            code=issue["FromLinter"]
        )
