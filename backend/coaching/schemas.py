from jsonschema import Draft202012Validator
from rest_framework.exceptions import ValidationError

PLAN_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "goal",
        "duration_weeks",
        "sessions_per_week",
        "session_minutes",
        "drills",
        "evidence_ids",
        "limitations",
    ],
    "properties": {
        "goal": {"type": "string", "minLength": 1, "maxLength": 500},
        "duration_weeks": {"type": "integer", "minimum": 1, "maximum": 12},
        "sessions_per_week": {"type": "integer", "minimum": 1, "maximum": 7},
        "session_minutes": {"type": "integer", "minimum": 5, "maximum": 120},
        "drills": {
            "type": "array",
            "minItems": 1,
            "maxItems": 8,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["name", "minutes", "instructions", "progress_measure"],
                "properties": {
                    "name": {"type": "string", "minLength": 1, "maxLength": 100},
                    "minutes": {"type": "integer", "minimum": 1, "maximum": 120},
                    "instructions": {"type": "string", "minLength": 1, "maxLength": 1500},
                    "progress_measure": {"type": "string", "minLength": 1, "maxLength": 500},
                },
            },
        },
        "evidence_ids": {
            "type": "array",
            "maxItems": 50,
            "uniqueItems": True,
            "items": {"type": "string"},
        },
        "limitations": {
            "type": "array",
            "minItems": 1,
            "maxItems": 10,
            "items": {"type": "string", "maxLength": 600},
        },
    },
}


def validate_plan(plan, allowed_ids):
    errors = list(Draft202012Validator(PLAN_SCHEMA).iter_errors(plan))
    if errors:
        raise ValidationError("训练计划格式无效。")
    if sum(d["minutes"] for d in plan["drills"]) != plan["session_minutes"]:
        raise ValidationError("训练时长与分项时长不一致。")
    if set(plan["evidence_ids"]) - set(allowed_ids):
        raise ValidationError("训练计划引用了无权访问的证据。")
    return plan
