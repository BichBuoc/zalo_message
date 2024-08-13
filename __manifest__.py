{
    'name': 'Zalo Message',
    'version': '1.0',
    'category': 'Communication',
    'summary': 'Send messages to Zalo users from Odoo',
    'description': 'Module to send messages to Zalo users using Zalo OA API.',
    'depends': ["base", "product", "website", "account", "contacts"],
    'data': [
        'security/ir.model.access.csv',
        'views/zalo_message_view.xml',
        'views/res_config_settings_views.xml',
        'data/scheduled_actions.xml',
        # 'data/email_template.xml',
        'views/res_partner_view.xml',
        'views/zalo_chat_popup_view.xml',
        'actions/zalo_chat_action.xml',
        'views/zalo_invite.xml',
        'actions/zalo_invite.xml',
        'views/zalo_message_history_views.xml',
        # 'data/zalo_message_data.xml',
        'data/scheduled_action_update_zalo_user_ids.xml',
    ],
    'installable': True,
    'application': True,

#     'assets': {
#     'web.assets_backend': [
#         'zalo_message/static/src/js/mail_composer.js',
#     ],
#     'web.assets_qweb': [
#         'zalo_message/static/src/xml/mail_composer_template.xml',
#     ],
# },

}
