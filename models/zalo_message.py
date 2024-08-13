import requests  # Import thư viện requests để thực hiện các yêu cầu HTTP
from odoo import models, fields, api  # Import các thành phần cần thiết từ Odoo

# Định nghĩa một lớp mới tên là ZaloMessage kế thừa từ models.Model
class ZaloMessage(models.Model):
    _name = 'zalo.message'  # Tên kỹ thuật của mô hình trong cơ sở dữ liệu Odoo
    _description = 'Tin nhắn Zalo'  # Mô tả ngắn gọn về mô hình

    # Trường lưu trữ ID người dùng Zalo để gửi tin nhắn đến, bắt buộc phải có
    user_id = fields.Char(string='User ID', required=True)
    # Trường lưu trữ nội dung tin nhắn cần gửi, bắt buộc phải có
    message_text = fields.Text(string='Nội dung tin nhắn', required=True)
    # Trường lưu trữ trạng thái của tin nhắn
    status = fields.Selection(
        [('draft', 'Bản nháp'), ('sent', 'Đã gửi'), ('error', 'Lỗi')],
        default='draft',  # Giá trị mặc định là 'Bản nháp'
        string='Trạng thái'
    )
    # Trường lưu trữ tin nhắn phản hồi từ API Zalo
    response_message = fields.Text(string='Tin nhắn phản hồi')

    # Định nghĩa phương thức send_message để gửi tin nhắn
    def send_message(self):
        # Lặp qua từng bản ghi trong mô hình
        for record in self:
            # Địa chỉ API của Zalo để gửi tin nhắn
            url = "https://openapi.zalo.me/v3.0/oa/message/cs"
            # Định nghĩa các header cho yêu cầu HTTP
            headers = {
                'Content-Type': 'application/json',  # Định dạng nội dung là JSON
                'access_token': self.env['ir.config_parameter'].sudo().get_param('zalo.access_token')  # Token truy cập để xác thực
            }
            # Định nghĩa nội dung của yêu cầu HTTP
            payload = {
                "recipient": {  # Đối tượng người nhận tin nhắn
                    "user_id": record.user_id  # ID người nhận
                },
                "message": {  # Nội dung tin nhắn
                    "text": record.message_text  # Nội dung tin nhắn
                }
            }

            try:
                # Gửi yêu cầu POST đến API Zalo
                response = requests.post(url, json=payload, headers=headers)
                # Kiểm tra nếu mã trạng thái HTTP là 200 (thành công)
                if response.status_code == 200:
                    # Cập nhật trạng thái thành 'Đã gửi' nếu gửi tin nhắn thành công
                    record.status = 'sent'
                    # Lấy tin nhắn phản hồi từ API
                    record.response_message = response.json().get('message', 'Tin nhắn đã gửi thành công.')
                else:
                    # Cập nhật trạng thái thành 'Lỗi' nếu có lỗi
                    record.status = 'error'
                    # Lưu lại tin nhắn lỗi từ API
                    record.response_message = f"Lỗi: {response.text}"
            except Exception as e:
                # Cập nhật trạng thái thành 'Lỗi' trong trường hợp gặp ngoại lệ
                record.status = 'error'
                # Lưu lại tin nhắn ngoại lệ
                record.response_message = f"Exception: {str(e)}"
