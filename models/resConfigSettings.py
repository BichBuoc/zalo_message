import requests
import logging
from datetime import datetime, timedelta
from odoo import fields, models, api, exceptions

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Cấu hình mức độ ghi nhật ký
    logging.basicConfig(level=logging.INFO)
    _logger = logging.getLogger(__name__)

    # Định nghĩa các trường lưu trữ thông tin OAuth của Zalo
    zalo_app_id = fields.Char(string="Zalo App ID", config_parameter='zalo.app_id')
    zalo_secret_key = fields.Char(string="Zalo Secret Key", config_parameter='zalo.secret_key')
    zalo_refresh_token = fields.Char(string="Zalo Refresh Token", config_parameter='zalo.refresh_token')
    zalo_access_token = fields.Char(string="Zalo Access Token", config_parameter='zalo.access_token')
    zalo_token_expiry = fields.Datetime(string="Access Token Expiry Time", config_parameter='zalo.token_expiry')

    @api.model
    def set_values(self):
        # Gọi phương thức cha để lưu các giá trị cấu hình
        super(ResConfigSettings, self).set_values()
        
        try:
            # Lưu từng tham số cấu hình bằng hệ thống cấu hình của Odoo
            self.env['ir.config_parameter'].sudo().set_param('zalo.app_id', self.zalo_app_id)
            self.env['ir.config_parameter'].sudo().set_param('zalo.secret_key', self.zalo_secret_key)
            self.env['ir.config_parameter'].sudo().set_param('zalo.refresh_token', self.zalo_refresh_token)
            self.env['ir.config_parameter'].sudo().set_param('zalo.access_token', self.zalo_access_token)
            self.env['ir.config_parameter'].sudo().set_param('zalo.token_expiry', self.zalo_token_expiry)

            # In ra các giá trị đã lưu vào nhật ký
            saved_zalo_app_id = self.env['ir.config_parameter'].sudo().get_param('zalo.app_id')
            saved_zalo_secret_key = self.env['ir.config_parameter'].sudo().get_param('zalo.secret_key')
            saved_zalo_refresh_token = self.env['ir.config_parameter'].sudo().get_param('zalo.refresh_token')
            saved_zalo_access_token = self.env['ir.config_parameter'].sudo().get_param('zalo.access_token')
            saved_zalo_token_expiry = self.env['ir.config_parameter'].sudo().get_param('zalo.token_expiry')

            # Ghi các giá trị vào nhật ký
            self._logger.info(
                f"Zalo App ID: {saved_zalo_app_id}\n"
                f"Zalo Secret Key: {saved_zalo_secret_key}\n"
                f"Zalo Refresh Token: {saved_zalo_refresh_token}\n"
                f"Zalo Access Token: {saved_zalo_access_token}\n"
                f"Zalo Token Expiry: {saved_zalo_token_expiry}"
            )
        except Exception as e:
            # Xử lý lỗi và ghi lỗi
            raise exceptions.UserError(f"An error occurred while saving the configuration: {str(e)}")

    # Định nghĩa phương thức để kiểm tra và cập nhật access_token
    def check_and_update_token(self):
        try:
            # Lấy thời gian hết hạn token từ cấu hình
            token_expiry_time_str = self.env['ir.config_parameter'].sudo().get_param('zalo.token_expiry')

            if token_expiry_time_str:
                self._logger.info("Token expiry time found: %s", token_expiry_time_str)

                # Chuyển đổi chuỗi thời gian thành đối tượng datetime
                token_expiry_time = datetime.strptime(token_expiry_time_str, '%Y-%m-%d %H:%M:%S')
                current_time = datetime.utcnow()
                self._logger.info("Current time: %s", current_time)
    
                # Tính thời gian còn lại
                time_remaining = token_expiry_time - current_time

                # Kiểm tra nếu thời gian còn lại ít hơn hoặc bằng 30 phút
                if time_remaining <= timedelta(minutes=30):
                    new_access_token = self.update_access_token()
                    self._logger.info("Access token updated due to expiry.")
                    return True, f"Access token đã được cập nhật mới: {new_access_token}"
                else:
                    self._logger.info("Token is still valid. Time until expiry: %s", time_remaining.total_seconds())
                    return False, f"Access token vẫn còn hiệu lực. Thời gian còn lại: {time_remaining}."
            else:
                self._logger.info("Token expiry time not found.")
                return False, "Thời gian hết hạn của token không tìm thấy."

        except ValueError as date_err:
            # Xử lý lỗi phân tích ngày tháng và ghi lỗi
            self._logger.error("Date parsing error: %s", date_err)
            raise exceptions.UserError(f"Lỗi phân tích ngày tháng: {date_err}")

        except Exception as e:
            # Xử lý lỗi chung và ghi lỗi
            self._logger.error("An error occurred while checking or updating the token: %s", e)
            raise exceptions.UserError(f"Có lỗi xảy ra trong khi kiểm tra hoặc cập nhật token: {str(e)}")

    # Hàm để cập nhật access_token
    def update_access_token(self):
        # Định nghĩa URL và headers cho yêu cầu POST tới API Zalo
        url = 'https://oauth.zaloapp.com/v4/oa/access_token'
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'secret_key': self.env['ir.config_parameter'].sudo().get_param('zalo.secret_key')  # Secret key để xác thực với API Zalo
        }
        # Dữ liệu cần thiết để gửi yêu cầu làm mới access_token
        data = {
            'refresh_token': self.env['ir.config_parameter'].sudo().get_param('zalo.refresh_token'),
            'app_id': self.env['ir.config_parameter'].sudo().get_param('zalo.app_id'),
            'grant_type': 'refresh_token'
        }
        try:
            # Thực hiện yêu cầu POST tới API Zalo để làm mới access_token
            response = requests.post(url, headers=headers, data=data)
            response.raise_for_status()  # Kiểm tra lỗi HTTP
        except requests.exceptions.HTTPError as http_err:
            # Xử lý lỗi HTTP và hiển thị thông báo lỗi thân thiện
            raise exceptions.UserError(f"Lỗi HTTP: {http_err}")
        except requests.exceptions.RequestException as req_err:
            # Xử lý lỗi yêu cầu và hiển thị thông báo lỗi thân thiện
            raise exceptions.UserError(f"Lỗi trong quá trình yêu cầu: {req_err}")

        try:
            # Phân tích cú pháp phản hồi JSON từ API
            result = response.json()
            if 'access_token' in result:
                # Nếu access_token tồn tại trong phản hồi, cập nhật các token và thời gian hết hạn
                new_access_token = result['access_token']
                new_refresh_token = result.get('refresh_token', self.env['ir.config_parameter'].sudo().get_param('zalo.refresh_token'))
                # Tính thời gian hết hạn mới 90,000 giây (25 giờ) kể từ hiện tại  timedelta(seconds=90000)
                new_expires_in = int(result['expires_in'])
                new_expiry_time = datetime.utcnow() + timedelta(seconds=new_expires_in)

                # Lưu trữ các token và thời gian hết hạn mới vào hệ thống cấu hình của Odoo
                self.env['ir.config_parameter'].sudo().set_param('zalo.access_token', new_access_token)
                self.env['ir.config_parameter'].sudo().set_param('zalo.refresh_token', new_refresh_token)
                # Định dạng thời gian hết hạn trước khi lưu
                formatted_expiry_time = new_expiry_time.strftime('%Y-%m-%d %H:%M:%S')
                self.env['ir.config_parameter'].sudo().set_param('zalo.token_expiry', formatted_expiry_time)
                
                return new_access_token
            else:
                # Nếu không tìm thấy access_token trong phản hồi, hiển thị thông báo lỗi
                raise exceptions.UserError("Không tìm thấy access token trong phản hồi. Vui lòng kiểm tra cấu hình Zalo OAuth.")
        except ValueError as json_err:
            # Xử lý lỗi phân tích JSON và hiển thị thông báo lỗi thân thiện
            raise exceptions.UserError(f"Lỗi phân tích JSON: {json_err}")

    def action_send_email(self):
        # Ghi log để kiểm tra quá trình gửi email
        _logger = logging.getLogger(__name__)
        
        # Import và sử dụng phương thức từ email_template
        EmailTemplate = self.env['email.template']
        
        for partner in self:
            email_to = partner.email
            partner_name = partner.name

            if email_to:  # Chỉ gửi email nếu có địa chỉ email
                subject, body_html = EmailTemplate.get_email_template(partner_name)
                
                email_values = {
                    'subject': subject,
                    'email_to': email_to,
                    'body_html': body_html,
                }

                # Gửi email
                mail = self.env['mail.mail'].create(email_values)
                mail.send()
                
                _logger.info(f"Email sent to {email_to} with subject: {subject}")
