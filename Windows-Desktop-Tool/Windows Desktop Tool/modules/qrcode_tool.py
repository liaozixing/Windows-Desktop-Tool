import qrcode
from PIL import Image
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt

def generate_qr_image(data: str, size: int = 10, border: int = 4) -> QPixmap:
    """
    生成二维码图片
    :param data: 文本内容
    :param size: 盒子大小
    :param border: 边框宽度
    :return: QPixmap 对象
    """
    if not data:
        return None
        
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=size,
            border=border,
        )
        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert PIL Image to QPixmap
        img = img.convert("RGBA")
        data = img.tobytes("raw", "RGBA")
        qim = QImage(data, img.size[0], img.size[1], QImage.Format_RGBA8888)
        pixmap = QPixmap.fromImage(qim)
        return pixmap
    except Exception as e:
        print(f"Generate QR Error: {e}")
        return None
