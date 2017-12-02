import logging

_logger = logging.getLogger('upgrade')

def migrate(cr, version):
    if not version:
        return

    cr.execute("""update project_task set direct_sale_line_id = sale_line_id""")
    cr.execute("""delete from procurement_order""")
    cr.execute("""delete from procurement_group""")