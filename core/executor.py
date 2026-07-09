"""共享线程池 — 全局复用，避免各模块反复创建销毁"""

from concurrent.futures import ThreadPoolExecutor

# 模块级线程池（全局复用）
executor = ThreadPoolExecutor(max_workers=4)
