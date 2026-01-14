# -*- coding: utf-8 -*-
from odoo import models, fields,api

# ============ Configuration Models ============

class CrmWorkType(models.Model):
    _name = 'crm.work.type'
    _description = 'Work Type'

    name = fields.Char(required=True)


class CrmTypeOfProject(models.Model):
    _name = 'crm.type.of.project'
    _description = 'Type of Project'

    name = fields.Char(required=True)


class CrmMaterialType(models.Model):
    _name = 'crm.material.type'
    _description = 'Material Type'

    name = fields.Char(required=True)


class CrmMaterialDescription(models.Model):
    _name = 'crm.material.description'
    _description = 'Material Description'

    name = fields.Char(required=True)


class CrmThicknessMM(models.Model):
    _name = 'crm.thickness.mm'
    _description = 'Thickness (mm)'

    name = fields.Char(required=True)


class CrmFinishType(models.Model):
    _name = 'crm.finish.type'
    _description = 'Finish Type'

    name = fields.Char(required=True)


class CrmColor(models.Model):
    _name = 'crm.color'
    _description = 'Color'

    name = fields.Char(required=True)


class CrmGlossinessLacquer(models.Model):
    _name = 'crm.glossiness.lacquer'
    _description = 'Glossiness of Lacquer'

    name = fields.Char(required=True)


class CrmDrawing(models.Model):
    _name = 'crm.drawing'
    _description = 'Drawing'

    name = fields.Char(required=True)


class CrmControlSample(models.Model):
    _name = 'crm.control.sample'
    _description = 'Control Sample'

    name = fields.Char(required=True)

class InstallationType(models.Model):
    _name = 'crm.installation.type'
    _description = 'Installation Type'

    name = fields.Char(required=True)

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    work_type_ids = fields.Many2many('crm.work.type', string='Work Type')
    type_of_project_ids = fields.Many2many('crm.type.of.project', string='Type of Project')
    material_type_ids = fields.Many2many('crm.material.type', string='Material Type')
    material_description_ids = fields.Many2many('crm.material.description', string='Material Description')
    thickness_mm_ids = fields.Many2many('crm.thickness.mm', string='Thickness (mm)')
    finish_type_ids = fields.Many2many('crm.finish.type', string='Finish Type')
    color_ids = fields.Many2many('crm.color', string='Color')
    glossiness_lacquer_ids = fields.Many2many('crm.glossiness.lacquer', string='Glossiness of Lacquer')
    drawing_ids = fields.Many2many('crm.drawing', string='Drawing')
    control_sample_ids = fields.Many2many('crm.control.sample', string='Control Sample')
    delivery_time = fields.Integer(string='Delivery Time')
    installation_type_ids = fields.Many2many('crm.installation.type',string='Installation')

    note_work_type = fields.Char(string='Note')
    note_type_of_project = fields.Char(string='Note')
    note_material_type = fields.Char(string='Note')
    note_material_description = fields.Char(string='Note')
    note_thickness_mm = fields.Char(string='Note')
    note_finish_type = fields.Char(string='Note')
    note_color = fields.Char(string='Note')
    note_glossiness_lacquer = fields.Char(string='Note')
    note_drawing = fields.Char(string='Note')
    note_control_sample = fields.Char(string='Note')
    note_delivery_time = fields.Char(string='Note')
    note_installation_type = fields.Char(string='Note')
