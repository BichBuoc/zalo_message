/** @odoo-module **/
import { Chatter } from "@mail/core/web/chatter";

import { AttachmentList } from "@mail/core/common/attachment_list";
import { testComposer } from "./testComposer";
import { Thread } from "@mail/core/common/thread";
import { Activity } from "@mail/core/web/activity";
import { SuggestedRecipientsList } from "@mail/core/web/suggested_recipient_list";
import { FollowerList } from "@mail/core/web/follower_list";
import { SearchMessagesPanel } from "@mail/core/common/search_messages_panel";

import { Dropdown } from "@web/core/dropdown/dropdown";
import { _t } from "@web/core/l10n/translation";
import { FileUploader } from "@web/views/fields/file_handler";

export class testSendMail extends Chatter {
  setup() {
    super.setup();
  }
}
testSendMail.components = {
  ...Chatter.components,
  Composer:testComposer,
};
