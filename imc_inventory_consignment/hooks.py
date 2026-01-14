def post_init_hook(env):
    Warehouse   = env['stock.warehouse'].sudo()
    PickingType = env['stock.picking.type'].sudo()
    Sequence    = env['ir.sequence'].sudo()

    for wh in Warehouse.search([]):
        wh_code = (wh.code or (wh.name[:3] if wh.name else 'WH')).upper()
        prefix  = f'{wh_code}/CON/'
        seq_code = f'stock.picking.consignment.{wh.id}'

        seq = Sequence.search([
            ('code', '=', seq_code),
            ('company_id', '=', wh.company_id.id),
        ], limit=1)
        if not seq:
            seq = Sequence.create({
                'name': f'{wh.name} Consignment Picking',
                'code': seq_code,
                'prefix': prefix,
                'padding': 5,
                'number_next': 1,
                'company_id': wh.company_id.id,
                'use_date_range': False,
            })
        else:
            if seq.prefix != prefix or seq.padding != 5:
                seq.write({'prefix': prefix, 'padding': 5})

        picking_type = PickingType.search([
            ('warehouse_id', '=', wh.id),
            ('name', '=', 'Consignment'),
        ], limit=1)

        vals = {
            'name': 'Consignment',
            'code': 'incoming',  # <-- بدل internal إلى incoming
            'warehouse_id': wh.id,
            'sequence_id': seq.id,   # استخدم تسلسلنا المخصص
            'sequence_code': 'CON',  # اختياري؛ لا يؤثر مع sequence_id
            'is_consignment': True,

            # مواقع افتراضية مناسبة للـ incoming:
            'default_location_src_id': env.ref('stock.stock_location_suppliers').id,
            'default_location_dest_id': wh.lot_stock_id.id,
        }
        if picking_type:
            picking_type.write(vals)
        else:
            PickingType.create(vals)
