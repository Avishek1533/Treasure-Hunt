from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import random
import sys

# Game state variables
camera_pos = (0, -200, 150)
player_pos = [0, 0, 0]
player_direction = 0
player_speed = 10
GRID_LENGTH = 950
first_person_view = False
top_view = False
zoom_level = 1
max_zoom = 3.0

# Game objects
treasure_collected = False
treasure_pos = [0, 0, 20]
police_positions = []
police_directions = []
game_over = False
level_complete = False
score = 0

police_patrol_range = 900

# Maze configuration
WALL_HEIGHT = 100
WALL_THICKNESS = 50
PLAYER_RADIUS = 15
COLLISION_MARGIN = 6
POLICE_RADIUS = 15

# Maze layout (1 = wall, 0 = path)
maze = [
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [1,0,0,1,0,0,0,1,0,1,0,0,0,1,0,0,0,1,0,1],
    [1,0,1,1,0,1,0,1,0,1,1,1,0,1,0,1,0,1,0,1],
    [1,0,1,0,0,1,0,0,0,0,0,1,0,0,0,1,0,0,0,1],
    [1,0,1,0,1,1,0,0,1,1,0,1,1,1,0,1,1,1,0,1],
    [1,0,0,0,0,0,0,1,0,0,0,0,0,1,0,0,0,1,0,1],
    [1,0,1,0,1,1,0,1,1,0,1,1,0,1,1,1,0,1,1,1],
    [1,0,0,0,0,1,0,0,0,0,0,1,0,0,0,1,0,0,0,1],
    [1,0,1,1,0,1,0,0,1,1,0,1,1,1,0,1,0,1,0,1],
    [1,0,1,0,0,0,0,0,0,1,0,0,0,1,0,0,0,1,0,1],
    [1,0,1,0,1,1,1,1,0,1,0,1,0,1,1,1,0,1,0,1],
    [1,0,0,0,0,0,0,1,0,0,0,0,0,1,0,0,0,1,0,1],
    [1,1,0,0,1,1,0,1,1,1,0,1,0,1,0,1,0,1,1,1],
    [1,0,0,0,0,1,0,0,0,0,0,1,0,0,0,1,0,0,0,1],
    [1,0,1,1,0,1,1,0,0,1,0,1,1,0,0,1,0,1,0,1],
    [1,0,1,0,0,0,0,0,0,1,0,0,0,1,0,0,0,1,0,1],
    [1,0,1,0,1,0,1,1,0,1,0,1,0,1,0,1,0,1,0,1],
    [1,0,0,0,0,0,0,1,0,0,0,0,0,1,0,0,0,0,0,1],
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
]

# Door positions (row, col)
DOOR_POSITIONS = [
    (1, 3), (1, 9), (1, 13), (5, 1), (9, 17), (13, 17), (17, 17)
]

# Colors
WALL_COLOR = (1, 1, 1)
WALL_BORDER_COLOR = (0, 0, 0)
DOOR_COLOR = (0.2, 0.4, 0.9)
FLOOR_COLOR = (0.25, 0.25, 0.25)
GRID_COLOR = (0.35, 0.35, 0.35)
PLAYER_TOP_COLOR = (1.0, 0.0, 0.0)
POLICE_COLOR = (0.0, 0.0, 1.0)
TREASURE_COLOR = (1.0, 0.84, 0.0)
BULLET_COLOR = (1.0, 0.0, 0.0)

# Game objects
wall_boundaries = []
maze_width = 0
maze_height = 0
maze_offset_x = 0
maze_offset_y = 0

police_original_positions = []

# Add these to your game state variables
level = 1
level_message_timer = 0
showing_level_message = False
num_police = 2  # Starting number of police
waiting_for_enter = False

