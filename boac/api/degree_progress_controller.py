"""
Copyright ©2021. The Regents of the University of California (Regents). All Rights Reserved.

Permission to use, copy, modify, and distribute this software and its documentation
for educational, research, and not-for-profit purposes, without fee and without a
signed licensing agreement, is hereby granted, provided that the above copyright
notice, this paragraph and the following two paragraphs appear in all copies,
modifications, and distributions.

Contact The Office of Technology Licensing, UC Berkeley, 2150 Shattuck Avenue,
Suite 510, Berkeley, CA 94720-1620, (510) 643-7201, otl@berkeley.edu,
http://ipira.berkeley.edu/industry-info for commercial licensing opportunities.

IN NO EVENT SHALL REGENTS BE LIABLE TO ANY PARTY FOR DIRECT, INDIRECT, SPECIAL,
INCIDENTAL, OR CONSEQUENTIAL DAMAGES, INCLUDING LOST PROFITS, ARISING OUT OF
THE USE OF THIS SOFTWARE AND ITS DOCUMENTATION, EVEN IF REGENTS HAS BEEN ADVISED
OF THE POSSIBILITY OF SUCH DAMAGE.

REGENTS SPECIFICALLY DISCLAIMS ANY WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE. THE
SOFTWARE AND ACCOMPANYING DOCUMENTATION, IF ANY, PROVIDED HEREUNDER IS PROVIDED
"AS IS". REGENTS HAS NO OBLIGATION TO PROVIDE MAINTENANCE, SUPPORT, UPDATES,
ENHANCEMENTS, OR MODIFICATIONS.
"""

from boac.api.errors import BadRequestError, ResourceNotFoundError
from boac.api.util import can_edit_degree_progress, can_read_degree_progress
from boac.lib.berkeley import dept_codes_where_advising
from boac.lib.http import tolerant_jsonify
from boac.lib.util import get as get_param
from boac.models.degree_progress_template import DegreeProgressTemplate
from boac.models.degree_progress_unit_requirement import DegreeProgressUnitRequirement
from flask import current_app as app, request
from flask_cors import cross_origin
from flask_login import current_user


@app.route('/api/degree/create', methods=['POST'])
@can_edit_degree_progress
def create_degree():
    params = request.get_json()
    name = get_param(params, 'name', None)
    if not name:
        raise BadRequestError('Degree template creation requires a degree \'name\'')
    degree = DegreeProgressTemplate.create(
        created_by=current_user.get_id(),
        degree_name=name,
        advisor_dept_codes=dept_codes_where_advising(current_user),
    )
    return tolerant_jsonify(degree.to_api_json())


@app.route('/api/degree/<template_id>/delete', methods=['DELETE'])
@can_edit_degree_progress
@cross_origin(allow_headers=['Content-Type'])
def delete(template_id):
    DegreeProgressTemplate.delete(template_id)
    return tolerant_jsonify({'message': f'Template {template_id} deleted'}), 200


@app.route('/api/degree/templates')
@can_read_degree_progress
def get_degree_templates():
    return tolerant_jsonify([template.to_api_json() for template in DegreeProgressTemplate.get_all_templates()])


@app.route('/api/degree/<template_id>/unit_requirement', methods=['POST'])
@can_edit_degree_progress
def add_unit_requirement(template_id):
    params = request.form
    name = params.get('name', None)
    min_units = params.get('minUnits', None)
    if not name or not min_units:
        raise BadRequestError('Unit requirement \'name\' and \'min units\' must be provided.')
    template = DegreeProgressTemplate.find_by_id(template_id)
    if not template:
        raise ResourceNotFoundError(f'Degree progress template with id={template_id} not found.')
    unit_requirement = DegreeProgressUnitRequirement.create(
        created_by=current_user.get_id(),
        min_units=min_units,
        name=name,
        template_id=template_id,
    )
    return tolerant_jsonify(unit_requirement.to_api_json())
