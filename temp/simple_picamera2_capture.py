import time
import logging
from picamera2 import Picamera2

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_picamera2():
    logger.info("启动Picamera2测试...")
    
    # 初始化摄像头
    try:
        picam2 = Picamera2()
        logger.info("成功初始化Picamera2")
        
        # 使用更简单的配置
        preview_config = picam2.create_preview_configuration(
            main={"size": (1280, 720)},
            controls={
                "FrameRate": 30.0,
                "ExposureMode": "auto",  # 使用字符串而不是枚举
                "AeEnable": True
            }
        )
        
        # 应用配置
        logger.info("应用预览配置...")
        picam2.configure(preview_config)
        
        # 启动摄像头
        logger.info("启动摄像头...")
        picam2.start()
        
        # 等待摄像头稳定
        logger.info("等待摄像头稳定(2秒)...")
        time.sleep(2)
        
        # 捕获图像
        logger.info("捕获图像...")
        metadata = picam2.capture_file("test_picamera2.jpg")
        
        # 检查图像是否成功保存
        import os
        if os.path.exists("test_picamera2.jpg"):
            file_size = os.path.getsize("test_picamera2.jpg")
            logger.info(f"图像捕获成功! 保存为: test_picamera2.jpg, 大小: {file_size} 字节")
            logger.info(f"元数据: 分辨率={metadata['ScalerCrop'][2]}x{metadata['ScalerCrop'][3]}, 曝光时间={metadata.get('ExposureTime', '未知')}μs")
        else:
            logger.error("图像保存失败!")
        
        # 停止并关闭
        logger.info("停止摄像头...")
        picam2.stop()
        picam2.close()
        logger.info("测试完成")
        return True
        
    except Exception as e:
        logger.error(f"测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_picamera2()