def init_3d():
    """Initialize OpenGL 3D settings including lighting"""
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_COLOR_MATERIAL)
    
    glLightfv(GL_LIGHT0, GL_POSITION, (0, 10, 0, 1))
    glLightfv(GL_LIGHT0, GL_AMBIENT, (0.3, 0.3, 0.3, 1))
    glLightfv(GL_LIGHT0, GL_DIFFUSE, (0.9, 0.9, 0.9, 1))
    glLightfv(GL_LIGHT0, GL_SPECULAR, (0.5, 0.5, 0.5, 1))
    
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
    
    init_wall_boundaries()
    place_game_objects()

def update_lighting():
    """Update the light position to maintain consistent lighting"""
    # Position the light in the scene
    glPushMatrix()
    glLoadIdentity()
    
    # Position light slightly above and in front of the camera
    light_pos = [camera_pos[0], camera_pos[1], camera_pos[2] + 50, 1.0]
    glLightfv(GL_LIGHT0, GL_POSITION, light_pos)
    
    glPopMatrix()

def place_game_objects():
    """Place treasure and police in valid positions"""
    global treasure_pos, police_positions, police_directions, police_original_positions
    
    rows = len(maze)
    cols = len(maze[0])
    cell_size = WALL_THICKNESS * 2
    
    # Find all open positions
    open_positions = []
    for i in range(rows):
        for j in range(cols):
            if maze[i][j] == 0:
                x = maze_offset_x + j * cell_size + cell_size/2
                y = maze_offset_y + i * cell_size + cell_size/2
                open_positions.append((x, y))
    
    # Place treasure (ensure it's not at starting position)
    if len(open_positions) > 1:
        treasure_pos[0], treasure_pos[1] = random.choice(open_positions[1:])
    
    # Place police officers (number based on current level)
    police_positions = []
    police_directions = []
    police_original_positions = []
    for _ in range(num_police):
        if len(open_positions) > 0:
            x, y = random.choice(open_positions)
            police_positions.append([x, y, 0])
            li=[0,90,180,270]
            dir=random.choice(li)
            police_directions.append(dir)
            police_original_positions.append([x, y])  # Store original position for patrol
            open_positions.remove((x, y))

def init_wall_boundaries():
    """Pre-calculate wall boundaries for collision detection"""
    global wall_boundaries, maze_width, maze_height, maze_offset_x, maze_offset_y
    
    rows = len(maze)
    cols = len(maze[0])
    cell_size = WALL_THICKNESS * 2
    
    maze_offset_x = -cols * WALL_THICKNESS
    maze_offset_y = -rows * WALL_THICKNESS
    maze_width = cols * cell_size
    maze_height = rows * cell_size
    
    wall_boundaries = []
    
    for i in range(rows):
        for j in range(cols):
            if maze[i][j] == 1:
                is_door = (i, j) in DOOR_POSITIONS
                x = maze_offset_x + j * cell_size
                y = maze_offset_y + i * cell_size
                wall_boundaries.append((
                    x - COLLISION_MARGIN,
                    y - COLLISION_MARGIN, 
                    x + cell_size + COLLISION_MARGIN, 
                    y + cell_size + COLLISION_MARGIN,
                    is_door
                ))

def draw_door(x, y, z, cell_size, wall_thickness, wall_height, orientation):
    """Draw a door on a wall"""
    door_width = cell_size * 0.4
    door_height = cell_size * 0.7
    
    glColor3f(*DOOR_COLOR)
    
    if orientation == 'vertical':
        glPushMatrix()
        glTranslatef(x, y + wall_thickness/2, z + wall_height/2)
        glScalef(door_width, wall_thickness*0.5, door_height)
        glutSolidCube(1.0)
        glDisable(GL_LIGHTING)
        glColor3f(*WALL_BORDER_COLOR)
        glutWireCube(1.01)
        glEnable(GL_LIGHTING)
        glPopMatrix()
    else:
        glPushMatrix()
        glTranslatef(x + wall_thickness/2, y, z + wall_height/2)
        glScalef(wall_thickness*0.5, door_width, door_height)
        glutSolidCube(1.0)
        glDisable(GL_LIGHTING)
        glColor3f(*WALL_BORDER_COLOR)
        glutWireCube(1.01)
        glEnable(GL_LIGHTING)
        glPopMatrix()

