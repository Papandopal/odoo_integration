from odoo import models, fields


class ImportedSkill(models.Model):
    _name = 'imported.skill'
    _description = 'Imported Skill'
    _order = 'name'

    position_id = fields.Many2one(
        'imported.position',
        string='Position',
        ondelete='cascade',
        required=True,
        index=True
    )
    name = fields.Char(string='Skill', required=True)
    skill_type = fields.Char(string='Type')
    value = fields.Char(string='Value')
    raw_data = fields.Json(string='Raw Payload', readonly=True)