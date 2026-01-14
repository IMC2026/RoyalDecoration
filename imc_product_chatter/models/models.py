from markupsafe import Markup, escape as esc
from odoo import api, fields, models, _

class ProductTemplate(models.Model):
    _inherit = "product.template"

    # 1) وقت آخر تغيير في الفورم (قبل الحفظ)
    x_last_field_change_dt = fields.Datetime(
        string="Last Field Change (Tech)",
        readonly=True,
        copy=False
    )

    # 2) التقط وقت التغيير الحقيقي عند تعديل أي من الحقول التالية
    @api.onchange(
        'name', 'barcode', 'default_code', 'categ_id',
        'list_price', 'standard_price', 'uom_id', 'uom_po_id',
        'taxes_id', 'supplier_taxes_id',
        'attribute_line_ids',
    )
    def _onchange_track_fields(self):
        self.x_last_field_change_dt = fields.Datetime.now()

    # 3) تنسيق القيم للعرض في اللوج
    @api.model
    def _format_value_for_log(self, record, field_name, value):
        field = record._fields.get(field_name)
        if field is None:
            return str(value)

        if field.type == "many2one":
            if not value:
                return "-"
            # إذا كان Recordset استخدم exists()
            if hasattr(value, "exists"):
                value = value.exists()
                if not value:
                    return "-"
                rec = value
            else:
                rec = self.env[field.comodel_name].browse(value).exists()
                if not rec:
                    return "-"
            return rec.display_name or str(rec.id)

        if field.type == "selection":
            if value in (False, None, ""):
                return "-"
            # آمن للتعامل مع selection الديناميكي
            sel_dict = {}
            try:
                pairs = field._description_selection(self.env)
                sel_dict = dict(pairs) if isinstance(pairs, (list, tuple)) else {}
            except Exception:
                try:
                    if isinstance(field.selection, (list, tuple)):
                        pairs = [p for p in field.selection if isinstance(p, (list, tuple)) and len(p) == 2]
                        sel_dict = dict(pairs)
                except Exception:
                    sel_dict = {}
            return sel_dict.get(value, str(value))

        if field.type == "boolean":
            return _("True") if value else _("False")

        if value in (False, None, ""):
            return "-"

        return str(value)

    # 4) أسماء من IDs (للإضافات الجديدة فقط؛ المحذوفة نأتي باسمها من السِنابت)
    def _names_from_ids(self, comodel, ids):
        if not ids:
            return []
        recs = self.env[comodel].browse(list(ids)).exists()
        return [r.display_name for r in recs]

    # 5) تسجيل التغييرات في الـ chatter
    def write(self, vals):
        # الحقول المرشّحة للتتبّع
        fields_to_check = [f for f in vals.keys() if f in self._fields]
        ignored = {"__last_update", "message_attachment_count", "message_follower_ids"}
        fields_to_check = [f for f in fields_to_check if f not in ignored]

        # سناب شوت قبل الكتابة (نحفظ IDs + names لعلاقيات o2m/m2m)
        old_snapshots = {}
        for rec in self:
            snap = {}
            for f in fields_to_check:
                field = rec._fields[f]
                val = rec[f]
                if field.type in ("one2many", "many2many"):
                    ids = list(getattr(val, "ids", []) or [])
                    # حفظ أسماء الصفوف الحالية حتى إن حُذفت لاحقاً
                    name_map = {}
                    try:
                        for rid in ids:
                            r = self.env[field.comodel_name].browse(rid)
                            # no .exists() هنا حتى لا نخسر الاسم بعد الحذف
                            name_map[rid] = r.display_name
                    except Exception:
                        pass
                    snap[f] = {"ids": ids, "names": name_map}
                elif field.type == "many2one":
                    snap[f] = val.id if val else False
                else:
                    snap[f] = val
            old_snapshots[rec.id] = snap

        res = super().write(vals)

        # بناء اللوج
        for rec in self:
            items = []
            snap = old_snapshots.get(rec.id, {})
            for f in fields_to_check:
                field = rec._fields[f]
                old_val = snap.get(f)
                new_val = rec[f]

                # ---- Many2many: إضافة/حذف عناصر ----
                if field.type == "many2many":
                    old_ids = set((old_val or {}).get("ids", []))
                    new_ids = set(getattr(new_val, "ids", []) or [])
                    added_ids = new_ids - old_ids
                    removed_ids = old_ids - new_ids
                    if not added_ids and not removed_ids:
                        continue

                    added_names = self._names_from_ids(field.comodel_name, added_ids)
                    removed_names = [ (old_val.get("names", {}).get(i) or str(i)) for i in removed_ids ]

                    parts = []
                    if added_names:
                        parts.append("+ " + ", ".join(esc(n) for n in added_names))
                    if removed_names:
                        parts.append("− " + ", ".join(esc(n) for n in removed_names))

                    items.append(
                        Markup("<li><b>{}</b>: {}</li>").format(
                            esc(field.string or f),
                            Markup("; ").join(Markup(p) for p in parts),
                        )
                    )
                    continue

                # ---- One2many: إضافة/حذف سطور (بدون deep diff) ----
                if field.type == "one2many":
                    old_ids = set((old_val or {}).get("ids", []))
                    new_ids = set(getattr(new_val, "ids", []) or [])
                    added_ids = new_ids - old_ids
                    removed_ids = old_ids - new_ids
                    if not added_ids and not removed_ids:
                        continue

                    added_names = self._names_from_ids(field.comodel_name, added_ids)
                    removed_names = [ (old_val.get("names", {}).get(i) or str(i)) for i in removed_ids ]

                    parts = []
                    if added_names:
                        parts.append("+ " + ", ".join(esc(n) for n in added_names))
                    if removed_names:
                        parts.append("− " + ", ".join(esc(n) for n in removed_names))

                    items.append(
                        Markup("<li><b>{}</b>: {}</li>").format(
                            esc(field.string or f),
                            Markup("; ").join(Markup(p) for p in parts),
                        )
                    )
                    continue

                # ---- باقي الأنواع + many2one (قيمة قديم → جديد) ----
                if field.type == "many2one":
                    old_id = old_val or False
                    new_id = new_val.id if hasattr(new_val, "id") else (new_val or False)
                    if old_id == new_id:
                        continue
                else:
                    if old_val == new_val:
                        continue

                pretty_old = self._format_value_for_log(rec, f, old_val)
                pretty_new = self._format_value_for_log(rec, f, new_val)
                items.append(
                    Markup("<li><b>{}</b>: {} → {}</li>").format(
                        esc(field.string or f), esc(pretty_old), esc(pretty_new)
                    )
                )

            if items:
                # بدون عنوان “Changes: …” — فقط القائمة
                body = Markup("<ul>") + Markup("").join(items) + Markup("</ul>")
                msg = rec.message_post(
                    body=body,
                    message_type="comment",
                    subtype_xmlid="mail.mt_note",
                )

                # استخدم وقت التغيير الحقيقي إن وُجد، وإلا write_date
                display_dt = rec.x_last_field_change_dt or rec.write_date
                if display_dt:
                    msg.sudo().write({'date': display_dt})

                # صفّر الحقل بعد الاستخدام
                if rec.x_last_field_change_dt:
                    rec.sudo().with_context(tracking_disable=True).write({
                        'x_last_field_change_dt': False
                    })

        return res
