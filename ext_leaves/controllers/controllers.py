# -*- coding: utf-8 -*-
import json
import logging
from werkzeug.exceptions import Forbidden

from odoo import http, tools, fields, _
from odoo.http import request
from odoo.addons.base.ir.ir_qweb.fields import nl2br
from odoo.addons.http_routing.models.ir_http import slug
from odoo.addons.website.controllers.main import QueryURL
from odoo.exceptions import ValidationError
from psycopg2 import IntegrityError
from odoo.addons.website_form.controllers.main import WebsiteForm
from datetime import datetime, timedelta
import math


class Websiteholiday(http.Controller):
    def _get_number_of_days(self, date_from, date_to):
        """ Returns a float equals to the timedelta between two dates given as string."""
        from_dt = fields.Datetime.from_string(date_from)
        to_dt = fields.Datetime.from_string(date_to)

        time_delta = to_dt - from_dt
        return math.ceil(time_delta.days + float(time_delta.seconds) / 86400)

    @http.route('/my/leaves/', type='http', auth="user", website=True, csrf=False)
    def holidayorder_create(self, **post):

        # values = self._prepare_portal_layout_values()
        uid = http.request.env.context.get('uid')
        if not uid:
            return http.request.render("website.403", {})
        # uids = http.request.env['portal.wizard.user'].sudo().search(['user_id','=',uid]).ids
        cuid = http.request.env['res.users'].sudo().browse(uid)
        employee_ids = cuid['employee_ids']
        if not employee_ids:
            return http.request.render("ext_leaves.error", {})
        employee_id = employee_ids[0]  # http.request.env['hr.employee'].sudo().browse(employee_ids)
        holiday_status_ids = http.request.env['hr.holidays.status'].sudo().search([]).ids
        holiday_status_id = http.request.env['hr.holidays.status'].sudo().browse(holiday_status_ids)

        if post:
            holiday = http.request.env['hr.holidays']
            try:
                with http.request.env.cr.savepoint():
                    ordere_holiday = holiday.sudo().create({
                        'name': post.get('name'),
                        'holiday_status_id': int(post.get('holiday_status_id')),
                        'date_from': post.get('date_from'),
                        'date_to': post.get('date_to'),
                        'employee_id': int(employee_id),
                        'number_of_days_temp': self._get_number_of_days(post.get('date_from'), post.get('date_to')),
                    })

            except ValidationError:
                return http.request.render("ext_leaves.leaveoverlap", {})

            except IntegrityError:
                return http.request.render("ext_leaves.constrain", {})
            return http.request.render("ext_leaves.welcome", {})
        return http.request.render("ext_leaves.index",
                                   {
                                       'holiday_status_id': holiday_status_id,
                                       'employee_id': employee_id,
                                       'uid': cuid,

                                   })