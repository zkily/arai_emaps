"""Generate manual menu breadcrumb hex images (FormingPlanningManual style)."""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

NAVY = (26, 58, 107)
WHITE = (255, 255, 255)
ORANGE_TOP = (240, 177, 122)
ORANGE_BOTTOM = (220, 150, 90)
ARROW = NAVY

W, H = 780, 46


def hex_points(cx: int, cy: int, hw: int, hh: int) -> list[tuple[int, int]]:
    """Horizontal chevron / elongated hex (flat top/bottom)."""
    return [
        (cx - hw + hh, cy),
        (cx + hw - hh, cy),
        (cx + hw, cy + hh),
        (cx + hw - hh, cy + 2 * hh),
        (cx - hw + hh, cy + 2 * hh),
        (cx - hw, cy + hh),
    ]


def draw_hex(
    draw: ImageDraw.ImageDraw,
    cx: int,
    cy: int,
    hw: int,
    hh: int,
    *,
    fill: tuple[int, int, int],
    outline: tuple[int, int, int] = NAVY,
    width: int = 2,
) -> None:
    pts = hex_points(cx, cy, hw, hh)
    draw.polygon(pts, fill=fill, outline=outline, width=width)


def draw_arrow(draw: ImageDraw.ImageDraw, x: int, y: int) -> None:
    """Small chevron pointing right (between hex steps)."""
    draw.polygon([(x + 10, y), (x, y - 5), (x, y + 5)], fill=ARROW)


def load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        r"C:\Windows\Fonts\meiryo.ttc",
        r"C:\Windows\Fonts\msgothic.ttc",
        r"C:\Windows\Fonts\YuGothM.ttc",
    ]
    for path in candidates:
        p = Path(path)
        if p.exists():
            return ImageFont.truetype(str(p), size=size)
    return ImageFont.load_default()


def draw_centered_text(
    draw: ImageDraw.ImageDraw,
    cx: int,
    cy: int,
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    fill: tuple[int, int, int],
) -> None:
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text((cx - tw // 2, cy - th // 2 - 1), text, font=font, fill=fill)


def render_menu(steps: list[tuple[str, bool]], out_path: Path) -> None:
    img = Image.new("RGB", (W, H), WHITE)
    draw = ImageDraw.Draw(img)
    font = load_font(15)

    # Layout tuned to match 04_menu_forming_planning.png (3 steps)
    centers = [130, 390, 650]
    hw, hh = 118, 18

    for i, (label, active) in enumerate(steps):
        cx = centers[i]
        cy = 5
        if active:
            # Simple vertical gradient fill
            base = Image.new("RGB", (W, H), WHITE)
            gdraw = ImageDraw.Draw(base)
            for row in range(2 * hh + 1):
                t = row / max(2 * hh, 1)
                r = int(ORANGE_TOP[0] * (1 - t) + ORANGE_BOTTOM[0] * t)
                g = int(ORANGE_TOP[1] * (1 - t) + ORANGE_BOTTOM[1] * t)
                b = int(ORANGE_TOP[2] * (1 - t) + ORANGE_BOTTOM[2] * t)
                pts = hex_points(cx, cy, hw, hh)
                y0, y1 = cy + row, cy + row
                # clip row inside hex via mask would be heavy; draw filled hex once
                _ = (r, g, b)
            draw_hex(draw, cx, cy, hw, hh, fill=ORANGE_TOP, outline=NAVY)
        else:
            draw_hex(draw, cx, cy, hw, hh, fill=WHITE, outline=NAVY)
        text_color = WHITE if active else NAVY
        draw_centered_text(draw, cx, cy + hh, label, font, text_color)
        if i < len(steps) - 1:
            ax = cx + hw + 8
            draw_arrow(draw, ax, cy + hh)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, format="PNG", optimize=True)
    print(f"Wrote {out_path} ({img.size[0]}x{img.size[1]})")


PRESETS: dict[str, tuple[str, list[tuple[str, bool]]]] = {
    "line_capacity": (
        "22_aps_menu_line_capacity.png",
        [
            ("1 APS管理メニュー", False),
            ("2 設備稼働管理", False),
            ("3 設備稼働設定", True),
        ],
    ),
    "capacity_matrix": (
        "24_aps_menu_capacity_matrix.png",
        [
            ("1 APS管理メニュー", False),
            ("2 設備稼働管理", False),
            ("3 設備稼働時間表", True),
        ],
    ),
}


def main() -> None:
    base = Path(__file__).resolve().parents[1] / "src/views/manual/images/FormingPlanningManual"
    preset = "line_capacity"
    out: Path | None = None
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg in PRESETS:
            preset = arg
        else:
            out = Path(arg)
    if len(sys.argv) > 2 and sys.argv[2] in PRESETS:
        preset = sys.argv[2]
    filename, steps = PRESETS[preset]
    if out is None:
        out = base / filename
    render_menu(steps, out)


if __name__ == "__main__":
    main()
