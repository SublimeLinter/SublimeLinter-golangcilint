install:
	rm -f -v "$${HOME}/Library/Application Support/Sublime Text/Installed Packages/SublimeLinter-golangcilint.sublime-package" 2>/dev/null
	zip -r9v "$${HOME}/Library/Application Support/Sublime Text/Installed Packages/SublimeLinter-golangcilint.sublime-package" LICENSE.md linter.py messages messages.json README.md screenshot.png
