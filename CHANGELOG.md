# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Entries for releases before this file existed were generated from commit subjects.

## [2.0.3] - 2026-09-03

- Add FOC-TEMP/FOC-BLSH FITS headers; adopt FocuserHeaderMixin (#872)

## [2.0.2] - 2026-09-01

- Maintenance release (dependency and metadata updates only).

## [2.0.1] - 2026-08-28

- Select bundled EAF SDK library by target architecture

## [2.0.0] - 2026-08-26

- Require stable pyobs-core>=2.0.0
- Gate auto-merge on the PR author, not the event actor
- Enable Dependabot auto-merge for patch/minor updates
- Add cooperative-init construction test for EAFFocuser
- Convert EAFFocuser to cooperative super().__init__() chain
- Remove upper bound on Python version
- Add baseline test suite and CI (pytest, pyrefly), grouped Dependabot
- Upgrade uv.lock to clear open Dependabot alerts
- Require pyobs-core>=2.0.0.dev48
- Add dependabot.yml, targeting develop for PRs
- Run EAF SDK calls through a background thread instead of the event loop
- Add Sphinx documentation
- Remove DEVELOPMENT.md file from the repository
- Avoid sync during ruff check in workflow
- publish sdist only
- Both workflows now install libudev-dev before the build step, and the ruff workflow points to the correct package path.
- uv and ruff
- changed python version
- Update README with detailed installation, configuration, and usage instructions for ZWO EAF module
- Link EAF_focuser with udev dynamically using find_library
- Migrate to pyobs 2.0 API with tooling updates
- Add DEVELOPMENT.md outlining migration to pyobs 2.0 API
- fixed method name to correct name
- cleaned up code
- started cli
- clean up
- explain udev
- removed lib
- added files
- build works
- added file
- initial commit
