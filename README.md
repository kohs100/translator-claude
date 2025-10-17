# Translator-claude
Fragment-based long document JP-to-KR translation.

## Features
* Fragment-based long document translation
* Context preserving translation between fragments
* Automatic fragment size shrinking based on [stop reason](https://docs.claude.com/ko/api/handling-stop-reasons)
* Cost-effective translation with [Messages Batches API](https://docs.claude.com/ko/docs/build-with-claude/batch-processing)

### Extended Thinking (ET)
* You can use advanced reasoning tokens by specifying think_budget over 1024
* Since the system prompt guides the model to output the contextual output ahead of the translation output, limited form of reasoning is already performed by the output structure itself. Consider using ET only if you are unsatisfied with translation quality.
  * In extended thinking mode, Anthropic API does not allow output prefill. Thus, using ET may increase output instability and occurrence of parsing error, especially in JSON mode.

### MD mode
`class TranslatorMD`
* Expected to be safe to use western-style quotation marks.
* Recommended.

### JSON mode
`class Translator`
* In this mode, model is guided to use japanese-style quotation mark (`「... 」` and `『... 』`).
  * This is primarily to alleviate the JSON output instability of Anthropic models.
  * The occurrence of JSON parsing error cannot be ignored if western-style quotation marks are included in the output.

## TODO
* On-demand context compression.

## Examples
### `.env` file
```
ANTHROPIC_API_KEY="sk-ant-api03-Pahk...3iAAA"
```
### How to run

* 銀河鉄道の夜 (은하철도의 밤)
  * https://www.aozora.gr.jp/cards/000081/files/456_15050.html
```
$ uv run main.py ginga_tetsudo
```
* 風の又三郎 (바람의 마타사부로)
   * https://www.aozora.gr.jp/cards/000081/card462.html
```
$ uv run main.py kazeno_matasaburo
```