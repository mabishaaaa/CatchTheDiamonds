from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import random
import time

window_width = 800
window_height = 600

base_width = 120
base_height = 18
base_pos = 36

diamond_size = 30

max_diamonds = 1

diamond_interval = 0.9  # seconds

speed = 160.0
speed_inc = 20.0

POINT_SIZE = 3
ICON_SIZE = 44

base_position = int(window_width / 2 - base_width / 2)
diamonds_list = []

paused = False
game_over = False
score = 0

last_diamond = 0.0
last_frame_time = None
game_start_time = None
current_speed = speed

icon_bounding_boxes = {}


def plot_point(x, y):
    glVertex2i(int(round(x)), int(round(y)))


def determine_zone(dx, dy):
    abs_dx = abs(dx)
    abs_dy = abs(dy)

    if abs_dx >= abs_dy:
        if dx >= 0 and dy >= 0:
            return 0
        if dx >= 0 and dy < 0:
            return 7
        if dx < 0 and dy >= 0:
            return 3
        return 4
    else:
        if dx >= 0 and dy >= 0:
            return 1
        if dx >= 0 and dy < 0:
            return 6
        if dx < 0 and dy >= 0:
            return 2
        return 5


def to_zone0(x, y, zone):
    mapping = [
        (x, y), (y, x), (y, -x), (-x, y),
        (-x, -y), (-y, -x), (-y, x), (x, -y)
    ]
    return mapping[zone]


def from_zone0(x, y, zone):
    mapping = [
        (x, y), (y, x), (-y, x), (-x, y),
        (-x, -y), (-y, -x), (y, -x), (x, -y)
    ]
    return mapping[zone]


def MPL(x_start, y_start, x_end, y_end):
    x0 = int(round(x_start))
    y0 = int(round(y_start))
    x1 = int(round(x_end))
    y1 = int(round(y_end))

    dx = x1 - x0
    dy = y1 - y0

    if dx == 0 and dy == 0:
        glBegin(GL_POINTS)
        plot_point(x0, y0)
        glEnd()
        return

    zone = determine_zone(dx, dy)
    rel_x1, rel_y1 = to_zone0(dx, dy, zone)

    zx0, zy0 = 0, 0
    zx1 = int(round(rel_x1))
    zy1 = int(round(rel_y1))

    if zx1 < zx0:
        temp_x = zx0
        temp_y = zy0
        zx0 = zx1
        zy0 = zy1
        zx1 = temp_x
        zy1 = temp_y

    dxz = zx1 - zx0
    dyz = zy1 - zy0

    d = 2 * dyz - dxz
    incrE = 2 * dyz
    incrNE = 2 * (dyz - dxz)

    x = zx0
    y = zy0

    glBegin(GL_POINTS)
    while x <= zx1:
        orig_x, orig_y = from_zone0(x, y, zone)
        plot_point(orig_x + x0, orig_y + y0)

        if d > 0:
            y += 1
            d += incrNE
        else:
            d += incrE

        x += 1
    glEnd()


def draw_diamond(cen_x, cen_y, size):
    half = int(size / 2)
    MPL(cen_x, cen_y + half, cen_x + half, cen_y)
    MPL(cen_x + half, cen_y, cen_x, cen_y - half)
    MPL(cen_x, cen_y - half, cen_x - half, cen_y)
    MPL(cen_x - half, cen_y, cen_x, cen_y + half)


def back_arrow(cen_x, cen_y, size, color):  #size  = icon_size
    glColor3f(color[0], color[1], color[2])

    half = int(size / 2)
    quarter = int(size / 4)

    tip_x = cen_x - half
    tip_y = cen_y

    # two diagonal lines forming "<"
    MPL(tip_x + quarter, tip_y + quarter, tip_x, tip_y)
    MPL(tip_x + quarter, tip_y - quarter, tip_x, tip_y)

    # horizontal shaft to the right
    line_start = tip_x
    line_end = line_start + size
    MPL(line_start, tip_y, line_end, tip_y)


def pause(cen_x, cen_y, size, color):
    glColor3f(color[0], color[1], color[2])

    half_height = int(size / 2)
    bar_width = 2
    gap = 10

    left_x = cen_x - gap
    right_x = cen_x + gap

    MPL(left_x, cen_y - half_height, left_x, cen_y + half_height)
    MPL(right_x, cen_y - half_height, right_x, cen_y + half_height)


def play(cen_x, cen_y, size, color):
    glColor3f(color[0], color[1], color[2])

    half = int(size / 2)
    x0, y0 = cen_x - half, cen_y - half
    x1, y1 = cen_x - half, cen_y + half
    x2, y2 = cen_x + half, cen_y

    MPL(x0, y0, x1, y1)
    MPL(x1, y1, x2, y2)
    MPL(x2, y2, x0, y0)


