# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### New
- The package carries the release version in its check plugin (`__version__`).

### Changed
- Licence is now GNU General Public License v2, matching the headers
  the source files carry. The `LICENSE` file previously held the MIT
  text, which contradicted them.

### Fixed
- One unreadable line from the alarm collector no longer crashes every
  "ISAM Alarm State" service of the host; that line is skipped. An alarm
  with a status other than 0 to 3 shows UNKNOWN with "Collector sent
  unknown alarm status".

## 0.1.0 - 2026-03-04
### New
- Initial migration from oegig-plugins to Checkmk 2.3.x v2 API
- Special agent fetches alarm data from collector web service via HTTP GET
- Check plugin discovers and monitors per-service alarm states
- MKP packaging via oposs/mkp-builder GitHub Action


