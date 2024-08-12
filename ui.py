import dearpygui.dearpygui as dpg

def create_ui(width, height, button_callback, color_callbacks, face_colors, toggle_raycasting, toggle_lighting, toggle_ssaa, toggle_rainbow_mode):
    dpg.create_context()

    def resize_ui(sender, app_data):
        new_width, new_height = dpg.get_viewport_client_width(), dpg.get_viewport_client_height()
        dpg.configure_item("ui_window", width=new_width // 4, height=new_height - 20)
        dpg.configure_item("child_window", width=-1, height=-1)

    dpg.set_viewport_resize_callback(resize_ui)

    with dpg.window(label="3D Cube Viewer", width=width // 4, height=height - 20, pos=(10, 10), tag="ui_window"):
        dpg.add_text("3D Cube Viewer")

        with dpg.child_window(tag="child_window", height=-1, width=-1):
            with dpg.collapsing_header(label="Colours", default_open=True):
                dpg.add_button(label="Randomize", callback=button_callback)

                for i in range(6):
                    def create_callback(index):
                        return lambda sender, app_data: color_callbacks[index](sender, app_data)

                    callback = create_callback(i)
                    dpg.add_color_picker(
                        label=f"Face {i + 1}",
                        tag=f"color_picker_{i}",
                        callback=callback,
                        default_value=face_colors[i] + (255,)
                    )

            dpg.add_checkbox(label="Show Raycasting Lines", callback=toggle_raycasting)
            dpg.add_checkbox(label="Enable Lighting", callback=toggle_lighting, default_value=True)
            dpg.add_checkbox(label="Enable SSAA", callback=toggle_ssaa, tag="ssaa_checkbox", default_value=False)
            dpg.add_checkbox(label="Enable Rainbow Mode", callback=toggle_rainbow_mode, tag="rainbow_mode_checkbox", default_value=False)

    dpg.create_viewport(title='3D Cube Viewer', width=width, height=height, resizable=True)
    dpg.setup_dearpygui()
    dpg.show_viewport()


def render_ui():
    dpg.render_dearpygui_frame()
