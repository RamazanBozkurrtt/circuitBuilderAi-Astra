"""Apply the Phase 3G eight-leg microphone correction to Sheet 2 and root only."""
from pathlib import Path
import copy
import uuid

import sexpdata as sx

BASE = Path(__file__).resolve().parents[2] / "hardware" / "kicad"
S = sx.Symbol


def n(key, *args):
    return [S(key), *args]


def kids(obj, key):
    return [x for x in obj if isinstance(x, list) and x and str(x[0]) == key]


def tag(obj, key):
    return next(iter(kids(obj, key)), None)


def unique(key):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "astra/phase3g/mic/" + key))


def fx(size=1.016, hidden=False, justify=None):
    out = n("effects", n("font", n("size", size, size)))
    if hidden:
        out.append(n("hide", S("yes")))
    if justify:
        out.append(n("justify", S(justify)))
    return out


def prop(key, value, x, y, hidden=False):
    return n("property", key, value, n("at", x, y, 0), fx(hidden=hidden))


def save(path, obj):
    path.write_text(sx.dumps(obj) + "\n", encoding="utf-8")


MIC_RAW = [f"MIC{ch}_{pol}_RAW" for ch in range(1, 5) for pol in ("P", "N")]
MIC_ISO = [f"MIC{ch}_{pol}_ISO" for ch in range(1, 5) for pol in ("P", "N")]
OLD = {f"MIC{ch}_AFTER_100R": f"MIC{ch}_P_RAW" for ch in range(1, 5)}
OLD.update({f"AFE{ch}_BEFORE_4u7": f"MIC{ch}_P_ISO" for ch in range(1, 5)})
for ch in range(1, 5):
    for pol in ("P", "N"):
        OLD[f"AFE{ch}{pol}_AFTER_47R"] = f"AFE{ch}_{pol}_RAW"
        OLD[f"ADC_AIN{ch}{pol}"] = f"ADC{ch}_{pol}_ISO"
OLD.update({"ADC_VREF": "ADC_VREF_RAW", "AFE_VCM_INPUT": "AFE_VCM_ISO"})

PINS = {
    "1": ("SEL", "input"), "2": ("S1A", "passive"),
    "3": ("S1B", "passive"), "4": ("D1", "passive"),
    "5": ("S2A", "passive"), "6": ("S2B", "passive"),
    "7": ("D2", "passive"), "8": ("GND", "power_in"),
    "9": ("D3", "passive"), "10": ("S3B", "passive"),
    "11": ("S3A", "passive"), "12": ("D4", "passive"),
    "13": ("S4B", "passive"), "14": ("S4A", "passive"),
    "15": ("EN", "input"), "16": ("VDD", "power_in"),
}
LEFT = [16, 15, 1, 8, 2, 3, 5, 6, 11, 10, 14, 13]
RIGHT = [4, 7, 9, 12]


def make_symbol():
    name = "TMUX1574PWR"
    footprint = "Package_SO:TSSOP-16_4.4x5mm_P0.65mm"
    url = "https://www.ti.com/lit/ds/symlink/tmux1574.pdf"
    body = n("symbol", name, n("pin_names", n("offset", 0.762)),
             n("in_bom", S("yes")), n("on_board", S("yes")),
             prop("Reference", "U", 0, 0), prop("Value", name, 0, 0),
             prop("Footprint", footprint, 0, 0, True),
             prop("Datasheet", url, 0, 0, True))
    height = 33.02
    body.append(n("symbol", name + "_0_1",
                  n("rectangle", n("start", -17.78, height / 2),
                    n("end", 17.78, -height / 2),
                    n("stroke", n("width", 0.254), n("type", S("default"))),
                    n("fill", n("type", S("background"))))))
    unit = n("symbol", name + "_1_1")
    offsets = {}
    for side, numbers in (("left", LEFT), ("right", RIGHT)):
        for j, number in enumerate(numbers):
            x = -22.86 if side == "left" else 22.86
            y = round(height / 2 - 3.81 - j * 2.54, 5)
            ang = 0 if side == "left" else 180
            pin_name, kind = PINS[str(number)]
            unit.append(n("pin", S(kind), S("line"), n("at", x, y, ang),
                          n("length", 5.08), n("name", pin_name, fx()),
                          n("number", str(number), fx())))
            offsets[str(number)] = (x, y, ang)
    body.append(unit)
    assert sorted(offsets) == sorted(PINS)
    return body, offsets


symbol, offsets = make_symbol()
lib_path = BASE / "Astra_Sequencing.kicad_sym"
library = sx.loads(lib_path.read_text(encoding="utf-8"))
assert not any(x[1] == "TMUX1574PWR" for x in kids(library, "symbol"))
library.append(copy.deepcopy(symbol))
save(lib_path, library)

