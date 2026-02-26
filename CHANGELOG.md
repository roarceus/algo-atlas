# CHANGELOG

<!-- version list -->

## v1.8.0 (2026-02-26)

### Bug Fixes

- **rust**: Add two spaces before inline comment to satisfy E261
  ([`bd16db6`](https://github.com/roarceus/algo-atlas/commit/bd16db6186d3eb91a57c180f8d4469498326bc86))

### Features

- **rust**: Add RustLanguage with rustc syntax checker and register
  ([`c01bf00`](https://github.com/roarceus/algo-atlas/commit/c01bf00157187bd0f4d83a4763480ca572307155))

- **rust**: Implement extract_method_name and count_method_params with regex
  ([`41d4ee9`](https://github.com/roarceus/algo-atlas/commit/41d4ee93385a521ad89d9d03cfba9425aded3819))

- **rust**: Implement run_test_case with rustc compile-and-run harness
  ([`c751b00`](https://github.com/roarceus/algo-atlas/commit/c751b00bdc07710162268a76b7f18cb9b9db084f))

### Testing

- **rust**: Add 24 tests for RustLanguage across 6 classes
  ([`dc1c7d9`](https://github.com/roarceus/algo-atlas/commit/dc1c7d9ee75aca98a0351a36a6a7625711492585))


## v1.7.0 (2026-02-24)

### Bug Fixes

- **go**: Compile with go build before running to avoid execution timeout
  ([`bba0fae`](https://github.com/roarceus/algo-atlas/commit/bba0fae8d5214f4e3bf2f762f6878a59794de7cf))

### Features

- **go**: Add GoLanguage with go build syntax checker and register
  ([`1356bba`](https://github.com/roarceus/algo-atlas/commit/1356bbaf7d75f4dd25c8791550481e7e0687d22f))

- **go**: Implement extract_method_name and count_method_params with regex
  ([`843a1a2`](https://github.com/roarceus/algo-atlas/commit/843a1a2bfb83eac582ef419335ea19dcf541761c))

- **go**: Implement run_test_case with go run harness and json.Marshal output
  ([`b03fc81`](https://github.com/roarceus/algo-atlas/commit/b03fc817dd0cc0be782b497f5165c2eaf8efc7ae))

### Testing

- **go**: Add 24 tests for GoLanguage across 6 classes
  ([`f67ed8e`](https://github.com/roarceus/algo-atlas/commit/f67ed8e436bb6cdd3f8968ffddd62216ccc07a49))


## v1.6.0 (2026-02-22)

### Bug Fixes

- **test**: Update code_snippets_raw count to 6 after adding C snippet
  ([`a3a1013`](https://github.com/roarceus/algo-atlas/commit/a3a1013095cf613b9257ec70e1454cd78be86d5c))

### Continuous Integration

- Gate release on CI workflow passing lint and test
  ([`09186e3`](https://github.com/roarceus/algo-atlas/commit/09186e3df2d8e16ef54306292c28fd13fbd3f20c))

### Features

- **c**: Add CLanguage class with gcc syntax checker
  ([`4c76a7b`](https://github.com/roarceus/algo-atlas/commit/4c76a7b68e58464bffece314db22bef120ecf12b))

- **c**: Implement extract_method_name and count_method_params
  ([`527b5d7`](https://github.com/roarceus/algo-atlas/commit/527b5d7447482f89d804691da8a098adb3c8d1e9))

- **c**: Implement run_test_case with gcc compile-and-run harness
  ([`75d1d2e`](https://github.com/roarceus/algo-atlas/commit/75d1d2e416550d6069e82c9778c06c02867c66c6))

### Testing

- **c**: Add 24 tests for CLanguage across 6 classes
  ([`ef540ea`](https://github.com/roarceus/algo-atlas/commit/ef540eaa56be406f54c0b4e4e3b97754135feab3))


## v1.5.0 (2026-02-20)

### Bug Fixes

- **cpp**: Add iostream include and use named arg vars to fix ref binding
  ([`205cb6a`](https://github.com/roarceus/algo-atlas/commit/205cb6add7fb309cc1bfed24724a2a7341daf3a5))

- **cpp**: Use verifier.execution_timeout from settings
  ([`1a9307d`](https://github.com/roarceus/algo-atlas/commit/1a9307d5d52e3bbedb4d9a8ede54d790c51dd2d5))

### Features

- **cpp**: Add CppLanguage class with g++ syntax checker
  ([`6e32e73`](https://github.com/roarceus/algo-atlas/commit/6e32e736d078288142697d819cc332e3e182c168))

- **cpp**: Implement extract_method_name and count_method_params
  ([`fcbce50`](https://github.com/roarceus/algo-atlas/commit/fcbce5040cf4ee3046530fd66b7b933f62f2c6b0))

- **cpp**: Implement run_test_case with g++ compile-and-run harness
  ([`54d0aa1`](https://github.com/roarceus/algo-atlas/commit/54d0aa1916d58fe3ecae5258a9fd025cb96c2fe1))

### Testing

- **cpp**: Add CppLanguage tests and update shared fixtures
  ([`aca3052`](https://github.com/roarceus/algo-atlas/commit/aca30521d94f60ab7a22be44296648f36dce593a))


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