def x_icon(cen_x, cen_y, size, color):
    glColor3f(color[0], color[1], color[2])

    half = int(size / 2)
    MPL(cen_x - half, cen_y - half, cen_x + half, cen_y + half)
    MPL(cen_x - half, cen_y + half, cen_x + half, cen_y - half)


def base(base_x, base_y, base_width, base_height, color):
    glColor3f(color[0], color[1], color[2])

    half_base = (base_width * 0.6) / 2.0  # narrower bottom

    half_top = base_width / 2.0

    bottom_y = base_y
    top_y = base_y + base_height

    MPL(base_x - half_base, bottom_y, base_x + half_base, bottom_y)
    MPL(base_x - half_base, bottom_y, base_x - half_top, top_y)
    MPL(base_x - half_top, top_y, base_x + half_top, top_y)
    MPL(base_x + half_top, top_y, base_x + half_base, bottom_y)


def overlap(ax0, ay0, ax1, ay1, bx0, by0, bx1, by1):        #First rectangle (A): (ax0, ay0) = bottom-left corner, (ax1, ay1) = top-right corner.
    if ax1 < bx0 or ax0 > bx1 or ay1 < by0 or ay0 > by1:    #Second rectangle (B): (bx0, by0) = bottom-left corner, (bx1, by1) = top-right corner.
        return False                                        #ax1 < bx0 → Rectangle A’s right side is to the left of Rectangle B’s left side.
    return True                                             #ax0 > bx1 → Rectangle A’s left side is to the right of Rectangle B’s right side.


def checker(px, py, rect):  # is_point_inside_rectangle         px, py = point’s coordinates.   rect = rectangle coordinates (x0, y0, x1, y1).
    x0, y0, x1, y1 = rect                                   
    if px >= x0 and px <= x1 and py >= y0 and py <= y1:     
        return True
    return False


def new_diamond():
    min_x = 40                  #horizontal range where a diamond can spawn.
    max_x = window_width - 40   # leaves a margin on the right.
    diamond_x = random.randint(min_x, max_x)
    diamond_y = window_height + int(diamond_size / 2)       #Sets the starting Y coordinate for the diamond so it appears just above the top edge of the window.

    diamond = {
        'x': diamond_x,
        'y': diamond_y,
        'size': diamond_size,
        'color': (random.random(), random.random(), random.random())
    }
    diamonds_list.append(diamond)       #Once in the list, the display_function() will draw it every frame, and idle_function() will move it down over time.


def reset_game():
    global diamonds_list, score, last_diamond, game_start_time, current_speed, paused, game_over

    diamonds_list = []
    score = 0
    last_diamond = time.time()
    game_start_time = time.time()
    current_speed = speed
    paused = False
    game_over = False


def update_icon_areas():
    global icon_bounding_boxes
    center_y = window_height - 40   #Calculates the vertical position of the icons: window_height is the top of the window. Subtracting 40 moves down from the top so the icons aren’t stuck to the window edge. This makes all icons sit at the same height.
    half_icon = int(ICON_SIZE / 2)  #This is needed because the icon’s position is stored by its center, but we need its bounding box, which uses edges.

    icon_bounding_boxes = {
        'left': (40 - half_icon, center_y - half_icon, 40 + half_icon, center_y + half_icon),   #(40, center_y) is the center of the back arrow icon.
                                                                                                #x0 = 40 - half_icon (left edge)

                                                                                                #y0 = center_y - half_icon (bottom edge)

                                                                                                #x1 = 40 + half_icon (right edge)

                                                                                                #y1 = center_y + half_icon (top edge)
        'pause': (int(window_width / 2) - half_icon, center_y - half_icon, int(window_width / 2) + half_icon, center_y + half_icon),    #The center is at window_width / 2 → exactly the middle of the window.
        'quit': (window_width - 40 - half_icon, center_y - half_icon, window_width - 40 + half_icon, center_y + half_icon)              #The center is window_width - 40 → near the right edge.
    }


def display_function():
    global diamonds_list, base_position

    glClear(GL_COLOR_BUFFER_BIT)        #Without this, old frame drawings would remain and overlap — leading to visual glitches.
    glPointSize(POINT_SIZE)

    back_arrow(40, window_height - 40, ICON_SIZE, (0.1, 0.9, 0.9))  #Draws a back arrow icon at position (40, window_height - 40).

    if paused:
        play(int(window_width / 2), window_height - 40, ICON_SIZE, (0.95, 0.85, 0.2))   #If paused → draws a play icon (triangle) in the center-top of the screen so you can resume the game.
    else:
        pause(int(window_width / 2), window_height - 40, ICON_SIZE, (0.95, 0.85, 0.2))  #Position is horizontally centered at window_width / 2 and 40 pixels down from the top.

    x_icon(window_width - 40, window_height - 40, ICON_SIZE, (0.95, 0.2, 0.2))

    base_base_x = base_position + base_width / 2
    base(base_base_x, base_pos, base_width+50, base_height+10, (0.85, 0.05, 0.05))   #Centered at base_base_x, vertical position base_pos.

    for diamond in diamonds_list:
        glColor3f(diamond['color'][0], diamond['color'][1], diamond['color'][2])
        draw_diamond(diamond['x'], int(round(diamond['y'])), diamond['size'])

    glFlush()  


