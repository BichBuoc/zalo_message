odoo.define('zalo_message.mail_composer', function (require) {
    'use strict';

    var core = require('web.core');
    var Widget = require('web.Widget');

    var MailComposer = Widget.extend({
        events: {
            'change .form-check-input': '_onCheckboxChange',
            'click .o-mail-Composer-send': '_onSendClick',
        },

        _onCheckboxChange: function (event) {
            var checkbox = $(event.currentTarget);
            if (checkbox.is(':checked')) {
                var zaloId = checkbox.data('zalo_user_id_fl');
                if (zaloId) {
                    this._selectedZaloIds.push(zaloId);
                }
            } else {
                var zaloId = checkbox.data('zalo_user_id_fl');
                var index = this._selectedZaloIds.indexOf(zaloId);
                if (index > -1) {
                    this._selectedZaloIds.splice(index, 1);
                }
            }
        },

        _onSendClick: function () {
            var messageContent = this.$('.o-mail-Composer-input').val();
            if (messageContent.trim() !== '' && this._selectedZaloIds.length > 0) {
                this._sendMessages(messageContent, this._selectedZaloIds);
            }
        },

        _sendMessages: function (messageContent, zaloIds) {
            this._rpc({
                model: 'zalo_message.zalo.chat.message',
                method: 'send_zalo_message',
                args: [messageContent, zaloIds],
            }).then(function () {
                console.log('Messages sent');
                this.$('.o-mail-Composer-input').val('');
                this._selectedZaloIds = [];
            }.bind(this));
        },

        init: function () {
            this._selectedZaloIds = [];
            this._super.apply(this, arguments);
        },
    });

    core.action_registry.add('mail_composer', MailComposer);
});
