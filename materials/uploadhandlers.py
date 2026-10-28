"""upload handler ที่ตัดไฟล์เกินขนาดตั้งแต่ตอนรับ (ตั้งไว้หน้าสุดใน FILE_UPLOAD_HANDLERS)"""
from django.core.files.uploadhandler import FileUploadHandler, SkipFile

from .models import max_upload_bytes


class MaxSizeUploadHandler(FileUploadHandler):
    """ข้ามไฟล์ทันทีที่รับเกิน max_upload_bytes() ไม่เก็บลงหน่วยความจำหรือ temp file ต่อ

    ไฟล์ที่ถูกข้ามจะไม่อยู่ใน request.FILES จึงตั้ง request.upload_too_large ให้ view
    แจ้งผู้ใช้ว่าไฟล์ใหญ่เกิน ส่วน byte ที่เหลือ Django ยังอ่านทิ้งจนจบ request
    เพดานขนาด request ทั้งก้อนต้องตั้งที่ web server ตอน deploy (ADR 0003)
    """

    def new_file(self, *args, **kwargs):
        super().new_file(*args, **kwargs)
        self.limit = max_upload_bytes()

    def receive_data_chunk(self, raw_data, start):
        if start + len(raw_data) > self.limit:
            self.request.upload_too_large = True
            raise SkipFile
        return raw_data

    def file_complete(self, file_size):
        return None
