from odoo import models, fields
from odoo.exceptions import UserError

from odoo import models
from datetime import datetime
from odoo import models, fields, api



class CrmActivityLog(models.Model):
    _name = 'crm.activity.log'
    _description = 'CRM Activity Log'

    name = fields.Char(string='Activity Name', required=True)
    activity_date = fields.Datetime(string='Activity Done Date', required=True)
    crm_lead_id = fields.Many2one('crm.lead', string='CRM Lead', required=True)



from datetime import datetime

class MailActivity(models.Model):
    _inherit = 'mail.activity'

    def unlink(self):
        # 🟢 خزّن البيانات قبل الحذف
        activities_data = []
        for activity in self:
            if activity.res_model == 'crm.lead':
                activities_data.append({
                    'res_id': activity.res_id,
                    'summary': activity.summary or 'Unnamed Activity',
                })

        # 🔴 نفّذ الحذف الحقيقي
        res = super().unlink()

        # 🟢 أنشئ سجل لوق بعد الحذف
        for data in activities_data:
            log = self.env['crm.activity.log'].create({
                'name': data['summary'],
                'activity_date': fields.Datetime.now(),  # تاريخ الحذف
                'crm_lead_id': data['res_id'],
            })

            lead = self.env['crm.lead'].browse(data['res_id'])
            lead.activity_log_ids = [(4, log.id)]  # إضافة العلاقة many2many

        return res

    # def action_feedback(self, feedback=False, **kwargs):
    #     # 🟢 خزّن البيانات قبل حذف النشاط
    #     activities_data = [
    #         {
    #             'res_model': activity.res_model,
    #             'res_id': activity.res_id,
    #             'summary': activity.summary
    #         }
    #         for activity in self
    #         if activity.res_model == 'crm.lead'
    #     ]
    #
    #     # استدعاء الأصل (سيؤدي إلى حذف السجل)
    #     res = super().action_feedback(feedback=feedback, **kwargs)
    #
    #     for data in activities_data:
    #         log = self.env['crm.activity.log'].create({
    #             'name': data['summary'] or 'Unnamed Activity',
    #             'activity_date': fields.Datetime.now(),
    #             'crm_lead_id': data['res_id'],
    #         })
    #
    #         lead = self.env['crm.lead'].browse(data['res_id'])
    #         lead.activity_log_ids = [(4, log.id)]
    #
    #     return res


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    activity_log_ids = fields.Many2many(
        'crm.activity.log',
        'crm_lead_activity_log_rel',  # اسم جدول الربط
        'lead_id',
        'log_id',
        string='Activity Logs'
    )