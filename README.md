# SublimeLinter-golangcilint [![Build Status](https://travis-ci.org/SublimeLinter/SublimeLinter-golangcilint.png?branch=master)](https://travis-ci.org/SublimeLinter/SublimeLinter-golangcilint)

This linter plugin for [SublimeLinter](https://github.com/SublimeLinter/SublimeLinter) provides an interface to [golangci-lint](https://github.com/golangci/golangci-lint).

It will be used with files that have the "Go" syntax.

**Note:** This project was originally inspired by a [similar package](https://github.com/alecthomas/SublimeLinter-contrib-golang-cilint) that unfortunately doesn’t takes in consideration a bug in golangci-lint that sends some errors to `/dev/stderr` rather than `/dev/stdout` causing the linter to fail or miss some important issues. I have fixed this in this version, and also added better error handling for unrelated files.

## Installation

SublimeLinter must be installed in order to use this plugin. Then use [Package Control](https://packagecontrol.io/) to install the linter plugin. Please make sure that the path to `golangci-lint` is available to SublimeLinter. To install, follow the instructions provided by [here](https://github.com/golangci/golangci-lint#install).


## Settings

- SublimeLinter settings: http://sublimelinter.com/en/latest/settings.html
- Linter settings: http://sublimelinter.com/en/latest/linter_settings.html
