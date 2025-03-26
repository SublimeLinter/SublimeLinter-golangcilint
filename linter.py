from SublimeLinter.lint import Linter, WARNING


class GolangCILint(Linter):
    def cmd(self):
        if self.settings.get("v1", False):
            return 'golangci-lint run ${args} --out-format tab ${file_path}'
        return 'golangci-lint run ${args} --output.tab.path stdout ${file_path}'
    tempfile_suffix = '-'
    # Column reporting is optional and not provided by all linters.
    # Issues reported by the 'typecheck' linter are treated as errors,
    # because they indicate code that won't compile. All other linter issues
    # are treated as warnings.
    regex = r'^(?P<filename>(\w+:\\\\)?.[^:]+):(?P<line>\d+)(:(?P<col>\d+))?\s+' + \
        r'(?P<code>(?P<error>typecheck)|\w+)\s+(?P<message>.+)$'
    default_type = WARNING
    defaults = {
        'selector': 'source.go',
    }
