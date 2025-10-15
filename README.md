# Translator-claude
Fragment-based long document JP-to-KR translation.

## Features
* Fragment-based long document translation
* Context preserving translation between fragments
* Automatic fragment size shrinking based on [stop reason](https://docs.claude.com/ko/api/handling-stop-reasons)
* Cost-effective translation with [Messages Batches API](https://docs.claude.com/ko/docs/build-with-claude/batch-processing)
* Use of japanese-style quotation mark (`「... 」` and `『... 』`).
  * This is primarily to alleviate the JSON output instability of Anthropic models.
  * The occurrence of JSON parsing error cannot be ignored if western-style quotation marks are included in the output.

## TODO
* On-demand context compression.
* Test of non-json output format to use western-style quotation marks.

## Examples
  ```
  $ uv run main.py
  ```
* 銀河鉄道の夜 (은하철도의 밤)
* https://www.aozora.gr.jp/cards/000081/files/456_15050.html