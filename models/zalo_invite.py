from odoo import models, fields, api
import requests
import json
import logging

class ZaloInvite(models.TransientModel):
    _name = 'zalo_message.zalo.invite'
    _description = 'Mời Quan Tâm Zalo'

    _logger = logging.getLogger(__name__)

    # Trường nội dung tin nhắn mời, định dạng HTML
    content = fields.Html(string='Nội Dung', required=True, help='Nội dung của tin nhắn mời Zalo và email')
    # Trường liên kết URL được bao gồm trong lời mời
    link_url = fields.Char(string='Liên Kết URL', help='Liên kết URL được bao gồm trong lời mời')
    # Trường URL ảnh, ví dụ như mã QR, được bao gồm trong lời mời
    image_url = fields.Char(string='URL Ảnh', help='URL của ảnh (ví dụ: qr.jpg) được bao gồm trong lời mời')
    # Trường liên kết đến đối tác, người nhận lời mời
    partner_id = fields.Many2one('res.partner', string='Người Nhận', required=True, help='Người nhận lời mời Zalo')
    # Trường chọn email mẫu
    mail_template_id = fields.Many2one('mail.template', string='Email Mẫu', help='Chọn mẫu email để gửi')

    @api.onchange('mail_template_id')
    def _onchange_mail_template(self):
        if self.mail_template_id:
            partner_name = self.partner_id.name or 'Khách hàng'
            content = self.mail_template_id.body_html
            # Thay thế biến trong mẫu email bằng tên đối tác
            personalized_content = content.replace('{{ partner_name }}', partner_name)
            self.content = personalized_content

    @api.model
    def default_get(self, fields):
        res = super(ZaloInvite, self).default_get(fields)

        partner_id = res.get('partner_id')
        partner = self.env['res.partner'].browse(partner_id)

        if not partner.exists():
            partner = self.env['res.partner'].search([], limit=1)

        # Nếu có email mẫu được chọn, lấy nội dung của nó
        mail_template_id = res.get('mail_template_id')
        if mail_template_id:
            template = self.env['mail.template'].browse(mail_template_id)
            content = template.body_html
        else:
            # Nếu không có email mẫu được chọn, lấy mẫu email đầu tiên
            template = self.env['mail.template'].search([], limit=1)
            content = template.body_html if template else ''

        partner_name = partner.name or 'Khách hàng'
        personalized_content = content.replace('{{ partner_name }}', partner_name)

        res.update({
            'content': personalized_content,
            'partner_id': partner.id,
            'mail_template_id': template.id,
        })
        return res

    def action_send_invite_via_email(self):
        self.ensure_one()

        if not self.partner_id.email:
            raise ValueError(f'Người nhận ({self.partner_id.name}) không có email.')

        if not self.mail_template_id:
            raise ValueError('Không có mẫu email nào được chọn.')

        email_values = {
            'subject': 'Lời mời quan tâm Zalo',
            'email_to': self.partner_id.email,
            'partner_ids': [(4, self.partner_id.id)],
            'body_html': self.content,
            
        }
        # Tạo và gửi email
        mail = self.env['mail.mail'].create(email_values)
        mail.send()

    def action_send_invite_via_zalo(self):
        self.send_invite_via_zalo()

    def send_invite_via_zalo(self):
        if not self.partner_id.phone:
            raise ValueError(f'Người nhận ({self.partner_id.name}) không có số điện thoại. Không thể gửi tin nhắn Zalo.')

        partner_name = self.partner_id.name or 'Khách hàng'
        template_data = {
            "content": self.content or 'Nội dung không có sẵn',
            "link_url": self.link_url or 'Liên kết không có sẵn',
            "image_url": self.image_url or 'URL ảnh không có sẵn',
            "recipient_name": partner_name,
            "recipient_address": self.partner_id.contact_address or 'Địa chỉ không có sẵn',
            "phone_number": self.partner_id.phone or 'Số điện thoại không có sẵn',
        }

        zalo_api_url = 'https://business.openapi.zalo.me/message/template'
        access_token = self.env['ir.config_parameter'].sudo().get_param('zalo.access_token')

        if not access_token:
            raise ValueError('Token truy cập Zalo không được cấu hình. Vui lòng kiểm tra cấu hình.')

        headers = {
            'Content-Type': 'application/json',
            'access_token': access_token,
        }

        payload = {
            'phone': self.partner_id.phone,
            'template_id': '123456789',
            'template_data': template_data,
            'tracking_id': 'tracking_id'
        }   

        try:
            response = requests.post(zalo_api_url, headers=headers, data=json.dumps(payload))

            if response.status_code != 200:
                self._logger.error(f"Failed to send Zalo message. Response: {response.text}")
                raise ValueError(f'Gửi tin nhắn Zalo thất bại: {response.text}')
            else:
                self._logger.info(f"Zalo message successfully sent to {self.partner_id.phone}.")
        except requests.RequestException as e:
            self._logger.error(f"Error occurred while sending Zalo message: {str(e)}")
            raise ValueError(f'Có lỗi xảy ra khi gửi tin nhắn Zalo: {str(e)}')
