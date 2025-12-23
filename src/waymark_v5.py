import flet as ft
import json
import os
from datetime import datetime
import shutil

# --- GLOBAL CONFIGURATION ---
# This finds the user's "AppData/Roaming" folder automatically
APP_DATA_ROOT = os.path.join(os.environ.get("APPDATA"), "WaymarkApp")
STORAGE_DIR = os.path.join(APP_DATA_ROOT, "waymark_data")
IMAGE_DIR = os.path.join(STORAGE_DIR, "images")

# Create the folders in the user's home directory instead of Program Files
for d in [APP_DATA_ROOT, STORAGE_DIR, IMAGE_DIR]:
    if not os.path.exists(d):
        try:
            os.makedirs(d)
        except PermissionError:
            # Fallback for extreme cases: save to the current directory
            # (only happens if AppData is somehow locked)
            pass

class WaymarkApp:
    """
    A comprehensive Minecraft Coordinate Tracker designed for high-legibility
    and responsive use across different monitor orientations.
    """
    def __init__(self, page: ft.Page):
        self.page = page
        self.current_world = ""
        self.selected_image_path = None
        self.edit_image_path = None 
        self.all_data = [] # Local cache of the current world's JSON content

        # Initialize FilePickers - Must be added to page.overlay for Flet 0.28.3
        self.file_picker = ft.FilePicker(on_result=self.handle_file_picker_result)
        self.edit_file_picker = ft.FilePicker(on_result=self.handle_edit_picker_result)
        self.page.overlay.extend([self.file_picker, self.edit_file_picker])
        
        self.configure_page()
        self.build_interface()
        self.init_world_data()

    def configure_page(self):
        """Initializes window dimensions and theme settings."""
        self.page.title = "Waymark - Minecraft Tracker v5.2"
        self.page.theme_mode = ft.ThemeMode.DARK
        self.page.bgcolor = "#121212"
        self.page.window_width = 1350
        self.page.window_height = 950
        self.page.padding = 0 

    def build_interface(self):
        """Constructs the sidebar and main registry dashboard."""
        # Branding Colors
        self.COLOR_ACCENT = "#4A6982"  # Dusty Blue
        self.COLOR_SIDEBAR = "#1B1B1B" # Dark Gray
        self.COLOR_OVERWORLD = "#1B2E1C" # Forest Green
        self.COLOR_NETHER = "#2E1B1B"    # Crimson Red

        # --- SIDEBAR UI COMPONENTS ---
        self.ui_title = ft.Text("WAYMARK", size=32, weight="black", italic=True, color=self.COLOR_ACCENT)
        self.ui_world_drop = ft.Dropdown(label="Current World", on_change=self.on_world_swap, expand=True)
        self.ui_seed_field = ft.TextField(label="Seed", read_only=True, expand=True, text_size=12)
        self.ui_seed_lock = ft.IconButton(ft.Icons.LOCK_OUTLINE, on_click=self.toggle_seed_security, icon_color=self.COLOR_ACCENT)
        self.ui_new_world_field = ft.TextField(label="New World Name", visible=False, on_submit=self.execute_world_creation)
        
        self.ui_dim_toggle = ft.RadioGroup(
            content=ft.Row([
                ft.Radio(value="overworld", label="Overworld"),
                ft.Radio(value="nether", label="Nether")
            ]),
            value="overworld",
            on_change=self.animate_input_card_color
        )
        
        self.ui_desc_in = ft.TextField(label="Description", border_radius=10)
        self.ui_x_in = ft.TextField(label="X", expand=1)
        self.ui_y_in = ft.TextField(label="Y", expand=1)
        self.ui_z_in = ft.TextField(label="Z", expand=1)
        self.ui_img_prev = ft.Image(src="", width=100, height=80, border_radius=10, visible=False, fit=ft.ImageFit.COVER)

        # --- ANIMATED INPUT CARD ---
        # Changes color smoothly based on selected dimension
        self.ui_input_card = ft.Container(
            padding=15, border_radius=15, bgcolor=self.COLOR_OVERWORLD, animate=300,
            content=ft.Column([
                ft.Text("COORDINATE DETAILS", size=11, weight="bold", color="grey400"),
                self.ui_desc_in,
                ft.Row([self.ui_x_in, self.ui_y_in, self.ui_z_in], spacing=5),
                ft.Row([self.ui_img_prev, ft.TextButton("Attach Screenshot", icon=ft.Icons.CAMERA, on_click=lambda _: self.file_picker.pick_files())], alignment="center"),
            ], spacing=15)
        )

        # --- SIDEBAR COMPOSITION ---
        sidebar_scrollable = ft.Column([
            ft.Text("WORLD MANAGEMENT", size=11, weight="bold", color="grey500"),
            ft.Row([self.ui_world_drop, ft.IconButton(ft.Icons.ADD_CIRCLE, on_click=self.show_new_world_field), ft.IconButton(ft.Icons.DELETE_FOREVER, icon_color="red400", on_click=self.show_delete_world_dialog)]),
            self.ui_new_world_field,
            ft.Row([self.ui_seed_field, self.ui_seed_lock]),
            ft.Divider(height=20, color="transparent"),
            ft.Text("DIMENSION", size=11, weight="bold", color="grey500"),
            self.ui_dim_toggle,
            self.ui_input_card,
        ], scroll=ft.ScrollMode.ADAPTIVE, expand=True, spacing=15)

        sidebar_panel = ft.Container(
            width=380, bgcolor=self.COLOR_SIDEBAR, padding=20,
            content=ft.Column([
                ft.Container(self.ui_title, alignment=ft.alignment.center, padding=ft.padding.only(bottom=10)),
                ft.Divider(color=self.COLOR_ACCENT),
                sidebar_scrollable,
                ft.Divider(color=self.COLOR_ACCENT),
                # Fixed footer to prevent scrollbar overlap
                ft.Row([
                    ft.ElevatedButton("SAVE", icon=ft.Icons.SAVE, on_click=self.process_new_entry, expand=True, height=55, bgcolor=self.COLOR_ACCENT, color="white"),
                    ft.IconButton(ft.Icons.DELETE_SWEEP, icon_color="red400", on_click=self.reset_form)
                ])
            ])
        )

        # --- REGISTRY VIEW ---
        self.ui_search = ft.TextField(hint_text="Search logs...", prefix_icon=ft.Icons.SEARCH, on_change=self.apply_search_filter, expand=True)
        self.ui_registry = ft.ListView(expand=True, spacing=15, padding=20)

        main_registry_panel = ft.Container(
            content=ft.Column([
                ft.Row([ft.Text("COORDINATE REGISTRY", size=24, weight="bold"), self.ui_search], alignment="spaceBetween"),
                ft.Divider(color=self.COLOR_ACCENT),
                self.ui_registry
            ]),
            padding=30, expand=True
        )

        self.page.add(ft.Row([sidebar_panel, main_registry_panel], expand=True, spacing=0))

    # --- CORE LOGIC: DATA HANDLING ---
    def init_world_data(self):
        """Loads available worlds from storage on startup."""
        files = sorted([f.replace(".json", "") for f in os.listdir(STORAGE_DIR) if f.endswith(".json")])
        if not files:
            files = ["My_First_World"]
            with open(os.path.join(STORAGE_DIR, "My_First_World.json"), "w") as f: json.dump([], f)
        
        self.ui_world_drop.options = [ft.dropdown.Option(f) for f in files]
        self.ui_world_drop.value = files[0]
        self.current_world = files[0]
        self.sync_registry_from_file()

    def sync_registry_from_file(self):
        """Reads JSON data for current world and populates UI."""
        self.ui_registry.controls.clear()
        self.ui_seed_field.value = ""
        path = os.path.join(STORAGE_DIR, f"{self.current_world}.json")
        
        if os.path.exists(path):
            with open(path, "r") as f:
                try: self.all_data = json.load(f)
                except: self.all_data = []
        
        # Load World Metadata (Seed) vs Waymark Entries
        for entry in self.all_data:
            if entry.get("type") == "world_meta":
                self.ui_seed_field.value = entry.get("seed", "")
            else:
                self.ui_registry.controls.append(self.build_waymark_card(entry))
        self.page.update()

    def build_waymark_card(self, entry):
        """Constructs a responsive card for a coordinate entry."""
        try:
            x, y, z = float(entry['x']), float(entry['y']), float(entry['z'])
            dim = entry.get("dimension", "overworld")
            card_color = self.COLOR_OVERWORLD if dim == "overworld" else self.COLOR_NETHER
            
            # Dimension Linking Logic
            label = "Nether Link (÷8)" if dim == "overworld" else "Overworld Link (×8)"
            cx, cz = (f"{(x/8):.2f}", f"{(z/8):.2f}") if dim == "overworld" else (f"{(x*8):.2f}", f"{(z*8):.2f}")
        except: x = y = z = 0; card_color = self.COLOR_SIDEBAR; label="Math Error"; cx = cz = "0"

        # Responsive Wrap Row for coordinates
        coord_layout = ft.Row(
            wrap=True, spacing=20, run_spacing=10,
            controls=[
                ft.Text(f"X: {x:.2f}", size=24, weight="black", color="red300"),
                ft.Text(f"Y: {y:.2f}", size=24, weight="black", color="green300"),
                ft.Text(f"Z: {z:.2f}", size=24, weight="black", color="blue300"),
            ]
        )

        img_path = entry.get("image", "")
        img_widget = ft.Image(src=img_path, width=120, height=80, border_radius=8, fit=ft.ImageFit.COVER) if img_path and os.path.exists(img_path) else ft.Icon(ft.Icons.IMAGE_NOT_SUPPORTED, size=40)

        return ft.Card(
            color=card_color,
            content=ft.Container(
                padding=15,
                content=ft.Column([
                    ft.Row([
                        ft.Container(img_widget, on_click=lambda _: self.preview_image(img_path)),
                        ft.Column([
                            ft.Text(entry['desc'], size=18, weight="bold"),
                            coord_layout,
                            ft.Text(f"{label}: X {cx} / Z {cz}", size=14, italic=True, color="orange300", weight="bold"),
                        ], expand=True),
                        ft.Column([
                            ft.Text(entry['created'], size=10, color="grey400"),
                            ft.Row([
                                ft.IconButton(ft.Icons.LOCATION_ON, tooltip="Copy /tp Command", on_click=lambda _: self.page.set_clipboard(f"/tp {x:.2f} {y:.2f} {z:.2f}")),
                                ft.IconButton(ft.Icons.EDIT, on_click=lambda _: self.show_edit_dialog(entry)),
                                ft.IconButton(ft.Icons.DELETE, icon_color="red400", on_click=lambda _: self.prompt_delete_entry(entry)),
                            ], spacing=0)
                        ], horizontal_alignment="end")
                    ])
                ])
            )
        )

    # --- LOGIC: USER ACTIONS ---
    def prompt_delete_entry(self, entry):
        """Double-check confirmation dialog before deleting an entry."""
        def finalize_delete(ev):
            self.all_data.remove(entry)
            self.save_registry_to_file()
            self.sync_registry_from_file()
            dlg.open = False
            self.page.update()

        dlg = ft.AlertDialog(
            title=ft.Text("Delete Waymark?"),
            content=ft.Text(f"Are you sure you want to delete '{entry['desc']}'? This cannot be undone."),
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: setattr(dlg, 'open', False) or self.page.update()),
                ft.ElevatedButton("Delete", bgcolor="red400", color="white", on_click=finalize_delete)
            ]
        )
        self.page.overlay.append(dlg)
        dlg.open = True
        self.page.update()

    def process_new_entry(self, e):
        """Validates and saves a new coordinate entry."""
        if not self.ui_desc_in.value: return
        
        stored_img = ""
        if self.selected_image_path:
            name = f"img_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
            stored_img = os.path.join(IMAGE_DIR, name)
            shutil.copy(self.selected_image_path, stored_img)
            
        now = datetime.now().strftime("%m/%d %H:%M")
        new_log = {
            "desc": self.ui_desc_in.value, 
            "x": self.ui_x_in.value or "0", "y": self.ui_y_in.value or "0", "z": self.ui_z_in.value or "0",
            "dimension": self.ui_dim_toggle.value,
            "created": now, "modified": now, "image": stored_img
        }
        
        self.all_data.insert(0, new_log)
        self.save_registry_to_file()
        self.sync_registry_from_file()
        self.reset_form(None)

    def show_edit_dialog(self, entry):
        """Modular edit window for existing entries."""
        self.edit_image_path = None
        e_desc = ft.TextField(label="Description", value=entry['desc'], expand=True)
        e_x = ft.TextField(label="X", value=entry['x'], expand=True)
        e_y = ft.TextField(label="Y", value=entry['y'], expand=True)
        e_z = ft.TextField(label="Z", value=entry['z'], expand=True)
        e_dim = ft.RadioGroup(content=ft.Row([ft.Radio(value="overworld", label="Overworld"), ft.Radio(value="nether", label="Nether")]), value=entry.get("dimension", "overworld"))

        def commit_changes(ev):
            final_img = entry.get("image", "")
            if self.edit_image_path:
                name = f"img_edit_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
                final_img = os.path.join(IMAGE_DIR, name)
                shutil.copy(self.edit_image_path, final_img)
            
            entry.update({
                "desc": e_desc.value, "x": e_x.value, "y": e_y.value, "z": e_z.value,
                "dimension": e_dim.value, "modified": datetime.now().strftime("%m/%d %H:%M"), "image": final_img
            })
            self.save_registry_to_file(); self.sync_registry_from_file(); dlg.open = False; self.page.update()

        dlg = ft.AlertDialog(
            title=ft.Text("Update Waymark"),
            content=ft.Container(width=600, height=450, padding=10, content=ft.Column([e_desc, e_dim, ft.Row([e_x, e_y, e_z]), ft.ElevatedButton("Swap Screenshot", icon=ft.Icons.IMAGE, on_click=lambda _: self.edit_file_picker.pick_files())])),
            actions=[ft.TextButton("Cancel", on_click=lambda _: setattr(dlg, 'open', False) or self.page.update()), ft.ElevatedButton("Update", on_click=commit_changes)]
        )
        self.page.overlay.append(dlg); dlg.open = True; self.page.update()

    # --- SYSTEM HANDLERS ---
    def save_registry_to_file(self):
        with open(os.path.join(STORAGE_DIR, f"{self.current_world}.json"), "w") as f:
            json.dump(self.all_data, f, indent=4)

    def animate_input_card_color(self, e):
        self.ui_input_card.bgcolor = self.COLOR_OVERWORLD if self.ui_dim_toggle.value == "overworld" else self.COLOR_NETHER
        self.page.update()

    def reset_form(self, e):
        self.ui_desc_in.value = self.ui_x_in.value = self.ui_y_in.value = self.ui_z_in.value = ""
        self.selected_image_path = None
        self.ui_img_prev.visible = False
        self.page.update()

    def toggle_seed_security(self, e):
        self.ui_seed_field.read_only = not self.ui_seed_field.read_only
        self.ui_seed_lock.icon = ft.Icons.CHECK if not self.ui_seed_field.read_only else ft.Icons.LOCK_OUTLINE
        if self.ui_seed_field.read_only:
            meta = next((i for i in self.all_data if i.get("type") == "world_meta"), None)
            if meta: meta["seed"] = self.ui_seed_field.value
            else: self.all_data.append({"type": "world_meta", "seed": self.ui_seed_field.value})
            self.save_registry_to_file()
        self.page.update()

    def show_new_world_field(self, e):
        self.ui_new_world_field.visible = not self.ui_new_world_field.visible
        self.page.update()

    def execute_world_creation(self, e):
        name = self.ui_new_world_field.value.strip().replace(" ", "_")
        if name:
            with open(os.path.join(STORAGE_DIR, f"{name}.json"), "w") as f: json.dump([], f)
            self.ui_new_world_field.value = ""; self.ui_new_world_field.visible = False
            self.init_world_data()

    def on_world_swap(self, e):
        self.current_world = self.ui_world_drop.value
        self.sync_registry_from_file()

    def handle_file_picker_result(self, e):
        if e.files:
            self.selected_image_path = e.files[0].path
            self.ui_img_prev.src = self.selected_image_path
            self.ui_img_prev.visible = True
            self.page.update()

    def handle_edit_picker_result(self, e):
        if e.files: self.edit_image_path = e.files[0].path

    def show_delete_world_dialog(self, e):
        def delete_confirmed(ev):
            path = os.path.join(STORAGE_DIR, f"{self.current_world}.json")
            if os.path.exists(path): os.remove(path)
            dlg.open = False; self.init_world_data()
        dlg = ft.AlertDialog(title=ft.Text("Wipe World Data?"), actions=[ft.TextButton("Back", on_click=lambda _: setattr(dlg, 'open', False) or self.page.update()), ft.TextButton("Delete Everything", on_click=delete_confirmed, style=ft.ButtonStyle(color="red"))])
        self.page.overlay.append(dlg); dlg.open = True; self.page.update()

    def apply_search_filter(self, e):
        term = self.ui_search.value.lower()
        self.ui_registry.controls.clear()
        for log in self.all_data:
            if log.get("type") != "world_meta" and term in log['desc'].lower():
                self.ui_registry.controls.append(self.build_waymark_card(log))
        self.page.update()

    def preview_image(self, path):
        if path and os.path.exists(path):
            dlg = ft.AlertDialog(content=ft.Image(src=path), actions=[ft.TextButton("Close", on_click=lambda _: setattr(dlg, 'open', False) or self.page.update())])
            self.page.overlay.append(dlg); dlg.open = True; self.page.update()

# --- RUN APPLICATION ---
if __name__ == "__main__":
    ft.app(target=WaymarkApp)