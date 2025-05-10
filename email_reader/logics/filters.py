from __future__ import annotations

import datetime
from enum import Enum
from pathlib import Path
from typing import Literal, Optional, Type, cast

from dateutil.relativedelta import relativedelta
from pydantic import BaseModel, model_validator
from sqlalchemy.types import DateTime, String

from email_reader.database.base import Base
from email_reader.database.tables.email import Email, MailBox
from email_reader.services.gmail import EmailAction, GmailService


class StringFilters(Enum):
    Contains = "contains"
    DoesNotContain = "does_not_contain"
    Equals = "__eq__"
    DoesNotEqual = "__neq__"

    def get_statement(self, model: Type[Base], field_name: str, field_value: str):
        field = getattr(model, field_name)
        if self == StringFilters.DoesNotContain:
            return ~field.contains(field_value)
        return getattr(field, self.value)(field_value)


class DatetimeFilters(Enum):
    GreaterThan = "__gt__"
    LessThan = "__lt__"

    def get_statement(self, model: Type[Base], field_name: str, field_value: str):
        field = getattr(model, field_name)
        return getattr(field, self.value)(self.field_value_parser(field_value))

    @classmethod
    def field_value_parser(cls, field_value: str) -> datetime.datetime:
        now = datetime.datetime.now()

        if field_value.endswith('d') or field_value.endswith('days'):
            dt = now - relativedelta(days=int(field_value.split('d')[0].strip()))
        elif field_value.endswith('m') or field_value.endswith('months'):
            dt = now - relativedelta(months=int(field_value.split('m')[0].strip()))
        else:
            try:
                dt = datetime.datetime.strptime("%Y-%m-%dT%H:%M:%S", field_value)
            except ValueError:
                pass

        if not dt:
            err = (
                'Invalid Format for Day\n'
                'Supported Formats are\n'
                '\t{number}-d (OR) {number} days for days\n'
                '\t{number}-m for months (OR) {number} months\n'
                '\t%Y-%m-%dT%H:%M:%S for exact timestamp\n'
                'Refer the Rules.md file for more details'
            )
            raise ValueError(err)

        return dt


class FilterCondition(BaseModel):

    class Rule(BaseModel):
        field: str
        predicate: StringFilters | DatetimeFilters
        value: str

        @model_validator(mode='before')
        def parse_rule(cls, data: dict) -> dict:
            field_name = data['field']
            filter_string = data['predicate']
            from email_reader.database.tables.email import Email
            field = getattr(Email, field_name)
            if isinstance(field.type, String):
                try:
                    data['predicate'] = StringFilters[filter_string]
                except KeyError:
                    avalable_filters = ", ".join([f"'{f.name}'" for f in StringFilters])
                    avalable_filters = " or".join(avalable_filters.rsplit(',', 1))
                    raise ValueError(
                        f"Filter Condition {filter_string} not support for String, Use {avalable_filters}"
                    )

                DatetimeFilters.field_value_parser(data['value'])

            elif isinstance(field.type, DateTime):
                try:
                    data['predicate'] = DatetimeFilters[filter_string]
                except KeyError:
                    avalable_filters = ", ".join([f"'{f.name}'" for f in DatetimeFilters])
                    avalable_filters = " or".join(avalable_filters.rsplit(',', 1))
                    raise ValueError(
                        f"Filter Condition {filter_string} not support for DateTime, Use {avalable_filters}"
                    )
            else:
                raise ValueError("Only String Fields and DateTime Fields are Supported in Filters")

            return data

        def get_statement(self):
            return self.predicate.get_statement(Email, self.field, self.value)

    operator: Literal['ANY', "ALL"]
    rules: list[FilterCondition.Rule]


class FilterAction(BaseModel):
    type: EmailAction
    folder: Optional[MailBox] = None

    @model_validator(mode='after')
    def require_folder_for_move(self) -> FilterAction:
        if self.type == EmailAction.MoveMessage and self.folder is None:
            raise ValueError("`folder` must be provided when `type` is MoveMessage")
        return self

    def __repr__(self) -> str:
        if self.type == EmailAction.MoveMessage:
            return f"A:{self.type.name}->{self.folder}"
        return f"A:{self.type.name}"

    def process_action(self, msg_id: str, gmail_service: GmailService) -> tuple[bool, Optional[str]]:
        if self.type == EmailAction.MarkAsRead or self.type == EmailAction.MarkAsUnread:
            return gmail_service.alter_email_read_state(msg_id, self.type)
        elif self.type == EmailAction.MoveMessage:
            return gmail_service.move_email(msg_id, cast(MailBox, self.folder))
        else:
            return False, "Unsupported Action"


class FilterRule(BaseModel):
    name: str
    conditions: FilterCondition
    actions: list[FilterAction]


class Rules(BaseModel):
    rules: list[FilterRule]

    @classmethod
    def from_file(cls, file: Path) -> Rules:
        return cls.model_validate_json(file.read_text())
