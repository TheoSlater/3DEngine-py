import pygame as pg
import numpy as np
import dearpygui.dearpygui as dpg
import random
from ui import create_ui, render_ui

pg.init()

WIDTH, HEIGHT = 800, 600
SSAA_SCALE = 2  # Scale factor for SSAA, use 2 for 2x SSAA

# Define high-resolution surface for SSAA
high_res_surface = pg.Surface((WIDTH * SSAA_SCALE, HEIGHT * SSAA_SCALE))

screen = pg.display.set_mode((WIDTH, HEIGHT))
pg.display.set_caption("3D Camera Orbit with Mouse")

font = pg.font.SysFont(None, 36)

# Define vertices, edges, faces, and face colors
vertices = np.array([
    [-1, -1, -1],
    [1, -1, -1],
    [1, 1, -1],
    [-1, 1, -1],
    [-1, -1, 1],
    [1, -1, 1],
    [1, 1, 1],
    [-1, 1, 1]
])
edges = [
    (0, 1), (1, 2), (2, 3), (3, 0),
    (4, 5), (5, 6), (6, 7), (7, 4),
    (0, 4), (1, 5), (2, 6), (3, 7)
]
faces = [
    [0, 1, 2, 3],  # Front face
    [4, 5, 6, 7],  # Back face
    [0, 1, 5, 4],  # Bottom face
    [2, 3, 7, 6],  # Top face
    [1, 2, 6, 5],  # Right face
    [0, 3, 7, 4]   # Left face
]
face_colors = [
    (255, 255, 255),   # White
    (255, 255, 255),   # White
    (255, 255, 255),   # White
    (255, 255, 255),   # White
    (255, 255, 255),   # White
    (255, 255, 255),   # White
]

# Define a static light source position (e.g., top-right)
light_pos = np.array([5, 5, 5])  # Static light source
ambient_light = 0.2
diffuse_light = 0.8

def rotate_x(angle):
    cos_angle, sin_angle = np.cos(angle), np.sin(angle)
    return np.array([
        [1, 0, 0],
        [0, cos_angle, -sin_angle],
        [0, sin_angle, cos_angle]
    ])

def rotate_y(angle):
    cos_angle, sin_angle = np.cos(angle), np.sin(angle)
    return np.array([
        [cos_angle, 0, sin_angle],
        [0, 1, 0],
        [-sin_angle, 0, cos_angle]
    ])

