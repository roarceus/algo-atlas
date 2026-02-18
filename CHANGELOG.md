# CHANGELOG

<!-- version list -->

## v1.4.0 (2026-02-18)

### Features

- Add Java language class with javac syntax checking
  ([`a4c0c69`](https://github.com/roarceus/algo-atlas/commit/a4c0c698cea0caf2b43d3314d155e80607b9e82c))

- Add Java method extraction and param counting with constructor skipping
  ([`fa47610`](https://github.com/roarceus/algo-atlas/commit/fa476105d3d54fd13398f6aeef3326a2fdcb406c))

- Implement Java test runner with javac compile and java execute
  ([`1be9fa9`](https://github.com/roarceus/algo-atlas/commit/1be9fa9ea32f96cc17717f1e3f3012ec4df8903a))

### Testing

- Add Java language support tests with fixtures and registry assertions
  ([`4fc4aa7`](https://github.com/roarceus/algo-atlas/commit/4fc4aa7ad267e6cbd75d89c3e9bef8c6b8cf4748))

- Fix test naming and data in test_java.py
  ([`5281c77`](https://github.com/roarceus/algo-atlas/commit/5281c77e738171c27d95ead6a599a90dd3283173))


## v1.3.0 (2026-02-16)

### Bug Fixes

- Remove unused imports from typescript.py
  ([`a124a14`](https://github.com/roarceus/algo-atlas/commit/a124a14346ef3b554b653c5219a09035fd535bdc))

### Features

- Add TypeScript language class with syntax checking
  ([`ed12b19`](https://github.com/roarceus/algo-atlas/commit/ed12b1930ec38b66afa9dd529639085cbe78999d))

- Add TypeScript method extraction and param counting Implement extract_method_name() and
  count_method_params() using regex patterns matching LeetCode TS signatures: function declarations,
  ([`d0e7594`](https://github.com/roarceus/algo-atlas/commit/d0e7594b81d7a2155bcefe5982d187c816589516))

- Implement TypeScript test runner via tsx subprocess
  ([`7e25bc1`](https://github.com/roarceus/algo-atlas/commit/7e25bc17dda5ba2aae6e40ae21c5163e47d03af1))

### Testing

- Add TypeScript language support tests Add 24 tests covering registry integration, metadata, syntax
  checking, method extraction, param counting, and test execution for TypeScript. Add TS fixtures to
  conftest.py and TS snippet to mock GraphQL response. Update registry and scraper test assertions.
  Total test count: 241.
  ([`f381273`](https://github.com/roarceus/algo-atlas/commit/f3812738680926f27bc831b9fd90c03b3db8412c))


## v1.2.0 (2026-02-13)

### Features

- Add JavaScript method extraction and param counting
  ([`ecc9366`](https://github.com/roarceus/algo-atlas/commit/ecc93669ecd6081f1b6456131a672d98eda06dd1))

- Add JavaScript syntax checker
  ([`21eee22`](https://github.com/roarceus/algo-atlas/commit/21eee226f0decbe206607e0381187c93abeac880))

- Implement JavaScript test runner via Node.js subprocess
  ([`0e4a3e5`](https://github.com/roarceus/algo-atlas/commit/0e4a3e5102ce97dd192c4a4f0d1db6093a57f20f))

### Testing

- Add JavaScript language support tests
  ([`f79ef64`](https://github.com/roarceus/algo-atlas/commit/f79ef64b0cc269c1baee56d414ee0fa1fbb0a561))


## v1.1.0 (2026-02-12)

### Bug Fixes

- Resolve flake8 lint errors
  ([`6fcc90d`](https://github.com/roarceus/algo-atlas/commit/6fcc90d34100b52c41e7140393db415dd22bf794))

### Features

- Add language parameter to verifier public API
  ([`48f85e0`](https://github.com/roarceus/algo-atlas/commit/48f85e08bb72c8cbc3dbc68ec4d6e16db002d058))

- Create languages/ package with base interface
  ([`a2c6a95`](https://github.com/roarceus/algo-atlas/commit/a2c6a953100fb1a98931c7aa436e72c02c682482))

- Make CLI and prompts language-aware
  ([`9e862aa`](https://github.com/roarceus/algo-atlas/commit/9e862aaafe189457fd8a07bf5c04c5ab34613da8))

- Make scraper language-aware
  ([`e387039`](https://github.com/roarceus/algo-atlas/commit/e3870399789d290fa8332188585891d89fb05d7d))

### Refactoring

- Migrate Python logic into languages/python.py
  ([`29e1dde`](https://github.com/roarceus/algo-atlas/commit/29e1dde0220a69d24b21c52dbfe02ca76d4c9c91))

### Testing

- Add tests for language support
  ([`b118790`](https://github.com/roarceus/algo-atlas/commit/b118790871839437b2fb4e7bc6d3d048254b70d6))


## v1.0.0 (2026-02-10)

- Initial Release
