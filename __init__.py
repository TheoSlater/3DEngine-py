import pygame as pg
import numpy as np
import random
from obj_loader import load_obj  # Import function to load OBJ files

pg.init()

WIDTH, HEIGHT = 800, 600
SSAA_SCALE = 12  # Scale factor for SSAA, use 2 for 2x SSAA

# Define high-resolution surface for SSAA
high_res_surface = pg.Surface((WIDTH * SSAA_SCALE, HEIGHT * SSAA_SCALE))

screen = pg.display.set_mode((WIDTH, HEIGHT))
pg.display.set_caption("3D Camera Orbit with Mouse")

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
        if pg.mouse.get_pressed()[1]:
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

    # Load the OBJ file
    vertices, faces, face_colors = load_obj('path/to/your/model.obj')

    show_rays = False  # Flag to toggle raycasting lines
    lighting_enabled = True  # Flag to toggle lighting

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

        # Clear high-resolution surface if SSAA is enabled
        if SSAA_SCALE > 1:
            high_res_surface.fill((0, 0, 0))

        cam_pos = camera.get_position()
        translated_vertices = np.array(vertices)
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
        if SSAA_SCALE > 1:
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

        pg.display.flip()
        clock.tick(60)

    pg.quit()

if __name__ == "__main__":
    main()