def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18, color=(1, 1, 1)):
    """Draw text on screen with specified color"""
    glColor3f(*color)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_player():
    """Draw the player character"""
    if first_person_view:
        return
    
    if top_view:
        glPushMatrix()
        glTranslatef(player_pos[0], player_pos[1], player_pos[2] + 5)
        glColor3f(*PLAYER_TOP_COLOR)
        glPushMatrix()
        glRotatef(90, 1, 0, 0)
        glutSolidCylinder(PLAYER_RADIUS, 5, 16, 1)
        glPopMatrix()
        glColor3f(1.0, 1.0, 0.0)
        glPushMatrix()
        glRotatef(player_direction, 0, 0, 1)
        glTranslatef(PLAYER_RADIUS * 0.5, 0, 2.5)
        glScalef(PLAYER_RADIUS, PLAYER_RADIUS/3, 5)
        glutSolidCube(1.0)
        glPopMatrix()
        glPopMatrix()
        return
       
    glPushMatrix()
    glTranslatef(*player_pos)
    glRotatef(player_direction, 0, 0, 1)
    glRotatef(-90, 0, 0, 1)
   
    # Head
    glPushMatrix()
    glColor3f(0.95, 0.75, 0.65)
    glTranslatef(0, 0, 70)
    glutSolidSphere(10, 16, 16)
    glPopMatrix()
   
    # Torso
    glPushMatrix()
    glColor3f(0.2, 0.2, 0.7)
    glTranslatef(0, 0, 45)
    glScalef(20, 12, 30)
    glutSolidCube(1.0)
    glPopMatrix()
   
    # Arms
    glPushMatrix()
    glColor3f(0.2, 0.2, 0.7)
    glTranslatef(12, 0, 45)
    glScalef(4, 4, 20)
    glutSolidCube(1.0)
    glPopMatrix()
   
    glPushMatrix()
    glColor3f(0.2, 0.2, 0.7)
    glTranslatef(-12, 0, 45)
    glScalef(4, 4, 20)
    glutSolidCube(1.0)
    glPopMatrix()
   
    # Legs
    glPushMatrix()
    glColor3f(0.1, 0.1, 0.3)
    glTranslatef(7, 0, 15)
    glScalef(6, 6, 30)
    glutSolidCube(1.0)
    glPopMatrix()
   
    glPushMatrix()
    glColor3f(0.1, 0.1, 0.3)
    glTranslatef(-7, 0, 15)
    glScalef(6, 6, 30)
    glutSolidCube(1.0)
    glPopMatrix()
   
    # Neck
    glPushMatrix()
    glColor3f(0.95, 0.75, 0.65)
    glTranslatef(0, 0, 65)
    glRotatef(-90, 1, 0, 0)
    gluCylinder(gluNewQuadric(), 4, 4, 5, 10, 2)
    glPopMatrix()
   
    glPopMatrix()

