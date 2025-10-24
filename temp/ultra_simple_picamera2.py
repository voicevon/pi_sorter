import time
import logging
from picamera2 import Picamera2

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_ultra_simple():
    logger.info("极简化Picamera2测试...")
    
    try:
        # 初始化摄像头
        picam2 = Picamera2()
        logger.info("成功初始化Picamera2")
        
        # 极简化配置，只设置分辨率
        config = picam2.create_still_configuration(main={"size": (1280, 720)})
        
        # 应用配置
        logger.info("应用配置...")
        picam2.configure(config)
        
        # 启动摄像头
        logger.info("启动摄像头...")
        picam2.start()
        
        # 等待稳定
        logger.info("等待2秒...")
        time.sleep(2)
        
        # 捕获图像
        logger.info("捕获图像...")
        metadata = picam2.capture_file("test_ultra_simple.jpg")
        
        # 检查结果
        import os
        if os.path.exists("test_ultra_simple.jpg"):
            file_size = os.path.getsize("test_ultra_simple.jpg")
            logger.info(f"✅ 图像捕获成功! 大小: {file_size} 字节")
            logger.info(f"元数据: {metadata}")
        else:
            logger.error("❌ 图像保存失败!")
        
        # 清理
        logger.info("停止摄像头...")
        picam2.stop()
        picam2.close()
        logger.info("测试完成")
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_ultra_simple()