import pygame
import math
import sys

# --- Game Constants ---
WIDTH, HEIGHT = 1000, 700
FPS = 60

# --- Celestial Scaling ---
SCALE = 10 
G_CONSTANT = 6.67430e-11

# Time Warp Setup
TIME_WARP_LEVELS = [1, 5, 25, 100, 1000]

# Colors
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_ROCKET = (200, 200, 200)
COLOR_NOSE = (50, 50, 50)
COLOR_FLAME = (255, 140, 0)
COLOR_PAD = (100, 100, 100)
COLOR_UI_BG = (40, 40, 50)
COLOR_UI_HOVER = (70, 70, 90)
COLOR_TRAJECTORY = (100, 255, 100)

class CelestialBody:
    def __init__(self, name, x, y, radius_m, mass_kg, soi_radius_m, color, atmo_height_m=0):
        self.name = name
        self.x = x / SCALE
        self.y = y / SCALE
        self.radius_m = radius_m
        self.radius_px = radius_m / SCALE
        self.mass = mass_kg
        self.soi_radius_px = soi_radius_m / SCALE
        self.color = color
        self.atmo_height_m = atmo_height_m
        self.mu = G_CONSTANT * self.mass

system_bodies = [
    CelestialBody("Earth", 0, 0, 318000, 1.48e22, 5000000, (60, 100, 140), 30000),
    CelestialBody("Moon", 0, -4500000, 86000, 1.77e20, 800000, (180, 180, 180), 0)
]