def draw_police():
    """Draw police NPCs with guns, hands, and legs"""
    for i, pos in enumerate(police_positions):
        glPushMatrix()
        glTranslatef(pos[0], pos[1], pos[2])
        glRotatef(police_directions[i], 0, 0, 1)
        glRotatef(-90, 0, 0, 1)
        
        # Body
        glColor3f(*POLICE_COLOR)
        glPushMatrix()
        glTranslatef(0, 0, 45)
        glScalef(20, 12, 30)  
        glutSolidCube(1.0)       
        glPopMatrix()
        
        # Head
        glColor3f(0.95, 0.75, 0.65)
        glPushMatrix()
        glTranslatef(0, 0, 70) 
        glutSolidSphere(10, 16, 16)
        glPopMatrix()
        
        # Hat
        glColor3f(1, 1, 1)
        glPushMatrix()
        glTranslatef(0, 0, 85)
        glRotatef(-90, 1, 0, 0)
        gluCylinder(gluNewQuadric(), 12, 8, 10, 10, 2)
        glPopMatrix()
        
 
        # Right arm
        glPushMatrix()
        glColor3f(0.95, 0.75, 0.65)
        glTranslatef(10,0,10)          
            
        gluCylinder(gluNewQuadric(), 2, 2, 40, 32, 32)
        glPopMatrix()

        # Left arm 
        glPushMatrix()
        glColor3f(0.95, 0.75, 0.65)
        glTranslatef(-10, 30,80)      
        glRotatef(130, 1, 0, 0)      
        gluCylinder(gluNewQuadric(), 2,2, 40, 32, 32)
        glPopMatrix()       
        # Gun
        glPushMatrix()
        glColor3f(1.0, 0.5, 0.3)
        glTranslatef(-10, 56,97)      
        glRotatef(130, 1, 0, 0)    
        gluCylinder(gluNewQuadric(), 2,2, 40, 32, 32)
        glPopMatrix()   

        #right leg
        glPushMatrix()
        glColor3f(*POLICE_COLOR)
        glTranslatef(10,0,-10)          
         
        gluCylinder(gluNewQuadric(), 2, 2, 35, 32, 32)
        glPopMatrix()

        # Left leg
        glPushMatrix()
        glColor3f(*POLICE_COLOR)
        glTranslatef(-10, 0,-10)      
     
        gluCylinder(gluNewQuadric(), 2,2, 35, 32, 32)
        glPopMatrix() 

        glPopMatrix() 

 
def draw_treasure():
    """Draw the treasure chest"""
    if treasure_collected:
        return
        
    glPushMatrix()
    glTranslatef(*treasure_pos)
    glColor3f(*TREASURE_COLOR)
    
    # Main chest
    glPushMatrix()
    glScalef(30, 20, 15)
    glutSolidCube(1.0)
    glPopMatrix()
   
    # Lid
    glPushMatrix()
    glTranslatef(0, 0, 15)
    glScalef(30, 20, 5)
    glutSolidCube(1.0)
    glPopMatrix()
   
    # Lock
    glColor3f(0.3, 0.3, 0.3)
    glPushMatrix()
    glTranslatef(0, -12, 10)
    glutSolidSphere(3, 10, 10)
    glPopMatrix()
    
    glPopMatrix()


def draw_maze():
    """Draw the maze with walls and doors"""
    rows = len(maze)
    cols = len(maze[0])
    cell_size = WALL_THICKNESS * 2
    
    offset_x = maze_offset_x
    offset_y = maze_offset_y
    
    for i in range(rows):
        for j in range(cols):
            if maze[i][j] == 1:
                x = offset_x + j * cell_size
                y = offset_y + i * cell_size
                z = 0
                
                glPushMatrix()
                glTranslatef(x + WALL_THICKNESS/2, y + WALL_THICKNESS/2, z + WALL_HEIGHT/2)
                glColor3f(*WALL_COLOR)
                glScalef(cell_size, cell_size, WALL_HEIGHT)
                glutSolidCube(1.0)
                
                glDisable(GL_LIGHTING)
                glColor3f(*WALL_BORDER_COLOR)
                glutWireCube(1.01)
                glEnable(GL_LIGHTING)
                glPopMatrix()
    
    # Draw doors
    for door_i, door_j in DOOR_POSITIONS:
        if 0 <= door_i < rows and 0 <= door_j < cols and maze[door_i][door_j] == 1:
            x = offset_x + door_j * cell_size
            y = offset_y + door_i * cell_size
            z = 0
            
            if door_j < cols - 1 and maze[door_i][door_j + 1] == 0:
                draw_door(x + cell_size - WALL_THICKNESS/2, y, z, cell_size, WALL_THICKNESS, WALL_HEIGHT, 'vertical')
            elif door_j > 0 and maze[door_i][door_j - 1] == 0:
                draw_door(x - WALL_THICKNESS/2, y, z, cell_size, WALL_THICKNESS, WALL_HEIGHT, 'vertical')
            elif door_i < rows - 1 and maze[door_i + 1][door_j] == 0:
                draw_door(x, y + cell_size - WALL_THICKNESS/2, z, cell_size, WALL_THICKNESS, WALL_HEIGHT, 'horizontal')
            elif door_i > 0 and maze[door_i - 1][door_j] == 0:
                draw_door(x, y - WALL_THICKNESS/2, z, cell_size, WALL_THICKNESS, WALL_HEIGHT, 'horizontal')
            else:
                draw_door(x + cell_size - WALL_THICKNESS/2, y, z, cell_size, WALL_THICKNESS, WALL_HEIGHT, 'vertical')

