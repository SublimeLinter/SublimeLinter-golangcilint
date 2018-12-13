install:
	rm -- "$${HOME}/Library/Application Support/Sublime Text 3/Installed Packages/SublimeLinter-golangcilint.sublime-package" 2>/dev/null
	zip -r9v "$${HOME}/Library/Application Support/Sublime Text 3/Installed Packages/SublimeLinter-golangcilint.sublime-package" LICENSE.md linter.py messages messages.json README.md screenshot.png
