# CHANGELOG

<!-- version list -->

## v1.13.0 (2026-03-08)

### Code Style

- Apply black and isort formatting
  ([`b1c55b9`](https://github.com/roarceus/algo-atlas/commit/b1c55b9c444922f24296eaa51084f26900887796))

### Features

- **php**: Add PHPLanguage skeleton with php -l syntax checker
  ([`e644138`](https://github.com/roarceus/algo-atlas/commit/e644138fca5128f61e9a0976c120f8016c2bac80))

- **php**: Implement extract_method_name and count_method_params
  ([`95e5c12`](https://github.com/roarceus/algo-atlas/commit/95e5c121d3003264c244116a58c929d6e03dd676))

- **php**: Implement run_test_case with php interpreter harness
  ([`54806f1`](https://github.com/roarceus/algo-atlas/commit/54806f18ef920c6c365864253f10161fdb915ff4))

### Testing

- **php**: Add test suite, fixtures, registry/scraper coverage, and README update
  ([`71beac6`](https://github.com/roarceus/algo-atlas/commit/71beac63505659261bdf1646bbe788031dc75752))


## v1.12.0 (2026-03-06)

### Code Style

- Apply black and isort formatting
  ([`c968fd6`](https://github.com/roarceus/algo-atlas/commit/c968fd6655e09a28abba5b5dad426d23acf63c1d))

### Features

- **ruby**: Add RubyLanguage skeleton with ruby -c syntax checker
  ([`b943748`](https://github.com/roarceus/algo-atlas/commit/b943748bf9ad9e7237897cd227278b3af0982cf7))

- **ruby**: Implement extract_method_name and count_method_params
  ([`7acbe58`](https://github.com/roarceus/algo-atlas/commit/7acbe585a16c329d79864b9cc7c1efb542c8503b))

- **ruby**: Implement run_test_case with ruby interpreter harness
  ([`3a3f614`](https://github.com/roarceus/algo-atlas/commit/3a3f6144e9c9dfe0868f6370728f95710f95679b))

### Testing

- **ruby**: Add test suite, fixtures, registry/scraper coverage, and README update
  ([`288a9f1`](https://github.com/roarceus/algo-atlas/commit/288a9f1dd415a721e230dcc16a21005fcd5478ed))


## v1.11.0 (2026-03-04)

### Bug Fixes

- **swift**: Remove bare f-string and apply black formatting
  ([`2dc059f`](https://github.com/roarceus/algo-atlas/commit/2dc059fe4ef3d3bafbac9c8ea65a774d730bad01))

- **swift**: Rename Main.swift to main.swift for top-level entry point
  ([`e30fcf5`](https://github.com/roarceus/algo-atlas/commit/e30fcf54b97b433c0838b5b0f6e63969163bd901))

### Code Style

- Apply black and isort formatting
  ([`57a589e`](https://github.com/roarceus/algo-atlas/commit/57a589eb81ff2411a083a1d7065c00f6910b9f05))

### Features

- **swift**: Add SwiftLanguage skeleton with swiftc syntax checker
  ([`75f8f37`](https://github.com/roarceus/algo-atlas/commit/75f8f37c640a72b9224b7a264e3a299c08b05ac5))

- **swift**: Implement extract_method_name and count_method_params
  ([`626c6c5`](https://github.com/roarceus/algo-atlas/commit/626c6c5ad2a82f89547d0b10c1d6feb853bdf12c))

- **swift**: Implement run_test_case with swiftc compile-and-run harness
  ([`1702b85`](https://github.com/roarceus/algo-atlas/commit/1702b857007736138e02c97c6ec26245dd894702))

### Testing

- **swift**: Add test suite, fixtures, registry/scraper coverage, and README update
  ([`3874a2c`](https://github.com/roarceus/algo-atlas/commit/3874a2c08fc92bdcc7c4cb0670a414c81b9c95c0))


## v1.10.0 (2026-03-02)

### Bug Fixes

- **ci**: Use fwilhe2/setup-kotlin@v1 (v2 does not exist)
  ([`d9a0c54`](https://github.com/roarceus/algo-atlas/commit/d9a0c5406a196decf4f758abbe647589dd54e1a9))

- **kotlin**: Move run_test_case stub back inside KotlinLanguage class
  ([`a41508c`](https://github.com/roarceus/algo-atlas/commit/a41508c5f1195aff8a77d979e019435faeee17d5))

### Code Style

- Apply black formatting to all source and test files
  ([`e1d52d5`](https://github.com/roarceus/algo-atlas/commit/e1d52d5bba34741db318b9eb6235b3925c7be0e1))

### Features

- **kotlin**: Add KotlinLanguage skeleton with kotlinc syntax checker
  ([`5e6bff7`](https://github.com/roarceus/algo-atlas/commit/5e6bff75894a861eb84af3cbed802b976b0b0e02))

- **kotlin**: Implement extract_method_name and count_method_params
  ([`7433f47`](https://github.com/roarceus/algo-atlas/commit/7433f47a57b9d205ab5f7250e0bc67e61ba73dd2))

- **kotlin**: Implement run_test_case with kotlinc compile-and-run harness
  ([`a233aeb`](https://github.com/roarceus/algo-atlas/commit/a233aeb3ffbad92944358c1d7b73fd4204916ae6))

### Testing

- **kotlin**: Add test suite, fixtures, registry/scraper coverage, and README update
  ([`9926441`](https://github.com/roarceus/algo-atlas/commit/9926441f282090d0c3ff555dd200696407a6f234))


## v1.9.0 (2026-02-28)

### Bug Fixes

- **csharp**: Add using System to Program.cs harness for Console access
  ([`a71a8d3`](https://github.com/roarceus/algo-atlas/commit/a71a8d3cc86b9e66f9ca408e8839c0d9fd8f070f))

- **csharp**: Target net8.0 to match available runtime on CI
  ([`aa8a5a7`](https://github.com/roarceus/algo-atlas/commit/aa8a5a72ff20be13f62588e1a69a64a373e51094))

### Documentation

- Add supported languages table to README
  ([`2122cc7`](https://github.com/roarceus/algo-atlas/commit/2122cc7835b6e8722d1dafdffb41515028e30f23))

- Update prerequisites, vault structure, and language list in README
  ([`7e6751e`](https://github.com/roarceus/algo-atlas/commit/7e6751e81feb4155f4b272130903ee9c806627d0))

### Features

- **csharp**: Add CSharpLanguage with dotnet build syntax checker and register
  ([`e336136`](https://github.com/roarceus/algo-atlas/commit/e3361363bb3bf348eff6c1071f7946c4c253f71b))

- **csharp**: Implement extract_method_name and count_method_params with regex
  ([`3042a81`](https://github.com/roarceus/algo-atlas/commit/3042a81169066d0520b8c318fed2664f5fbbab47))

- **csharp**: Implement run_test_case with dotnet compile-and-run harness
  ([`1836cd6`](https://github.com/roarceus/algo-atlas/commit/1836cd60d845e693d8c8160e7df99df76e923b0b))

### Testing

- **csharp**: Add test suite, fixtures, and registry/scraper coverage
  ([`1db3f24`](https://github.com/roarceus/algo-atlas/commit/1db3f241f9705da556be01ea88950c812e29c22e))


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
