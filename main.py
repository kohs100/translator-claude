import os
import sys
import glob

from libtrans import TranslatorMD, TranslationResult, concat_translation_result
from libdoc import Document

from dotenv import load_dotenv

load_dotenv()

INIT_FRAGMENT_SIZE_LINE = 200
MODEL_NAME = "claude-sonnet-4-5-20250929"
TEMP_DIR = "./responses"
DO_THINK = False


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

        for i, r in enumerate(res):
            with open(f"{out_path}.{i}.ctx.md", "wt") as f:
                f.write(r.output.context)
            with open(f"{out_path}.{i}.trs.md", "wt") as f:
                f.write(r.output.translation)

        with open(out_path, "wt") as f:
            f.write(translation)

        results.extend(res)


def main():
    api_key = os.getenv("ANTHROPIC_API_KEY")
    assert api_key is not None, "Please provide valid anthropic api key!"

    series_name = sys.argv[1]
    path_docs = glob.glob(f"documents/{series_name}/*")
    path_docs.sort()

    max_num_lines = 0
    print("Document order:")
    for path in path_docs:
        doc = Document.from_file(path, False)
        num_lines = len(doc.lines)
        if max_num_lines < num_lines:
            max_num_lines = num_lines
        print(f"{path} - {num_lines} lines")
        del doc
    print(f"Max # of lines = {max_num_lines}")

    if max_num_lines < INIT_FRAGMENT_SIZE_LINE:
        print(f"Initial batch size can cover all documents. Good to go!")
    elif INIT_FRAGMENT_SIZE_LINE < 200:
        print("Consider using larger initial fragment size!")

    inp = input("Continue? (Yy)")
    if inp.lower() != "y":
        print("Exiting...")
        exit()

    if DO_THINK:
        output_dir = f"results/{series_name}_think"
    else:
        output_dir = f"results/{series_name}"

    os.makedirs(output_dir, exist_ok=True)
    path_output = [f"{output_dir}/{fname.rsplit("/")[-1]}" for fname in path_docs]

    translate_files(
        api_key,
        path_docs,
        path_output,
        think_budget=2048 if DO_THINK else 0,
    )


if __name__ == "__main__":
    main()
