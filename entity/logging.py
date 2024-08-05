import os
import logging

# 创建、设置指定文件
# 获取当前文件地址
log_dir = os.path.dirname(os.path.abspath(__file__))

# 当前文件上两级目录
log_dir = os.path.dirname(os.path.dirname(log_dir))
# log_dir = os.path.dirname(os.path.dirname(log_dir))

log_file_path = '{}\\logs\\vanna'.format(log_dir)
try:
    fh = logging.FileHandler(log_file_path + "vanna_test_logger.log")
except FileNotFoundError:
    # 创建文件A.log
    os.makedirs(log_file_path)
    with open(log_file_path + "vanna_test_logger.log", 'w') as f:
        f.write('')
    fh = logging.FileHandler(log_file_path + "vanna_test_logger.log")

# 设置输出级别
fh.setLevel(logging.DEBUG)

# 设置输出格式
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s : %(message)s')
fh.setFormatter(formatter)

# 创建logger
logger = logging.getLogger('vanna_test_logger')
logger.setLevel(logging.DEBUG)  # 设置日志级别
# 将handler添加到logger
logger.addHandler(fh)