def idle_function():        #, which GLUT calls repeatedly whenever the program is idle (i.e., no other events like mouse or keyboard are happening).
    global last_frame_time, last_diamond, current_speed, score, game_over, paused

    current_time = time.time()

    if last_frame_time is None:
        last_frame_time = current_time

    time_passed = current_time - last_frame_time
    last_frame_time = current_time

    if not paused and not game_over:
        if len(diamonds_list) < max_diamonds and (current_time - last_diamond) >= diamond_interval:
            new_diamond()
            last_diamond = current_time #Update last_diamond to the current time so the next diamond won't spawn immediately.

        current_speed = speed + speed_inc * ((current_time - game_start_time) / 60.0)

        diamonds_to_remove = []     #Prepares a list to store indexes of diamonds that should be removed (either caught or missed).

        for i, diamond in enumerate(diamonds_list):         #diamond = dictionary containing the diamond's properties (x, y, size, color).
            diamond['y'] -= current_speed * time_passed     #Subtracting from y makes it fall.  
            # diamond['y'] -= 0.2
            ax0 = diamond['x'] - diamond['size'] // 2   #These variables define the bounding box for the diamond:
            ay0 = diamond['y'] - diamond['size'] // 2   #The // 2 centers the box on the diamond’s position.
            ax1 = diamond['x'] + diamond['size'] // 2
            ay1 = diamond['y'] + diamond['size'] // 2

            # bx0 = base_position - 8         #collision detection is a little more forgiving — a diamond doesn’t have to perfectly touch the base to be “caught.”
            # by0 = base_pos
            # bx1 = base_position + base_width + 8    #top-right of base
            # by1 = base_pos + base_height * 3

            bx0 = base_position       
            by0 = base_pos
            bx1 = base_position + base_width    #top-right of base
            by1 = base_pos + base_height

            if overlap(ax0, ay0, ax1, ay1, bx0, by0, bx1, by1):
                diamonds_to_remove.append(i)
                score += 1
                print("Score:", score)
            elif ay1 < 0:
                game_over = True
                paused = True
                print("GAME OVER")
                print("FINAL SCORE:", score)
                break

        for idx in sorted(diamonds_to_remove, reverse=True):
            diamonds_list.pop(idx)

    glutPostRedisplay()


def special_key_function(key, x, y):
    global base_position
    if key == GLUT_KEY_LEFT:
        base_position = max(8, base_position - 30)      #The max(8) part ensures the base doesn’t go off the left edge of the screen.
    elif key == GLUT_KEY_RIGHT:
        base_position = min(window_width - base_width - 8, base_position + 30)      #window_width - base_width - 8 is the furthest right the base’s left edge can go without sticking out of the window.


def mouse(button, state, mouse_x, mouse_y):
    global paused, game_over

    window_y = window_height - mouse_y

    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        for name, rect in icon_bounding_boxes.items():      #Loops over all clickable icons in the game. it is in update icon function
            if checker(mouse_x, window_y, rect):
                if name == 'left':
                    reset_game()
                    print("starting over")
                elif name == 'pause':
                    if game_over:
                        reset_game()
                        print("starting over")
                    else:
                        paused = not paused
                        print("Paused" if paused else "Resumed")
                elif name == 'quit':
                    game_over = True
                    paused = True
                    print("GAME OVER")
                    print("FINAL SCORE:", score)
                    glutLeaveMainLoop()


def reshape_function(width, height):
    global window_width, window_height
    window_width = width
    window_height = height      #Updates the global window_height to the new height passed by GLUT.

    glViewport(0, 0, width, height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(0, width, 0, height, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    update_icon_areas()


def init():
    glClearColor(0.02, 0.02, 0.02, 1.0)
    glPointSize(POINT_SIZE)
    update_icon_areas()


def main():
    global last_frame_time, last_diamond, game_start_time

    glutInit([])  
    glutInitDisplayMode(GLUT_SINGLE | GLUT_RGBA)  
    glutInitWindowSize(window_width, window_height)     #Sets the initial size of the window using the previously defined global variables (window_width and window_height).
    glutInitWindowPosition(100, 100)
    glutCreateWindow(b"Catch the Diamonds!")        #The b prefix means the string is a byte literal, as required by GLUT.

    init()

    glutDisplayFunc(display_function)
    glutIdleFunc(idle_function)
    glutReshapeFunc(reshape_function)

    glutSpecialFunc(special_key_function)
    glutMouseFunc(mouse)

    last_frame_time = time.time()
    last_diamond = time.time()
    game_start_time = time.time()


    glutMainLoop()
main()

