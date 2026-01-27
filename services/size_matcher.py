import re
from bs4 import BeautifulSoup


def parse_size_spec(size_str):
    """
    Parse size specification string and extract inner diameters and outer diameter.
    
    Examples:
    - "25/63" -> inner: [25], outer: 63
    - "32/75 Плюс" -> inner: [32], outer: 75
    - "25+25/90" -> inner: [25], outer: 90
    - "2x20x1,9/110" -> inner: [20], outer: 110
    - "2x25x2,3+2x20x1,9/140" -> inner: [25, 20], outer: 140
    - "2x40x3,7+40x5,5+32x4,4/160" -> inner: [40, 32], outer: 160
    - "32+32 SDR11 32+25 SDR7,4/145" -> inner: [32, 25], outer: 145
    
    Returns:
        dict with 'inner_diameters' (set of ints) and 'outer_diameter' (int or None)
    """
    if not size_str:
        return {'inner_diameters': set(), 'outer_diameter': None, 'full_size': None}
    
    size_str = size_str.strip()
    
    parts = size_str.rsplit('/', 1)
    
    if len(parts) == 2:
        before_slash = parts[0].strip()
        after_slash = parts[1].strip()
        
        outer_match = re.match(r'^(\d+)', after_slash)
        outer_diameter = int(outer_match.group(1)) if outer_match else None
        
        full_size_match = re.match(r'^(\d+(?:/\d+)?)', size_str)
        full_size = full_size_match.group(1) if full_size_match else None
    else:
        before_slash = size_str
        outer_diameter = None
        full_size = None
    
    inner_diameters = set()
    
    segments = re.split(r'\+|\s+', before_slash)
    
    for segment in segments:
        segment = segment.strip()
        if not segment:
            continue
        
        segment = re.sub(r'SDR[\d,\.]+', '', segment, flags=re.IGNORECASE).strip()
        segment = segment.replace('х', 'x')
        
        nxdxt_match = re.match(r'^(\d+)x(\d+)(?:x[\d,\.]+)?$', segment, re.IGNORECASE)
        if nxdxt_match:
            diameter = int(nxdxt_match.group(2))
            inner_diameters.add(diameter)
            continue
        
        dxt_match = re.match(r'^(\d+)(?:x[\d,\.]+)?$', segment)
        if dxt_match:
            diameter = int(dxt_match.group(1))
            inner_diameters.add(diameter)
            continue
    
    return {
        'inner_diameters': inner_diameters,
        'outer_diameter': outer_diameter,
        'full_size': full_size
    }


def normalize_table_size(cell_value):
    """
    Normalize size value from table cell for comparison.
    Extracts the base size number or full size spec if contains '/'.
    
    Examples:
    - "25" -> {"value": 25, "has_slash": False, "full": "25", "inner": 25, "outer": None}
    - "32/75" -> {"value": None, "has_slash": True, "full": "32/75", "inner": 32, "outer": 75}
    - "32/75 Плюс" -> {"value": None, "has_slash": True, "full": "32/75", "inner": 32, "outer": 75}
    - "63" -> {"value": 63, "has_slash": False, "full": "63", "inner": 63, "outer": None}
    """
    if not cell_value:
        return None
    
    cell_value = str(cell_value).strip()
    
    if '/' in cell_value:
        match = re.match(r'^(\d+)/(\d+)', cell_value)
        if match:
            inner = int(match.group(1))
            outer = int(match.group(2))
            return {
                'value': None,
                'has_slash': True,
                'full': f"{inner}/{outer}",
                'inner': inner,
                'outer': outer
            }
    
    match = re.match(r'^(\d+)', cell_value)
    if match:
        val = int(match.group(1))
        return {
            'value': val,
            'has_slash': False,
            'full': match.group(1),
            'inner': val,
            'outer': None
        }
    
    return None


