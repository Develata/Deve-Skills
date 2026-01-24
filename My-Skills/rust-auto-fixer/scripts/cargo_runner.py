import subprocess
import json
import tempfile
import os
import shutil
import sys
import re

# 增强的依赖配置，用于处理需要特定 feature 的常见库
ENHANCED_DEPS = {
    "serde": 'serde = { version = "*", features = ["derive"] }',
    "tokio": 'tokio = { version = "*", features = ["full"] }',
    "reqwest": 'reqwest = { version = "*", features = ["json", "blocking"] }',
    "clap": 'clap = { version = "*", features = ["derive"] }',
    "rand": 'rand = "*"', 
}

def detect_dependencies(code: str) -> list[str]:
    """
    基于 use 语句的简单依赖嗅探。
    """
    deps = set()
    for match in re.finditer(r'^\s*use\s+([a-zA-Z0-9_]+)(?:::|;)', code, re.MULTILINE):
        root = match.group(1)
        if root not in ["std", "core", "alloc", "crate", "super", "self"]:
            deps.add(root)
    return sorted(list(deps))

def format_rust_code(file_path: str) -> str:
    """
    使用 rustfmt 格式化代码，并返回格式化后的内容。
    如果 rustfmt 失败或未安装，返回 None。
    """
    try:
        subprocess.run(
            ["rustfmt", file_path],
            check=True,
            capture_output=True,
            timeout=10
        )
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return None

def check_rust_code(code: str) -> str:
    """
    创建一个临时 Cargo 项目，写入代码，自动检测依赖，运行 cargo check。
    如果成功，运行 rustfmt 并返回 "SUCCESS\n<formatted_code>"。
    如果失败，返回错误信息。
    """
    # 使用固定目录以利用 Cargo 缓存 (target 目录)
    # 在 Windows 上，gettempdir 通常是 AppData/Local/Temp
    base_tmp_dir = os.path.join(tempfile.gettempdir(), "trae_rust_auto_fixer_cache")
    os.makedirs(base_tmp_dir, exist_ok=True)
    
    # 我们在这个目录下创建一个项目 "project"
    project_dir = os.path.join(base_tmp_dir, "project")
    src_dir = os.path.join(project_dir, "src")
    os.makedirs(src_dir, exist_ok=True)
    
    # 自动检测依赖
    detected_deps = detect_dependencies(code)
    dep_toml_lines = []
    for dep in detected_deps:
        if dep in ENHANCED_DEPS:
            dep_toml_lines.append(ENHANCED_DEPS[dep])
        else:
            dep_toml_lines.append(f'{dep} = "*"')
    
    dep_section = "\n".join(dep_toml_lines)

    # 初始化 Cargo.toml
    # 注意：如果依赖改变了，Cargo 会处理。
    cargo_toml = f"""
    [package]
    name = "temp_check"
    version = "0.1.0"
    edition = "2021"
    
    [dependencies]
    {dep_section}
    """
    
    with open(os.path.join(project_dir, "Cargo.toml"), "w") as f:
        f.write(cargo_toml)
        
    # 写入 main.rs
    main_rs_path = os.path.join(src_dir, "main.rs")
    with open(main_rs_path, "w", encoding="utf-8") as f:
        f.write(code)
        
    # 2. 运行 cargo check
    try:
        # 使用 --message-format=json 获取机器可读的错误
        result = subprocess.run(
            ["cargo", "check", "--message-format=json"],
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=60
        )
    except subprocess.TimeoutExpired:
        return "ERROR: Compilation timed out."
    except Exception as e:
        return json.dumps({"error": f"Failed to run cargo: {str(e)}"})

    # 3. 解析输出
    errors = []
    for line in result.stdout.splitlines():
        try:
            msg = json.loads(line)
            if msg.get("reason") == "compiler-message" and msg.get("message", {}).get("level") == "error":
                rendered = msg["message"].get("rendered", "")
                errors.append(rendered)
        except:
            continue

    if not errors:
        # 成功！尝试格式化代码
        formatted_code = format_rust_code(main_rs_path)
        if formatted_code:
            return f"SUCCESS\n{formatted_code}"
        else:
            # 格式化失败（可能未安装 rustfmt），返回原始代码或仅返回 SUCCESS
            # 为了保持一致性，最好返回原始代码如果格式化失败
            with open(main_rs_path, "r", encoding="utf-8") as f:
                raw_code = f.read()
            return f"SUCCESS\n{raw_code}"
    
    return "\n".join(errors)

if __name__ == "__main__":
    # 支持两种模式：
    # 1. python cargo_runner.py path/to/file.rs
    # 2. python cargo_runner.py "fn main() { ... }" (直接传代码串，虽然有长度限制但方便调试)
    
    if len(sys.argv) < 2:
        print("Usage: python cargo_runner.py <file_path_or_code_string>")
        sys.exit(1)
        
    input_arg = sys.argv[1]
    
    # 如果是文件路径
    if os.path.exists(input_arg) and os.path.isfile(input_arg):
        with open(input_arg, "r", encoding="utf-8") as f:
            code_content = f.read()
    else:
        # 假设是代码字符串
        code_content = input_arg
        
    print(check_rust_code(code_content))