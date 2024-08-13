from odoo import models, fields, api
import logging
import requests

_logger = logging.getLogger(__name__)

class ZaloChatMessage(models.TransientModel):
    _name = 'zalo_message.zalo.chat.message'
    _description = 'Gửi tin nhắn Zalo Chat'

    # Trường lưu trữ ID Zalo của người nhận
    zalo_user_id_fl = fields.Char(string='Zalo ID', required=True)
    # Trường lưu trữ chủ đề của tin nhắn
    message_subject = fields.Char(string='Chủ đề tin nhắn', required=True)
    # Trường lưu trữ nội dung tin nhắn
    message_content = fields.Text(string='Nội dung tin nhắn', required=True)
    # Trường lưu trữ ngày giờ gửi tin nhắn
    send_date = fields.Datetime(string="Ngày gửi", readonly=True)
    # Trường lưu trữ trạng thái gửi tin nhắn
    status = fields.Selection([
        ('draft', 'Bản nháp'),
        ('sent', 'Đã gửi'),
        ('error', 'Lỗi')
    ], string='Trạng thái', readonly=True, default='draft')
    # Trường lưu trữ phản hồi từ API sau khi gửi tin nhắn
    response_message = fields.Text(string='Thông điệp phản hồi')

    @api.model
    def default_get(self, fields_list):
        """
        Thiết lập giá trị mặc định cho các trường trong form view dựa trên context.
        - Lấy ID của record hiện tại từ context.
        - Cập nhật giá trị trường zalo_user_id_fl từ record contact.
        """
        res = super(ZaloChatMessage, self).default_get(fields_list)
        # Lấy ID của record hiện tại từ context
        active_id = self.env.context.get('active_id')
        if active_id:
            # Lấy record contact từ ID
            contact = self.env['res.partner'].browse(active_id)
            # Cập nhật giá trị trường zalo_user_id_fl từ record contact
            res['zalo_user_id_fl'] = contact.zalo_user_id_fl
        return res

    def send_zalo_message(self):
        """
        Gửi tin nhắn Zalo đến người dùng với thông tin từ trường trong form.
        - Lấy access token từ cấu hình hệ thống.
        - Tạo payload và gửi yêu cầu đến API Zalo.
        - Xử lý phản hồi từ API và cập nhật trạng thái.
        """
        for record in self:
            # Lấy access token từ cấu hình hệ thống
            access_token = self.env['ir.config_parameter'].sudo().get_param('zalo.access_token')
            url = "https://openapi.zalo.me/v3.0/oa/message/cs"
            headers = {
                'Content-Type': 'application/json',
                'access_token': access_token
            }

            # Tạo payload cho yêu cầu gửi tin nhắn
            payload = {
                "recipient": {
                    "user_id": record.zalo_user_id_fl
                },
                "message": {
                    "text": record.message_content
                }
            }

            try:
                # Gửi yêu cầu POST đến API Zalo
                response = requests.post(url, json=payload, headers=headers)
                response_json = response.json()
                _logger.debug("API response: %s", response_json)

                # Xử lý phản hồi từ API
                error_code = response_json.get('error', None)
                if response.status_code == 200 and error_code == 0:
                    response_message = response_json.get('message', 'Tin nhắn đã được gửi thành công.')
                    record.status = 'sent'
                    notification_type = 'success'
                    notification_message = 'Tin nhắn Zalo đã được gửi thành công.'
                else:
                    if error_code in [10, 11]:  # Xử lý lỗi access_token không hợp lệ hoặc hết hạn
                        response_message = response_json.get('message', 'Token truy cập không hợp lệ hoặc đã hết hạn.')
                        # Cập nhật token
                        token_updater = self.env['res.config.settings']
                        token_updater._update_access_token()  # Gọi hàm cập nhật access_token
                        record.status = 'error'
                        notification_type = 'danger'
                        notification_message = f"Gửi tin nhắn thất bại: {response_message}. Token đã được làm mới."
                    else:
                        error_message = response_json.get('message', 'Lỗi không xác định.')
                        response_message = f"Lỗi: {error_message}"
                        record.status = 'error'
                        notification_type = 'danger'
                        notification_message = f"Gửi tin nhắn thất bại: {error_message}"
            except requests.RequestException as e:
                # Xử lý lỗi khi gửi yêu cầu
                response_message = f"Yêu cầu lỗi: {str(e)}"
                record.status = 'error'
                _logger.exception("Gửi tin nhắn Zalo thất bại: %s", e)
                notification_type = 'danger'
                notification_message = f"Đã xảy ra lỗi khi gửi yêu cầu: {str(e)}"
            except Exception as e:
                # Xử lý lỗi không xác định
                response_message = f"Exception: {str(e)}"
                record.status = 'error'
                _logger.exception("Gửi tin nhắn Zalo thất bại: %s", e)
                notification_type = 'danger'
                notification_message = f"Đã xảy ra lỗi: {str(e)}"

            # Cập nhật phản hồi và ngày gửi
            record.response_message = response_message
            record.send_date = fields.Datetime.now()
            _logger.info("Tin nhắn Zalo đã được gửi. Phản hồi: %s", response_message)

            # Lưu tin nhắn vào lịch sử
            self.env['zalo_message.history'].create({
                'zalo_user_id_fl': record.zalo_user_id_fl,
                'message_subject': record.message_subject,
                'message_content': record.message_content,
                'send_date': record.send_date,
                'status': record.status,
                'response_message': record.response_message
            })

            # Hiển thị thông báo cho người dùng
            result = {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Thông báo',
                    'message': notification_message,
                    'type': notification_type,
                    'sticky': False if notification_type == 'success' else True,
                }
            }

        return result

class ZaloChatMessageHistory(models.Model):
    _name = 'zalo_message.history'
    _description = 'Lịch sử tin nhắn Zalo Chat'

    # Trường lưu trữ ID Zalo của người nhận
    zalo_user_id_fl = fields.Char(string='Zalo ID', required=True)
    # Trường lưu trữ chủ đề của tin nhắn
    message_subject = fields.Char(string='Chủ đề tin nhắn', required=True)
    # Trường lưu trữ nội dung tin nhắn
    message_content = fields.Text(string='Nội dung tin nhắn', required=True)
    # Trường lưu trữ các tệp đính kèm liên quan đến tin nhắn
    attachment_ids = fields.Many2many('ir.attachment', string='Tệp đính kèm')
    # Trường lưu trữ ngày giờ gửi tin nhắn
    send_date = fields.Datetime(string="Ngày gửi", readonly=True)
    # Trường lưu trữ trạng thái gửi tin nhắn
    status = fields.Selection([
        ('draft', 'Bản nháp'),
        ('sent', 'Đã gửi'),
        ('error', 'Lỗi')
    ], string='Trạng thái', readonly=True)
    # Trường lưu trữ phản hồi từ API sau khi gửi tin nhắn
    response_message = fields.Text(string='Thông điệp phản hồi')