def draw_floor():
    """Draw the floor grid"""
    glColor3f(*FLOOR_COLOR)
    glBegin(GL_QUADS)
    glVertex3f(-GRID_LENGTH, -GRID_LENGTH, 0)
    glVertex3f(GRID_LENGTH, -GRID_LENGTH, 0)
    glVertex3f(GRID_LENGTH, GRID_LENGTH, 0)
    glVertex3f(-GRID_LENGTH, GRID_LENGTH, 0)
    glEnd()
   
    glColor3f(*GRID_COLOR)
    glBegin(GL_LINES)
    for i in range(-GRID_LENGTH, GRID_LENGTH + 1, 50):
        glVertex3f(i, -GRID_LENGTH, 1)
        glVertex3f(i, GRID_LENGTH, 1)
    for i in range(-GRID_LENGTH, GRID_LENGTH + 1, 50):
        glVertex3f(-GRID_LENGTH, i, 1)
        glVertex3f(GRID_LENGTH, i, 1)
    glEnd()
    
def is_point_in_wall(x, y, radius=0):
    """Check if a point is inside a wall with optional radius"""
    for min_x, min_y, max_x, max_y, is_door in wall_boundaries:
        if (x + radius > min_x and 
            x - radius < max_x and 
            y + radius > min_y and 
            y - radius < max_y):
            return True
    return False

def check_wall_collision(new_x, new_y):
    """Improved collision detection with sliding"""
    current_x, current_y = player_pos[0], player_pos[1]
    
    if is_point_in_wall(new_x, new_y, PLAYER_RADIUS):
        # Try moving only in X direction
        if not is_point_in_wall(new_x, current_y, PLAYER_RADIUS):
            return new_x, current_y, True
        
        # Try moving only in Y direction
        if not is_point_in_wall(current_x, new_y, PLAYER_RADIUS):
            return current_x, new_y, True
        
        # If both axes collide, stay in place
        return current_x, current_y, False
    
    # No collision
    return new_x, new_y, True

def movement_with_collision_detection(dx, dy):
    """Move player with collision detection"""
    new_x = player_pos[0] + dx
    new_y = player_pos[1] + dy
    
    final_x, final_y, moved = check_wall_collision(new_x, new_y)
    
    player_pos[0] = final_x
    player_pos[1] = final_y
    
    return moved

def move_police():
    """Move police NPCs with patrol behavior"""
    for i in range(len(police_positions)):
        # Get original position for this police
        orig_x, orig_y = police_original_positions[i]
        current_x, current_y, _ = police_positions[i]
        
        # Calculate distance from original position
        dist_sq = (current_x - orig_x)**2 + (current_y - orig_y)**2

        
        # If too far from original position, turn around
        if dist_sq > police_patrol_range**2:
            police_directions[i] = (police_directions[i] + 180) % 360
        

        
        # Calculate movement
        dx = math.cos(math.radians(police_directions[i])) *0.5
        dy = math.sin(math.radians(police_directions[i])) *0.5
        
        new_x = police_positions[i][0] + dx
        new_y = police_positions[i][1] + dy
        
        # Check for wall collisions
        if not is_point_in_wall(new_x, new_y, POLICE_RADIUS):
            police_positions[i][0] = new_x
            police_positions[i][1] = new_y
        else:
            # Change direction if hitting a wall
            police_directions[i] = (police_directions[i] + 180) % 360

