from odoo import models, fields, api


class ResUsers(models.Model):
    _inherit = 'res.users'

    external_user_id = fields.Char(
        string='External User ID',
        help='Your user ID from the course project application. '
    )

    @api.model_create_multi
    def create(self, vals_list):
        users = super().create(vals_list)

        internal_group = self.env.ref('base.group_user', raise_if_not_found=False)
        portal_group = self.env.ref('base.group_portal', raise_if_not_found=False)
        home_action = self.env.ref(
            'OdooIntegration.action_imported_position',
            raise_if_not_found=False
        )

        if internal_group:
            for user in users:
                commands = []

                if portal_group and portal_group in user.group_ids:
                    commands.append((3, portal_group.id))
                if internal_group not in user.group_ids:
                    commands.append((4, internal_group.id))

                if commands:
                    user.sudo().write({'group_ids': commands})
                    
                if home_action and not user.action_id:
                    user.sudo().write({'action_id': home_action.id})

        return users
