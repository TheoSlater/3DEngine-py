import pygame as pg

# Constants for the UI
BUTTON_COLOR = (0, 128, 255)
BUTTON_HOVER_COLOR = (0, 100, 200)
TEXT_COLOR = (255, 255, 255)
BACKGROUND_COLOR = (30, 30, 30)  # This can be removed or replaced
BUTTON_RADIUS = 10
BUTTON_PADDING = 10

def draw_ui(screen):
    font = pg.font.Font(None, 36)
    
    # Draw title
    title_text = font.render("3D Cube Viewer", True, TEXT_COLOR)
    screen.blit(title_text, (BUTTON_PADDING, BUTTON_PADDING))

    # Draw button
    button_rect = pg.Rect(BUTTON_PADDING, 50, 150, 40)
    mouse_pos = pg.mouse.get_pos()
    if button_rect.collidepoint(mouse_pos):
        button_color = BUTTON_HOVER_COLOR
    else:
        button_color = BUTTON_COLOR
    
    pg.draw.rect(screen, button_color, button_rect, border_radius=BUTTON_RADIUS)
    
    # Draw button text
    button_text = font.render("Click Me", True, TEXT_COLOR)
    text_rect = button_text.get_rect(center=button_rect.center)
    screen.blit(button_text, text_rect)
