import ezdxf
import os

def parse_to_float(size_str):
# ... (rest of function remains same)
    # Remove units and extra spaces
    size_str = size_str.replace("mm", "").replace("\"", "").strip()
    
    # Check if it's a fraction (e.g., 1/4 or 1 1/16)
    if "/" in size_str:
        if " " in size_str:
            parts = size_str.split(" ")
            try:
                whole = float(parts[0])
                frac = parts[1].split("/")
                decimal = whole +S (float(frac[0]) / float(frac[1]))
            except (ValueError, IndexError):
                return 0.0
        else:
            frac = size_str.split("/")
            try:
                decimal = float(frac[0]) / float(frac[1])
            except (ValueError, IndexError):
                return 0.0
        return decimal
    
    # Otherwise assume it's a simple number
    try:
        return float(size_str)
    except ValueError:
        return 0.0

def create_wrench_holder_dxf(filename=None):
    if filename is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        filename = os.path.join(script_dir, "updated_wrench_holder.dxf")
        
    doc = ezdxf.new("R2010")
    # Set units to Millimeters (4)
    doc.header['$INSUNITS'] = 4
    msp = doc.modelspace()
    IN_TO_MM = 25.4

    # SAE Data: (Part No, Size, Length in inches, Box End Thickness in inches)
    sae_raw = [
        ("3108", "1/4", 5.00, 0.23),
        ("3110", "5/16", 5.50, 0.25),
        ("3111", "11/32", 5.50, 0.28),
        ("3112", "3/8", 6.00, 0.30),
        ("3114", "7/16", 6.50, 0.33),
        ("3116", "1/2", 7.00, 0.36),
        ("3118", "9/16", 7.50, 0.35),
        ("3120", "5/8", 8.06, 0.41),
        ("3122", "11/16", 8.87, 0.42),
        ("3124", "3/4", 9.75, 0.45),
        ("3126", "13/16", 10.62, 0.46),
        ("3128", "7/8", 11.50, 0.48),
        ("3130", "15/16", 12.37, 0.51),
        ("3132", "1", 13.25, 0.55),
        ("3134", "1 1/16", 14.12, 0.58),
    ]
    
    # Metric Data: (Part No, Size, Overall Length (mm), Box End Thickness (mm))
    metric_raw = [
        ("MC6", "6 mm", 127, 6.0),
        ("MC7", "7 mm", 127, 6.0),
        ("MC8", "8 mm", 140, 6.8),
        ("MC9", "9 mm", 152, 7.8),
        ("MC10", "10 mm", 165, 8.2),
        ("MC11", "11 mm", 165, 8.2),
        ("MC12", "12 mm", 178, 8.6),
        ("MC13", "13 mm", 178, 8.6),
        ("MC14", "14 mm", 191, 9.0),
        ("MC15", "15 mm", 191, 9.0),
        ("MC16", "16 mm", 205, 10.2),
        ("MC17", "17 mm", 225, 10.9),
        ("MC18", "18 mm", 225, 10.9),
        ("MC19", "19 mm", 248, 11.7),
        ("MC20", "20 mm", 270, 12.4),
        ("MC21", "21 mm", 270, 12.4),
        ("MC22", "22 mm", 292, 12.4),
        ("MC23", "23 mm", 292, 12.4),
        ("MC24", "24 mm", 314, 14.0),
    ]

    # Process SAE
    sae_processed = []
    for p, s, l, t in sae_raw:
        size_in = parse_to_float(s)
        size_mm = size_in * IN_TO_MM
        sae_processed.append({
            'part_no': p,
            'size_label': s + "\"",
            'length': round(l * IN_TO_MM, 2),
            'size_mm': size_mm,
            'slot_width': round(t * IN_TO_MM, 2)
        })
    # SAE: Smallest to Largest (Ascending) from top to bottom
    sae_processed.sort(key=lambda x: x['size_mm'])

    # Process Metric
    metric_processed = []
    for p, s, l, t in metric_raw:
        size_mm = parse_to_float(s)
        metric_processed.append({
            'part_no': p,
            'size_label': s,
            'length': l,
            'size_mm': size_mm,
            'slot_width': t
        })
    # Metric: Biggest to Smallest (Descending) from top to bottom
    metric_processed.sort(key=lambda x: x['size_mm'], reverse=True)

    spacings = [10.0, 9.0, 8.0, 7.0, 6.0, 5.0]
    text_height = 5.0
    
    # SAE: Point Right, Text on Left
    current_y = 0.0
    sae_base_x = 50.0
    for i, w in enumerate(sae_processed):
        sw = w['slot_width']
        l = w['length']
        size_mm = w['size_mm']
        radius = size_mm / 2
        
        # Rectangle
        points = [
            (sae_base_x, current_y),
            (sae_base_x + l, current_y),
            (sae_base_x + l, current_y - sw),
            (sae_base_x, current_y - sw),
            (sae_base_x, current_y)
        ]
        msp.add_lwpolyline(points, dxfattribs={'layer': 'Rectangles'})

        # Circle at right end
        msp.add_circle((sae_base_x + l - radius, current_y - radius), radius=radius, dxfattribs={'layer': 'Circles'})

        # Text on left
        msp.add_text(w['part_no'], 
                     dxfattribs={'height': text_height, 'layer': 'Text'}
                     ).set_placement((sae_base_x - 2, current_y - sw/2), align=ezdxf.enums.TextEntityAlignment.RIGHT)
        msp.add_text(w['size_label'], 
                     dxfattribs={'height': text_height, 'layer': 'Text'}
                     ).set_placement((sae_base_x - 2, current_y - sw), align=ezdxf.enums.TextEntityAlignment.RIGHT)
        
        s = spacings[i] if i < len(spacings) else 5.0
        current_y -= (sw + s)

    # Metric: Point Left, Text on Right
    current_y = 0.0
    # Determine Metric base X (the right edge where text is)
    # Let's put it some distance from the SAE set
    max_sae_len = max(w['length'] for w in sae_processed)
    max_metric_len = max(w['length'] for w in metric_processed)
    metric_base_x = sae_base_x + max_sae_len + max_metric_len + 100.0
    
    for i, w in enumerate(metric_processed):
        sw = w['slot_width']
        l = w['length']
        size_mm = w['size_mm']
        radius = size_mm / 2
        
        # Rectangle points LEFT from metric_base_x
        points = [
            (metric_base_x, current_y),
            (metric_base_x - l, current_y),
            (metric_base_x - l, current_y - sw),
            (metric_base_x, current_y - sw),
            (metric_base_x, current_y)
        ]
        msp.add_lwpolyline(points, dxfattribs={'layer': 'Rectangles'})
        
        # Circle at left end
        msp.add_circle((metric_base_x - l + radius, current_y - radius), radius=radius, dxfattribs={'layer': 'Circles'})
        
        # Text on right
        msp.add_text(w['part_no'], 
                     dxfattribs={'height': text_height, 'layer': 'Text'}
                     ).set_placement((metric_base_x + 2, current_y - sw/2), align=ezdxf.enums.TextEntityAlignment.LEFT)
        msp.add_text(w['size_label'], 
                     dxfattribs={'height': text_height, 'layer': 'Text'}
                     ).set_placement((metric_base_x + 2, current_y - sw), align=ezdxf.enums.TextEntityAlignment.LEFT)
        
        s = spacings[i] if i < len(spacings) else 5.0
        current_y -= (sw + s)

    doc.saveas(filename)
    print(f"File '{filename}' created successfully.")

if __name__ == "__main__":
    create_wrench_holder_dxf()
