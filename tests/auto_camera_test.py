#!/usr/bin/env python3
"""
自动化摄像头功能测试脚本 - 仅支持CSI摄像头
Automated Camera Function Test Script - only supports CSI cameras
"""

import numpy as np
import os
import sys
import time
from datetime import datetime

# 导入picamera2
from picamera2 import Picamera2
print("✅ picamera2库已导入，将测试CSI摄像头")

# 标记picamera2可用
PICAMERA2_AVAILABLE = True

class CameraTest:
    def __init__(self):
        self.test_results = []
        self.test_images_dir = "test_images"
        
    def log_result(self, test_name, success, message="", details=""):
        """记录测试结果"""
        result = {
            'test': test_name,
            'success': success,
            'message': message,
            'details': details,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        self.test_results.append(result)
        
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{status} {test_name}: {message}")
        if details:
            print(f"   详情: {details}")
    
    def setup_test_environment(self):
        """设置测试环境"""
        print("🔧 设置测试环境...")
        
        # 创建测试图像目录
        if not os.path.exists(self.test_images_dir):
            os.makedirs(self.test_images_dir)
            self.log_result("环境设置", True, f"创建测试目录: {self.test_images_dir}")
        else:
            self.log_result("环境设置", True, f"测试目录已存在: {self.test_images_dir}")
    
    def test_camera_detection(self):
        """测试摄像头设备检测"""
        print("\n📷 测试摄像头设备检测...")
        
        # 仅检测CSI摄像头
        try:
            picam2 = Picamera2()
            camera_info = picam2.sensor_modes
            picam2.close()
            
            self.log_result(
                "CSI摄像头检测", 
                True, 
                "发现CSI摄像头",
                f"支持 {len(camera_info)} 种模式"
            )
            return ("CSI", 0)
        except Exception as e:
            self.log_result("CSI摄像头检测", False, f"CSI摄像头不可用: {str(e)}")
            return None
    
    def test_camera_connection(self, camera_info):
        """测试摄像头连接"""
        if camera_info is None:
            return None
            
        camera_type, camera_id = camera_info
        print(f"\n🔌 测试{camera_type}摄像头连接...")
        
        # 仅支持CSI摄像头
        try:
            picam2 = Picamera2()
            config = picam2.create_still_configuration()
            picam2.configure(config)
            picam2.start()
            
            # 获取摄像头属性
            sensor_modes = picam2.sensor_modes
            main_stream = config["main"]
            width = main_stream["size"][0]
            height = main_stream["size"][1]
            
            self.log_result(
                "CSI摄像头连接", 
                True, 
                f"CSI摄像头连接成功",
                f"分辨率: {width}x{height}, 支持模式: {len(sensor_modes)}"
            )
            
            return ("CSI", picam2)
            
        except Exception as e:
            self.log_result("CSI摄像头连接", False, f"无法连接CSI摄像头: {str(e)}")
            return None
    
    def test_camera_settings(self, camera_obj):
        """测试摄像头设置"""
        if camera_obj is None:
            return
            
        camera_type, cam = camera_obj
        print(f"\n⚙️ 测试{camera_type}摄像头设置...")
        
        # 仅支持CSI摄像头
        try:
            # 测试CSI摄像头配置
            config = cam.create_still_configuration(main={"size": (1280, 1024)})
            cam.configure(config)
            
            # 获取实际配置
            main_stream = config["main"]
            actual_width = main_stream["size"][0]
            actual_height = main_stream["size"][1]
            
            self.log_result(
                "CSI分辨率设置", 
                True, 
                f"分辨率设置成功: {actual_width}x{actual_height}"
            )
            
            # 测试CSI摄像头控制参数
            controls_tests = [
                ("Brightness", 0.5, "亮度"),
                ("Contrast", 1.0, "对比度"),
                ("Saturation", 1.0, "饱和度"),
            ]
            
            for control, value, name in controls_tests:
                try:
                    cam.set_controls({control: value})
                    self.log_result(f"CSI{name}设置", True, f"{name}: {value}")
                except Exception as e:
                    self.log_result(f"CSI{name}设置", False, f"{name}设置失败: {str(e)}")
                    
        except Exception as e:
            self.log_result("CSI摄像头设置", False, f"CSI摄像头设置失败: {str(e)}")
    
    def test_image_capture(self, camera_obj):
        """测试图像采集"""
        if camera_obj is None:
            return False
            
        camera_type, cam = camera_obj
        print(f"\n📸 测试{camera_type}图像采集...")
        
        # 仅支持CSI摄像头
        try:
            # CSI摄像头图像采集
            frame = cam.capture_array()
            
            if frame is None:
                self.log_result("CSI图像采集", False, "采集到空图像")
                return False
            
            # 检查图像属性
            height, width = frame.shape[:2]
            channels = frame.shape[2] if len(frame.shape) == 3 else 1
            
            self.log_result(
                "CSI图像采集", 
                True, 
                f"图像采集成功",
                f"尺寸: {width}x{height}, 通道数: {channels}"
            )
            
            # 保存测试图像
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            image_path = os.path.join(self.test_images_dir, f"csi_test_capture_{timestamp}.jpg")
            
            # 使用picamera2直接保存图像
            cam.capture_file(image_path)
            if os.path.exists(image_path):
                self.log_result("CSI图像保存", True, f"测试图像已保存: {image_path}")
                return True
            else:
                self.log_result("CSI图像保存", False, "图像保存失败")
                return False
                
        except Exception as e:
            self.log_result("CSI图像采集", False, f"CSI图像采集失败: {str(e)}")
            return False
    
    def test_image_quality(self, camera_obj):
        """测试图像质量 - 使用numpy进行基本分析"""
        if camera_obj is None:
            return
            
        camera_type, cam = camera_obj
        print(f"\n🔍 测试{camera_type}图像质量...")
        
        # 采集多帧图像进行质量分析
        frames = []
        
        try:
            for i in range(10):
                frame = cam.capture_array()
                if frame is not None:
                    frames.append(frame)
                time.sleep(0.1)
        except Exception as e:
            self.log_result("CSI图像质量", False, f"CSI图像采集失败: {str(e)}")
            return
        
        if not frames:
            self.log_result("CSI图像质量", False, "无法采集到图像进行质量分析")
            return
        
        # 分析图像质量
        avg_frame = np.mean(frames, axis=0).astype(np.uint8)
        
        # 使用numpy进行基本图像分析
        try:
            # 转换为灰度图 (简单平均RGB通道)
            if len(avg_frame.shape) == 3:
                gray = np.mean(avg_frame, axis=2).astype(np.uint8)
            else:
                gray = avg_frame
                
            mean_brightness = np.mean(gray)
            std_brightness = np.std(gray)
            
            # 检测是否过暗或过亮
            if mean_brightness < 50:
                self.log_result("CSI亮度检查", False, f"图像过暗: {mean_brightness:.1f}")
            elif mean_brightness > 200:
                self.log_result("CSI亮度检查", False, f"图像过亮: {mean_brightness:.1f}")
            else:
                self.log_result("CSI亮度检查", True, f"亮度正常: {mean_brightness:.1f}")
            
            # 检查对比度
            if std_brightness < 20:
                self.log_result("CSI对比度检查", False, f"对比度过低: {std_brightness:.1f}")
            else:
                self.log_result("CSI对比度检查", True, f"对比度正常: {std_brightness:.1f}")
                
            # 使用numpy计算简单的清晰度指标 (像素梯度)
            # 计算水平和垂直方向的梯度
            dx = np.diff(gray, axis=1)
            dy = np.diff(gray, axis=0)
            gradient_magnitude = np.sqrt(dx**2 + dy**2)
            clarity = np.mean(gradient_magnitude)
            
            if clarity < 10:
                self.log_result("CSI清晰度检查", False, f"图像模糊: {clarity:.1f}")
            else:
                self.log_result("CSI清晰度检查", True, f"图像清晰: {clarity:.1f}")
                
        except Exception as e:
            self.log_result("CSI图像质量分析", False, f"图像质量分析失败: {str(e)}")
    
    def test_capture_speed(self, camera_obj):
        """测试采集速度"""
        if camera_obj is None:
            return 0
            
        camera_type, cam = camera_obj
        print(f"\n⚡ 测试{camera_type}采集速度...")
        
        # 测试连续采集速度
        start_time = time.time()
        frame_count = 0
        test_duration = 5  # 测试5秒
        
        # 仅支持CSI摄像头
        try:
            while time.time() - start_time < test_duration:
                frame = cam.capture_array()
                if frame is not None:
                    frame_count += 1
        except Exception as e:
            self.log_result(f"{camera_type}采集速度", False, f"CSI速度测试失败: {str(e)}")
            return 0
        
        actual_duration = time.time() - start_time
        fps = frame_count / actual_duration if actual_duration > 0 else 0
        
        if fps >= 20:
            self.log_result(f"{camera_type}采集速度", True, f"采集速度: {fps:.1f} FPS")
        else:
            self.log_result(f"{camera_type}采集速度", False, f"采集速度过低: {fps:.1f} FPS")
        
        return fps
    
    def generate_report(self):
        """生成测试报告"""
        print("\n📊 生成测试报告...")
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        report_path = os.path.join(self.test_images_dir, "camera_test_report.txt")
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("摄像头功能测试报告\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"总测试数: {total_tests}\n")
            f.write(f"通过测试: {passed_tests}\n")
            f.write(f"失败测试: {failed_tests}\n")
            f.write(f"通过率: {(passed_tests/total_tests)*100:.1f}%\n\n")
            
            f.write("详细测试结果:\n")
            f.write("-" * 30 + "\n")
            
            for result in self.test_results:
                status = "✅ 通过" if result['success'] else "❌ 失败"
                f.write(f"{status} {result['test']}: {result['message']}\n")
                if result['details']:
                    f.write(f"   详情: {result['details']}\n")
                f.write(f"   时间: {result['timestamp']}\n\n")
        
        print(f"📄 测试报告已保存: {report_path}")
        print(f"\n🎯 测试总结: {passed_tests}/{total_tests} 通过 ({(passed_tests/total_tests)*100:.1f}%)")
        
        return passed_tests == total_tests
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始摄像头功能自动化测试...")
        print("=" * 50)
        
        # 设置测试环境
        self.setup_test_environment()
        
        # 检测摄像头设备
        camera_info = self.test_camera_detection()
        if camera_info is None:
            print("\n❌ 摄像头设备检测失败，无法继续测试")
            self.generate_report()
            return False
        
        # 连接摄像头
        camera_obj = self.test_camera_connection(camera_info)
        if camera_obj is None:
            print("\n❌ 摄像头连接失败，无法继续测试")
            self.generate_report()
            return False
        
        try:
            # 运行各项测试
            self.test_camera_settings(camera_obj)
            
            if self.test_image_capture(camera_obj):
                self.test_image_quality(camera_obj)
                self.test_capture_speed(camera_obj)
            
        finally:
            # 释放摄像头资源
            if camera_obj:
                camera_type, cam = camera_obj
                try:
                    cam.stop()
                    cam.close()
                except Exception as e:
                    print(f"⚠️  释放摄像头资源时出错: {str(e)}")
        
        # 生成测试报告
        return self.generate_report()

def main():
    """主函数"""
    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        print("摄像头功能自动化测试脚本")
        print("用法: python auto_camera_test.py")
        print("\n测试项目:")
        print("- 摄像头设备检测")
        print("- 摄像头连接测试")
        print("- 摄像头设置测试")
        print("- 图像采集测试")
        print("- 图像质量分析")
        print("- 采集速度测试")
        return
    
    tester = CameraTest()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 所有摄像头测试通过！")
        sys.exit(0)
    else:
        print("\n⚠️  部分摄像头测试失败，请检查测试报告")
        sys.exit(1)

if __name__ == "__main__":
    main()