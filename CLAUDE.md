## Python 环境
使用 miniconda base 环境运行 Python：`/opt/homebrew/Caskroom/miniconda/base/bin/python`。安装包时用 `/opt/homebrew/Caskroom/miniconda/base/bin/pip`，禁止使用系统自带 Python。

## .NET 环境
使用 `/usr/local/share/dotnet/dotnet`（.NET 10.0 SDK，VSCode 安装）。

## 图片识别
收到任何图片时，必须用 MCP 工具 `describe_image` 识别，禁止用 Read 工具直接读图文件。
