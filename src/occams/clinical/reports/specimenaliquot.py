"""
Patient aliquot report.

Formerly: avrcdataexport/sql/additional/SpecimenAliquot.sql
"""

from sqlalchemy import func, null
from sqlalchemy.orm import aliased

from occams.clinical import models, Session
from occams.clinical.reports.codebook import row, types
from occams.lab import models as lab


NAME = 'SpecimenAliquot'


def codebook():

    return iter([
        row('aliquot_type', NAME, types.STRING, is_required=True),
        row('store_date', NAME, types.DATE),
        row('volume', NAME, types.NUMERIC),
        row('cell_amount', NAME, types.NUMERIC),
        row('aliquot_location', NAME, types.STRING),
        row('freezer', NAME, types.STRING),
        row('rack', NAME, types.STRING),
        row('box', NAME, types.STRING),
        row('aliquot_count', NAME, types.NUMERIC, is_required=True),
        row('aliquot_state', NAME, types.STRING, is_required=True),
        row('sent_date', NAME, types.DATE),
        row('sent_name', NAME, types.STRING),
        row('sent_notes', NAME, types.STRING),
        row('thawed_num', NAME, types.NUMERIC),
        row('special_instruction', NAME, types.STRING),
        row('inventory_date', NAME, types.DATE),
        row('aliquot_notes', NAME, types.STRING),
        row('specimen_type', NAME, types.STRING, is_required=True),
        row('collect_time', NAME, types.TIME),
        row('collect_date', NAME, types.DATE),
        row('specimen_study', NAME, types.STRING),
        row('specimen_cycle', NAME, types.STRING),
        row('specimen_destination', NAME, types.STRING),
        row('specimen_state', NAME, types.STRING),
        row('tubes', NAME, types.NUMERIC),
        row('tube_type', NAME, types.STRING),
        row('specimen_notes', NAME, types.STRING),
        row('our', NAME, types.STRING, is_required=True),
        row('nurse_email', NAME, types.STRING),
        row('aeh_num', NAME, types.STRING)
        ])


def query_report():
    AliquotLocation = aliased(lab.Location)
    SpecimenLocation = aliased(lab.Location)

    query = (
        Session.query(
            lab.AliquotType.title.label('aliquot_type'),
            lab.Aliquot.store_date.label('store_date'),
            lab.Aliquot.volume.label('volume'),
            lab.Aliquot.cell_amount.label('cell_amount'),
            AliquotLocation.title.label('aliquot_location'),
            lab.Aliquot.freezer.label('freezer'),
            lab.Aliquot.rack.label('rack'),
            lab.Aliquot.box.label('box'),
            func.count().label('aliquot_count'),
            lab.AliquotState.title.label('aliquot_state'),
            lab.Aliquot.sent_date.label('sent_date'),
            lab.Aliquot.sent_name.label('sent_name'),
            lab.Aliquot.sent_notes.label('sent_notes'),
            lab.Aliquot.thawed_num.label('thawed_num'),
            lab.SpecialInstruction.title.label('special_instruction'),
            lab.Aliquot.inventory_date.label('inventory_date'),
            lab.Aliquot.notes.label('aliquot_notes'),
            lab.SpecimenType.title.label('specimen_type'),
            lab.Specimen.collect_time.label('collect_time'),
            lab.Specimen.collect_date.label('collect_date'),
            models.Study.title.label('specimen_study'),
            models.Study.week.label('specimen_cycle'),
            SpecimenLocation.title.label('specimen_destination'),
            lab.SpecimenState.title.label('specimen_state'),
            lab.Specimen.tubes.label('tubes'),
            lab.SpecimenType.tube_type.label('tube_type'),
            lab.Specimen.notes.label('specimen_notes'),
            models.Patient.our.label('our'),
            models.Patient.nurse.label('nurse_email'),
            models.Patient.legacy_number.label('aeh_num'))
        .select_from(lab.Aliquot)
        .outerjoin(lab.Aliquot.type)
        .outerjoin(lab.Aliquot.state)
        .outerjoin(AliquotLocation, lab.Aliquot.location)
        .outerjoin(lab.Aliquot.special_instruction)
        .join(lab.Aliquot.specimen)
        .outerjoin(lab.Specimen.cycle)
        .outerjoin(models.Cycle.study)
        .outerjoin(lab.Specimen.type)
        .outerjoin(lab.Specimen.state)
        .join(lab.Spcimen.patient)
        .filter(lab.AliquotState.title != u'Aliquot Not used')
        .filter(func.coalesce(lab.Aliquot.freezer,
                              lab.Aliquot.rack,
                              lab.Aliquot.box) != null())
        .group_by(
            lab.AliquotType.title,
            lab.Aliquot.store_date,
            lab.Aliquot.volume,
            lab.Aliquot.cell_amount,
            AliquotLocation.title,
            lab.Aliquot.freezer,
            lab.Aliquot.rack,
            lab.Aliquot.box,
            lab.AliquotState.title,
            lab.Aliquot.sent_date,
            lab.Aliquot.sent_name,
            lab.Aliquot.sent_notes,
            lab.Aliquot.thawed_num,
            lab.SpecialInstruction.title,
            lab.Aliquot.inventory_date,
            lab.Aliquot.notes,
            lab.Specimen.type.title,
            lab.Specimen.collect_time,
            lab.Specimen.collect_date,
            models.Study.title,
            models.Cycle.week,
            SpecimenLocation.title,
            lab.SpecimenState.title,
            lab.Specimen.tubes,
            lab.SpecimenType.tube_type,
            lab.Specimen.notes,
            models.Patient.id,
            models.Patient.our,
            models.Patient.nurse,
            models.Patient.legacy_number))

    return query