sheet_path = BASE / "power_regulation.kicad_sch"
sheet = sx.loads(sheet_path.read_text(encoding="utf-8"))
assert not any(x[1] == "Astra_Sequencing:TMUX1574PWR" for x in kids(tag(sheet, "lib_symbols"), "symbol"))
embedded = copy.deepcopy(symbol)
embedded[1] = "Astra_Sequencing:TMUX1574PWR"
tag(sheet, "lib_symbols").append(embedded)

# The two old microphone pair groups occupy these otherwise empty rectangles.
# Preserve the AFE/ADC and VREF switches at y=890 and x=100/240 at y=1050.
old_refs = {f"U{x}" for x in range(240, 244)} | {f"C{x}" for x in range(360, 364)}


def in_old_area(x, y):
    return 990 <= y <= 1110 and ((420 <= x <= 710) or (820 <= x <= 1110))


def remove_old(obj):
    kind = str(obj[0])
    if kind == "symbol":
        ref = next((p[2] for p in kids(obj, "property") if p[1] == "Reference"), None)
        return ref in old_refs
    if kind in ("label", "text", "no_connect", "junction"):
        at = tag(obj, "at")
        return at is not None and in_old_area(at[1], at[2])
    if kind == "wire":
        pts = kids(tag(obj, "pts"), "xy")
        return bool(pts) and all(in_old_area(p[1], p[2]) for p in pts)
    return False


sheet[:] = [x for x in sheet if not (isinstance(x, list) and x and remove_old(x))]
assert not any(next((p[2] for p in kids(x, "property") if p[1] == "Reference"), None) in old_refs
               for x in kids(sheet, "symbol"))


def wire_label(net, x, y, angle):
    dx, dy = {0: (-5.08, 0), 180: (5.08, 0)}[angle]
    ex, ey = round(x + dx, 5), round(y + dy, 5)
    sheet.append(n("wire", n("pts", n("xy", x, y), n("xy", ex, ey)),
                   n("stroke", n("width", 0), n("type", S("default"))),
                   n("uuid", unique(f"wire/{net}/{x}/{y}"))))
    sheet.append(n("label", net, n("at", ex, ey, 0),
                   fx(.889, justify="right" if angle == 0 else "left"),
                   n("uuid", unique(f"label/{net}/{ex}/{ey}"))))


def add_device(ref, x, y, supply, nets, pair):
    instance = n("symbol", n("lib_id", "Astra_Sequencing:TMUX1574PWR"),
                 n("at", x, y, 0), n("unit", 1), n("in_bom", S("yes")),
                 n("on_board", S("yes")), n("dnp", S("no")),
                 n("uuid", unique(ref)))
    for key, value, hidden in (
        ("Reference", ref, False), ("Value", "TMUX1574PWR", False),
        ("Footprint", "Package_SO:TSSOP-16_4.4x5mm_P0.65mm", True),
        ("Datasheet", "https://www.ti.com/lit/ds/symlink/tmux1574.pdf", True),
        ("Function", f"Phase 3G microphone channels {pair}; {supply} side", True),
    ):
        instance.append(prop(key, value, x, y - 22.86 + (0 if key == "Reference" else 2.54), hidden))
    instance.append(n("instances", n("project", "circuitBuilderAi-Astra",
                      n("path", "/a89958ad-9daf-4465-87fb-0da6e733aead/c46ad3ab-53c4-4782-9638-c5343c581d6a",
                        n("reference", ref), n("unit", 1)))))
    for number, (ox, oy, angle) in offsets.items():
        px, py = round(x + ox, 5), round(y - oy, 5)
        instance.append(n("pin", number, n("uuid", unique(ref + "/" + number))))
        net = nets[number]
        wire_label(net, px, py, angle)
    sheet.append(instance)


def add_cap(ref, x, y, supply):
    # Match the existing 100 nF Sheet 2 bypass component construction.
    template = next(x for x in kids(sheet, "symbol")
                    if next((p[2] for p in kids(x, "property") if p[1] == "Reference"), None) == "C359")
    part = copy.deepcopy(template)
    tag(part, "at")[1:3] = [x, y]
    tag(part, "uuid")[1] = unique(ref)
    old_x, old_y = tag(template, "at")[1:3]
    for p in kids(part, "property"):
        if p[1] == "Reference":
            p[2] = ref
        at = tag(p, "at")
        if at:
            at[1:3] = [round(at[1] + x - old_x, 5), round(at[2] + y - old_y, 5)]
    path = tag(tag(part, "instances"), "project")
    tag(tag(path, "path"), "reference")[1] = ref
    for p in kids(part, "pin"):
        tag(p, "uuid")[1] = unique(ref + "/" + p[1])
    sheet.append(part)
    for number, dy, net in (("1", -3.81, supply), ("2", 3.81, "POWER_GND")):
        px, py = x, round(y + dy, 5)
        ey = round(py + (-2.54 if number == "1" else 2.54), 5)
        sheet.append(n("wire", n("pts", n("xy", px, py), n("xy", px, ey)),
                       n("stroke", n("width", 0), n("type", S("default"))),
                       n("uuid", unique(f"wire/{ref}/{number}"))))
        sheet.append(n("label", net, n("at", px, ey, 0), fx(.889),
                       n("uuid", unique(f"label/{ref}/{number}"))))


