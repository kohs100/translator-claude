import os

from libtrans import Translator, TranslationResult, concat_translation_result
from libdoc import Document

from dotenv import load_dotenv

load_dotenv()

INIT_FRAGMENT_SIZE_LINE = 100 # For testing purpose. 256-512 is recommended.
MODEL_NAME = "claude-sonnet-4-5-20250929"
TEMP_DIR = "./responses"

def translate_files(
    api_key: str, path_docs: list[str], path_output: list[str], think_budget: int
):
    assert len(path_docs) == len(path_output)

    translator = Translator(
        api_key, MODEL_NAME, INIT_FRAGMENT_SIZE_LINE, think_budget, TEMP_DIR
    )
    results: list[TranslationResult] = []

    for doc_path, out_path in zip(path_docs, path_output):
        print(f"Processing {doc_path}...")

        doc = Document.from_file(doc_path)
        res = translator.translate_paragraph(doc.as_paragraph(), results)
        translation = concat_translation_result(res)

        with open(out_path, "wt") as f:
            f.write(translation)

        results.extend(res)


def main():
    api_key = os.getenv("ANTHROPIC_API_KEY")
    assert api_key is not None, "Please provide valid anthropic api key!"

    path_docs = ["documents/ginga_tetsudo-1.txt", "documents/ginga_tetsudo-2.txt"]

    translate_files(
        api_key,
        path_docs,
        ["results/ginga_tetsudo-1.txt", "results/ginga_tetsudo-2.txt"],
        think_budget=0,
    )

    translate_files(
        api_key,
        path_docs,
        ["results/ginga_tetsudo-1-think.txt", "results/ginga_tetsudo-2-think.txt"],
        think_budget=2048,
    )


if __name__ == "__main__":
    main()
