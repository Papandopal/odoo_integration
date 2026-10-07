import requests
from dataclasses import dataclass, field
from typing import List, Optional

from odoo import models, fields
from odoo.exceptions import UserError

def _get(data: dict, *names):
    if not isinstance(data, dict):
        return None
    lowered = {k.lower(): v for k, v in data.items()}
    for name in names:
        if name.lower() in lowered:
            return lowered[name.lower()]
    return None

@dataclass
class ApiSkill:
    name: str
    type: str
    value: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> "ApiSkill":
        if not isinstance(data, dict):
            raise ValueError(f"Skill must be an object, got {type(data).__name__}")

        name = _get(data, "Name", "name")
        if not name:
            raise ValueError("Skill.Name is required")

        skill_type = _get(data, "Type", "type")
        if not skill_type:
            raise ValueError("Skill.Type is required")

        raw_value = _get(data, "AverageValue", "averageValue")
        if raw_value is None:
            raw_value = ""
        elif not isinstance(raw_value, str):
            raw_value = str(raw_value)

        return cls(name=str(name), type=str(skill_type), value=raw_value)


@dataclass
class ApiPosition:
    title: str
    position_id: Optional[str] = None
    skills: List[ApiSkill] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "ApiPosition":
        if not isinstance(data, dict):
            raise ValueError(f"Position must be an object, got {type(data).__name__}")

        title = _get(data, "Title", "title")
        if not title:
            raise ValueError("Position.Title is required")

        raw_skills = _get(data, "Skills", "skills") or []
        if not isinstance(raw_skills, list):
            raise ValueError("Position.Skills must be a list")

        position_id = _get(data, "PositionId", "positionId")

        return cls(
            title=str(title),
            position_id=str(position_id) if position_id else None,
            skills=[ApiSkill.from_dict(s) for s in raw_skills],
        )


def parse_positions(payload) -> List[ApiPosition]:
    if not isinstance(payload, list):
        raise ValueError(
            f"API response must be a JSON array, got {type(payload).__name__}"
        )
    return [ApiPosition.from_dict(item) for item in payload]

class ImportWizard(models.TransientModel):
    _name = 'import.wizard'
    _description = 'Import Positions from External API'

    external_user_id = fields.Char(
        string='Your External User ID',
        default=lambda self: self.env.user.external_user_id or '',
        help='Your ID from the course project app. Saved to your profile.'
    )
    position_ids = fields.Char(
        string='Position IDs',
        required=True,
        help='Comma-separated list of position IDs, e.g. "8f1c...,3a2b...".'
    )

    def _get_config(self, key: str) -> str:
        value = self.env['ir.config_parameter'].sudo().get_param(key)
        if not value:
            raise UserError(
                f"Configuration parameter '{key}' is not set. "
                "Please contact your administrator."
            )
        return value

    def _upsert_position(self, pos, raw_pos):
        Position = self.env['imported.position'].sudo()
        Skill = self.env['imported.skill'].sudo()

        existing = Position.search([
            ('external_id', '=', pos.position_id or ''),
            ('external_user_id', '=', self.external_user_id),
        ], limit=1)

        if existing:
            existing.write({
                'name': pos.title,
                'raw_data': raw_pos,
            })
            existing.skill_ids.unlink()
            position = existing
        else:
            position = Position.create({
                'name': pos.title,
                'external_id': pos.position_id or '',
                'external_user_id': self.external_user_id,
                'raw_data': raw_pos,
            })

        raw_skills = _get(raw_pos, "Skills", "skills") or []
        if not isinstance(raw_skills, list):
            raw_skills = []

        for raw_skill, skill in zip(raw_skills, pos.skills):
            Skill.create({
                'position_id': position.id,
                'name': skill.name,
                'skill_type': skill.type,
                'value': skill.value,   
                'raw_data': raw_skill if isinstance(raw_skill, dict) else {},
            })

        return position

    def action_import(self):
        self.ensure_one()

        if not self.external_user_id:
            raise UserError("Please enter your External User ID.")

        cleaned = ','.join(
            p.strip() for p in (self.position_ids or '').split(',') if p.strip()
        )
        if not cleaned:
            raise UserError("Please enter at least one Position ID.")

        if (self.env.user.external_user_id or '') != self.external_user_id:
            self.env.user.sudo().write({
                'external_user_id': self.external_user_id
            })

        api_url = self._get_config('project.api_url')
        params = {'positionIds': cleaned}

        try:
            response = requests.get(api_url, params=params, timeout=30)
        except requests.RequestException as e:
            raise UserError(f"Connection error: {e}")

        if response.status_code != 200:
            raise UserError(
                f"API error: {response.status_code} {response.text}"
            )

        try:
            payload = response.json()
        except ValueError:
            raise UserError("API did not return valid JSON.")

        try:
            positions = parse_positions(payload)
        except ValueError as e:
            raise UserError(f"Invalid API payload: {e}")

        if not positions:
            raise UserError(
                "No positions were returned. Check that the IDs are correct."
            )

        raw_items = payload if isinstance(payload, list) else []

        for raw_pos, pos in zip(raw_items, positions):
            self._upsert_position(pos, raw_pos)

        return {
            'type': 'ir.actions.act_window',
            'name': 'My Positions',
            'res_model': 'imported.position',
            'view_mode': 'list,form',
            'target': 'main',
            'domain': [('external_user_id', '=', self.external_user_id)],
            'context': {'create': False},
        }
