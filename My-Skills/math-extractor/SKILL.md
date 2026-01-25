---
name: math-extractor
description: Extracts strictly mathematical terms (Definitions, Theorems, Lemmas, Propositions, Proofs) from documents (PDF, MD, TEX, TXT), handling PDF conversion and AI-based cleaning. Use when the user wants to extract math content from a file.
---

# Math Extractor

This skill extracts mathematical definitions, theorems, lemmas, propositions, and proofs from documents.

## Input Schema

```xml
<input_schema>
  <file_path>Path to the source file (pdf/md/tex/txt)</file_path>
</input_schema>
```

## Logic & Workflow

The Agent must follow this Chain of Thought (CoT):

1.  **Env Check**: First, verify that `scripts/processor.py` can access the necessary API keys (MinerU & LLM) from the environment. If missing, return a configuration error.
2.  **Validation**: Check file extension. If not .pdf/.md/.tex/.txt, return "不支持当前文件格式".
3.  **Conversion**:
    *   If PDF: Call `convert_pdf`. The script internally uses the pre-configured MinerU key.
    *   If conversion fails (or key missing), return "未设定好pdf转化为md的工具".
4.  **Preprocessing**:
    *   Call `clean_and_chunk` (implemented in `clean_content`).
    *   Aggressively remove images, TOCs, and References to save tokens.
5.  **Extraction (Batch AI)**:
    *   Call `batch_extract_math` (implemented in `batch_extract`).
    *   The script uses the pre-configured LLM credentials to process chunks in parallel.
6.  **Merge & Output**:
    *   Save to `{filename}_extracted.md` and return the path.

## Usage

To use this skill, execute the python script with the file path. The API keys must be set in the environment variables: `MINERU_API_KEY`, `EXTRACTION_API_KEY`, `EXTRACTION_BASE_URL`.

```bash
python scripts/processor.py <file_path> <output_directory>
```