def project(points, scale=100):
    return [(int(p[0] * scale) + WIDTH // 2, int(p[1] * scale) + HEIGHT // 2) for p in points]

def calculate_face_depth(face_vertices):
    """Calculate the average depth of the face vertices relative to the camera."""
    cam_pos = np.array([0, 0, 0])  # Camera at the origin
    depths = [np.dot(v - cam_pos, np.array([0, 0, 1])) for v in face_vertices]
    return np.mean(depths)

def compute_face_normal(face_vertices):
    """Calculate the normal vector for a face."""
    v0, v1, v2 = face_vertices[0], face_vertices[1], face_vertices[2]
    edge1 = v1 - v0
    edge2 = v2 - v0
    normal = np.cross(edge1, edge2)
    norm_length = np.linalg.norm(normal)
    return normal / norm_length if norm_length > 0 else normal

def compute_lighting(normal, face_center):
    """Compute the lighting for a face based on its normal and the light source position."""
    light_dir = light_pos - face_center
    light_dir = light_dir / np.linalg.norm(light_dir)
    dot_product = np.dot(normal, light_dir)
    diffuse = max(dot_product, 0) * diffuse_light
    return ambient_light + diffuse

def update_face_colors():
    """Change the colors of the cube faces to random colors and update the color pickers."""
    global face_colors
    face_colors = [(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)) for _ in face_colors]

    # Convert colors to the [0.0, 1.0] range and update color pickers
    for i, color in enumerate(face_colors):
        dpg.set_value(f"color_picker_{i}", [c / 255.0 for c in color])  # Update color picker value
        print(f"Face {i + 1} color randomized to {face_colors[i]}")

def update_color_picker(i, sender, app_data):
    """Update face color from color picker."""
    try:
        color = app_data
        if i is not None and color is not None and len(color) >= 3:  # Ensure there is color data
            # Convert the color from [0.0, 1.0] range to [0, 255] range
            color = tuple(int(c * 255) for c in color[:3])
            face_colors[i] = color
            print(f"Face {i + 1} color updated to {face_colors[i]}")
        else:
            print(f"Received invalid data for face {i if i is not None else 'unknown'}")
    except Exception as e:
        print(f"Error updating color for face {i if i is not None else 'unknown'}: {e}")

def is_face_facing_light(normal, face_center):
    """Check if the face is facing the light source."""
    light_dir = light_pos - face_center
    light_dir = light_dir / np.linalg.norm(light_dir)
    return np.dot(normal, light_dir) > 0

class Camera:
    def __init__(self):
        self.angle_pitch = self.angle_yaw = 0
        self.distance = 5
        self.rotation_speed = 0.01
        self.last_mouse_pos = None

    def control(self):
        if pg.mouse.get_pressed()[0]:
            mouse_x, mouse_y = pg.mouse.get_pos()
            if self.last_mouse_pos:
                dx, dy = mouse_x - self.last_mouse_pos[0], mouse_y - self.last_mouse_pos[1]
                self.angle_yaw += dx * self.rotation_speed
                self.angle_pitch -= dy * self.rotation_speed
            self.last_mouse_pos = (mouse_x, mouse_y)
        else:
            self.last_mouse_pos = None

    def get_position(self):
        x = self.distance * np.cos(self.angle_pitch) * np.sin(self.angle_yaw)
        y = self.distance * np.sin(self.angle_pitch)
        z = self.distance * np.cos(self.angle_pitch) * np.cos(self.angle_yaw)
        return np.array([x, y, z])

def main():
    clock = pg.time.Clock()
    camera = Camera()
    
    show_rays = False  # Flag to toggle raycasting lines
    lighting_enabled = True  # Flag to toggle lighting
    ssaa_enabled = False  # Flag to toggle SSAA
    rainbow_mode = False  # Flag to toggle rainbow mode
    hue = 0  # Initial hue value for rainbow mode

    def toggle_raycasting(sender, app_data):
        nonlocal show_rays
        show_rays = app_data
        print(f"Raycasting {'enabled' if show_rays else 'disabled'}")
    
    def toggle_lighting(sender, app_data):
        nonlocal lighting_enabled
        lighting_enabled = app_data
        print(f"Lighting {'enabled' if lighting_enabled else 'disabled'}")

    def toggle_ssaa(sender, app_data):
        nonlocal ssaa_enabled
        ssaa_enabled = app_data
        print(f"SSAA {'enabled' if ssaa_enabled else 'disabled'}")
        
    def toggle_rainbow_mode(sender, app_data):
        nonlocal rainbow_mode
        rainbow_mode = app_data
        print(f"Rainbow mode {'enabled' if rainbow_mode else 'disabled'}")

    # Ensure that each face has its own callback correctly initialized
    color_callbacks = [lambda sender, app_data, i=i: update_color_picker(i, sender, app_data) for i in range(6)]
    
    # Pass the update_face_colors function and color picker callbacks
    create_ui(WIDTH, HEIGHT, update_face_colors, color_callbacks, face_colors, toggle_raycasting, toggle_lighting, toggle_ssaa, toggle_rainbow_mode)
    
    running = True

    while running:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_r:  # Toggle raycasting lines with the 'R' key
                    show_rays = not show_rays
                if event.key == pg.K_l:  # Toggle lighting with the 'L' key
                    lighting_enabled = not lighting_enabled
                    print(f"Lighting {'enabled' if lighting_enabled else 'disabled'}")

        camera.control()

        # Update the rainbow mode colors
        if rainbow_mode:
            hue = (hue + 1) % 360  # Increment hue and wrap around at 360
            for i in range(6):
                c = pg.Color(0, 0, 0)
                # Ensure the hue stays within the 0-360 range by using modulo operation
                adjusted_hue = (hue + i * 60) % 360
                c.hsva = (adjusted_hue, 100, 100, 100)  # Set HSVA with hue in range, and alpha set to 100
                face_colors[i] = tuple(c)[:3]  # Only keep the RGB components


        # Clear high-resolution surface if SSAA is enabled
        if ssaa_enabled:
            high_res_surface.fill((0, 0, 0))

        cam_pos = camera.get_position()
        translated_vertices = vertices
        rotation_matrix = np.dot(rotate_x(camera.angle_pitch), rotate_y(camera.angle_yaw))
        rotated_vertices = np.dot(translated_vertices, rotation_matrix)
        projected_vertices = project(rotated_vertices)

        face_distances = []
        for i, face in enumerate(faces):
            face_vertices = [rotated_vertices[v] for v in face]
            face_center = np.mean(face_vertices, axis=0)
            face_normal = compute_face_normal(face_vertices)

            if lighting_enabled:
                face_lighting = compute_lighting(face_normal, face_center)
                face_color = np.array(face_colors[i]) * face_lighting
            else:
                face_color = np.array(face_colors[i])
                
            face_color = np.clip(face_color, 0, 255).astype(int)
            face_distance = calculate_face_depth(face_vertices)
            face_distances.append((i, face_distance, [projected_vertices[v] for v in face], face_color, face_center, face_normal))

        # Sort faces based on their distance from the camera (further faces first)
        face_distances.sort(key=lambda x: x[1], reverse=True)

        # Draw faces in the sorted order to ensure proper depth rendering
        if ssaa_enabled:
            # Draw faces on the high-resolution surface
            for i, _, polygon, color, _, _ in face_distances:
                # Use anti-aliased polygons if desired
                pg.draw.polygon(high_res_surface, tuple(color), [(int(p[0] * SSAA_SCALE), int(p[1] * SSAA_SCALE)) for p in polygon])
            
            # Downsample high-resolution surface to the final screen resolution
            scaled_surface = pg.transform.scale(high_res_surface, (WIDTH, HEIGHT))
            screen.blit(scaled_surface, (0, 0))
        else:
            for i, _, polygon, color, _, _ in face_distances:
                # Draw faces directly on the screen
                pg.draw.polygon(screen, tuple(color), polygon)
        
        # Add Raycasting lines
        if show_rays:
            light_pos_screen = project([light_pos])[0]
            for _, _, polygon, _, face_center, face_normal in face_distances:
                face_center_screen = project([face_center])[0]
                ray_color = (255, 0, 0) if not is_face_facing_light(face_normal, face_center) else (255, 255, 255)
                pg.draw.line(screen, ray_color, light_pos_screen, face_center_screen, 1)
        
        # Calculate and display FPS
        fps = clock.get_fps()
        fps_text = font.render(f"FPS: {int(fps)}", True, (255, 255, 255))
        screen.blit(fps_text, (2, 2))

        render_ui()
        pg.display.flip()
        clock.tick(60)

    dpg.destroy_context()
    pg.quit()

if __name__ == "__main__":
    main()


