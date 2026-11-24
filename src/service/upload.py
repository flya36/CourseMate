import io
import zipfile
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException

ALLOWED_EXT = {".pdf", ".pptx"}
MAX_SIZE = 20 * 1024 * 1024          # 20MB
BASE_DIR = Path(__file__).resolve().parents[2]
UPLOAD_DIR = BASE_DIR / "uploads"

PDF_MAGIC = b"%PDF-"
ZIP_MAGIC = b"PK\x03\x04"
PPTX_ENTRY = "ppt/presentation.xml"


def sniff(head: bytes) -> str:
    """按文件头判断真实类型。PDF 规范允许 %PDF- 前有少量字节，所以在前面找而不是只认开头。"""
    if PDF_MAGIC in head[:1024]:
        return "pdf"
    if head.startswith(ZIP_MAGIC):
        return "zip"
    return "unknown"


def is_real_pptx(data: bytes) -> bool:
    """zip 只说明是压缩包；真正的 pptx 必须有 ppt/presentation.xml。
    只读目录、不解压内容 —— 避免 zip bomb。"""
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            names = z.namelist()
    except zipfile.BadZipFile:
        return False
    return PPTX_ENTRY in names and len(names) < 10000


def safe_filename(filename: str | None) -> str:
    """只留 basename：去掉路径分隔符与控制字符，截到 255（对齐 DB 列宽）。"""
    name = (filename or "").replace("\\", "/").rsplit("/", 1)[-1]
    name = "".join(ch for ch in name if ch >= " ").strip()
    name = name[:255]
    if not name:
        raise HTTPException(400, "文件名不能为空")
    return name


def validate_upload(filename: str, data: bytes) -> str:
    """三层校验：后缀 → 体积 → 真实类型（魔数）。全过返回 '.pdf'/'.pptx'，否则抛异常。

    注意：体积这一层是兜底。调用方必须先用 read(MAX_SIZE + 1) 截断，
    否则 2GB 的文件在 read() 那一刻就已经 OOM 了，走不到这里。
    """
    if not data:
        raise HTTPException(400, "文件为空")

    ext = ("." + filename.rsplit(".", 1)[-1].lower()) if "." in filename else ""
    if ext not in ALLOWED_EXT:
        raise HTTPException(415, f"不支持的文件类型：{ext or '(无后缀)'}，只接受 .pdf / .pptx")

    if len(data) > MAX_SIZE:
        raise HTTPException(413, f"文件超过 {MAX_SIZE // 1024 // 1024}MB 上限")

    kind = sniff(data)
    if ext == ".pdf" and kind != "pdf":
        raise HTTPException(415, "文件内容不是有效 PDF（后缀与实际类型不符）")
    if ext == ".pptx" and (kind != "zip" or not is_real_pptx(data)):
        raise HTTPException(415, "文件内容不是有效 PPTX（后缀与实际类型不符）")

    return ext


def save_upload(data: bytes, ext: str) -> str:
    """落盘名一律服务端生成：用户给的 filename 不参与路径拼接。
    返回相对路径（posix 分隔符），给库里存。"""
    if ext not in ALLOWED_EXT:                     # 不信任调用方传来的 ext
        raise HTTPException(415, "不支持的文件类型")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True) 
    path = UPLOAD_DIR / f"{uuid4().hex}{ext}"
    path.write_bytes(data)
    return path.relative_to(BASE_DIR).as_posix()

def resolve_path(rel_path: str) -> Path:
    """库里存的相对路径 → 磁盘绝对路径；顺带挡住 .. 逃逸。"""
    p = (BASE_DIR / rel_path).resolve()
    if UPLOAD_DIR.resolve() not in p.parents:
        raise HTTPException(400, "非法文件路径")
    return p