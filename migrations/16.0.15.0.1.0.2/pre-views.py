import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    cr.execute("DELETE FROM ir_ui_view WHERE id in (SELECT res_id from ir_model_data WHERE module = 'zalo_connector' AND name = 'view_move_form_inherit')");
