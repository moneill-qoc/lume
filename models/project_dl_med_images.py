from odoo import models, fields, api, tools
import logging

_logger = logging.getLogger(__name__)


class project_task_image_tab_inherit(models.Model):
    _inherit = 'project.task'

    dl_image = fields.Image("DL Image", related='partner_id.dl_image',
                            readonly=True, store=False, copy=False)
