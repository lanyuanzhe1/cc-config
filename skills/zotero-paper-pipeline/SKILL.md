---
name: zotero-paper-pipeline
description: Find a paper and save it into the local Zotero library with the PDF attached, then translate the PDF to Chinese with the local pdf2zh Docker service and attach the translated file under the same item. Use when the user says 加文献/存到 Zotero/翻译这篇 PDF/给条目挂译文, provides an arXiv ID, DOI, or paper title, or asks to run the Zotero + PDFMathTranslate workflow.
---

# Zotero 入库 + 中文翻译流水线

一条命令级流程：**找元数据 → 建条目 → 传 PDF → docker 翻译 → 挂译文 → 校验**。

## 环境事实（本机已确认）

| 项 | 值 |
|---|---|
| Zotero | `/Applications/Zotero.app`，本地 API `http://127.0.0.1:23119`（已开启） |
| 写入鉴权 | 请求头 `Zotero-Server-ID: <serverID>`；serverID 存在 `~/Zotero/zotero.sqlite` 的 `settings` 表 `localAPI\|serverID` |
| API key | `POST /api/local/authorize` 直接返回 `{"key": "..."}`（remember=true，无需点确认） |
| 翻译服务 | Docker 容器 `pdf-translator-local`，镜像 `awwaawwa/pdfmathtranslate-next`，`pdf2zh --gui`，端口 `127.0.0.1:7860` |
| 翻译配置 | 容器内 env 已配好：OpenAICompatible(OpenRouter) + `inclusionai/ling-3.0-flash`，`zh-CN`，`NO_MONO=true`（只出双语版） |

## 快速开始

```bash
S=~/.agents/skills/zotero-paper-pipeline/scripts/zotero.py

# 1. 列出 collection（找目标分类 key）
python3 $S collections

# 2. arXiv 文献入库 + 传 PDF（自动建条目、下载 arXiv PDF、3 段式上传）
python3 $S add-arxiv 2502.14907 --collection "LLM&agent"

# 3. 翻译（见下节），然后挂译文
python3 $S attach <ITEM_KEY> /tmp/out/xxx.dual.pdf --title "Full Text PDF (中文翻译)"
```

DOI 入口用 `add-doi 10.1038/s41566-026-01889-0 --collection 太赫兹`。

**已录用会议版**（arXiv + ICLR 这类）：不要用 preprint 类型，直接建成 conferencePaper。

```bash
python3 $S add-arxiv 2502.14907 --collection "LLM&agent" \
  --venue "ICLR 2026" \
  --venue-full "International Conference on Learning Representations (ICLR) 2026" \
  --place "Rio de Janeiro, Brazil" --year 2026 \
  --openreview "https://openreview.net/forum?id=NRWUAo075J"
```

写入字段：`conferenceName=ICLR 2026`、`proceedingsTitle=<venue-full>`、`archiveID=arXiv:xxxx`、`extra` 里记 `Accepted at ...` 与 OpenReview 链接。

## 翻译步骤

```bash
C=pdf-translator-local
open -a Docker                     # 守护进程没起时先起（开机后默认不启动），等 docker info 通
docker start $C                      # 未运行时先起（GUI 服务，7860）
docker cp paper.pdf $C:/work.pdf
docker exec $C pdf2zh /work.pdf --output /work_out
docker cp $C:/work_out/work.no_watermark.zh-CN.dual.pdf ./out.pdf
```

输出命名：`<名>.no_watermark.zh-CN.dual.pdf`（默认双语，带 `no_watermark` 前缀段）。
先跑 `--pages 1-2` 验证链路（约 1 分钟），再跑全文。

## 流程清单

1. **元数据**：arXiv 用 `export.arxiv.org/api/query?id_list=<id>`（必须带 `User-Agent`，否则空响应）；DOI 用 `api.crossref.org/works/<doi>`。
2. **查重**：`GET /api/users/0/items?q=<标题片段>`，命中就只补附件，不建新条目。
3. **建条目**：`POST /api/users/0/items`，body 必须是**数组**；`libraryID: 1` + `collections: [KEY]`。
4. **传文件**：三段式，缺一步都失败——
   - `POST /items/<key>/file`，`application/x-www-form-urlencoded`，字段 `md5/filename/filesize/mtime`，头 `If-None-Match: *` → 返回 `{url, uploadKey}`
   - `POST <url>`，裸二进制
   - 再 `POST /items/<key>/file`，字段 `upload=<uploadKey>` → 204
5. **翻译**：见上；长文 20+ 页约 5–15 分钟，用日志文件轮询，不要加 `| tail`（会缓冲到结束才出）。
6. **挂译文**：把译文当子附件 `imported_file` + 三段式上传，标题写`Full Text PDF (中文翻译)`。
7. **校验**：`GET /items/<key>` 看 `md5`/`filename` 非空，`/items/<key>/children` 看到两条 PDF。

## 坑（都踩过）

