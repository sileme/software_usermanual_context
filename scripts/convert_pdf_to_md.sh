#!/bin/bash
# convert_pdf_to_md.sh — 批量将 PDF 手册转换为 Markdown
# 用法: bash scripts/convert_pdf_to_md.sh <pdf_dir> <output_dir>
# 示例: bash scripts/convert_pdf_to_md.sh corpus/raw/dakota corpus/md/dakota

set -euo pipefail

PDF_DIR="${1:?缺少参数: <pdf_dir>}"
OUTPUT_DIR="${2:?缺少参数: <output_dir>}"
LOG_FILE="$OUTPUT_DIR/_conversion.log"

if ! command -v mineru &>/dev/null && ! command -v magic-pdf &>/dev/null && ! python -c "import mineru" 2>/dev/null; then
    echo "[ERROR] MinerU 未安装。请先执行: pip install mineru"
    exit 1
fi

if [ ! -d "$PDF_DIR" ]; then
    echo "[ERROR] PDF 目录不存在: $PDF_DIR"
    exit 1
fi

mkdir -p "$OUTPUT_DIR"

shopt -s nullglob
PDF_FILES=("$PDF_DIR"/*.pdf)
shopt -u nullglob

if [ ${#PDF_FILES[@]} -eq 0 ]; then
    echo "[WARN] 未在 $PDF_DIR 中找到 PDF 文件"
    exit 0
fi

echo "======== $(date '+%Y-%m-%d %H:%M:%S') ========" | tee -a "$LOG_FILE"
echo "输入目录: $PDF_DIR" | tee -a "$LOG_FILE"
echo "输出目录: $OUTPUT_DIR" | tee -a "$LOG_FILE"
echo "文件数量: ${#PDF_FILES[@]}" | tee -a "$LOG_FILE"
echo "-------------------------------------------" | tee -a "$LOG_FILE"

SUCCESS=0
FAIL=0

for pdf in "${PDF_FILES[@]}"; do
    filename=$(basename "$pdf" .pdf)
    echo -n "[$(date '+%H:%M:%S')] $filename.pdf ... " | tee -a "$LOG_FILE"

    if mineru -i "$pdf" -o "$OUTPUT_DIR" >> "$LOG_FILE" 2>&1; then
        # MinerU may produce output in a subdirectory; find and move the .md file
        MD_FILE=$(find "$OUTPUT_DIR" -name "${filename}.md" -type f 2>/dev/null | head -1)
        if [ -z "$MD_FILE" ]; then
            # Try alternative naming patterns
            MD_FILE=$(find "$OUTPUT_DIR" -name "*.md" -type f -newer "$LOG_FILE" 2>/dev/null | head -1)
        fi
        if [ -n "$MD_FILE" ] && [ "$MD_FILE" != "$OUTPUT_DIR/${filename}.md" ]; then
            mv "$MD_FILE" "$OUTPUT_DIR/${filename}.md" 2>/dev/null || true
        fi
        echo "OK" | tee -a "$LOG_FILE"
        SUCCESS=$((SUCCESS + 1))
    else
        echo "FAILED" | tee -a "$LOG_FILE"
        FAIL=$((FAIL + 1))
    fi
done

echo "-------------------------------------------" | tee -a "$LOG_FILE"
echo "完成: 成功 $SUCCESS / 失败 $FAIL / 总计 ${#PDF_FILES[@]}" | tee -a "$LOG_FILE"

# 清理 MinerU 中间产物
find "$OUTPUT_DIR" -type d -name "_*" -exec rm -rf {} + 2>/dev/null || true
find "$OUTPUT_DIR" -type f \( -name "*.json" -o -name "*.png" -o -name "*.jpg" \) -delete 2>/dev/null || true
echo "中间产物已清理" | tee -a "$LOG_FILE"
