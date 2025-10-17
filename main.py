import os
import sys
import glob

from libtrans import TranslatorMD, TranslationResult, concat_translation_result
from libdoc import Document

from dotenv import load_dotenv

load_dotenv()

INIT_FRAGMENT_SIZE_LINE = 200 # For testing purpose. 256-512 is recommended.
MODEL_NAME = "claude-sonnet-4-5-20250929"
TEMP_DIR = "./responses"

def translate_files(
    api_key: str, path_docs: list[str], path_output: list[str], think_budget: int
):
    assert len(path_docs) == len(path_output)

    translator = TranslatorMD(
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

    series_name = sys.argv[1]
    path_docs = glob.glob(f"documents/{series_name}/*")
    path_docs.sort()

    print("Document order:")
    for path in path_docs:
        print(path)
    input("Continue?")

    os.makedirs(f"results/{series_name}", exist_ok=True)
    path_output = [f"results/{series_name}/{fname.rsplit("/")[-1]}" for fname in path_docs]

    # os.makedirs(f"results/{series_name}_think", exist_ok=True)
    # path_output_think = [f"results/{series_name}_think/{fname.rsplit("/")[-1]}" for fname in path_docs]

    translate_files(
        api_key,
        path_docs,
        path_output,
        think_budget=0,
    )

    # translate_files(
    #     api_key,
    #     path_docs,
    #     path_output_think,
    #     think_budget=2048,
    # )


if __name__ == "__main__":
    main()
