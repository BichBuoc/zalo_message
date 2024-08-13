from odoo import models

class EmailTemplate(models.AbstractModel):
    _name = 'email.template'

    def get_email_template(self, partner_name):
        # Đường dẫn ảnh QR
        qr_image_url = 'https://page-photo-qr.zdn.vn/1722218151/4d16fcddec9805c65c89.jpg'
        
        subject = 'Khám phá Zalo OA của chúng tôi và không bỏ lỡ cơ hội!'
        body_html = f'''
            <p>Kính gửi {partner_name},</p>
            <p>Chúng tôi rất vui mừng giới thiệu đến bạn Zalo Official Account (OA) của chúng tôi - nơi bạn sẽ tìm thấy những thông tin thú vị và cập nhật mới nhất.</p>
            <p>Nhấp vào liên kết dưới đây để trở thành người đầu tiên nhận được những ưu đãi đặc biệt và thông tin hữu ích:</p>
            <p><a href="https://zalo.me/237403422853377668" target="_blank" style="color: #007bff; font-weight: bold;">Khám phá ngay Zalo OA của chúng tôi!</a></p>
            <p>Hoặc quét mã QR bên dưới để tham gia nhanh chóng:</p>
            <p><img src="{qr_image_url}" alt="QR Code" style="max-width: 200px; display: block; margin: 0 auto;"/></p>
            <p>Chúng tôi rất mong được chào đón bạn!</p>
            <p>Trân trọng,</p>
            <p>Đội ngũ của chúng tôi</p>
        '''
        return subject, body_html
