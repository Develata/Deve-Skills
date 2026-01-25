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

To use this skill, execute the python script with the file path.

**Required Environment Variables:**
*   `EXTRACTION_API_KEY`: API Key for LLM (e.g., OpenAI, DeepSeek).
*   `EXTRACTION_BASE_URL`: Base URL for LLM API (default: `https://api.openai.com/v1`).

**Optional Environment Variables:**
*   `MINERU_API_KEY`: Required only for PDF conversion.
*   `MINERU_BASE_URL`: Base URL for MinerU API (default: `https://api.mineru.com/v1`).
*   `LLM_MODEL`: Model name to use (default: `gpt-4o`).

```bash
python scripts/processor.py <file_path> <output_directory>
```

## Features

*   **Robust PDF Conversion**: Uses MinerU for high-quality PDF to Markdown conversion.
*   **Smart Chunking**: Splits text by paragraphs to avoid breaking math formulas.
*   **Cost Optimization**: Heuristically filters out non-math chunks to save tokens.
*   **Math Protection**: Whitelists safe HTML tags to prevent accidental deletion of math inequalities (e.g., `a < b`).
*   **Encoding Fallback**: Automatically tries UTF-8, GBK, and Latin-1 encodings.
*   **Retry Logic**: Built-in retries for API calls to handle network instability.
