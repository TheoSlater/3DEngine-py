import pygame as pg
import numpy as np
from obj_loader import load_obj

pg.init()

WIDTH, HEIGHT = 800, 600
SSAA_SCALE = 2

high_res_surface = pg.Surface((WIDTH * SSAA_SCALE, HEIGHT * SSAA_SCALE))

screen = pg.display.set_mode((WIDTH, HEIGHT))
pg.display.set_caption("3D Camera Orbit with Mouse")

# Initialize font for FPS display
font = pg.font.SysFont(None, 36)

# Define lighting
light_pos = np.array([5, 5, 5])
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

def project(points, scale=100, width=800, height=600):
    return [(int(p[0] * scale) + width // 2, int(p[1] * scale) + height // 2) for p in points]

def compute_face_normal(face_vertices):
    """Calculate the normal vector for a face."""
    if len(face_vertices) < 3:
        raise ValueError("Face vertices must contain at least 3 vertices.")
    
    v0, v1, v2 = face_vertices[:3]
    edge1 = v1 - v0
    edge2 = v2 - v0
    normal = np.cross(edge1, edge2)
    norm_length = np.linalg.norm(normal)
    return normal / norm_length if norm_length > 0 else normal

def compute_lighting(normal, face_center, light_pos, ambient_light, diffuse_light):
    """Compute the lighting for a face based on its normal and the light source position."""
    light_dir = light_pos - face_center
    light_dir /= np.linalg.norm(light_dir)
    diffuse = max(np.dot(normal, light_dir), 0) * diffuse_light
    return ambient_light + diffuse

def is_face_facing_light(normal, face_center, light_pos):
    """Check if the face is facing the light source."""
    light_dir = light_pos - face_center
    light_dir /= np.linalg.norm(light_dir)
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

    vertices, faces, edges = load_obj('./objects/car.obj')

    show_rays = False

    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                return
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_r:
                    show_rays = not show_rays

        camera.control()

        if SSAA_SCALE > 1:
            high_res_surface.fill((0, 0, 0))

        cam_pos = camera.get_position()
        translated_vertices = np.array(vertices)
        
        try:
            rotation_matrix_x = rotate_x(camera.angle_pitch)
            rotation_matrix_y = rotate_y(camera.angle_yaw)
            rotation_matrix = np.dot(rotation_matrix_x, rotation_matrix_y)
            print(f"Rotation matrix X:\n{rotation_matrix_x}")
            print(f"Rotation matrix Y:\n{rotation_matrix_y}")
            print(f"Combined rotation matrix:\n{rotation_matrix}")

            rotated_vertices = np.dot(translated_vertices, rotation_matrix)
            print(f"Rotated vertices:\n{rotated_vertices}")

            projected_vertices = project(rotated_vertices, width=WIDTH, height=HEIGHT)
            print(f"Projected vertices:\n{projected_vertices}")
            
        except AssertionError as e:
            print(f"AssertionError: {e}")
            raise
        except Exception as e:
            print(f"Exception: {e}")
            raise

        face_distances = []
        for i, face in enumerate(faces):
            face_vertices = [rotated_vertices[v] for v in face]
            if len(face_vertices) < 3:
                continue
            
            face_center = np.mean(face_vertices, axis=0)
            face_normal = compute_face_normal(face_vertices)

            face_lighting = compute_lighting(face_normal, face_center, light_pos, ambient_light, diffuse_light)
            face_color = np.array([255, 255, 255]) * face_lighting
            face_color = np.clip(face_color, 0, 255).astype(int)
            face_distance = np.mean([v[2] for v in face_vertices])
            face_distances.append((i, face_distance, [projected_vertices[v] for v in face], face_color, face_center, face_normal))

        face_distances.sort(key=lambda x: x[1], reverse=True)

        if SSAA_SCALE > 1:
            for _, _, polygon, color, _, _ in face_distances:
                pg.draw.polygon(high_res_surface, tuple(color), [(int(p[0] * SSAA_SCALE), int(p[1] * SSAA_SCALE)) for p in polygon])

            scaled_surface = pg.transform.smoothscale(high_res_surface, (WIDTH, HEIGHT))
            screen.blit(scaled_surface, (0, 0))
        else:
            for _, _, polygon, color, _, _ in face_distances:
                pg.draw.polygon(screen, tuple(color), polygon)

        if show_rays:
            light_pos_screen = project([light_pos], width=WIDTH, height=HEIGHT)[0]
            for _, _, polygon, _, face_center, face_normal in face_distances:
                face_center_screen = project([face_center], width=WIDTH, height=HEIGHT)[0]
                ray_color = (255, 0, 0) if not is_face_facing_light(face_normal, face_center, light_pos) else (255, 255, 255)
                pg.draw.line(screen, ray_color, light_pos_screen, face_center_screen, 1)

        fps = clock.get_fps()
        fps_text = font.render(f"FPS: {int(fps)}", True, (255, 255, 255))
        screen.blit(fps_text, (10, 10))

        pg.display.flip()
        clock.tick(120)

if __name__ == "__main__":
    main()
