"""Package-library artifact only; no board/placement/routing is created.

TPS62135 SLVSBH3B, RGX0011A drawing 4221908/A, pp.44-46.
Drawing p.45 is used in its displayed land-pattern orientation.
"""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
dest=ROOT/'hardware/kicad/Astra_Sequencing.pretty'
dest.mkdir(exist_ok=True)
text=['(footprint "Texas_RGX0011A" (version 20241229) (generator "pcbnew") (layer "F.Cu")',
'(descr "TI RGX0011A 11-pad VQFN 3x2mm; 4221908/A 10/2015, TPS62135 pp44-46. No separate EP.") (attr smd)',
'(fp_text reference "REF**" (at 0 -2.5) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))',
'(fp_text value "Texas_RGX0011A" (at 0 2.5) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))',
'(fp_rect (start -1.5 -1) (end 1.5 1) (stroke (width 0.1) (type default)) (fill none) (layer "F.Fab"))',
'(fp_rect (start -1.75 -1.95) (end 1.75 1.95) (stroke (width 0.05) (type default)) (fill none) (layer "F.CrtYd"))',
'(fp_circle (center -1.5 -0.5) (end -1.4 -0.5) (stroke (width 0.15) (type default)) (fill none) (layer "F.SilkS"))']
for n,y in [(1,-0.5),(2,0),(3,0.5)]:
    # Solder-mask defined bar pads; three stencil apertures per bar per p.46.
    text.append(f'(pad "{n}" smd roundrect (at 0 {y}) (size 2.4 0.25) (layers "F.Cu" "F.Mask") (roundrect_rratio 0.2) (solder_mask_margin -0.025))')
    for x in [-0.86,0,0.86]:text.append(f'(pad "" smd rect (at {x} {y}) (size 0.66 0.25) (layers "F.Paste"))')
for n,x,y in [(11,-0.75,-1.4),(10,-0.25,-1.4),(9,0.25,-1.4),(8,0.75,-1.4),(4,-0.75,1.4),(5,-0.25,1.4),(6,0.25,1.4),(7,0.75,1.4)]:
    text.append(f'(pad "{n}" smd roundrect (at {x} {y}) (size 0.25 0.6) (layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.2))')
text.append(')')
(dest/'Texas_RGX0011A.kicad_mod').write_text('\n'.join(text)+'\n')
table=ROOT/'hardware/kicad/fp-lib-table'
assert not table.exists(), 'Do not overwrite an existing footprint table'
table.write_text('(fp_lib_table (version 7) (lib (name "Astra_Sequencing") (type "KiCad") (uri "${KIPRJMOD}/Astra_Sequencing.pretty") (options "") (descr "Verified Sheet 2 package definition; no PCB")))\n')
