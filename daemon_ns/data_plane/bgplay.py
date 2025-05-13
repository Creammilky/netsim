def elem2bgplay(rec, elem):
    msg = {
        'type': elem.type,
        'timestamp': elem.time,
        'target': {
            'prefix': elem.fields['prefix'],
        },
        'source': {
            'as_number': elem.peer_asn,
            'ip': elem.peer_address,
            'project': rec.project,
            'collector': rec.collector,
            'id': f"{rec.project}-{rec.collector}-{elem.peer_asn}-{elem.peer_address}"
        }
    }
    if elem.type == 'A':
        msg['path'] = [
            {'owner': str(asn), 'as_number': str(asn)}
            for asn in elem.fields['as-path'].split()
        ]
    return msg
