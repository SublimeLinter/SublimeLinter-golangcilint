import os
import json
import logging
from SublimeLinter.lint import NodeLinter
from SublimeLinter.lint.linter import LintMatch

logger = logging.getLogger('SublimeLinter.plugin.golangcilint')


class Golangcilint(NodeLinter):
    cmd = "golangci-lint run --fast --out-format json"
    defaults = {"selector": "source.go"}
    axis_base = (1, 1)

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
            line=issue["Pos"]["Line"] - self.axis_base[0],
            col=issue["Pos"]["Column"] - self.axis_base[1],
            code=issue["FromLinter"]
        )
