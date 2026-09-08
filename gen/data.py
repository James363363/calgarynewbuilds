# -*- coding: utf-8 -*-
"""Data layer for calgarynewbuilds.ca.
In CI (Cloudflare Pages) it loads data/source.json.gz.b64 — no third-party deps.
Locally, extract_from_xlsx() refreshes that file from the master workbook (needs pandas)."""
import re, json, math, os, gzip, base64

SITE = 'https://calgarynewbuilds.ca'
HERE = os.path.dirname(os.path.abspath(__file__))
SRC_JSON = os.path.join(HERE, '..', 'data', 'source.json.gz.b64')

def clean(v):
    if v is None: return ''
    if isinstance(v, float) and math.isnan(v): return ''
    s = str(v).strip()
    return '' if s in ('nan', 'NaN', '—', '-') else s

def slugify(name):
    s = name.lower()
    s = s.split('/')[0].split('(')[0].strip()
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')
    return s

def is_dead(notes):
    return bool(re.search(r'\bSOLD OUT\b|NOT VERIFIED as currently offered|appears sold out|fully sold', notes, re.I))

def price_sort_key(p):
    """Rough numeric value from a price string for sorting; None if unknown."""
    p = clean(p)
    if not p: return None
    m = re.search(r'\$\s?([\d,]+(?:\.\d+)?)\s?(M|k)?', p, re.I)
    if not m: return None
    n = float(m.group(1).replace(',', ''))
    suf = (m.group(2) or '').lower()
    if suf == 'm': n *= 1_000_000
    elif suf == 'k': n *= 1_000
    if n < 10_000: n *= 1000
    low = re.search(r'\blow\b', p, re.I); high = re.search(r'\bhigh\b', p, re.I); mid = re.search(r'\bmid\b', p, re.I)
    if n >= 100_000 and n % 100_000 == 0:
        if low: n += 10_000
        elif mid: n += 50_000
        elif high: n += 80_000
    return int(n)

def product_bucket(line):
    l = line.lower()
    if 'condo' in l: return 'Condos'
    if 'town' in l: return 'Townhomes'
    if 'duplex' in l or 'paired' in l or 'side by side' in l or 'semi' in l: return 'Duplex / Paired'
    if 'estate' in l: return 'Estate'
    if 'front' in l: return 'Front-Drive'
    if 'laned' in l or 'lane' in l: return 'Laned'
    if 'bungalow' in l: return 'Bungalow'
    if 'single' in l: return 'Single Family'
    return 'Other'

def extract_from_xlsx(xlsx_path):
    """Local-only: parse the master workbook into the raw structure stored in source.json."""
    import pandas as pd
    xl = pd.ExcelFile(xlsx_path)
    comms = []
    cdf = xl.parse('Communities')
    for _, r in cdf.iterrows():
        name = clean(r['Community'])
        if not name: continue
        comms.append({
            'name': name, 'slug': slugify(name),
            'quadrant': clean(r['Quadrant']), 'area': clean(r['Area / Location']),
            'developer': clean(r['Land Developer']), 'status': clean(r['Status']),
            'price_from': clean(r['Price From (approx.)']), 'website': clean(r['Website']),
            'notes': clean(r['Notes']),
            'lat': float(r['Lat']) if clean(r['Lat']) else None,
            'lng': float(r['Lng']) if clean(r['Lng']) else None,
            'sales_centre': clean(r['Sales Centre / Showhomes']),
            'geo_conf': clean(r['Geo Confidence']).lower(),
        })
    idf = xl.parse('Inventory')
    offers = []
    for i, r in idf.iterrows():
        notes = clean(r['Notes'])
        o = {
            'id': i, 'community': clean(r['Community']), 'quadrant': clean(r['Quadrant']),
            'builder': clean(r['Builder']), 'line': clean(r['Product Line']),
            'bucket': product_bucket(clean(r['Product Line'])),
            'price': clean(r['Price From']), 'price_n': price_sort_key(r['Price From']),
            'gst': clean(r['GST Note']), 'size': clean(r['Size (sq ft)']),
            'beds': clean(r['Beds']), 'baths': clean(r['Baths']), 'garage': clean(r['Garage']),
            'suite': clean(r['Legal Suite']), 'multigen': clean(r['Multi-Gen']),
            'walkout': clean(r['Walkout']), 'netzero': clean(r['Net-Zero / Solar']),
            'qp': clean(r['Quick Poss.']), 'notes': notes, 'source': clean(r['Source']),
            'dead': is_dead(notes),
        }
        o['cslug'] = slugify(o['community'])
        offers.append(o)
    scdf = xl.parse('Sales Contacts')
    contacts = []
    for _, r in scdf.iterrows():
        c = {k: clean(r[col]) for k, col in [
            ('builder','Builder'),('community','Community'),('phone','Phone'),
            ('email','Email'),('hours','Hours'),('person','Contact Person'),('source','Source')]}
        if c['builder']: contacts.append(c)
    qdf = xl.parse('Spec Homes (QP)', header=1)
    qps = []
    for _, r in qdf.iterrows():
        q = {k: clean(r[col]) for k, col in [
            ('builder','Builder'),('community','Community'),('count','# QP Listed'),
            ('range','Price Range'),('possession','Earliest Possession'),('source','Source')]}
        if q['builder']: qps.append(q)
    bdf = xl.parse('Builders')
    builders = []
    for _, r in bdf.iterrows():
        b = {
            'name': clean(r['Builder']), 'parent': clean(r['Parent / Group']),
            'category': clean(r['Category']), 'segments': clean(r['Product Segments']),
            'website': clean(r['Website']), 'realtor': clean(r['Realtor Program']),
        }
        if b['name']: builders.append(b)
    return {'comms': comms, 'offers': offers, 'contacts': contacts, 'qps': qps, 'builders': builders}

def save_source(bundle, path=SRC_JSON):
    raw = json.dumps(bundle, ensure_ascii=False, separators=(',', ':'), sort_keys=True).encode('utf-8')
    gz = gzip.compress(raw, 9, mtime=0)
    b64 = base64.b64encode(gz).decode('ascii')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        f.write('\n'.join(b64[i:i+120] for i in range(0, len(b64), 120)) + '\n')

def load():
    with open(SRC_JSON) as f:
        b64 = f.read().replace('\n', '')
    bundle = json.loads(gzip.decompress(base64.b64decode(b64)).decode('utf-8'))
    return bundle['comms'], bundle['offers'], bundle['contacts'], bundle['qps'], bundle['builders']