def check_police_detection():
    """Check if player is in any police detection zone"""
    global game_over
    
    for police in police_positions:
        px, py, pz = police
        player_x, player_y, _ = player_pos
        
        # Calculate distance to player
        dist_to_player = math.sqrt((px - player_x)**2 + (py - player_y)**2)
        
        # If player is in detection range (150 units)
        if dist_to_player < 150:
            game_over = True
            return
def draw_police_detection_zone():
    """Draw red circles showing police detection zones"""
    glDisable(GL_LIGHTING)
    for police in police_positions:
        px, py, pz = police
        glColor3f(1.0, 0.0, 0.0)  # Red color
        glBegin(GL_TRIANGLE_FAN)
        glVertex3f(px, py, 1)  # Center point
        for angle in range(0, 361, 10):
            rad = math.radians(angle)
            x = px + 150 * math.cos(rad)  # 150 is detection radius
            y = py + 150 * math.sin(rad)
            glVertex3f(x, y, 1)  # Slightly above floor to avoid z-fighting
        glEnd()
    glEnable(GL_LIGHTING)

def advance_level():
    """Advance to the next level after treasure collection"""
    global level, treasure_collected, level_complete, num_police
    global showing_level_message, level_message_timer, waiting_for_enter
    
    level += 1
    num_police += 1  # Increase number of police
    
    # Reset game state
    treasure_collected = False
    level_complete = False
    
    # Show level message
    showing_level_message = True
    level_message_timer = 120  # Show for 120 frames (about 2 seconds)
    waiting_for_enter = True  # Wait for enter key press
    
    # Regenerate game objects
    place_game_objects()

def check_game_events():
    """Check for treasure collection and police encounters"""
    global treasure_collected, level_complete, game_over
    
    # Check treasure collection
    if not treasure_collected:
        dist_to_treasure = math.sqrt(
            (player_pos[0] - treasure_pos[0])**2 +
            (player_pos[1] - treasure_pos[1])**2
        )
        if dist_to_treasure < PLAYER_RADIUS + 20:
            treasure_collected = True
            level_complete = True
            advance_level()  # Call advance_level when treasure is collected
    
    # Check police encounters (direct collision)
    for police in police_positions:
        dist_to_police = math.sqrt(
            (player_pos[0] - police[0])**2 +
            (player_pos[1] - police[1])**2
        )
        if dist_to_police < PLAYER_RADIUS + POLICE_RADIUS:
            game_over = True
            break

def keyboardListener(key, x, y):
    """Handle keyboard inputs"""
    global player_pos, player_direction, first_person_view, top_view, zoom_level, game_over, waiting_for_enter
   
    # Resume gameplay after level up when Enter is pressed
    if waiting_for_enter and (key == b'\r' or key == b'\n'):
        waiting_for_enter = False
        return
    
    # Don't process other inputs while waiting for Enter
    if waiting_for_enter:
        return
   
    # Reset the game if R is pressed
    if key == b'r' and game_over:
        reset_game()
        return
   
    if game_over or level_complete:
        return
    
    # Toggle views
    if key == b'v':
        if top_view:
            top_view = False
            first_person_view = True
        elif first_person_view:
            first_person_view = False
            top_view = False
        else:
            top_view = True
        update_camera()
        return
        
    # Toggle zoom
    if key == b'z' and not first_person_view and not top_view:
        zoom_level = max_zoom if zoom_level == 1.0 else 1.0
        update_camera()
        return
        
    # Top-down view
    if key == b't':
        top_view = True
        first_person_view = False
        update_camera()
        return
   
    # Movement vectors
    forward_x = math.cos(math.radians(player_direction)) * player_speed
    forward_y = math.sin(math.radians(player_direction)) * player_speed
    right_x = math.cos(math.radians(player_direction - 90)) * player_speed
    right_y = math.sin(math.radians(player_direction - 90)) * player_speed
   
    # Movement controls
    if key == b'w':
        movement_with_collision_detection(forward_x, forward_y)
    elif key == b's':
        movement_with_collision_detection(-forward_x, -forward_y)
    elif key == b'a':
        movement_with_collision_detection(-right_x, -right_y)
    elif key == b'd':
        movement_with_collision_detection(right_x, right_y)
    elif key == b'q':
        player_direction = (player_direction + 5) % 360
    elif key == b'e':
        player_direction = (player_direction - 5) % 360
   
    update_camera()

