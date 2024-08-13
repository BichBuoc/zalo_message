/** @odoo-module **/
import { _t } from "@web/core/l10n/translation";
import { Composer } from "@mail/core/common/composer";
export class testComposer extends Composer {
  setup() {
    super.setup();
  }

  async sendMessage() {

    console.log("my sendMessage");

    if (this.props.composer.message) {
        this.editMessage();
        return;
    }
    await this.processMessage(async (value) => {
        const postData = {
            attachments: this.props.composer.attachments,
            isNote: this.props.type === "note",
            mentionedChannels: this.props.composer.mentionedChannels,
            mentionedPartners: this.props.composer.mentionedPartners,
            cannedResponseIds: this.props.composer.cannedResponses.map((c) => c.id),
            parentId: this.props.messageToReplyTo?.message?.id,
        };
        await this._sendMessage(value, postData);
    });
}
}
