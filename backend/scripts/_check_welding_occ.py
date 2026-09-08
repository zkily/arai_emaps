from pathlib import Path

t = Path(
    r"C:\Users\arai-235\Desktop\Smart-EMAPs\frontend\src\views\mes\productionInstruction\welding\WeldingInstruction.vue"
).read_text(encoding="utf-8")
keys = [
    "formatOccupancyDisplay",
    "shouldShowOccupancy",
    "hasOccupancy",
    "occupancy-tags",
    "lineOccupancyDisplay",
    "occupancy_only",
    "is_advance_notice",
    "占用",
]
for k in keys:
    print(f"{k}: {k in t}")
