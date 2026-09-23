# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Status

The repository is currently a bare scaffold: only `README.md`, `LICENSE` (MIT), and a `.gitignore`.
There is no source code, dependency manifest, build system, or test suite yet.

## Product intent

DbFAQ stores routine SQL queries as "FAQs" (Frequently Asked Queries) so they can be re-run
against a database on demand. Any design work should stay anchored to that: saved query
definitions, a target database connection, and repeated execution of those saved queries.

## Stack

Python is the intended language — `.gitignore` is GitHub's Python template, and nothing else is
present. The specific tooling (package manager, framework, DB driver, test runner) has not been
chosen. When the first real code lands, replace this section with the actual build/lint/test
commands, including how to run a single test, and document the architecture once it spans more
than one file.
