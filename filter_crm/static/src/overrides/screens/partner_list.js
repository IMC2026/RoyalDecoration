// your_module/static/src/components/activity/activity_extended.js
/** @odoo-module **/

import { Activity } from "@mail/components/activity/activity";
import { patch } from "@web/core/utils/patch";

patch(Activity.prototype, {
    async onClickDoneAndScheduleNext() {
        const { id, res_id, res_model, summary } = this.props.activity;
        const thread = this.threadService.getThread(res_model, res_id);
        debugger;
        // ✅ إغلاق النوافذ إن وجدت
        if (this.props.onClickDoneAndScheduleNext) {
            this.props.onClickDoneAndScheduleNext();
        }
        if (this.props.close) {
            this.props.close();
        }

        // ✅ إنهاء النشاط الحالي
        await this.rpc({
            model: "mail.activity",
            method: "action_feedback",
            args: [[id]],
        });

        // ✅ إنشاء سجل جديد في crm.activity.log مباشرة من JS
        if (res_model === "crm.lead") {
            await this.rpc({
                model: "crm.activity.log",
                method: "create",
                args: [{
                    name: summary || "Unnamed Activity",
                    activity_date: new Date().toISOString(),
                    crm_lead_id: res_id,
                }],
            });
        }

        // ✅ تحديث المحادثة والأنشطة
        this.threadService.fetchNewMessages(thread);

        if (this.props.reload) {
            this.props.reload(thread, ["activities", "attachments"]);
        }
        debugger;

        // ✅ فتح نافذة جدولة جديدة
        await new Promise((resolve) => {
            this.env.services.action.doAction({
                type: 'ir.actions.act_window',
                name: 'Schedule Activity',
                res_model: 'mail.activity',
                view_mode: 'form',
                target: 'new',
                context: {
                    default_res_model: res_model,
                    default_res_id: res_id,
                },
            }, {
                onClose: resolve,
            });
        });

        // ✅ إعادة تحميل الأنشطة بعد الجدولة
        if (this.props.reload) {
            this.props.reload(thread, ["activities"]);
        }
    },
});
