# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2] - 2025-03-06
### Added
 - Allow enqueuing objects by their ids in the Enqueue objects view
 - Allow setting CUSTOM_LOG_LEVELS for the flask app

### Changed
 - Change license to LGPLv3
 - Use get_redis_url from workflow for Redis connection
 - Simplify database fixtures in tests
 - Switch from setup.py to pyproject.toml for packaging

## [1.1] - 2020-08-04
### Added
 - Add autocompletion when entering freeze reasons.
 - Enqueue objects using a background RQ job to make the UI more responsive.
 - Add 'View latest SIP' button to 'Manage frozen objects' page.

## 1.0 - 2020-06-17
### Added
 - First release.

[1.1]: https://github.com/finnish-heritage-agency/passari-web-ui/compare/1.0...1.1
[1.2]: https://github.com/finnish-heritage-agency/passari-web-ui/compare/1.1...1.2
