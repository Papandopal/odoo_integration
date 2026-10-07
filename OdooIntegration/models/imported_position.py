from odoo import models, fields


class ImportedPosition(models.Model):
    _name = 'imported.position'
    _description = 'Imported Position'
    _order = 'import_date desc'

    _sql_constraints = [
        (
            'unique_external_per_user',
            'UNIQUE(external_id, external_user_id)',
            'This position is already imported for this user.',
        ),
    ]

    name = fields.Char(string='Title', required=True)
    external_id = fields.Char(
        string='External Position ID',
        required=True,
        index=True
    )
    external_user_id = fields.Char(
        string='External User ID',
        required=True,
        index=True
    )
    import_date = fields.Datetime(
        string='Imported',
        default=fields.Datetime.now,
        readonly=True
    )
    skill_ids = fields.One2many(
        'imported.skill',
        'position_id',
        string='Skills'
    )
    raw_data = fields.Json(
        string='Raw Payload',
        readonly=True,
        help='Original JSON object received from the API.'
    )