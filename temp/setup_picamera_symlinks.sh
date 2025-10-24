#!/bin/bash

# 检查并激活虚拟环境
if [ -f "~/pi_sorter/venv/bin/activate" ]; then
    source ~/pi_sorter/venv/bin/activate
    echo "✓ 已激活虚拟环境"
else
    echo "⚠️ 虚拟环境激活失败，使用系统Python"
fi

# 获取虚拟环境site-packages路径
VENV_SITE_PACKAGES=$(python3 -c 'import site; print(site.getsitepackages()[0])')
echo "虚拟环境site-packages路径: $VENV_SITE_PACKAGES"

# 动态查找系统包路径
find_system_package() {
    local package_name=$1
    local paths=("/usr/lib/python3/dist-packages" "/usr/local/lib/python3.13/dist-packages" "/usr/lib/python3.13/dist-packages")
    
    for path in "${paths[@]}"; do
        if [ -d "$path/$package_name" ]; then
            echo "$path/$package_name"
            return 0
        fi
    done
    
    echo ""
    return 1
}

# 创建picamera2符号链接
echo "创建picamera2符号链接..."
PICAMERA_PATH=$(find_system_package "picamera2")
if [ -n "$PICAMERA_PATH" ]; then
    sudo ln -sf "$PICAMERA_PATH" "$VENV_SITE_PACKAGES/picamera2"
    if [ -L "$VENV_SITE_PACKAGES/picamera2" ]; then
        echo "✓ picamera2符号链接创建成功"
    else
        echo "✗ picamera2符号链接创建失败"
    fi
else
    echo "✗ 未找到picamera2包"
fi

# 创建pykms符号链接
echo "创建pykms符号链接..."
PYKMS_PATH=$(find_system_package "pykms")
if [ -n "$PYKMS_PATH" ]; then
    sudo ln -sf "$PYKMS_PATH" "$VENV_SITE_PACKAGES/pykms"
    if [ -L "$VENV_SITE_PACKAGES/pykms" ]; then
        echo "✓ pykms符号链接创建成功"
    else
        echo "✗ pykms符号链接创建失败"
    fi
else
    echo "✗ 未找到pykms包"
fi

# 测试基本导入
echo "测试picamera2导入..."
python3 -c "import picamera2; print('picamera2导入成功')" 2>&1 || echo "✗ picamera2导入失败"

# 检查libcamera命令
echo "检查libcamera工具..."
if command -v cam &> /dev/null; then
    echo "✓ libcamera工具可用: cam"
    cam --help | head -3
else
    echo "✗ libcamera工具不可用"
fi

echo "设置完成！"