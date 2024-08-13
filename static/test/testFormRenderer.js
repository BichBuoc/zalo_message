/** @odoo-module **/
import { testSendMail } from "./testSendMail";
import { registry } from "@web/core/registry";
import { AttachmentView } from "@mail/core/common/attachment_view";
import { Component, onWillStart, markup, useState } from "@odoo/owl";

import { FormRenderer } from "@web/views/form/form_renderer";
import { formView } from "@web/views/form/form_view";
export class testFormRenderer extends FormRenderer {
  setup() {
    super.setup();
    this.mailComponents = {
        ...this.mailComponents,
        Chatter: testSendMail,
      }
      console.log(this.mailComponents)
  }
}

registry.category("views").add("testFormRenderer", {
  ...formView,
  Renderer: testFormRenderer,
});
