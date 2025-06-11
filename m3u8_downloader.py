import subprocess
import os
import argparse
import tempfile
import time
from typing import Optional, Dict, List, Union

def download_m3u8(
    url: str,
    output_file: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None,
    ffmpeg_path: str = "ffmpeg",
    timeout: int = 600,
    quiet: bool = False,
    log_callback=None,
    retry: int = 3,
    retry_delay: int = 5
) -> bool:
    """
    下载 M3U8 流媒体并转换为 MP4 文件
    
    参数:
        url: M3U8 文件的 URL
        output_file: 输出文件名，默认为根据 URL 生成
        headers: 自定义 HTTP 请求头，默认为浏览器常用请求头
        ffmpeg_path: FFmpeg 可执行文件路径
        timeout: 下载超时时间（秒）
        quiet: 是否安静模式（不输出详细日志）
        log_callback: 日志回调函数，用于自定义日志处理
        retry: 重试次数
        retry_delay: 重试间隔时间（秒）
    
    返回:
        下载是否成功
    """
    # 如果未提供输出文件名，从 URL 生成
    if not output_file:
        # 从 URL 提取文件名或使用时间戳
        output_file = f"output_{int(time.time())}.mp4"
    
    # 确保输出文件是 MP4 格式
    if not output_file.lower().endswith('.mp4'):
        output_file += '.mp4'
    
    # 设置默认请求头
    default_headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Connection': 'keep-alive',
    }
    
    # 合并默认请求头和用户提供的请求头
    request_headers = {**default_headers, **(headers or {})}
    
    # 检查输出文件是否已存在
    if os.path.exists(output_file):
        log(f"文件已存在: {output_file}", quiet, log_callback)
        return False
    
    log(f"开始下载: {url}", quiet, log_callback)
    
    # 构建 FFmpeg 命令
    headers_str = ''.join([f"{k}: {v}\r\n" for k, v in request_headers.items()])
    cmd = [
        ffmpeg_path,
        "-headers", headers_str,
        "-i", url,
        "-c", "copy",
        "-bsf:a", "aac_adtstoasc",
        "-timeout", str(timeout),
        output_file
    ]
    
    # 重试机制
    for attempt in range(retry + 1):
        try:
            log(f"尝试下载 (第 {attempt + 1}/{retry + 1} 次)", quiet, log_callback)
            
            # 执行命令
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )
            
            # 实时输出进度
            for line in process.stdout:
                if not quiet:
                    print(line.strip())
            
            # 等待完成
            process.wait()
            
            if process.returncode == 0:
                log(f"下载完成: {output_file}", quiet, log_callback)
                return True
            else:
                log(f"下载失败，错误码: {process.returncode}", quiet, log_callback)
                if attempt < retry:
                    log(f"将在 {retry_delay} 秒后重试...", quiet, log_callback)
                    time.sleep(retry_delay)
        
        except Exception as e:
            log(f"下载过程中出错: {e}", quiet, log_callback)
            if attempt < retry:
                log(f"将在 {retry_delay} 秒后重试...", quiet, log_callback)
                time.sleep(retry_delay)
    
    log("达到最大重试次数，下载失败", quiet, log_callback)
    return False

def log(message: str, quiet: bool, callback=None) -> None:
    """处理日志输出"""
    if not quiet:
        print(message)
    if callback:
        callback(message)

def download_m3u8_cli():
    """命令行接口"""
    parser = argparse.ArgumentParser(description="M3U8 流媒体下载工具")
    parser.add_argument("--url", required=True, help="M3U8 文件的 URL")
    parser.add_argument("--output", "-o", help="输出文件名")
    parser.add_argument("--user-agent", "-ua", help="自定义 User-Agent")
    parser.add_argument("--referer", "-r", help="自定义 Referer")
    parser.add_argument("--cookie", "-c", help="自定义 Cookie")
    parser.add_argument("--ffmpeg", default="ffmpeg", help="ffmpeg 可执行文件路径")
    parser.add_argument("--quiet", "-q", action="store_true", help="安静模式")
    parser.add_argument("--retry", type=int, default=3, help="重试次数")
    parser.add_argument("--retry-delay", type=int, default=5, help="重试间隔时间（秒）")
    
    args = parser.parse_args()
    
    # 构建请求头
    headers = {}
    if args.user_agent:
        headers["User-Agent"] = args.user_agent
    if args.referer:
        headers["Referer"] = args.referer
    if args.cookie:
        headers["Cookie"] = args.cookie
    
    # 调用下载函数
    success = download_m3u8(
        url=args.url,
        output_file=args.output,
        headers=headers,
        ffmpeg_path=args.ffmpeg,
        quiet=args.quiet,
        retry=args.retry,
        retry_delay=args.retry_delay
    )
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(download_m3u8_cli())