def update_camera():
    """Update camera position based on view mode"""
    global camera_pos
   
    if top_view:
        maze_center_x = maze_offset_x + maze_width/2
        maze_center_y = maze_offset_y + maze_height/2
        camera_pos = (maze_center_x, maze_center_y, 800)
    elif first_person_view:
        eye_height = 70
        camera_pos = (player_pos[0], player_pos[1], player_pos[2] + eye_height)
    else:
        distance_behind = 200 * zoom_level
        height_above = 150 * zoom_level
        camera_angle = player_direction + 180
        dx = math.cos(math.radians(camera_angle)) * distance_behind
        dy = math.sin(math.radians(camera_angle)) * distance_behind
        camera_pos = (player_pos[0] + dx, player_pos[1] + dy, player_pos[2] + height_above)

def setupCamera():
    """Configure camera projection and view"""
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    
    if top_view:
        margin = max(maze_width, maze_height) * 0.6
        glOrtho(
            maze_offset_x - margin, 
            maze_offset_x + maze_width + margin,
            maze_offset_y - margin, 
            maze_offset_y + maze_height + margin,
            0.1, 2000
        )
    elif first_person_view:
        gluPerspective(70, 1.25, 0.1, 2000)
    else:
            gluPerspective(45, 1.25, 0.1, 2000)
   
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    x, y, z = camera_pos
   
    if top_view:
        gluLookAt(x, y, z, x, y, 0, 0, 1, 0)
    elif first_person_view:
        look_x = player_pos[0] + math.cos(math.radians(player_direction)) * 10
        look_y = player_pos[1] + math.sin(math.radians(player_direction)) * 10
        look_z = player_pos[2] + 70
        gluLookAt(x, y, z, look_x, look_y, look_z, 0, 0, 1)
    else:
        gluLookAt(x, y, z, player_pos[0], player_pos[1], player_pos[2] + 40, 0, 0, 1)

def idle():
    """Idle function for continuous updates"""
    global level_message_timer, showing_level_message
    
    if showing_level_message and not waiting_for_enter:
        level_message_timer -= 1
        if level_message_timer <= 0:
            showing_level_message = False
    
    if not game_over and not showing_level_message and not waiting_for_enter:
        move_police()
        check_police_detection() 
        check_game_events()
    glutPostRedisplay()

def display():
    """Main display function"""
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    setupCamera()
    update_lighting()
    draw_floor()
    draw_police_detection_zone() 
    draw_maze()
    draw_player()
    draw_police()
    draw_treasure()
    display_game_info()
    glutSwapBuffers()