class Rocket:
    def __init__(self, start_body, thruster_count):
        self.x = start_body.x
        self.y = start_body.y - start_body.radius_px - 5 
        
        self.vx = 0
        self.vy = 0
        self.angle = 0  
        self.thrusting = False
        self.thruster_count = thruster_count
        self.rotation_speed = 120 

        base_mass = 5000
        base_thrust = 200000
        
        self.mass_kg = base_mass + (thruster_count ** 1.6) * 1500 
        self.thrust_n = base_thrust * thruster_count
        
        self.drag_coeff = 0.4
        self.cross_section_area = 4.0 

    def update(self, dt, bodies):
        keys = pygame.key.get_pressed()

        # 1. Rotation
        if keys[pygame.K_a]: self.angle -= self.rotation_speed * dt
        if keys[pygame.K_d]: self.angle += self.rotation_speed * dt
        self.angle %= 360

        # 2. Thrust
        tx, ty = 0, 0
        self.thrusting = keys[pygame.K_w]
        if self.thrusting:
            rad = math.radians(self.angle)
            thrust_accel = self.thrust_n / self.mass_kg
            tx = math.sin(rad) * thrust_accel
            ty = -math.cos(rad) * thrust_accel

        # 3. Sphere of Influence
        active_body = system_bodies[0] 
        for body in bodies:
            if body.name != "Earth": 
                dist_to_body_px = math.hypot(self.x - body.x, self.y - body.y)
                if dist_to_body_px < body.soi_radius_px:
                    active_body = body
                    break

        # 4. Gravity
        dx_px = active_body.x - self.x
        dy_px = active_body.y - self.y
        dist_px = math.hypot(dx_px, dy_px)
        
        if dist_px == 0: dist_px = 1
        dist_m = dist_px * SCALE

        g_accel = active_body.mu / (dist_m ** 2)
        dir_x, dir_y = dx_px / dist_px, dy_px / dist_px
        gx, gy = dir_x * g_accel, dir_y * g_accel

        # 5. Drag
        drag_x, drag_y = 0, 0
        altitude_m = dist_m - active_body.radius_m
        
        if active_body.atmo_height_m > 0 and altitude_m < active_body.atmo_height_m:
            air_density = max(0, 1.225 * (1 - (altitude_m / active_body.atmo_height_m)))
            vel_mag = math.hypot(self.vx, self.vy)
            if vel_mag > 0:
                drag_force = 0.5 * air_density * (vel_mag ** 2) * self.drag_coeff * self.cross_section_area
                drag_accel = drag_force / self.mass_kg
                drag_x = -(self.vx / vel_mag) * drag_accel
                drag_y = -(self.vy / vel_mag) * drag_accel

        # Apply Kinematics
        self.vx += (gx + tx + drag_x) * dt
        self.vy += (gy + ty + drag_y) * dt
        self.x += (self.vx / SCALE) * dt
        self.y += (self.vy / SCALE) * dt

        # 6. Surface Collision
        current_dist_px = math.hypot(self.x - active_body.x, self.y - active_body.y)
        if current_dist_px < active_body.radius_px + 2:
            self.x = active_body.x - dir_x * (active_body.radius_px + 2)
            self.y = active_body.y - dir_y * (active_body.radius_px + 2)
            self.vx, self.vy = 0, 0

        return active_body 

    def get_future_trajectory(self, active_body, scale, steps=1200, dt_sim=10.0):
        sim_x, sim_y = self.x, self.y
        sim_vx, sim_vy = self.vx, self.vy
        points = []
        
        for _ in range(steps):
            dx = active_body.x - sim_x
            dy = active_body.y - sim_y
            dist_px = math.hypot(dx, dy)
            if dist_px == 0: dist_px = 1
            dist_m = dist_px * scale
            
            if dist_px < active_body.radius_px:
                points.append((sim_x, sim_y))
                break 
            if dist_px > active_body.soi_radius_px:
                points.append((sim_x, sim_y))
                break
                
            g_accel = active_body.mu / (dist_m ** 2)
            sim_vx += (dx / dist_px) * g_accel * dt_sim
            sim_vy += (dy / dist_px) * g_accel * dt_sim
            sim_x += (sim_vx / scale) * dt_sim
            sim_y += (sim_vy / scale) * dt_sim
            
            if _ % 5 == 0:
                points.append((sim_x, sim_y))
        return points

    def _rotate_points(self, points, screen_x, screen_y, rad):
        return [(screen_x + px*math.cos(rad) - py*math.sin(rad), screen_y + px*math.sin(rad) + py*math.cos(rad)) for px, py in points]

    def draw(self, surface, cam_x, cam_y, zoom):
        if zoom < 0.05: return 

        screen_x = (self.x - cam_x) * zoom
        screen_y = (self.y - cam_y) * zoom
        rad = math.radians(self.angle)
        
        body_points = [(-10*zoom, -15*zoom), (10*zoom, -15*zoom), (10*zoom, 25*zoom), (-10*zoom, 25*zoom)]
        nose_points = [(0, -35*zoom), (-10*zoom, -15*zoom), (10*zoom, -15*zoom)]
        
        pygame.draw.polygon(surface, COLOR_ROCKET, self._rotate_points(body_points, screen_x, screen_y, rad))
        pygame.draw.polygon(surface, COLOR_BLACK, self._rotate_points(body_points, screen_x, screen_y, rad), 2)
        pygame.draw.polygon(surface, COLOR_NOSE, self._rotate_points(nose_points, screen_x, screen_y, rad))
        
        if self.thrusting:
            # Custom flame rendering based on thruster count
            flames = []
            if self.thruster_count == 2: flames = [-5, 5]
            elif self.thruster_count == 4: flames = [-7.5, -2.5, 2.5, 7.5]
            elif self.thruster_count == 8: flames = [-10.5, -7.5, -4.5, -1.5, 1.5, 4.5, 7.5, 10.5]
            
            for offset in flames:
                flame = [((offset - 1.5)*zoom, 25*zoom), ((offset + 1.5)*zoom, 25*zoom), (offset*zoom, 45*zoom)]
                pygame.draw.polygon(surface, COLOR_FLAME, self._rotate_points(flame, screen_x, screen_y, rad))

