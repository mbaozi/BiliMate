#!/usr/bin/env python3
import os
import shutil
import zipapp
import tempfile

# 项目根目录
PROJECT_ROOT = os.path.join(os.getcwd(), "")
print(f"项目根目录: {PROJECT_ROOT}")

# 要打包的文件和目录（仅包含用户指定的源码）
SOURCES_TO_INCLUDE = [
    "app",
    "config.py",
    "run.py",
    "runtime"
]

# 输出pyz文件路径
OUTPUT_PYZ = "bilimate.pyz"

# 创建临时目录
with tempfile.TemporaryDirectory() as temp_dir:
    print(f"创建临时目录: {temp_dir}")
    
    # 只复制用户指定的源码到临时目录
    for source in SOURCES_TO_INCLUDE:
        source_path = os.path.join(PROJECT_ROOT, source)
        dest_path = os.path.join(temp_dir, source)
        
        if os.path.isdir(source_path):
            shutil.copytree(source_path, dest_path)
            print(f"复制目录: {source}")
        else:
            shutil.copy2(source_path, dest_path)
            print(f"复制文件: {source}")
    
    # 生成pyz文件，只包含用户指定的源码
    print(f"生成pyz文件: {OUTPUT_PYZ}")
    zipapp.create_archive(
        temp_dir, 
        OUTPUT_PYZ, 
        interpreter="/usr/bin/env python3",
        main="run:main"  # 调用run.py中的main函数作为入口点
    )
    
    print(f"pyz文件生成成功: {OUTPUT_PYZ}")