def display_game_info():
    """Display game status information"""
    view_mode = "Top View" if top_view else "First Person" if first_person_view else "Third Person"
    
    # Handle game over display
    if game_over:
        # Show the game over message in the center of the screen
        draw_text(400, 400, "GAME OVER", GLUT_BITMAP_TIMES_ROMAN_24, color=(1.0, 0.0, 0.0))
        draw_text(350, 350, "YOU WERE CAUGHT BY THE POLICE!", GLUT_BITMAP_HELVETICA_18, color=(1.0, 0.3, 0.3))
        draw_text(370, 300, f"SCORE: LEVEL {level}", GLUT_BITMAP_HELVETICA_18, color=(1.0, 0.7, 0.0))
        draw_text(340, 250, "PRESS 'R' TO RESTART", GLUT_BITMAP_HELVETICA_18, color=(0.0, 1.0, 0.5))
        
        # Still show the controls and info at the side
        y_pos = 750
        for line in [
            f"Level: {level}",
            f"View Mode: {view_mode}",
            "Controls:",
            "R: Restart game",
            "ESC: Exit game"
        ]:
            draw_text(20, y_pos, line, color=(0.8, 0.8, 1.0))
            y_pos -= 20
        return
    
    # Handle level up message
    elif showing_level_message:
        # Make text bigger and centered
        draw_text(400, 400, f"LEVEL {level}", GLUT_BITMAP_TIMES_ROMAN_24, color=(0.2, 0.8, 0.2))
        draw_text(350, 350, f"{num_police} POLICE OFFICERS HUNTING YOU!", GLUT_BITMAP_HELVETICA_18, color=(1.0, 0.5, 0.0))
        if waiting_for_enter:
            draw_text(350, 300, "PRESS ENTER TO CONTINUE", GLUT_BITMAP_HELVETICA_18, color=(0.0, 1.0, 1.0))
        return
        
    # Regular game info display
    status = "LEVEL COMPLETE - Treasure Collected!" if level_complete else "Find the treasure and avoid the police!"
    status_color = (0.0, 1.0, 0.3) if level_complete else (1.0, 0.8, 0.0)
    
    # Draw status with special color
    draw_text(20, 750, status, color=status_color)
    
    y_pos = 730
    # Draw level info with light blue
    draw_text(20, y_pos, f"Level: {level}", color=(0.4, 0.7, 1.0))
    y_pos -= 20
    
    # Draw view mode info with light purple
    draw_text(20, y_pos, f"View Mode: {view_mode}", color=(0.7, 0.5, 1.0))
    y_pos -= 20
    
    # Draw controls title with light yellow
    draw_text(20, y_pos, "Controls:", color=(1.0, 1.0, 0.7))
    y_pos -= 20
    
    # Draw controls with light cyan
    for line in [
        "W/S: Move forward/backward",
        "A/D: Strafe left/right",
        "Q/E: Rotate left/right",
        "V: Toggle view mode",
        "T: Top-down view",
        "Z: Toggle zoom"
    ]:
        draw_text(20, y_pos, line, color=(0.7, 1.0, 1.0))
        y_pos -= 20

def reset_game():
    """Reset the game to initial state"""
    global player_pos, game_over, treasure_collected, level_complete
    global police_positions, police_directions, police_original_positions
    global level, num_police, showing_level_message, waiting_for_enter
    
    # Reset game state
    game_over = False
    treasure_collected = False
    level_complete = False
    showing_level_message = False
    waiting_for_enter = False
    
    # Reset to level 1
    level = 1
    num_police = 2  # Initial number of police
    
    # Reset player position
    cell_size = WALL_THICKNESS * 2
    for i in range(len(maze)):
        for j in range(len(maze[0])):
            if maze[i][j] == 0:
                player_pos[0] = maze_offset_x + j * cell_size + cell_size/2
                player_pos[1] = maze_offset_y + i * cell_size + cell_size/2
                player_pos[2] = 0
                break
    
    # Regenerate game objects
    place_game_objects()
    update_camera()

def init():
    """Initialize the game"""
    glClearColor(0.5, 0.7, 1.0, 1.0)
    init_3d()
    
    # Find starting position
    cell_size = WALL_THICKNESS * 2
    for i in range(len(maze)):
        for j in range(len(maze[0])):
            if maze[i][j] == 0:
                player_pos[0] = maze_offset_x + j * cell_size + cell_size/2
                player_pos[1] = maze_offset_y + i * cell_size + cell_size/2
                player_pos[2] = 0
                return
    
    player_pos[0] = 0
    player_pos[1] = 0
    player_pos[2] = 0

def main():
    """Main function"""
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(1000, 800)
    glutInitWindowPosition(100, 100)
    glutCreateWindow(b"Treasure Robbery Game")
    
    init()
    glutDisplayFunc(display)
    glutIdleFunc(idle)
    glutKeyboardFunc(keyboardListener)
    glutSpecialFunc(lambda *args: None)
    glutMouseFunc(lambda *args: None)
    glutReshapeFunc(lambda w, h: glViewport(0, 0, w, h))
    
    update_camera()
    glutMainLoop()

if __name__ == "__main__":
    main()