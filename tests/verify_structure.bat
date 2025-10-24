@echo off
echo === Pi Sorter 项目结构验证 ===
echo.

echo 📁 检查主要目录:
if exist "src" (echo   ✓ src 目录存在) else (echo   ✗ src 目录不存在)
if exist "config" (echo   ✓ config 目录存在) else (echo   ✗ config 目录不存在)
if exist "docs" (echo   ✓ docs 目录存在) else (echo   ✗ docs 目录不存在)
if exist "tests" (echo   ✓ tests 目录存在) else (echo   ✗ tests 目录不存在)
if exist "历史文档" (echo   ✓ 历史文档 目录存在) else (echo   ✗ 历史文档 目录不存在)

echo.
echo 📄 检查关键文件:
if exist "README.md" (echo   ✓ README.md 存在) else (echo   ✗ README.md 不存在)
if exist "main.py" (echo   ✓ main.py 存在) else (echo   ✗ main.py 不存在)
if exist "requirements.txt" (echo   ✓ requirements.txt 存在) else (echo   ✗ requirements.txt 不存在)

echo.
echo 📚 检查文档结构:
if exist "docs\文档导航.md" (echo   ✓ 文档导航.md 存在) else (echo   ✗ 文档导航.md 不存在)
if exist "docs\01-项目概述" (echo   ✓ 01-项目概述 目录存在) else (echo   ✗ 01-项目概述 目录不存在)
if exist "docs\02-需求与设计" (echo   ✓ 02-需求与设计 目录存在) else (echo   ✗ 02-需求与设计 目录不存在)
if exist "docs\03-开发环境" (echo   ✓ 03-开发环境 目录存在) else (echo   ✗ 03-开发环境 目录不存在)
if exist "docs\04-技术实现" (echo   ✓ 04-技术实现 目录存在) else (echo   ✗ 04-技术实现 目录不存在)
if exist "docs\05-配置说明" (echo   ✓ 05-配置说明 目录存在) else (echo   ✗ 05-配置说明 目录不存在)
if exist "docs\06-使用指南" (echo   ✓ 06-使用指南 目录存在) else (echo   ✗ 06-使用指南 目录不存在)
if exist "docs\07-测试与部署" (echo   ✓ 07-测试与部署 目录存在) else (echo   ✗ 07-测试与部署 目录不存在)

echo.
echo ✅ 项目结构验证完成!
echo.
echo 📖 要查看完整文档导航，请打开: docs\文档导航.md
echo 🚀 要快速开始，请查看: docs\06-使用指南\快速开始.md
pause