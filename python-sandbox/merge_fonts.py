import sys
import os
from fontTools.ttLib import TTFont
from fontTools.ttLib.scaleUpem import scale_upem
from fontTools.merge import Merger

def main():
    if len(sys.argv) < 3:
        print("Usage: python merge_fonts.py <output_path> <input_font1> <input_font2> ...")
        sys.exit(1)
        
    output_path = sys.argv[1]
    input_paths = sys.argv[2:]
    
    print(f"Loading input fonts: {input_paths}")
    
    # 1. Rescale all input fonts to the same UPEM (1000)
    rescaled_fonts = []
    temp_paths = []
    target_upem = 1000
    
    for i, path in enumerate(input_paths):
        print(f"Loading and scaling {path} to {target_upem} UPEM...")
        try:
            font = TTFont(path)
            # Scale to 1000 UPEM
            scale_upem(font, target_upem)
            # Save to a temporary file
            temp_path = f"temp_scaled_{i}.ttf"
            font.save(temp_path)
            temp_paths.append(temp_path)
        except Exception as e:
            print(f"Error scaling font {path}: {e}")
            # Clean up and exit
            for p in temp_paths:
                if os.path.exists(p):
                    os.remove(p)
            sys.exit(1)
        
    try:
        # 2. Merge the rescaled fonts
        print("Merging rescaled fonts...")
        merger = Merger()
        merged_font = merger.merge(temp_paths)
        
        # 3. Rename the merged font to "SandboxFont"
        new_family_name = "SandboxFont"
        name_table = merged_font["name"]
        
        # Update name records to use SandboxFont name
        name_table.setName(new_family_name, 1, 3, 1, 0x409)  # Family name
        name_table.setName("Regular", 2, 3, 1, 0x409)       # Subfamily name
        name_table.setName(f"{new_family_name} Regular", 4, 3, 1, 0x409)  # Full name
        name_table.setName(f"{new_family_name}-Regular", 6, 3, 1, 0x409)  # Postscript name
        
        name_table.setName(new_family_name, 1, 1, 0, 0) # Mac Family name
        name_table.setName("Regular", 2, 1, 0, 0)       # Mac Subfamily name
        name_table.setName(f"{new_family_name} Regular", 4, 1, 0, 0)  # Mac Full name
        name_table.setName(f"{new_family_name}-Regular", 6, 1, 0, 0)  # Mac Postscript name
        
        # 4. Save the merged font
        merged_font.save(output_path)
        print(f"Merged font successfully saved to {output_path}")
        
    except Exception as e:
        print(f"Error merging fonts: {e}")
        sys.exit(1)
    finally:
        # Clean up temporary rescaled files
        for path in temp_paths:
            if os.path.exists(path):
                os.remove(path)

if __name__ == "__main__":
    main()