def filter_accessory_table(table_html, size_spec, use_outer_diameter=False):
    """
    Filter HTML table rows based on size specification matching.
    
    Args:
        table_html: HTML string containing a table
        size_spec: dict from parse_size_spec()
        use_outer_diameter: if True, match against outer diameter instead of inner
        
    Returns:
        Filtered HTML table string or None if no matches
    """
    if not table_html or not size_spec:
        return None
    
    soup = BeautifulSoup(table_html, 'html.parser')
    table = soup.find('table')
    
    if not table:
        return None
    
    thead = table.find('thead')
    header_row = None
    
    if thead:
        header_row = thead.find('tr')
    else:
        first_row = table.find('tr')
        if first_row and first_row.find('th'):
            header_row = first_row
    
    tbody = table.find('tbody')
    if tbody:
        data_rows = tbody.find_all('tr')
    else:
        all_rows = table.find_all('tr')
        if header_row and header_row in all_rows:
            data_rows = [r for r in all_rows if r != header_row]
        else:
            data_rows = all_rows[1:] if all_rows else []
    
    matched_rows = []
    
    for row in data_rows:
        cells = row.find_all(['td', 'th'])
        if not cells:
            continue
        
        first_cell_value = cells[0].get_text(strip=True)
        normalized = normalize_table_size(first_cell_value)
        
        if not normalized:
            continue
        
        if normalized['has_slash']:
            if size_spec['full_size'] and normalized['full'] == size_spec['full_size']:
                matched_rows.append(row)
            elif use_outer_diameter and size_spec['outer_diameter']:
                if normalized['outer'] == size_spec['outer_diameter']:
                    matched_rows.append(row)
            elif not use_outer_diameter and normalized['inner'] in size_spec['inner_diameters']:
                matched_rows.append(row)
        else:
            cell_value = normalized['value']
            
            if use_outer_diameter:
                if size_spec['outer_diameter'] and cell_value == size_spec['outer_diameter']:
                    matched_rows.append(row)
            else:
                if cell_value in size_spec['inner_diameters']:
                    matched_rows.append(row)
    
    if not matched_rows:
        return None
    
    new_table = soup.new_tag('table')
    
    for attr, value in table.attrs.items():
        new_table[attr] = value
    
    if 'class' not in new_table.attrs:
        new_table['class'] = []
    if 'accessory-match-table' not in new_table.get('class', []):
        new_table['class'] = list(new_table.get('class', [])) + ['accessory-match-table']
    
    if header_row:
        new_thead = soup.new_tag('thead')
        new_thead.append(header_row.__copy__())
        new_table.append(new_thead)
    
    new_tbody = soup.new_tag('tbody')
    for row in matched_rows:
        new_tbody.append(row.__copy__())
    new_table.append(new_tbody)
    
    return str(new_table)


def get_matching_accessories(size_item, accessory_blocks):
    """
    Get filtered accessory tables for a size item.
    
    Args:
        size_item: SizeItem model instance (needs 'size' attribute)
        accessory_blocks: list of AccessoryBlock model instances
        
    Returns:
        List of dicts with 'block' and 'filtered_table' for matching accessories
    """
    if not size_item or not accessory_blocks:
        return []
    
    size_value = None
    if hasattr(size_item, 'size_text'):
        size_value = size_item.size_text
    elif hasattr(size_item, 'size'):
        size_value = size_item.size
    elif hasattr(size_item, 'name'):
        size_value = size_item.name
    
    if not size_value:
        return []
    
    size_spec = parse_size_spec(size_value)
    
    if not size_spec['inner_diameters'] and not size_spec['outer_diameter']:
        return []
    
    results = []
    
    for block in accessory_blocks:
        if not block.is_active or not block.table_html:
            continue
        
        filtered = filter_accessory_table(
            block.table_html,
            size_spec,
            use_outer_diameter=block.use_outer_diameter
        )
        
        if filtered:
            results.append({
                'block': block,
                'filtered_table': filtered
            })
    
    return results
