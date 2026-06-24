---
name: pdf-generation-chrome
description: Use Playwright MCP plugin (Chromium) for HTML→PDF conversion from Jupyter notebooks
metadata: 
  node_type: memory
  type: project
  originSessionId: 5fbc6e8c-ca2b-417d-a941-048c0a7aa807
---

PDF generation workflow for homework assignments:
1. Execute notebook on AWS server (`jupyter nbconvert --to notebook --execute --inplace`)
2. Export to HTML with embedded images (`jupyter nbconvert --to html --EmbedImagesPreprocessor.embed_images=True`)
3. Download HTML to local via SSH (`ssh ... cat > local.html`)
4. Start HTTP server in the HTML directory (`python -m http.server 8897`)
5. Use Playwright MCP plugin (Chromium) to navigate and print to PDF
6. Clean up: kill HTTP server, delete HTML, delete .playwright-mcp/

**Why:** Playwright MCP uses its own Chromium binary, separate from user's Chrome. The user's Google account logout was caused by this interference and resolved. Weasyprint was tried but failed on macOS due to missing system libraries (pango/GTK).

**How to apply:** For any future homework PDF export, follow this pipeline. Never use Playwright for random browsing — only for PDF generation. Prefix PDF filenames with `homework_` (e.g., `homework_H3-3.pdf`).

[[server-connection]]
