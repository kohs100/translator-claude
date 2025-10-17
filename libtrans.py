from typing import List
from datetime import datetime
import json
import time
import os
from dataclasses import dataclass

import anthropic
from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
from anthropic.types.messages.batch_create_params import Request
from anthropic.types import MessageParam, ThinkingConfigParam

from libdoc import Paragraph
from pydantic import BaseModel

class ModelOutput(BaseModel):
    context: str
    translation: str

@dataclass
class TranslationResult:
    output: ModelOutput
    paragraph: Paragraph

def get_next_batch(batch_lines: int):
    assert batch_lines > 1
    new_sz = batch_lines // 2
    if batch_lines % 2 == 1:
        new_sz += 1
    return new_sz

def concat_translation_result(trs: list[TranslationResult]) -> str:
    doc = trs[0].paragraph.doc
    prev_tr: None | TranslationResult = None
    result_lines: list[str] = []

    for curr_tr in trs:
        assert curr_tr.paragraph.doc is doc
        if prev_tr is None:
            result_lines.append(curr_tr.output.translation)
        else:
            prev_lines = prev_tr.paragraph.lines
            curr_lines = curr_tr.paragraph.lines

            assert len(prev_lines) > 0
            assert len(curr_lines) > 0

            prev_ln = prev_lines[-1].linenum
            curr_ln = curr_lines[0].linenum

            if prev_tr.paragraph.eidx < curr_tr.paragraph.sidx:
                result_lines.append(
                    f"CONCATENATION ERROR: No translation exists in line {prev_ln} - {curr_ln}"
                )
            else:
                num_empty_lines = curr_ln - prev_ln
                assert num_empty_lines >= 0
                result_lines.extend("" for _ in range(num_empty_lines))
                result_lines.append(curr_tr.output.translation)
        prev_tr = curr_tr
    return "\n".join(result_lines)


