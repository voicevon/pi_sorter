import logging
from picamera2 import Picamera2

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_minimal():
    logger.info("最小化Picamera2测试...")
    
    try:
        # 列出可用的摄像头
        cameras = Picamera2.global_camera_info()
        logger.info(f"找到摄像头数量: {len(cameras)}")
        for i, cam_info in enumerate(cameras):
            logger.info(f"摄像头 {i}: {cam_info}")
        
        # 如果找不到摄像头，尝试不同方法
        if len(cameras) == 0:
            logger.warning("未找到摄像头，尝试直接初始化...")
            picam2 = Picamera2(0)  # 尝试使用索引0
            logger.info("成功初始化摄像头")
            picam2.close()
        
        return True
        
    except Exception as e:
        logger.error(f"测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_minimal()