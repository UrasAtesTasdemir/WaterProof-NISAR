"""Deterministic, credential-free identities and stale-response guards."""
import hashlib
import json


def identity(kind, **parameters):
    return hashlib.sha256(json.dumps(dict(kind=kind, **parameters),sort_keys=True,allow_nan=False,separators=(',',':')).encode()).hexdigest()


def catalog_request(lat, lon, dates):
    return identity('catalog-v1',lat=float(lat),lon=float(lon),start=str(dates[0]),end=str(dates[1]),
                    dataset='NISAR',level='GCOV',max_results=250)


def analysis_request(products,lat,lon,km,polarizations=('HHHH','HVHV'),filter_size=3,dead_zone_db=1.5):
    return identity('analysis-v2',products=sorted(p['product_id'] for p in products),lat=float(lat),lon=float(lon),
                    km=float(km),polarizations=list(polarizations),filter_size=filter_size,dead_zone_db=dead_zone_db,
                    place_size_m=500,mask='all-dates-common',processing='linear-mean-then-db-v1')


def accept_result(state, slot, request_id, payload):
    """A result only belongs to the currently active request; safe against late responses."""
    if state.get(slot+'_active') != request_id:
        return False
    state[slot] = dict(request_id=request_id,payload=payload)
    return True


def current_result(state,slot,request_id):
    item=state.get(slot)
    return item['payload'] if item and item.get('request_id') == request_id else None