class Translator:
    PROMPT_SYSTEM_PATH="system_prompt.md"
    PROMPT_DIRECTIVE = "**task**\nAccording to the given contextual information, translate the Japanese document into Korean."
    OUTPUT_PREFILL = '{\n  "context": "'

    def __init__(
        self,
        api_key: str,
        model_name: str,
        init_batch_size: int,
        think_budget: int,
        temp_dir: str | None = None,
    ):
        self.client = anthropic.Anthropic(api_key=api_key)
        assert (
            think_budget == 0 or think_budget >= 1024
        ), "Extended thinking budget must be above 1024."
        self.model_name = model_name
        self.think_budget = think_budget
        self.batch_size = init_batch_size
        self.temp_dir = temp_dir

        if temp_dir is not None:
            os.makedirs(temp_dir, exist_ok=True)

        with open(self.PROMPT_SYSTEM_PATH, "rt") as f:
            self.PROMPT_SYSTEM = f.read()

    def shrink_batch(self):
        assert self.batch_size > 1, "Cannot shrink batch size. Already 1"
        new_sz = self.batch_size // 2
        if self.batch_size % 2 == 1:
            new_sz += 1
        print(f"Shrinking batch size. {self.batch_size} -> {new_sz}")
        self.batch_size = new_sz

    @property
    def do_think(self) -> bool:
        assert (
            self.think_budget == 0 or self.think_budget >= 1024
        ), "Extended thinking budget must be above 1024."
        return self.think_budget >= 1024

    def parse_output(
        self,
        generation: str
    ) -> ModelOutput:
        return ModelOutput.model_validate_json(generation)

    def translate_paragraph(
        self,
        para: Paragraph,
        prev: List[TranslationResult],
    ) -> List[TranslationResult]:
        et = str(self.think_budget) if self.do_think else "X"
        print(
            f"Requested {para.sidx}-{para.eidx} / {len(para.doc.lines)}. ET Budget: {et}"
        )

        if self.batch_size < para.num_lines:
            results: List[TranslationResult] = []
            for p in para.split(self.batch_size):
                res = self.translate_paragraph(p, prev + results)
                results.extend(res)
            return results

        prev_context = "\n".join(p.output.context for p in prev)

        req_messages: List[MessageParam] = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": self.PROMPT_DIRECTIVE,
                    },
                    {
                        "type": "text",
                        "text": f"**context**\n{prev_context}",
                    },
                    {
                        "type": "text",
                        "text": f"**fragment**\n{para.as_multiline_text()}",
                    },
                ],
            },
        ]
        if self.do_think:
            req_thinking: ThinkingConfigParam = {
                "type": "enabled",
                "budget_tokens": self.think_budget,
            }
        else:
            req_thinking: ThinkingConfigParam = {"type": "disabled"}
            # Response prefill cannot be used in extended thinking mode
            req_messages.append(
                {
                    "role": "assistant",
                    "content": [{"type": "text", "text": self.OUTPUT_PREFILL}],
                }
            )
        batch_obj = self.client.messages.batches.create(
            requests=[
                Request(
                    custom_id="cid",
                    params=MessageCreateParamsNonStreaming(
                        model=self.model_name,
                        max_tokens=64000,
                        temperature=1,
                        system=self.PROMPT_SYSTEM,
                        messages=req_messages,
                        thinking=req_thinking,
                    ),
                )
            ]
        )

        batch_id = batch_obj.id
        state = batch_obj.processing_status

        print(f"Batch {batch_id} created.", end="")
        while state == "in_progress":
            time.sleep(5)
            batch_obj = self.client.messages.batches.retrieve(batch_id)
            state = batch_obj.processing_status
            print(".", end="", flush=True)
        print(f"\nBatch {batch_id} processing status is {state}")

        dt = datetime.now().strftime("%Y%m%d-%H%M%S")

        resp: anthropic.types.Message | None = None
        for res in self.client.messages.batches.results(batch_id):
            batchresult = res.result
            match batchresult.type:
                case "succeeded":
                    resp = batchresult.message
                case "errored":
                    raise ValueError(f"Error: {batchresult.error}")
                case "expired":
                    raise ValueError(f"Request expired {res.custom_id}")
                case "canceled":
                    raise ValueError(f"Request canceled")

        assert resp is not None, "No successful message found!!"
        if self.temp_dir is not None:
            with open(f"{self.temp_dir}/{dt}.json", "wt") as f:
                json.dump(resp.model_dump(), f, ensure_ascii=False, indent=2)

        if resp.stop_reason is None:
            raise ValueError("stop reason is none.")

        if resp.stop_reason == "max_tokens":
            print(f"Reached max token!")
            self.shrink_batch()
            return self.translate_paragraph(para, prev)
        elif resp.stop_reason == "refusal":
            print(f"Initiating refusal fallback. Temporarily shrinking batch size...")
            old_batch_size = self.batch_size
            self.shrink_batch()
            gens = self.translate_paragraph(para, prev)
            self.batch_size = old_batch_size
            return gens
        elif resp.stop_reason != "end_turn":
            raise ValueError(
                f"Model terminated with unexpected reason: {resp.stop_reason}"
            )

        if len(resp.content) == 0:
            raise ValueError("Empty response returned!!")

        result: None | str = None
        think_result: None | str = None
        for cnt in resp.content:
            if cnt.type == "text":
                if result is None:
                    result = cnt.text
                else:
                    raise ValueError("Multiple text content!!")
            if cnt.type == "thinking":
                think_result = cnt.thinking
            elif cnt.type == "redacted_thinking":
                think_result = "REDACTED"

        assert result is not None, "Text content is not found!!"
        result = result.strip()

        if self.do_think:
            # Response prefill cannot be used in extended thinking mode
            assert think_result is not None
            if result.startswith("```json") and result.endswith("```"):
                print("Think result is wrapped with codeblock!! (```json)")
                result = result[7:-3]
            elif result.startswith("```") and result.endswith("```"):
                print("Think result is wrapped with codeblock!! (```)")
                result = result[3:-3]
            gen = self.parse_output(result)
        else:
            assert think_result is None
            gen = self.parse_output(self.OUTPUT_PREFILL + result)

        return [TranslationResult(gen, para)]

class TranslatorMD(Translator):
    PROMPT_SYSTEM_PATH="system_prompt_2.md"
    OUTPUT_PREFILL = "## Context"

    def parse_output(self, generation: str) -> ModelOutput:
        generation = generation.strip()
        assert generation.lower().startswith(self.OUTPUT_PREFILL.lower())

        trs_head = "## Translation\n"

        ctx_start = len(self.OUTPUT_PREFILL)
        ctx_end = generation.lower().find(trs_head.lower())
        trs_start = ctx_end + len(trs_head)

        ctx = generation[ctx_start:ctx_end].strip()
        trs = generation[trs_start:].strip()

        return ModelOutput(context=ctx, translation=trs)