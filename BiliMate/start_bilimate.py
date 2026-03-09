#!/usr/bin/env python3
import os
import sys
import requests
import zipfile
import shutil
from datetime import datetime

# 升级服务器地址
UPGRADE_SERVER = "https://update.mbaozi.cn"


def get_latest_version():
    """
    获取最新版本信息
    
    Returns:
        dict: 包含success、message和data字段的结果
            data字段包含：latest_version, download_url, is_available
    """
    try:
        print("获取最新版本信息...")
        
        # 构建API请求URL
        url = f"{UPGRADE_SERVER}/api/apps/BiliMate/check-update"
        
        # 发送请求
        response = requests.get(
            url,
            params={"currentVersion": "0.0.0"},  # 初始版本设为0.0.0，确保总是获取最新版本
            timeout=30
        )
        
        print(f"响应状态码: {response.status_code}")
        
        # 解析响应
        result = response.json()
        
        # 处理响应结果
        if result.get("success"):
            need_update = result.get("needUpdate", False)
            data = result.get("data", {})
            
            return {
                "success": True,
                "message": "获取最新版本信息成功",
                "data": {
                    "latest_version": data.get("version", ""),
                    "download_url": data.get("downloadUrl", ""),
                    "is_available": need_update
                }
            }
        else:
            return {
                "success": False,
                "message": result.get("message", "获取最新版本信息失败"),
                "data": {}
            }
    
    except Exception as e:
        return {
            "success": False,
            "message": f"获取最新版本信息失败: {str(e)}",
            "data": {}
        }


def download_upgrade_package(download_url):
    """
    下载升级包
    
    Args:
        download_url (str): 升级包下载URL
        
    Returns:
        str: 下载后的文件路径
    """
    try:
        print(f"开始下载升级包: {download_url}")
        
        # 生成下载文件路径
        file_name = f"bilimate_upgrade_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        download_path = os.path.join(os.getcwd(), file_name)
        
        # 发送请求
        response = requests.get(
            download_url,
            stream=True,
            timeout=60
        )
        
        # 检查响应状态码
        if response.status_code != 200:
            print(f"下载失败，状态码: {response.status_code}")
            return None
        
        # 获取文件大小
        file_size = int(response.headers.get("Content-Length", 0))
        print(f"升级包大小: {file_size} bytes")
        
        # 下载文件
        downloaded_size = 0
        last_progress = 0
        with open(download_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded_size += len(chunk)
                    
                    # 计算下载进度
                    if file_size > 0:
                        progress = (downloaded_size / file_size) * 100
                        if int(progress) > last_progress:
                            last_progress = int(progress)
                            print(f"下载进度: {progress:.2f}%")
        
        # 检查下载是否完整
        if file_size > 0 and downloaded_size != file_size:
            print("下载不完整，文件大小不匹配")
            if os.path.exists(download_path):
                os.remove(download_path)
            return None
        
        print(f"升级包下载完成: {download_path}")
        return download_path
    
    except Exception as e:
        print(f"下载升级包失败: {str(e)}")
        return None


def extract_upgrade_package(upgrade_package_path):
    """
    解压升级包
    
    Args:
        upgrade_package_path (str): 升级包路径
        
    Returns:
        bool: 是否解压成功
    """
    try:
        print(f"开始解压升级包: {upgrade_package_path}")
        
        # 检查升级包文件是否存在
        if not os.path.exists(upgrade_package_path):
            print("升级包文件不存在")
            return False
        
        # 检查升级包文件是否为zip格式
        if not zipfile.is_zipfile(upgrade_package_path):
            print("升级包文件格式错误，不是有效的zip文件")
            return False
        
        # 解压升级包
        with zipfile.ZipFile(upgrade_package_path, 'r') as zf:
            # 遍历zip文件中的所有文件
            for member in zf.namelist():
                # 跳过目录
                if member.endswith('/'):
                    continue
                
                # 计算目标文件路径
                target_path = os.path.join(os.getcwd(), member)
                
                # 创建目标目录
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                
                # 提取文件
                zf.extract(member, os.getcwd())
                print(f"提取文件: {member} -> {target_path}")
        
        print("升级包解压完成")
        return True
    
    except Exception as e:
        print(f"解压升级包失败: {str(e)}")
        return False


def main():
    """
    主函数：检查并启动 BiliMate
    """
    print("BiliMate 初始化脚本")
    print("=" * 50)
    
    # 检查当前目录是否有 bilimate.pyz 文件
    bilimate_pyz = os.path.join(os.getcwd(), "bilimate.pyz")
    
    if os.path.exists(bilimate_pyz):
        print("发现 bilimate.pyz 文件，直接启动...")
    else:
        print("未发现 bilimate.pyz 文件，开始下载最新版本...")
        
        # 获取最新版本信息
        version_info = get_latest_version()
        if not version_info.get("success"):
            print(f"获取版本信息失败: {version_info.get('message')}")
            sys.exit(1)
        
        data = version_info.get("data", {})
        download_url = data.get("download_url")
        
        if not download_url:
            print("未获取到下载链接")
            sys.exit(1)
        
        # 下载升级包
        upgrade_package = download_upgrade_package(download_url)
        if not upgrade_package:
            print("下载升级包失败")
            sys.exit(1)
        
        # 解压升级包
        if not extract_upgrade_package(upgrade_package):
            print("解压升级包失败")
            sys.exit(1)
        
        # 清理临时文件
        if os.path.exists(upgrade_package):
            os.remove(upgrade_package)
            print(f"清理临时文件: {upgrade_package}")
        
        # 再次检查 bilimate.pyz 文件
        if not os.path.exists(bilimate_pyz):
            print("解压后仍未找到 bilimate.pyz 文件")
            sys.exit(1)
        
        print("下载并解压完成，准备启动...")
    
    # 启动 bilimate.pyz
    print("启动 BiliMate...")
    os.system(f"python {bilimate_pyz}")


if __name__ == "__main__":
    main()
