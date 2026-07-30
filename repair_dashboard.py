from pathlib import Path
import shutil

dashboard = Path("dashboard(18).py")
backup = Path("dashboard_duplicated_backup.py")
output = Path("dashboard.py")

text = dashboard.read_text(encoding="utf-8")

status_marker = """render_status_bar(
    current_page=st.session_state.current_page,
    selected_ticker=ticker,
    market_connected=True,
)"""

status_position = text.find(status_marker)

if status_position == -1:
    raise RuntimeError("Could not find the final status-bar block.")

correct_end = status_position + len(status_marker)
clean_code = text[:correct_end].rstrip() + "\n"

shutil.copy2(dashboard, backup)
output.write_text(clean_code, encoding="utf-8")

print("Fixed dashboard created:", output)
print("Backup created:", backup)