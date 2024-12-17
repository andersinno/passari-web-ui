from wtforms.validators import ValidationError

from passari_workflow.db.models import MuseumObject
from passari_workflow.queue.queues import get_enqueued_object_ids

from ..db import db


def object_ids_exist_check(form, field):
    """
    Check that all given object IDs exist
    """
    if not field.data:
        raise ValidationError("No object ID was provided")

    existing_object_ids = [
        result[0] for result in
        db.session.query(MuseumObject.id)
        .filter(MuseumObject.id.in_(field.data))
        .all()
    ]

    missing_object_ids = set(field.data) - set(existing_object_ids)

    if missing_object_ids:
        raise ValidationError(
            f"Following objects don't exist: "
            f"{', '.join([str(o) for o in sorted(missing_object_ids)])}"
        )


def object_with_reason_exist_check(form, field):
    """
    Check that at least one frozen object with the given reason exists
    """
    result = (
        db.session.query(MuseumObject)
        .filter(MuseumObject.frozen)
        .filter(MuseumObject.freeze_reason == field.data)
        .first()
    )

    if not result:
        raise ValidationError("No objects with this reason were found.")


def object_ids_pending_preservation_check(form, field):
    """
    Check that all objects with the given IDs are pending preservation
    """
    if not field.data:
        raise ValidationError("No object IDs provided")

    pending_object_ids = [
        result[0] for result in
        db.session.query(MuseumObject.id)
        .with_transformation(MuseumObject.filter_preservation_pending)
        .all()
    ]

    not_pending = set(field.data) - set(pending_object_ids)

    if not_pending:
        raise ValidationError(
            f"Following objects are not pending preservation: "
            f"{', '.join([str(o) for o in sorted(not_pending)])}"
        )


def object_ids_not_processed_before_check(form, field):
    """
    Check that none of the given objects has been added
    to the workflow before.
    """
    if not field.data:
        raise ValidationError("No object IDs provided")

    object_ids = set(field.data)
    enqueued_object_ids = get_enqueued_object_ids()
    already_enqueued = object_ids.intersection(enqueued_object_ids)

    if already_enqueued:
        raise ValidationError(
            f"Objects already in the workflow and can't be enqueued: "
            f"{', '.join(str(id) for id in sorted(already_enqueued))}"
        )