- 修改条目必须带 `If-Unmodified-Since-Version: <version>`，否则 428。PATCH 里 `headers` 要**按关键字传**，位置传参会把它当成 body 或 raw。
- 请求体不是数组 → `Uploaded data must be a JSON array`。
- `pdf2zh` 参数是 `--output`，不是 `-o`（会报 unrecognized arguments）。
- 三段式上传偶发 404 `No endpoint found`（大 body 路由抖动）或 412 `file exists` 但 `~/Zotero/storage/<KEY>/` 是空的；两者都要**重试**，412+空目录就把旧附件删掉重建。脚本已内置重试。
- `POST /api/local/authorize` 有时会挂住等 GUI 确认；把已授权的 key 缓存到 `~/.cache/zotero-paper-pipeline/key`，先用缓存。
- `settings` 表结构是 `(setting, key, value)` 三列，serverID 查询要 `setting='localAPI' AND key='serverID'`。
- 容器镜像里**没有 `ps`/`kill`**：清进程用 `docker top`（宿主机看不到 VM 内 pid，`kill` 无效），要进容器扫 `/proc/*/cmdline` 再 `os.kill`。
- 容器内存上限约 3.8 GB，**并行跑两份全文会 OOM（exit 137）**，串行跑。
- **单个附件 >20 MB 传不上去**（25 MB 稳定 404）；先用 `pymupdf` 压到 16 MB 左右：`doc.save(out, garbage=4, deflate=True, clean=True, deflate_images=True, deflate_fonts=True)`。压完记得改文件名，别撞已有附件。
- Zotero 升级/重启后本地 API 会短暂不监听（curl 返回 000）；`osascript -e 'quit app "Zotero"' && open -a Zotero` 重启即可，别以为 pref 坏了。
- 两页约 1 分钟；24 页论文整篇约 8–10 分钟。输出文件名形如 `<名>.no_watermark.zh-CN.dual.pdf`。

## 校验

```bash
curl -s -H "Zotero-Server-ID: $SID" "http://127.0.0.1:23119/api/users/0/items/<KEY>/children" \
 | python3 -c "import json,sys;[print(i['data'].get('title'),i['data'].get('filename'),(i['data'].get('md5') or '')[:8]) for i in json.load(sys.stdin)]"
```

条目下应看到两条 PDF（原文 + 中文翻译），md5 非空；`~/Zotero/storage/<KEY>/` 里有真实文件。

## 脚本

`scripts/zotero.py`：`collections` / `add-arxiv`（含 `--venue` 会议模式）/ `add-doi` / `attach` / `upload`，自带 serverID 与 key 自动获取与上传重试。


## 重译 + 批注迁移（旧译文换模型重跑）

条目上已有旧译文附件和批注，想换翻译模型重译并保留批注时：

```bash
S=~/.agents/skills/zotero-paper-pipeline/scripts
# 1) 取条目/附件 key 和旧批注
#    GET /users/0/items/<PARENT>/children
#    GET /users/0/items/<旧译文附件>/children?itemType=annotation   → 存 JSON
# 2) 重译原文（pdftranslate 已带 --disable-rich-text-translate）
pdftranslate "<原文.pdf>" --output /tmp/out
# 3) 压到 <20MB（见下方字体子集化）
# 4) 重新锚定批注位置（输出为 PyMuPDF 左上原点坐标）
python3 $S/remap_annotations.py /tmp/out/xxx.zh.dual.pdf /tmp/old_ann.json /tmp/remap.json
# 5) 建附件 + 上传 + 迁移批注 + 删旧附件（内部会翻转 y 坐标）
python3 $S/migrate_annotations.py /tmp/out/xxx.zh.dual.pdf /tmp/remap.json <PARENT_KEY> <旧译文附件KEY> "Full Text PDF (中文翻译)"
# 6) 目视校验
open "zotero://open-pdf/library/items/<新译文附件KEY>"
```

要点：

- **Zotero `annotationPosition` 用 PDF 原生坐标（左下原点、y 向上）**，PyMuPDF 是左上原点；
  写回前必须 `y' = 页高 − y`，否则批注整体上下镜像错位。可用库里其它文献的批注验证：
  翻转后与文字的 bbox 吻合即正确。
- 新旧译文**版面相同**（BabelDOC 按原 PDF 版面排），但换行/行首位置会因译文长度变化，
  所以按批注文本在新译文里做模糊匹配再生成 rects，比直接搬旧坐标更贴合。
- 自动匹配差的条目在 `remap_annotations.py` 的 `MANUAL` 里给锚定短语（如
  `{"XXXX": ["令牌高效代码接口"]}`），脚本会按短语精确取位置。
- 校验：`curl` 取新附件的 annotation，把 rects 翻转回左上原点后抽取覆盖文字，
  应与批注文本语义一致；再在 Zotero 里打开目视。

### 压缩：优先字体子集化

BabelDOC 有时会把整份 CJK 字体嵌进 PDF（单个 FontFile2 解压后 10–25 MB），
这种文件 `doc.save(garbage=4, deflate=True, ...)` 几乎压不动（52 MB → 49 MB）。
用 PyMuPDF 的字体子集化就能降到几 MB：

```python
doc = pymupdf.open(src)
doc.subset_fonts()          # 只保留实际用到的字形
doc.save(dst, garbage=4, deflate=True, clean=True, deflate_images=True, deflate_fonts=True)
```

子集化后抽检几页（正文、公式、图表、特殊字体标题）确认没有字形损坏再上传。
