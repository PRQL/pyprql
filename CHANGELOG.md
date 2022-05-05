# Changelog

<!--next-version-placeholder-->

## v0.4.3 (2022-05-05)
### Fix
* ***:** Merge 42 ([`6cca7e2`](https://github.com/prql/PyPrql/commit/6cca7e21747f785172ce37e51875c7317765a3f1))

### Documentation
* **docs:** Correct file links ([`6eb1910`](https://github.com/prql/PyPrql/commit/6eb19103c0b4cf6bf524c8378608c8e3cba55e0e))
* **README.md:** Add CodeCov coverage ([`93f1009`](https://github.com/prql/PyPrql/commit/93f1009ec9d7bf8e6992da5b935d5df0e4ddf006))

## v0.4.2 (2022-04-16)
### Fix
*  Fixes enforce typing breaking on subscripted generics by forking and providing a flag to ignore this non-error. ([`cb19cbc`](https://github.com/prql/PyPrql/commit/cb19cbc81275b291856818fd5689881007d5ee3c))

### Documentation
* **index.md:** Add docs badge to docs ([`3029853`](https://github.com/prql/PyPrql/commit/3029853a76dfc0952e2e2904e6ffede3019c3726))
* **README.md:** Add ReadTheDocs ([`4d5404c`](https://github.com/prql/PyPrql/commit/4d5404c6c5a34375bcb8a8472f9d18265024f471))
* **docs:** Add tests to the sphinx build ([`049ff35`](https://github.com/prql/PyPrql/commit/049ff353e37b180201228c45411713ef73f78761))
* **tests:** Document tests ([`950e55d`](https://github.com/prql/PyPrql/commit/950e55dbaef0579b7e72664d51de0cea50b7ef6b))
* **README.md:** Add badges ([`c176d65`](https://github.com/prql/PyPrql/commit/c176d65e22f091f8ac6db7a03a2a0745a7f37139))
* ***:** Correct urls ([`0622add`](https://github.com/prql/PyPrql/commit/0622add58fdb0dcf271102ac69f4a6dc71eb2ff5))
* **README.md:** Get those badges ([`2547540`](https://github.com/prql/PyPrql/commit/2547540aee2108b6c326e219e1a21bed35ca2a8d))
* **LICENSE:** Add license ([`7119bec`](https://github.com/prql/PyPrql/commit/7119bec4a80a1f4b11c4134bf034d5dcf8dbca41))
* **docs:** Add Sphinx support ([`f966f34`](https://github.com/prql/PyPrql/commit/f966f349d6c81f31f8abd87f929addb4b73d2e81))
* ***:** Provide docstrings throughout ([`c1b7b6d`](https://github.com/prql/PyPrql/commit/c1b7b6dc18db481f8c678cf09811afa3a25d9988))

## v0.4.1 (2022-04-14)
### Fix
*  Fixes #27 ([`b666dd0`](https://github.com/qorrect/PyPrql/commit/b666dd03135bb209431575f5d1481e29299576cd))

## v0.4.0 (2022-04-11)
### Feature
* **cli.py:** Support reading from tsvs ([`d2d675b`](https://github.com/prql/PyPrql/commit/d2d675b7f398f8b32b27117cff1d2305ee85a811))
* ***:** Support saving to tsv ([`5a2630f`](https://github.com/prql/PyPrql/commit/5a2630f7314b0a2ad04333b745d870f39d083486))
* **cli.py:** Support cli saving to csv ([`79382c1`](https://github.com/prql/PyPrql/commit/79382c1aef6bd0e9c7f1e4686fde84b1e11b5f6d))
* **prql.py:** Parse to statements ([`2808f26`](https://github.com/prql/PyPrql/commit/2808f26fb13b82d3800b6e0e92f3a12733291b9e))
* **prql.py:** Adds grammar for to ([`3899c89`](https://github.com/prql/PyPrql/commit/3899c89fcd6dc735a2fe6a09fd488bfff0a0fb4b))
* **cli.py:** Import csv ([`c847eb2`](https://github.com/prql/PyPrql/commit/c847eb269b0f48889e5b625b97377283a54b1bd1))
* Adding expression parsing for complex expressions without requiring '()' ([`855ebd0`](https://github.com/prql/PyPrql/commit/855ebd0166e06f9d1e288c63b7e529f73e105e61))
* Adding completion for show columns and \d+ ([`7b7f676`](https://github.com/prql/PyPrql/commit/7b7f6768a4519de7ac8fbdc8458b57fe35b8baf7))
*  Adding code completion on table names for ':', fixes the handling of prev_selection by clearing out on whitespace ([`46f7676`](https://github.com/prql/PyPrql/commit/46f7676af190d1e5d008cc9f283628a2a47304f2))

### Fix
* **prql.lark:** Match file names directly ([`259763b`](https://github.com/prql/PyPrql/commit/259763b877f9e4385c60f3a986961b9a533892df))
* **prql.lark:** Support extensions for to statement ([`82325a6`](https://github.com/prql/PyPrql/commit/82325a66c5d5d73e8382011fe2ca681f24914aa6))
* **prql.parl:** Add filename parameter ([`f567cd6`](https://github.com/prql/PyPrql/commit/f567cd6b0a8e2e58488ef392e3d212159ab76f2a))
* Closes #20, All derives should now be in where clause ([`c736b25`](https://github.com/prql/PyPrql/commit/c736b25b97a3fc7b3a2f873df6860139626b38d2))
* Closes #21, replace_tables now available to all to_sql transformations ([`eb12075`](https://github.com/prql/PyPrql/commit/eb1207595af4f86df9496c1c7d441b5ab4f8b566))
* Final commit for fix11 ([`421fb04`](https://github.com/prql/PyPrql/commit/421fb044b687a63547c45562193ad18c4940145e))
*  Fix11 , use the AST in the completer.  This adds support for table aliases when completing fields. ([`9e79119`](https://github.com/prql/PyPrql/commit/9e79119b0fd308ab5928f50e447e4623a9ed18c2))
* Fixes #10 typing a letter afer period was not auto completing ([`ee8c7f5`](https://github.com/prql/PyPrql/commit/ee8c7f57bd84e0b535441b546a96949f57280ecb))

### Documentation
* **cli.py:** Document connect_str properly ([`95e568d`](https://github.com/prql/PyPrql/commit/95e568d6ba4bd581ba276290cc4dd10dff9a87f4))
* Adding more prql examples ([`2e5149e`](https://github.com/prql/PyPrql/commit/2e5149e36d167bb16d82de30676941b7c3f519a4))
* Adding prql examples ([`8ae2070`](https://github.com/prql/PyPrql/commit/8ae2070a6d07c51c5df201de4a73a7435942478f))

## v0.3.0 (2022-04-01)
### Feature
* **prql.lark:** Add join aliases ([`94a405e`](https://github.com/prql/PyPrql/commit/94a405ee44632f378476645c4303e08e91a275ef))

## v0.2.5 (2022-03-29)
### Fix
* **cli.py:** Remove sql print ([`fdf639e`](https://github.com/prql/PyPrql/commit/fdf639e65e8522c57ea1c9400bd1c41de78833ac))
* **cli.py:** Match exit to [""] ([`aa40c42`](https://github.com/prql/PyPrql/commit/aa40c421c99ad52ee798294f1c5ebe4059352575))
* **cli.py:** Match exit to empty list ([`f8c04a3`](https://github.com/prql/PyPrql/commit/f8c04a359190009d2aa121e13a3d4261aee5b7cc))

## v0.2.4 (2022-03-29)
### Fix
* **cli.py:** Check for sqlalchemy error ([`fe2c804`](https://github.com/prql/PyPrql/commit/fe2c804470139699a3708a286167ba1c297b0aaa))
* **cli.py:** Increase default limit ([`b5e7be4`](https://github.com/prql/PyPrql/commit/b5e7be4b574e476495367dd5af26df3633d47b38))
* **cli.py:** Append limit to select only ([`66f1d57`](https://github.com/prql/PyPrql/commit/66f1d57cdd3e69141383f712a2ae71c1eb34a2ec))

### Documentation
* **prql.py:** Add annotations ([`a03b653`](https://github.com/prql/PyPrql/commit/a03b653590a8fd4daef26f9ae26f718498ccf75a))
* **cli.py:** Correct docstrings ([`ee2a5f2`](https://github.com/prql/PyPrql/commit/ee2a5f2eeee8c8ce8b5e8cdc3aad8022c591527a))
* ***:** Add module level docstings ([`a9d30de`](https://github.com/prql/PyPrql/commit/a9d30de78450f24953b4e27b16532a6baa5a777f))

## v0.2.3 (2022-03-21)
### Fix
* Fixes examples command in the cli ([`30d2b2f`](https://github.com/prql/PyPrql/commit/30d2b2f27e4bf64d59d64f8f4fa566a2c8111e6b))

## v0.2.2 (2022-03-21)
### Fix
* Fixes inline documentation and bottom toolbar of CLI ([`b5d32d5`](https://github.com/prql/PyPrql/commit/b5d32d5f0bccb131e090b63617844666e646ff6c))

## v0.2.1 (2022-03-21)
### Fix
* Changing cli name to pyprql to prevent name collision with prql proper - fixing lint ([`22fd6bd`](https://github.com/prql/PyPrql/commit/22fd6bdcc22a647cc5b10533620b74fd03cd74cf))
* Changing cli name to pyprql to prevent name collision with prql proper ([`8125fff`](https://github.com/prql/PyPrql/commit/8125fff32bf1c351ca64825bed763f83fa88b639))

### Documentation
* Updating README ([`b84e771`](https://github.com/prql/PyPrql/commit/b84e771d242d91ef42f25492420c5bc08aef124b))

## v0.2.0 (2022-03-20)
### Feature
* Restructuring for redistribution ([`29b75bf`](https://github.com/prql/PyPrql/commit/29b75bf6f38adb213e4b4443672dee3dea15f388))

### Fix
* Fixing imports ([`1031cce`](https://github.com/prql/PyPrql/commit/1031cce38abdf704aec63a637ccadccd1429c670))
* Clean-up for redistribution ([`e8080d4`](https://github.com/prql/PyPrql/commit/e8080d4bf8b39a2a043820a8d8f58f2070b03fd0))
* Fixing imports for redistribution ([`896234a`](https://github.com/prql/PyPrql/commit/896234a288e22e922d9b89d368ed76b51ec13762))

## v0.1.2 (2022-03-20)
### Documentation
* **cli.py:** Add docstrings throughout ([`fd28c49`](https://github.com/prql/PyPrql/commit/fd28c49f71a88b34ddac478f929142a1a33446cc))
* **pyprql:** Add module-level docstrings ([`a018801`](https://github.com/prql/PyPrql/commit/a018801b0ae35d6300d3c8b444bb88e619504b97))

### Performance
* **prql.lark:** Grammar cleanup ([`c25980a`](https://github.com/prql/PyPrql/commit/c25980a420d1c117a7d3a4456fffffdccc8b0038))

## v0.1.1 (2022-03-15)
### Fix
* **pyproject.toml:** Change release booleans ([`e668700`](https://github.com/prql/PyPrql/commit/e6687007e34529b0b337ca38047b84c239b157bc))

## v0.1.0 (2022-03-15)
### Feature
* **cli.py:** Add code for entrypoint ([`1802938`](https://github.com/prql/PyPrql/commit/1802938055cc6dea4167dfa60ef51d934086dfa3))
