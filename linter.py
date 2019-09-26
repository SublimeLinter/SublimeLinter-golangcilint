from SublimeLinter.lint import Linter, WARNING


class GolangCILint(Linter):
    cmd = 'golangci-lint run --fast'
    # Column reporting is optional and not provided by all linters.
    # Issues reported by the 'typecheck' linter are treated as errors,
    # because they indicate code that won't compile. All other linter issues
    # are treated as warnings.
    regex = r'^(?P<filename>(\w+:\\\\)?.[^:]+):(?P<line>\d+):((?P<col>\d+):)? ' + \
        r'(?P<message>.+\(((?P<error>typecheck)|\w+)\))$'
    default_type = WARNING
    defaults = {
        'selector': 'source.go'
    }
