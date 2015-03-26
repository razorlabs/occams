"""
Patient aliquot report.

Formerly: avrcdataexport/sql/additional/SpecimenAliquot.sql
"""


#
# BBB: Lab is not part of the studies app, but needs to be
#      generated anyway until we can implement LIMS, in which
#      case it'll have it's own export page/process in that app.
#


from sqlalchemy import func, null
from sqlalchemy.orm import aliased

from .. import models, Session
from .plan import ExportPlan
from .codebook import row, types


class LabPlan(ExportPlan):

    name = 'SpecimenAliquot'

    title = 'Specimen'

    @property
    def is_enabled(self):
        return any(n in Session.bind.url.database
                   for n in ['aeh', 'cctg', 'mhealth'])

    def codebook(self):
        return iter([
            row('aliquot_type', self.name, types.STRING,
                is_required=True, is_system=True),
            row('store_date', self.name, types.DATE, is_system=True),
            row('volume', self.name, types.NUMERIC, is_system=True),
            row('cell_amount', self.name, types.NUMERIC, is_system=True),
            row('aliquot_location', self.name, types.STRING, is_system=True),
            row('freezer', self.name, types.STRING, is_system=True),
            row('rack', self.name, types.STRING, is_system=True),
            row('box', self.name, types.STRING, is_system=True),
            row('aliquot_count', self.name, types.NUMERIC,
                is_required=True, is_system=True),
            row('aliquot_state', self.name, types.STRING,
                is_required=True, is_system=True),
            row('sent_date', self.name, types.DATE, is_system=True),
            row('sent_name', self.name, types.STRING, is_system=True),
            row('sent_notes', self.name, types.STRING, is_system=True),
            row('thawed_num', self.name, types.NUMERIC, is_system=True),
            row('special_instruction', self.name, types.STRING,
                is_system=True),
            row('inventory_date', self.name, types.DATE, is_system=True),
            row('aliquot_notes', self.name, types.STRING, is_system=True),
            row('specimen_type', self.name, types.STRING,
                is_required=True, is_system=True),
            row('collect_time', self.name, types.TIME, is_system=True),
            row('collect_date', self.name, types.DATE, is_system=True),
            row('specimen_study', self.name, types.STRING, is_system=True),
            row('specimen_cycle', self.name, types.STRING, is_system=True),
            row('specimen_destination', self.name, types.STRING,
                is_system=True),
            row('specimen_state', self.name, types.STRING, is_system=True),
            row('tubes', self.name, types.NUMERIC, is_system=True),
            row('tube_type', self.name, types.STRING, is_system=True),
            row('specimen_notes', self.name, types.STRING, is_system=True),
            row('site', self.name, types.STRING,
                is_required=True, is_system=True),
            row('pid', self.name, types.STRING,
                is_required=True, is_system=True),
            row('our', self.name, types.STRING,
                is_required=True, is_system=True),
            row('nurse_email', self.name, types.STRING, is_system=True),
            row('aeh_num', self.name, types.STRING, is_system=True)
            ])

    def data(self,
             use_choice_labels=False,
             expand_collections=False,
             ignore_private=True):

        # Import here to avoid breaking installations that don't use lab.
        from occams.lims import models as lab

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
                models.Cycle.week.label('specimen_cycle'),
                SpecimenLocation.title.label('specimen_destination'),
                lab.SpecimenState.title.label('specimen_state'),
                lab.Specimen.tubes.label('tubes'),
                lab.SpecimenType.tube_type.label('tube_type'),
                lab.Specimen.notes.label('specimen_notes'),
                models.Site.name.label('site'),
                models.Patient.pid.label('pid'),
                models.Patient.pid.label('our'),
                models.Patient.nurse.label('nurse_email'),
                (Session.query(models.PatientReference.reference_number)
                 .join(models.ReferenceType)
                 .filter(models.ReferenceType.name == u'aeh_num')
                 .filter(models.PatientReference.patient_id == models.Patient.id)
                 .limit(1)
                 .correlate(models.Patient)
                 .as_scalar()
                 .label('aeh_num')))
            .select_from(lab.Aliquot)
            .join(lab.Aliquot.specimen)
            .outerjoin(lab.Aliquot.aliquot_type)
            .outerjoin(lab.Aliquot.state)
            .outerjoin(AliquotLocation, lab.Aliquot.location)
            .outerjoin(SpecimenLocation, lab.Specimen.location)
            .outerjoin(lab.Aliquot.special_instruction)
            .outerjoin(lab.Specimen.cycle)
            .outerjoin(models.Cycle.study)
            .outerjoin(lab.Specimen.specimen_type)
            .outerjoin(lab.Specimen.state)
            .join(lab.Specimen.patient)
            .join(models.Patient.site)
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
                lab.SpecimenType.title,
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
                models.Patient.pid,
                models.Patient.nurse,
                'aeh_num',
                models.Site.name))

        return query