channels = ((1, 2, 500.38, 640.08, 435.61, 575.31, 1050.29, "U240", "U241", "C360", "C361"),
            (3, 4, 900.43, 1040.13, 835.66, 975.36, 1050.29, "U242", "U243", "C362", "C363"))
for ch1, ch2, xa, xb, ca, cb, y, ra, rb, rca, rcb in channels:
    legs = [(ch, pol) for ch in (ch1, ch2) for pol in ("P", "N")]
    nets_a = {"16": "2V8_MIC", "8": "POWER_GND", "15": "POWER_GND", "1": "POWER_GND"}
    nets_b = {"16": "5V_AFE", "8": "POWER_GND", "15": "POWER_GND", "1": "POWER_GND"}
    for j, (ch, pol) in enumerate(legs):
        src, drain, spare = ((2, 4, 3), (5, 7, 6), (11, 9, 10), (14, 12, 13))[j]
        mid = f"MIC{ch}_{pol}_MID"
        nets_a.update({str(src): f"MIC{ch}_{pol}_RAW", str(drain): mid, str(spare): "POWER_GND"})
        nets_b.update({str(src): mid, str(drain): f"MIC{ch}_{pol}_ISO", str(spare): "POWER_GND"})
    add_device(ra, xa, y, "2V8_MIC", nets_a, f"{ch1}/{ch2}")
    add_device(rb, xb, y, "5V_AFE", nets_b, f"{ch1}/{ch2}")
    add_cap(rca, ca, y, "2V8_MIC")
    add_cap(rcb, cb, y, "5V_AFE")
    sheet.append(n("text", f"Phase 3G: MIC{ch1}/{ch2} P,N; EN=SEL=0; spare SxB grounded; rail-off isolation.",
                   n("at", xa - 76.2, 1007, 0), fx(1.27, justify="left"),
                   n("uuid", unique(f"note/{ch1}"))))

# Existing AFE/ADC/VREF switches keep their wiring. Rename only their future
# endpoint labels and Sheet 2 ports to the corrected Phase 3G contract.
for obj in sheet:
    if isinstance(obj, list) and obj and str(obj[0]) in ("label", "hierarchical_label"):
        obj[1] = OLD.get(obj[1], obj[1])

for i, net in enumerate(MIC_RAW + MIC_ISO):
    if net.endswith("_P_RAW") or net.endswith("_P_ISO"):
        continue
    x, y = round(20.32 + i * 78.74, 5), 29.21
    sheet.append(n("hierarchical_label", net, n("shape", S("passive")),
                   n("at", x, y, 0), fx(.889, justify="left"),
                   n("uuid", unique("hier/" + net))))
    sheet.append(n("wire", n("pts", n("xy", x, y), n("xy", x, 31.75)),
                   n("stroke", n("width", 0), n("type", S("default"))),
                   n("uuid", unique("hierwire/" + net))))
    sheet.append(n("label", net, n("at", x, 31.75, 0), fx(.889),
                   n("uuid", unique("hierlabel/" + net))))

save(sheet_path, sheet)

root_path = BASE / "circuitBuilderAi-Astra.kicad_sch"
root = sx.loads(root_path.read_text(encoding="utf-8"))
sheet_box = next(x for x in kids(root, "sheet") if any(p[1] == "Sheetfile" and
                 p[2] == "power_regulation.kicad_sch" for p in kids(x, "property")))
for pin in kids(sheet_box, "pin"):
    pin[1] = OLD.get(pin[1], pin[1])
existing = {p[1] for p in kids(sheet_box, "pin")}
for i, net in enumerate(x for x in MIC_RAW + MIC_ISO if x not in existing):
    y = round(304.8 + 5.08 * i, 2)
    pin = n("pin", net, S("passive"), n("at", 800, y, 0),
            n("uuid", unique("rootpin/" + net)), fx())
    sheet_box.append(pin)
    root.append(n("no_connect", n("at", 800, y),
                  n("uuid", unique("rootnc/" + net))))
assert len({p[1] for p in kids(sheet_box, "pin")}) == len(kids(sheet_box, "pin"))
save(root_path, root)
print("Phase 3G microphone and hierarchy amendment applied")
