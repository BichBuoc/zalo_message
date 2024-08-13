from odoo import models, fields, api, _
import logging
import requests
import json

_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = 'res.partner'

    zalo_user_id_fl = fields.Char(string='Zalo User ID')

    def action_send_email(self):
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

                try:
                    mail = self.env['mail.mail'].create(email_values)
                    mail.send()
                    _logger.info(f"Email sent to {email_to} with subject: {subject}")
                except Exception as e:
                    _logger.error(f"Failed to send email to {email_to}. Error: {e}")

    # Hàm gọi để hoạt động nút thao tác zalo
    def action_handle_zalo_buttons(self):
        self.ensure_one()  # Đảm bảo rằng chỉ có một record được xử lý

        if self.zalo_user_id_fl:
            # Nếu có zalo_user_id_fl, gọi hàm mở popup chat
            return self.action_open_zalo_chat_popup()
        else:
            # Nếu không có zalo_user_id_fl, gọi hàm gửi mời quan tâm
            return self.action_zalo_invite()

    def action_open_zalo_chat_popup(self):
        # Định nghĩa hành động để mở popup chat Zalo
        try:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Zalo Chat'),
                'res_model': 'zalo_message.zalo.chat.message',  # Thay thế bằng model bạn sử dụng cho popup Zalo Chat
                'view_mode': 'form',
                'view_id': self.env.ref('zalo_message.view_zalo_chat_popup_form').id,
                'target': 'new',
                'context': {'default_partner_id': self.id}
            }
        except Exception as e:
            _logger.error(f"Error opening Zalo chat popup: {e}")

    def action_zalo_invite(self):
        # Định nghĩa hành động để gửi mời quan tâm
        try:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Mời quan tâm zalo'),
                'res_model': 'zalo_message.zalo.invite',  # Thay thế bằng model bạn sử dụng để gửi mời Zalo
                'view_mode': 'form',
                'view_id': self.env.ref('zalo_message.view_zalo_invite_form').id,
                'target': 'new',
                'context': {'default_partner_id': self.id}
            }
        except Exception as e:
            _logger.error(f"Error opening Zalo invite form: {e}")

    @api.model
    def update_zalo_user_ids(self):
        _logger.info("Starting to update Zalo User IDs...")

        # Lấy danh sách các Zalo User IDs từ API
        try:
            user_id_list = self._get_zalo_user_ids()
        except Exception as e:
            _logger.error(f"Error fetching Zalo User IDs: {e}")
            return
        
        # Chia danh sách thành các lô nhỏ hơn để xử lý
        batch_size = 2  # Số lượng user ID mỗi lần xử lý
        for i in range(0, len(user_id_list), batch_size):
            batch_user_ids = user_id_list[i:i + batch_size]

            try:
                user_info_list = self._get_zalo_user_details(batch_user_ids)
            except Exception as e:
                _logger.error(f"Error fetching Zalo User details: {e}")
                continue

            for user_info in user_info_list:
                phone_number = user_info.get('shared_info', {}).get('phone')
                user_id = user_info.get('user_id')
                display_name = user_info.get('display_name', 'Unknown')

                _logger.info(f"Current User Info: Phone Number: {phone_number}, User ID: {user_id}, Display Name: {display_name}")

                if user_id:
                    try:
                        # Kiểm tra xem đã có contact nào với user_id này chưa
                        contact_with_user_id = self.env['res.partner'].search([('zalo_user_id_fl', '=', user_id)], limit=1)
                        if contact_with_user_id:
                            # Nếu đã có contact với user_id, kiểm tra xem có cần cập nhật số điện thoại không
                            if phone_number and not contact_with_user_id.phone:
                                contact_with_user_id.write({'phone': phone_number})
                            else:
                                _logger.info(f"Contact with Zalo User ID {user_id} already exists and has phone number. No update needed.")
                            continue

                        if phone_number:
                            # Định dạng lại tất cả các số điện thoại trong Odoo Contacts để chuẩn bị so sánh
                            contacts = self.env['res.partner'].search([('zalo_user_id_fl', '=', False)])
                            for contact in contacts:
                                formatted_phone_contact = self.format_phone_number(contact.phone)
                                formatted_phone_zalo = self.format_phone_number(phone_number)

                                # Kiểm tra xem có contact nào với số điện thoại này mà chưa có zalo_user_id_fl
                                if formatted_phone_contact and formatted_phone_contact == formatted_phone_zalo:
                                    contact.write({'zalo_user_id_fl': user_id})
                                    break
                            else:
                                # Nếu không có contact nào với số điện thoại này, tạo contact mới
                                new_contact = self.env['res.partner'].create({
                                    'name': display_name,
                                    'phone': phone_number,
                                    'zalo_user_id_fl': user_id
                                })
                                _logger.info(f"Created new contact with ID: {new_contact.id}")
                        else:
                            # Nếu không có số điện thoại, tạo contact mới chỉ với user_id và display_name
                            new_contact = self.env['res.partner'].create({
                                'name': display_name,
                                'zalo_user_id_fl': user_id
                            })
                            _logger.info(f"Created new contact with ID: {new_contact.id} without phone number")
                    except Exception as e:
                        _logger.error(f"Error processing Zalo user info: {e}")

        _logger.info("Finished updating Zalo User IDs.")

    def _get_zalo_user_ids(self, last_interaction_period='L7D'):
        access_token = self.env['ir.config_parameter'].sudo().get_param('zalo.access_token')
        url = 'https://openapi.zalo.me/v3.0/oa/user/getlist'
        headers = {'access_token': access_token}
        all_user_ids = []
        offset = 0
        count = 50  # Số lượng user ID mỗi lần yêu cầu

        while True:
            params = {
                'data': json.dumps({
                    'offset': offset,
                    'count': count,
                    'last_interaction_period': last_interaction_period,
                    'is_follower': 'true'
                })
            }

            try:
                response = requests.get(url, headers=headers, params=params)
                response.raise_for_status()
                data = response.json()
                users = data.get('data', {}).get('users', [])

                # Nếu không có dữ liệu, kết thúc vòng lặp
                if not users:
                    break

                # Lấy danh sách user IDs từ phản hồi
                current_user_ids = [user['user_id'] for user in users]
                all_user_ids.extend(current_user_ids)
                
                # Cập nhật offset để lấy dữ liệu tiếp theo
                offset += count

                # Nếu số lượng users nhận được ít hơn count, dừng vòng lặp
                if len(users) < count:
                    break

            except requests.exceptions.RequestException as e:
                _logger.error(f'Error fetching Zalo User IDs: {e}')
                break

        return all_user_ids


    # Hàm lấy chi tiết thông tin theo user id được lấy ra từ danh sách
    def _get_zalo_user_details(self, user_ids):
        access_token = self.env['ir.config_parameter'].sudo().get_param('zalo.access_token')
        url = 'https://openapi.zalo.me/v3.0/oa/user/detail'
        headers = {
            'access_token': access_token
        }
        user_info_list = []
        
        for user_id in user_ids:
            params = {
                'data': json.dumps({"user_id": user_id})
            }
            try:
                response = requests.get(url, headers=headers, params=params)
                response.raise_for_status()  # Kiểm tra phản hồi HTTP
                data = response.json()
                _logger.info(f'API Response for User ID {user_id} Details: {json.dumps(data, indent=4)}')
                user_info = data.get('data', {})
                if user_info:
                    user_info_list.append(user_info)
            except requests.exceptions.RequestException as e:
                _logger.error(f'Error fetching details for Zalo User ID {user_id}: {e}')
        
        return user_info_list

    def format_phone_number(self, phone_number):
        """Chuyển đổi số điện thoại từ dạng +84 384 353 091 thành 84384353091 và trả về dạng số nguyên."""
        # Đảm bảo số điện thoại là chuỗi
        phone_number = str(phone_number)
        # Loại bỏ dấu '+' và khoảng trắng
        formatted_number = phone_number.replace('+', '').replace(' ', '')
        
        # Chuyển đổi sang số nguyên
        try:
            formatted_number_int = int(formatted_number)
            return formatted_number_int
        except ValueError:
            _logger.error(f"Unable to convert phone number to int: {formatted_number}")
            return None
