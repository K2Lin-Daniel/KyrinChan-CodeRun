import sys
import os
from fontTools.ttLib import TTFont, TTCollection
from fontTools.ttLib.scaleUpem import scale_upem
from fontTools.merge import Merger

def main():
    if len(sys.argv) < 3:
        print("Usage: python merge_fonts.py <output_path> <input_font1> <input_font2> ...")
        sys.exit(1)
        
    output_path = sys.argv[1]
    input_paths = sys.argv[2:]
    
    print(f"Input paths: {input_paths}")
    
    # 1. Handle TrueType Collections (.ttc) by extracting to temporary .ttf files
    processed_paths = []
    temp_ttfs = []
    
    for i, path in enumerate(input_paths):
        if path.lower().endswith('.ttc'):
            print(f"Extracting font from collection {path}...")
            try:
                ttc = TTCollection(path)
                font = ttc[0]  # Get the first font in the collection
                temp_ttf = f"temp_extracted_{i}.ttf"
                font.save(temp_ttf)
                processed_paths.append(temp_ttf)
                temp_ttfs.append(temp_ttf)
            except Exception as e:
                print(f"Error extracting from collection {path}: {e}")
                sys.exit(1)
        else:
            processed_paths.append(path)
            
    # 2. Rescale and normalize all input fonts to the same UPEM (1000)
    temp_scaled_paths = []
    target_upem = 1000
    
    for i, path in enumerate(processed_paths):
        print(f"Loading and scaling {path} to {target_upem} UPEM...")
        try:
            font = TTFont(path)
            print(f"  sfntVersion: {repr(font.sfntVersion)}, Tables: {list(font.keys())}")
            
            # Scale to 1000 UPEM
            scale_upem(font, target_upem)
            
            # Normalize OS/2 table
            if 'OS/2' in font:
                os2 = font['OS/2']
                os2.version = 4
                defaults = {
                    'ulCodePageRange1': 0,
                    'ulCodePageRange2': 0,
                    'sxHeight': 0,
                    'sCapHeight': 0,
                    'usDefaultChar': 0,
                    'usBreakChar': 32,
                    'usMaxContext': 0,
                }
                for attr, default_val in defaults.items():
                    if not hasattr(os2, attr):
                        setattr(os2, attr, default_val)
                for attr in ['usLowerOpticalPointSize', 'usUpperOpticalPointSize']:
                    if hasattr(os2, attr):
                        delattr(os2, attr)
                        
            # Save to a temporary file
            temp_path = f"temp_scaled_{i}.ttf"
            font.save(temp_path)
            temp_scaled_paths.append(temp_path)
        except Exception as e:
            print(f"Error scaling font {path}: {e}")
            # Clean up
            for p in temp_scaled_paths + temp_ttfs:
                if os.path.exists(p):
                    os.remove(p)
            sys.exit(1)
            
    # 3. Find common tables and drop incompatible ones
    try:
        print("Filtering incompatible tables...")
        fonts = [TTFont(p) for p in temp_scaled_paths]
        common_tables = set(fonts[0].keys())
        for font in fonts[1:]:
            common_tables.intersection_update(font.keys())
            
        print(f"Common tables: {common_tables}")
        
        for i, font in enumerate(fonts):
            for tag in list(font.keys()):
                if tag not in common_tables:
                    print(f"  Removing table {tag} from font {temp_scaled_paths[i]}")
                    del font[tag]
            font.save(temp_scaled_paths[i])
            font.close()
            
    except Exception as e:
        print(f"Error filtering tables: {e}")
        # Clean up
        for p in temp_scaled_paths + temp_ttfs:
            if os.path.exists(p):
                os.remove(p)
        sys.exit(1)
        
    try:
        # 4. Merge the rescaled fonts
        print("Merging rescaled fonts...")
        merger = Merger()
        merged_font = merger.merge(temp_scaled_paths)
        
        # 5. Rename the merged font to "SandboxFont"
        new_family_name = "SandboxFont"
        name_table = merged_font["name"]
        
        # Remove conflicting name records that could override family name
        records_to_keep = []
        for r in name_table.names:
            if r.nameID not in (16, 17, 18, 21, 22, 25):
                records_to_keep.append(r)
        name_table.names = records_to_keep
        
        # Update name records to use SandboxFont name
        name_table.setName(new_family_name, 1, 3, 1, 0x409)  # Family name
        name_table.setName("Regular", 2, 3, 1, 0x409)       # Subfamily name
        name_table.setName(f"{new_family_name} Regular", 4, 3, 1, 0x409)  # Full name
        name_table.setName(f"{new_family_name}-Regular", 6, 3, 1, 0x409)  # Postscript name
        
        name_table.setName(new_family_name, 1, 1, 0, 0) # Mac Family name
        name_table.setName("Regular", 2, 1, 0, 0)       # Mac Subfamily name
        name_table.setName(f"{new_family_name} Regular", 4, 1, 0, 0)  # Mac Full name
        name_table.setName(f"{new_family_name}-Regular", 6, 1, 0, 0)  # Mac Postscript name
        
        # Make sure directory exists
        out_dir = os.path.dirname(output_path)
        if out_dir and not os.path.exists(out_dir):
            os.makedirs(out_dir, exist_ok=True)
            
        # 6. Save the merged font
        merged_font.save(output_path)
        print(f"Merged font successfully saved to {output_path}")
        
    except Exception as e:
        import traceback
        print(f"Error merging fonts: {e}")
        traceback.print_exc()
        sys.exit(1)
    finally:
        # Clean up all temporary files
        for path in temp_scaled_paths + temp_ttfs:
            if os.path.exists(path):
                os.remove(path)

if __name__ == "__main__":
    main()
