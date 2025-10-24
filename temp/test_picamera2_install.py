import sys
try:
    import picamera2
    print("Picamera2 installed")
    if hasattr(picamera2, "__version__"):
        print(f"Version: {picamera2.__version__}")
    sys.exit(0)
except ImportError:
    print("Picamera2 not installed")
    sys.exit(1)