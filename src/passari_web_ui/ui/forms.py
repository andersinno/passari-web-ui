from flask_wtf import FlaskForm
from wtforms.fields import BooleanField, Field, IntegerField, StringField
from wtforms.validators import InputRequired, ValidationError
from wtforms.widgets import TextArea

from passari_web_ui.db import db
from passari_web_ui.ui.utils import get_available_object_count
from passari_workflow.db.models import MuseumObject

from .validators import (
    object_ids_exist_check,
    object_with_reason_exist_check
)


class EnqueueObjectsForm(FlaskForm):
    """
    Form to enqueue a certain amount of objects
    """
    object_count = IntegerField(validators=[InputRequired()])

    def validate_object_count(self, field):
        available_count = get_available_object_count()

        if available_count == 0:
            raise ValidationError(
                "There are no objects pending preservation at the moment"
            )

        if field.data < 1 or field.data > available_count:
            raise ValidationError(
                f"Object count has to be in range 1 - {available_count}"
            )


class ReenqueueObjectForm(FlaskForm):
    """
    Form to re-enqueue a single object
    """
    object_id = IntegerField("Object ID", validators=[InputRequired()])

    def validate_object_id(self, field):
        exists = (
            db.session.query(MuseumObject)
            .filter(MuseumObject.id == field.data)
            .one_or_none()
        )
        if not exists:
            raise ValidationError("Object with the given ID does not exist")


class MultipleObjectIDField(Field):
    """
    Field for retrieving a list of multiple object IDs
    """
    widget = TextArea()

    def _value(self):
        if self.data:
            return "\n".join(self.data)
        else:
            return ""

    def process_formdata(self, valuelist):
        if valuelist:
            try:
                self.data = [
                    int(entry.strip()) for entry in valuelist[0].split("\n")
                ]
            except ValueError:
                self.data = None
        else:
            self.data = []


class FreezeObjectsForm(FlaskForm):
    """
    Form for freezing multiple objects with a single reason
    """
    object_ids = MultipleObjectIDField(
        "Object IDs", validators=[object_ids_exist_check]
    )
    reason = StringField(
        description=(
            "Reason for freezing the object(s). Use an identical reason for "
            "multiple related objects to ensure they can be all unfrozen with "
            "one query."
        ),
        validators=[InputRequired()]
    )


class UnfreezeObjectsForm(FlaskForm):
    """
    Form to unfreeze objects with the given reason
    """
    reason = StringField(
        description=(
            "Reason used to freeze the object(s). All objects with this exact "
            "reason are unfrozen."
        ),
        validators=[object_with_reason_exist_check]
    )
    enqueue = BooleanField(
        description="Enqueue objects immediately after unfreezing.",
        default=False
    )