def draw_minimap(screen, rocket, bodies):
    map_w, map_h = 160, 250
    map_rect = pygame.Rect(WIDTH - map_w - 20, 20, map_w, map_h)
    
    pygame.draw.rect(screen, (30, 30, 30), map_rect)
    pygame.draw.rect(screen, COLOR_WHITE, map_rect, 2)
    
    system_height = 5500000 / SCALE
    scale = map_h / system_height
    map_cx, map_cy = 0, -2250000 / SCALE 
    
    def get_map_coords(global_x, global_y):
        mx = map_rect.centerx + (global_x - map_cx) * scale
        my = map_rect.centery + (global_y - map_cy) * scale
        return int(mx), int(my)

    for body in bodies:
        mx, my = get_map_coords(body.x, body.y)
        m_rad = max(2, int(body.radius_px * scale)) 
        pygame.draw.circle(screen, body.color, (mx, my), m_rad)

    rx, ry = get_map_coords(rocket.x, rocket.y)
    pygame.draw.circle(screen, (255, 0, 0), (rx, ry), 3)

def draw_button(screen, rect, text, font, mouse_pos):
    is_hovered = rect.collidepoint(mouse_pos)
    color = COLOR_UI_HOVER if is_hovered else COLOR_UI_BG
    pygame.draw.rect(screen, color, rect, border_radius=8)
    pygame.draw.rect(screen, COLOR_WHITE, rect, 2, border_radius=8)
    text_surf = font.render(text, True, COLOR_WHITE)
    screen.blit(text_surf, text_surf.get_rect(center=rect.center))
    return is_hovered

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Orbital Launch Simulator")
    clock = pygame.time.Clock()
    
    font_ui = pygame.font.SysFont("Courier New", 18, bold=True)
    font_title = pygame.font.SysFont("Courier New", 48, bold=True)
    font_button = pygame.font.SysFont("Courier New", 24, bold=True)

    game_state = "MAIN_MENU" 
    rocket = None
    zoom = 1.0
    time_warp_idx = 0

    running = True
    while running:
        # Cap dt to avoid lag spikes ruining physics
        dt = min(clock.tick(FPS) / 1000.0, 0.033) 
        mouse_pos = pygame.mouse.get_pos()
        mouse_clicked = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_clicked = True
            
            # Scroll to Zoom
            if event.type == pygame.MOUSEWHEEL and game_state == "PLAY":
                zoom += event.y * 0.1
                zoom = max(0.005, min(zoom, 5.0))
                
            # Keyboard controls for Time Warp
            if event.type == pygame.KEYDOWN and game_state == "PLAY":
                if event.key == pygame.K_PERIOD: # > key
                    time_warp_idx = min(time_warp_idx + 1, len(TIME_WARP_LEVELS) - 1)
                if event.key == pygame.K_COMMA:  # < key
                    time_warp_idx = max(time_warp_idx - 1, 0)

        screen.fill(COLOR_BLACK)

        if game_state == "MAIN_MENU":
            title_surf = font_title.render("ORBITAL LAUNCH", True, COLOR_WHITE)
            screen.blit(title_surf, (WIDTH//2 - title_surf.get_width()//2, 150))

            btn_play = pygame.Rect(WIDTH//2 - 100, 300, 200, 60)
            btn_exit = pygame.Rect(WIDTH//2 - 100, 400, 200, 60)

            if draw_button(screen, btn_play, "PLAY", font_button, mouse_pos) and mouse_clicked:
                game_state = "SELECTION"
            if draw_button(screen, btn_exit, "EXIT", font_button, mouse_pos) and mouse_clicked:
                running = False

        elif game_state == "SELECTION":
            title_surf = font_title.render("SELECT LOADOUT", True, COLOR_WHITE)
            screen.blit(title_surf, (WIDTH//2 - title_surf.get_width()//2, 100))

            btn_dual = pygame.Rect(WIDTH//2 - 150, 250, 300, 60)
            btn_quad = pygame.Rect(WIDTH//2 - 150, 350, 300, 60)
            btn_octa = pygame.Rect(WIDTH//2 - 150, 450, 300, 60)

            if draw_button(screen, btn_dual, "Dual Boost (Light)", font_button, mouse_pos) and mouse_clicked:
                rocket = Rocket(system_bodies[0], 2)
                game_state = "PLAY"
            if draw_button(screen, btn_quad, "Quad Boost (Standard)", font_button, mouse_pos) and mouse_clicked:
                rocket = Rocket(system_bodies[0], 4)
                game_state = "PLAY"
            if draw_button(screen, btn_octa, "Octa Boost (Heavy)", font_button, mouse_pos) and mouse_clicked:
                rocket = Rocket(system_bodies[0], 8)
                game_state = "PLAY"

        elif game_state == "PLAY":
            
            # --- Safety Override ---
            # Instantly drop time warp to 1x if the player tries to thrust
            keys = pygame.key.get_pressed()
            if keys[pygame.K_w]:
                time_warp_idx = 0
            
            warp_multiplier = TIME_WARP_LEVELS[time_warp_idx]

            # --- Physics Sub-stepping ---
            # Run the physics loop multiple times per frame for high time warp stability
            active_body = None
            for _ in range(warp_multiplier):
                active_body = rocket.update(dt, system_bodies)

            cam_x = rocket.x - (WIDTH / 2) / zoom
            cam_y = rocket.y - (HEIGHT / 2) / zoom

            # Dynamic Sky
            earth = system_bodies[0]
            earth_altitude = (math.hypot(rocket.x - earth.x, rocket.y - earth.y) * SCALE) - earth.radius_m
            ratio = min(max(earth_altitude / earth.atmo_height_m, 0), 1)
            screen.fill((int(135 * (1 - ratio)), int(206 * (1 - ratio)), int(235 * (1 - ratio))))

            # Draw Planets
            for body in system_bodies:
                bx = int((body.x - cam_x) * zoom)
                by = int((body.y - cam_y) * zoom)
                br = max(1, int(body.radius_px * zoom))
                pygame.draw.circle(screen, body.color, (bx, by), br)
                if body.atmo_height_m > 0:
                    pygame.draw.circle(screen, (100, 150, 255), (bx, by), int((body.radius_px + (body.atmo_height_m / SCALE)) * zoom), 1)

            # Draw Trajectory
            traj_points = rocket.get_future_trajectory(active_body, SCALE)
            screen_traj = [(int((px - cam_x) * zoom), int((py - cam_y) * zoom)) for px, py in traj_points]
            if len(screen_traj) > 1:
                pygame.draw.lines(screen, COLOR_TRAJECTORY, False, screen_traj, 2)

            # Draw Elements
            rocket.draw(screen, cam_x, cam_y, zoom)
            draw_minimap(screen, rocket, system_bodies)

            # Telemetry
            alt_m = (math.hypot(rocket.x - active_body.x, rocket.y - active_body.y) * SCALE) - active_body.radius_m
            
            # Flash warp text yellow if accelerated
            warp_color = (255, 255, 0) if warp_multiplier > 1 else COLOR_WHITE
            
            screen.blit(font_ui.render(f"SoI:  {active_body.name}", True, COLOR_WHITE), (20, 20))
            screen.blit(font_ui.render(f"Alt:  {int(alt_m):,} m", True, COLOR_WHITE), (20, 45))
            screen.blit(font_ui.render(f"Vel:  {int(math.hypot(rocket.vx, rocket.vy)):,} m/s", True, COLOR_WHITE), (20, 70))
            screen.blit(font_ui.render(f"Mass: {int(rocket.mass_kg):,} kg", True, COLOR_WHITE), (20, 95))
            screen.blit(font_ui.render(f"Zoom: {zoom:.2f}x", True, COLOR_WHITE), (20, 120))
            screen.blit(font_ui.render(f"Warp: {warp_multiplier}x (< > to change)", True, warp_color), (20, 145))

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()