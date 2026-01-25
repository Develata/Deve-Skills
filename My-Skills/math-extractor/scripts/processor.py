import os
import re
import json
import concurrent.futures
import requests
import logging
import argparse
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global Configuration
CONFIG = {
    'MINERU_API_KEY': os.getenv('MINERU_API_KEY', ''),
    'EXTRACTION_API_KEY': os.getenv('EXTRACTION_API_KEY', ''),
    'EXTRACTION_BASE_URL': os.getenv('EXTRACTION_BASE_URL', 'https://api.openai.com/v1'),
    'MINERU_BASE_URL': os.getenv('MINERU_BASE_URL', 'https://api.mineru.com/v1'), # Placeholder URL
    'LLM_MODEL': os.getenv('LLM_MODEL', 'gpt-4o')
}

class MathProcessor:
    def __init__(self):
        self._validate_config()

    def _validate_config(self):
        # 必须检查提取用的 API Key
        if not CONFIG['EXTRACTION_API_KEY']:
             logger.error("Configuration Error: 'EXTRACTION_API_KEY' environment variable is missing.")
             raise ValueError("Configuration Error: 'EXTRACTION_API_KEY' environment variable is missing.")
        
        # 警告：如果没有 PDF key，只能处理文本
        if not CONFIG['MINERU_API_KEY']:
            logger.warning("'MINERU_API_KEY' is missing. PDF conversion will fail.")

    def clean_content(self, text):
        """
        Regex cleaning for images/figures/HTML.
        Must remove "References"/"Bibliography" sections.
        """
        # Remove References/Bibliography section (from the header to the end)
        # Matches "References" or "Bibliography" on a line by itself (or with minimal whitespace)
        text = re.sub(r'(?im)^\s*(References|Bibliography)\s*$.*', '', text, flags=re.DOTALL)
        
        # Remove images/figures (markdown style ![...](...))
        text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
        
        # Remove HTML tags - Use whitelist to protect math inequalities
        # Only remove specific, unsafe tags
        tags_to_remove = r'(script|style|div|span|p|br|iframe|video|img)'
        text = re.sub(r'<' + tags_to_remove + r'[^>]*>', '', text, flags=re.IGNORECASE)
        text = re.sub(r'</' + tags_to_remove + r'>', '', text, flags=re.IGNORECASE)
        
        # Remove TOC (heuristics: lines with multiple dots ...... and numbers at end)
        text = re.sub(r'(?m)^.*\.{4,}\s*\d+\s*$', '', text)
        
        return text.strip()

    def convert_pdf_to_md(self, file_path):
        """
        Uses CONFIG['MINERU_API_KEY'] to convert PDF to Markdown.
        """
        if not CONFIG['MINERU_API_KEY']:
            raise ValueError("未设定好pdf转化为md的工具 (Missing MINERU_API_KEY)")

        url = f"{CONFIG['MINERU_BASE_URL']}/pdf_to_markdown" # Hypothetical endpoint
        headers = {'Authorization': f"Bearer {CONFIG['MINERU_API_KEY']}"}
        
        try:
            logger.info(f"Converting PDF: {file_path}")
            with open(file_path, 'rb') as f:
                files = {'file': f}
                # [ACTION REQUIRED] 取消注释以下几行以启用真实转换
                response = requests.post(url, headers=headers, files=files, timeout=120) # 2 min timeout for PDF
                response.raise_for_status()
                # 假设 MinerU 返回格式是 {'markdown': '...'}，根据实际 API 调整
                return response.json().get('markdown', '')
        except requests.exceptions.RequestException as e:
             # Return error message to be displayed to user
             error_msg = f"PDF conversion error: {str(e)}. Please check MINERU_BASE_URL and MINERU_API_KEY."
             logger.error(error_msg)
             return error_msg
        except Exception as e:
            logger.error(f"PDF conversion failed: {str(e)}")
            raise RuntimeError(f"PDF conversion failed: {str(e)}")

    def batch_extract(self, chunks):
        """
        Uses CONFIG['EXTRACTION_API_KEY'] and CONFIG['EXTRACTION_BASE_URL'].
        Implements concurrent.futures.ThreadPoolExecutor for speed.
        """
        if not CONFIG['EXTRACTION_API_KEY']:
            raise ValueError("Missing EXTRACTION_API_KEY")

        # Heuristic filtering to save tokens
        MATH_KEYWORDS = {
            "theorem", "definition", "lemma", "proof", "proposition", 
            "定理", "定义", "命题", "let", "assume", "suppose", "=", "\\", 
            "corollary", "推论", "example", "例"
        }

        results = [""] * len(chunks)
        chunks_to_process = []
        
        for i, chunk in enumerate(chunks):
            # Check if chunk contains any math keywords
            if any(k in chunk.lower() for k in MATH_KEYWORDS):
                chunks_to_process.append((i, chunk))
            else:
                # Skip non-math chunks
                results[i] = "" 

        if not chunks_to_process:
            logger.info("No math keywords found in chunks. Skipping extraction.")
            return ""

        logger.info(f"Processing {len(chunks_to_process)}/{len(chunks)} chunks with math content...")

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_to_index = {
                executor.submit(self._extract_chunk, chunk): i 
                for i, chunk in chunks_to_process
            }
            for future in concurrent.futures.as_completed(future_to_index):
                index = future_to_index[future]
                try:
                    results[index] = future.result()
                except Exception as e:
                    logger.error(f"Chunk {index} extraction failed: {e}")
                    results[index] = "" # Or keep original?
        
        return "\n\n".join(filter(None, results))

    def _extract_chunk(self, chunk, retries=3):
        headers = {
            "Authorization": f"Bearer {CONFIG['EXTRACTION_API_KEY']}",
            "Content-Type": "application/json"
        }
        data = {
            "model": CONFIG['LLM_MODEL'], # Configurable model
            "messages": [
                {"role": "system", "content": "You are a math extraction tool. Extract strictly mathematical terms (Definitions, Theorems, Lemmas, Propositions, Proofs) from the text. Keep only the math content. Do NOT change LaTeX/Code formatting. Do NOT output markdown code blocks (like ```latex). Output plain text only."},
                {"role": "user", "content": chunk}
            ]
        }
        
        for attempt in range(retries):
            try:
                response = requests.post(
                    f"{CONFIG['EXTRACTION_BASE_URL']}/chat/completions", 
                    headers=headers, 
                    json=data,
                    timeout=60 # Add timeout
                )
                response.raise_for_status()
                result = response.json()
                content = result['choices'][0]['message']['content']
                
                # Post-processing to remove potential markdown code blocks
                # Remove ```latex or ```markdown or just ``` 
                # Stronger regex to remove all code block markers
                content = re.sub(r'```[a-zA-Z]*', '', content).replace('```', '')
                
                return content.strip()
            except Exception as e:
                if attempt == retries - 1:
                    logger.error(f"Failed to extract chunk after {retries} attempts: {e}")
                    raise
                logger.warning(f"Attempt {attempt + 1} failed, retrying... Error: {e}")
                import time
                time.sleep(2) # Simple backoff

    def chunk_text(self, text, max_size=2000):
        """
        Smart chunking respecting paragraph boundaries.
        """
        # Split by 2 or more newlines to get paragraphs
        paragraphs = re.split(r'\n{2,}', text)
        chunks = []
        current_chunk = []
        current_size = 0
        
        for para in paragraphs:
            para_len = len(para)
            # If adding this paragraph exceeds max_size and we have content, yield current chunk
            if current_size + para_len > max_size and current_chunk:
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = []
                current_size = 0
            
            # If a single paragraph is larger than max_size, we have to split it hard
            # or accept it being slightly larger. Here we accept it to avoid breaking formulas.
            # But if it's WAY too large (e.g. > 2*max_size), we might want to split by single newline.
            
            current_chunk.append(para)
            current_size += para_len + 2 # +2 for the newline separator
            
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))
            
        return chunks if chunks else [""]

    def process_pipeline(self, file_path, output_dir):
        """
        The main entry point.
        """
        file_path = Path(file_path)
        if not file_path.exists():
            msg = f"Error: File {file_path} not found."
            logger.error(msg)
            return msg

        # Validation
        ext = file_path.suffix.lower()
        if ext not in ['.pdf', '.md', '.tex', '.txt']:
            return "不支持当前文件格式"

        logger.info(f"Processing file: {file_path}")

        # Conversion
        content = ""
        if ext == '.pdf':
            try:
                content = self.convert_pdf_to_md(file_path)
            except Exception as e:
                return f"未设定好pdf转化为md的工具: {str(e)}"
        else:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                # Try latin-1 fallback
                try:
                    logger.warning("UTF-8 decode failed, trying GBK...")
                    with open(file_path, 'r', encoding='gbk') as f:
                        content = f.read()
                except UnicodeDecodeError:
                     logger.warning("GBK decode failed, trying Latin-1...")
                     with open(file_path, 'r', encoding='latin-1') as f:
                        content = f.read()

        # Preprocessing
        logger.info("Cleaning content...")
        cleaned = self.clean_content(content)
        
        # Chunking (Smart chunking)
        logger.info("Chunking content...")
        chunks = self.chunk_text(cleaned, max_size=2000)
        
        # Extraction
        try:
            logger.info("Extracting math content...")
            extracted = self.batch_extract(chunks)
        except Exception as e:
            logger.error(f"Extraction failed: {str(e)}")
            return f"Extraction failed: {str(e)}"

        # Merge & Output
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        out_path = output_dir / f"{file_path.stem}_extracted.md"
        
        logger.info(f"Saving to {out_path}...")
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(extracted)
            
        return str(out_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract math content from documents.")
    parser.add_argument("file_path", help="Path to the source file (pdf/md/tex/txt)")
    parser.add_argument("output_dir", help="Directory to save the extracted markdown")
    
    args = parser.parse_args()
    
    processor = MathProcessor()
    result = processor.process_pipeline(args.file_path, args.output_dir)
    print(result)
