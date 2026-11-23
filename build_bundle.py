"""Build the Krita makeup brush bundle from the generated source scans."""

from dataclasses import dataclass
from hashlib import md5
from io import BytesIO
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZIP_STORED, ZipFile, ZipInfo
import xml.etree.ElementTree as ET

from PIL import Image, ImageDraw, ImageOps, PngImagePlugin


ROOT = Path(__file__).resolve().parent
TITLE = "Makeup Atelier"
MIME = "application/x-krita-resourcebundle"
MANIFEST = "urn:oasis:names:tc:opendocument:xmlns:manifest:1.0"
META = "urn:oasis:names:tc:opendocument:xmlns:meta:1.0"
DC = "http://purl.org/dc/elements/1.1/"
for prefix, namespace in {"manifest": MANIFEST, "meta": META, "dc": DC}.items():
    ET.register_namespace(prefix, namespace)


@dataclass(frozen=True)
class Brush:
    name: str
    slug: str
    source: str
    tile: tuple[int, int, int, int] | None
    size: int
    spacing: float
    opacity: float
    flow: float
    rotation: str
    pressure_size: str | None
    color: str
    paper: str
    smudge: bool = False

    @property
    def filename(self):
        return f"makeup-atelier-{self.slug}.png"


BRUSHES = (
    Brush("Foundation Sponge", "foundation-sponge", "makeup-imprints", (0, 0, 2, 2), 145, 0.42,
          0.86, 0.66, "fuzzy", "0,0.62;1,1;", "#a8614d", "#f7e6d9"),
    Brush("Powder Veil", "powder-veil", "makeup-imprints", (1, 0, 2, 2), 205, 0.19,
          0.62, 0.24, "fuzzy", None, "#b65d7d", "#f7e4e8"),
    Brush("Eyeshadow Feather", "eyeshadow-feather", "makeup-imprints", (0, 1, 2, 2), 110, 0.18,
          0.78, 0.48, "drawingangle", "0,0.5;1,1;", "#754367", "#f1e4ee"),
    Brush("Mica Dust", "mica-dust", "mica-flecks", None, 165, 0.34,
          0.93, 0.83, "fuzzy", None, "#f6dbaa", "#59404d"),
    Brush("Wing Liner", "wing-liner", "makeup-details", (0, 0, 2, 2), 27, 0.09,
          1, 0.96, "drawingangle", "0,0.10;0.25,0.3;1,1;", "#31202b", "#f8e7dd"),
    Brush("Petal Blush", "petal-blush", "makeup-details", (1, 0, 2, 2), 195, 0.31,
          0.69, 0.34, "fuzzy", "0,0.58;1,1;", "#c95470", "#f9e4e2"),
    Brush("Sun Freckles", "sun-freckles", "makeup-details", (0, 1, 2, 2), 155, 0.73,
          0.81, 0.8, "drawingangle", "0,0.59;1,1;", "#8b482f", "#f2d8ba"),
    Brush("Velvet Lip Stain", "velvet-lip-stain", "makeup-details", (1, 1, 2, 2), 94, 0.28,
          0.77, 0.45, "drawingangle", "0,0.5;1,1;", "#a63556", "#f5dbe2"),
    Brush("Cheek Contour", "cheek-contour", "contour-imprints", (0, 0, 1, 2), 172, 0.095,
          0.72, 0.23, "drawingangle", "0,0.48;1,1;", "#855846", "#eed7c3"),
    Brush("Detail Contour", "detail-contour", "contour-imprints", (0, 1, 1, 2), 67, 0.19,
          0.69, 0.34, "drawingangle", "0,0.38;1,1;", "#795249", "#f1dacc"),
    Brush("Soft Focus Blender", "soft-focus-blender", "makeup-imprints", (1, 0, 2, 2), 108, 0.065,
          0.88, 1, "fuzzy", None, "#9a5e70", "#f0dbe0", smudge=True),
)


def make_tip(brush, source):
    if brush.tile is not None:
        column, row, columns, rows = brush.tile
        width, height = source.width // columns, source.height // rows
        source = source.crop((column * width, row * height,
                              (column + 1) * width, (row + 1) * height))

    # Convert the scan to coverage and remove the faint paper tone before cropping.
    coverage = ImageOps.invert(ImageOps.grayscale(source))
    black_level = 180 if brush.slug == "wing-liner" or brush.smudge else 226
    coverage = coverage.point([round(255 * (max(0, min(1, (v - 11) / black_level))) ** 1.08)
                               for v in range(256)])
    bounds = coverage.point(lambda v: 255 if v >= 10 else 0).getbbox()
    if bounds is None:
        raise ValueError(f"Empty texture for {brush.name}")
    coverage = ImageOps.expand(coverage.crop(bounds), border=8, fill=0)
    coverage.thumbnail((512, 512), Image.Resampling.LANCZOS)
    coverage = ImageOps.expand(coverage, border=2, fill=0)
    return ImageOps.invert(coverage)


def png(image, metadata=None):
    output = BytesIO()
    image.save(output, format="PNG", pnginfo=metadata)
    return output.getvalue()


def paint_icon(brush, tip, index):
    image = Image.new("RGB", (200, 200), brush.paper)
    alpha = ImageOps.invert(tip)
    alpha.thumbnail((154, 140), Image.Resampling.LANCZOS)
    image.paste(brush.color, ((200 - alpha.width) // 2, (174 - alpha.height) // 2), alpha)
    draw = ImageDraw.Draw(image)
    draw.line((16, 163, 183, 163), fill=brush.color)
    draw.text((16, 175), f"{index:02} / {brush.name.upper()}", fill=brush.color)
    return image


def sensor(sensor_id, curve=None):
    params = ET.Element("params", id=sensor_id)
    if sensor_id == "drawingangle":
        params.attrib.update(fanCornersEnabled="0", lockedAngleMode="0", angleOffset="0")
    if curve:
        ET.SubElement(params, "curve").text = curve
    return "<!DOCTYPE params>\n" + ET.tostring(params, encoding="unicode")


def make_preset(brush, tip, icon):
    engine = "colorsmudge" if brush.smudge else "paintbrush"
    definition = ET.Element(
        "Brush", type="png_brush", BrushVersion="2", filename=brush.filename,
        angle="0", spacing=str(brush.spacing), useAutoSpacing="0",
        autoSpacingCoeff="1", scale=str(brush.size / max(tip.size)),
        ColorAsMask="1", BrushApplication="0",
    )
    settings = {
        "paintop": engine,
        "brush_definition": ET.tostring(definition, encoding="unicode"),
        "requiredBrushFile": brush.filename,
        "requiredBrushFilesList": brush.filename,
        "ColorSource/Type": "plain",
        "CompositeOp": "normal",
        "PaintOpAction": 1 if brush.smudge else 2,
        "OpacityVersion": 2,
        "PressureOpacity": str(brush.slug != "wing-liner").lower(),
        "OpacityUseCurve": "true",
        "OpacitySensor": sensor("pressure", "0,0.14;0.5,0.48;1,1;"),
        "OpacityValue": brush.opacity,
        "PressureFlow": "false",
        "FlowUseCurve": "false",
        "FlowValue": brush.flow,
        "PressureSize": str(bool(brush.pressure_size)).lower(),
        "SizeUseCurve": "true",
        "SizeSensor": sensor("pressure", brush.pressure_size),
        "SizeValue": 1,
        "PressureRotation": "true",
        "RotationUseCurve": "true",
        "RotationSensor": sensor(brush.rotation),
        "RotationValue": 1,
        "PressureScatter": "false",
    }
    if brush.smudge:
        settings.update({
            "PressureColorRate": "false",
            "ColorRateValue": 0,
            "PressureSmudgeRate": "true",
            "SmudgeRateMode": 1,
            "SmudgeRateUseNewEngine": "true",
            "SmudgeRateUseCurve": "true",
            "SmudgeRateSensor": sensor("pressure", "0,0.12;0.5,0.43;1,1;"),
            "SmudgeRateValue": 0.86,
            "PressureSmudgeRadius": "true",
            "SmudgeRadiusUseCurve": "false",
            "SmudgeRadiusValue": 0.72,
            "SmudgeRadiusVersion": 2,
        })
    preset = ET.Element("Preset", name=f"Makeup - {brush.name}", paintopid=engine)
    for key, value in settings.items():
        ET.SubElement(preset, "param", name=key, type="string").text = str(value)
    metadata = PngImagePlugin.PngInfo()
    metadata.add_text("version", "2.2")
    metadata.add_text("preset", ET.tostring(preset, encoding="unicode"), zip=True)
    return png(icon, metadata)


def qname(namespace, name):
    return f"{{{namespace}}}{name}"


def make_manifest(resources):
    def attr(name):
        return qname(MANIFEST, name)

    manifest = ET.Element(attr("manifest"), {attr("version"): "1.2"})
    ET.SubElement(manifest, attr("file-entry"), {
        attr("media-type"): MIME, attr("full-path"): "/",
    })
    for path, data in resources.items():
        kind = path.split("/")[0]
        entry = ET.SubElement(manifest, attr("file-entry"), {
            attr("media-type"): kind, attr("full-path"): path,
            attr("md5sum"): md5(data).hexdigest(),
        })
        if kind == "paintoppresets":
            tags = ET.SubElement(entry, attr("tags"))
            ET.SubElement(tags, attr("tag")).text = TITLE
    return ET.tostring(manifest, encoding="utf-8", xml_declaration=True)


def make_metadata():
    metadata = ET.Element(qname(META, "meta"))
    ET.SubElement(metadata, qname(META, "generator")).text = "Makeup Atelier builder"
    ET.SubElement(metadata, qname(META, "bundle-version")).text = "1"
    ET.SubElement(metadata, qname(DC, "title")).text = TITLE
    ET.SubElement(metadata, qname(DC, "description")).text = (
        "Eleven brushes for digital makeup and portrait painting, including a pigment blender."
    )
    return ET.tostring(metadata, encoding="utf-8", xml_declaration=True)


def main():
    resources = {}
    preview = Image.new("RGB", (200, 150), "#f8f2ed")
    for index, brush in enumerate(BRUSHES):
        with Image.open(ROOT / "sources" / f"{brush.source}.png") as source:
            tip = make_tip(brush, source)
        icon = paint_icon(brush, tip, index + 1)
        preview.paste(icon.resize((50, 50), Image.Resampling.LANCZOS),
                      ((index % 4) * 50, (index // 4) * 50))
        resources[f"brushes/{brush.filename}"] = png(tip)
        resources[f"paintoppresets/makeup-atelier-{brush.slug}.kpp"] = make_preset(brush, tip, icon)

    with ZipFile(ROOT / "Makeup Atelier.bundle", "w") as bundle:
        bundle.writestr(ZipInfo("mimetype"), MIME, compress_type=ZIP_STORED)
        files = {
            **resources,
            "meta.xml": make_metadata(),
            "META-INF/manifest.xml": make_manifest(resources),
            "preview.png": png(preview),
        }
        for path, data in files.items():
            bundle.writestr(ZipInfo(path), data, compress_type=ZIP_DEFLATED)


if __name__ == "__main__":
    main()
