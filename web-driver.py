# Selenium imports
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoAlertPresentException
from selenium.common.exceptions import NoSuchElementException

from bs4 import BeautifulSoup
import time
import os
import os.path
import sys
import json
import random

with open('env.json') as f:
    env = json.load(f)
# Check if the local path environment variable exists
try:
    local_path = env.get('local_path')
except:
    sys.exit('Please provide a local path to this folder in env.py')

page_2048 = 'https://play2048.co/'
overall_delay=0.0

# create firefox driver
try:
    options = Options()
    options.binary_location = 'C:\\Program Files\\Mozilla Firefox\\firefox.exe'
    options.add_argument("-profile")
    # options.add_argument("-headless")
    options.add_argument(local_path+"\\firefox-profiles\\main")
    options.geo_enabled = False
    driver = webdriver.Firefox(options=options, service_log_path=os.path.devnull)
except:
    sys.exit('Firefox failed to launch, please check the install location above')

# Start the page
driver.get(page_2048)
time.sleep(5)

# Disable scrolling
driver.execute_script("document.body.style.overflow='hidden';")


# Function to calculate the score of a given grid
# Takes the 2D list representing tile arrangement as input
def calculate_grid_score(tile_list):
    """
    Calculate the score of a given 2D list representing the 2048 game grid.
    The score is based on several strategic elements:
    - Tile values and their positions.
    - Highest tile value, especially if located in a corner.
    - Number of empty tiles for maneuverability.
    - Potential merges (additional complexity).
    """
    score = 0
    highest_tile = 0
    empty_tiles = 0
    size = len(tile_list)

    # Check if the highest tile is in a corner
    corners = [tile_list[0][0], tile_list[0][-1], tile_list[-1][0], tile_list[-1][-1]]

    for i, row in enumerate(tile_list):
        for j, tile in enumerate(row):
            if tile > 0:
                # Increase score by tile value
                score += tile

                # Update highest tile value
                if tile > highest_tile:
                    highest_tile = tile

                # Check for potential merges with adjacent tiles (vertically and horizontally)
                if i < size - 1 and tile == tile_list[i+1][j]:  # Check vertically
                    score += tile * 5
                if j < size - 1 and tile == tile_list[i][j+1]:  # Check horizontally
                    score += tile * 5
            else:
                # Count empty tiles
                empty_tiles += 1

    # Add bonus for highest tile being in a corner
    if highest_tile in corners:
        score += highest_tile * 20

    # Increase score for highest tile and empty tiles
    score += highest_tile * 10
    score += empty_tiles * 50

    return score



# Return a simulated possible next random tile placement
# Takes the 2D list representing tile arrangement as input
def simulate_random_tile(tile_list):
    empty_tiles = []

    # Go through tile list and create an array of all those that are empty
    for row_index, row in enumerate(tile_list):
        for tile_index, tile in enumerate(row):
            if tile == 0: 
                empty_tiles.append([row_index,tile_index])
    
    if empty_tiles == []: return tile_list

    # Get a random empty space to add the new time to
    random_tile_num = random.randint(0, len(empty_tiles)-1)
    random_tile = empty_tiles[random_tile_num]

    # Get the new tile value (90% are 2, 10% are 4)
    random_decimal = random.random()
    if random_decimal <= 0.9: new_tile_value = 2
    else: new_tile_value = 4

    # Set the tile and return the list
    tile_list[random_tile[0]][random_tile[1]] = new_tile_value
    return tile_list


# Helper function to merge tiles in a given row
def merge_row(row):
    merged_row = []
    prev_tile = None
    merge_count = 0

    for tile in row:
        if tile == 0:
            continue

        if prev_tile is None:
            prev_tile = tile
        elif prev_tile == tile:
            merged_row.append(prev_tile * 2)
            prev_tile = None
            merge_count += 1
        else:
            merged_row.append(prev_tile)
            prev_tile = tile

    if prev_tile is not None:
        merged_row.append(prev_tile)

    while len(merged_row) < 4:
        merged_row.append(0)

    return merged_row


# Simulate what will happen to the grid if the UP arrow is pressed
# Takes the 2D list representing tile grid as input
def simulate_up_movement(tile_list):
    # Transpose the grid to simplify the logic (temporarily)
    tile_list = [[tile_list[j][i] for j in range(4)] for i in range(4)]
    # Apply the merge function to each row
    updated_tile_list = [merge_row(row) for row in tile_list]
    # Transpose the grid back to its original orientation
    updated_tile_list = [[updated_tile_list[j][i] for j in range(4)] for i in range(4)]
    return updated_tile_list


# Simulate what will happen to the grid if the LEFT arrow is pressed
# Takes the 2D list representing tile grid as input
def simulate_left_movement(tile_list):
    # Apply the merge function to each row directly for left movement
    updated_tile_list = [merge_row(row) for row in tile_list]
    return updated_tile_list


# Simulate what will happen to the grid if the RIGHT arrow is pressed
# Takes the 2D list representing tile grid as input
def simulate_right_movement(tile_list):
    # Reverse each row, simulate left movement, and reverse again to get right movement
    reversed_tile_list = [row[::-1] for row in tile_list]
    updated_tile_list = simulate_left_movement(reversed_tile_list)
    updated_tile_list = [row[::-1] for row in updated_tile_list]
    return updated_tile_list


# Simulate what will happen to the grid if the DOWN arrow is pressed
# Takes the 2D list representing tile grid as input
def simulate_down_movement(tile_list):
    # Transpose and reverse the grid to simplify the logic
    tile_list = [[tile_list[j][i] for j in range(4)] for i in range(4)]
    tile_list = [row[::-1] for row in tile_list]
    # Apply the merge function to each row
    updated_tile_list = [merge_row(row) for row in tile_list]
    # Reverse and transpose the grid back to its original orientation
    updated_tile_list = [row[::-1] for row in updated_tile_list]
    updated_tile_list = [[updated_tile_list[j][i] for j in range(4)] for i in range(4)]
    return updated_tile_list


# Return a direction to move based on array of directions
def select_direction(directions_arr):
    # Sort the array
    directions_arr.sort(reverse=True)
    # Place the first element (highest score) in the best array and pop it off the original arr
    best_directions = [directions_arr[0][1]]
    directions_arr.pop(0)
    # Add any other equivalent scores to the best array (add the direction)
    for direction in directions_arr:
        if (direction[0] == directions_arr[0][0]): best_directions.append(direction[1])
    # Select a random direction from the best array
    random_num = random.randint(0, len(best_directions) - 1) 
    return best_directions[random_num]


# Return a random direction to move
def pick_random_direction():
    random_num = random.randint(1, 4) 
    if random_num == 1: return Keys.ARROW_UP
    elif random_num == 2: return Keys.ARROW_RIGHT
    elif random_num == 3: return Keys.ARROW_DOWN
    else: return Keys.ARROW_LEFT


# To remove all elements included in an array by class, xpath, or id
def remove_elements(element_removal_array):
    for element_info in element_removal_array:
        element_type, element_value = element_info 
        try:
            if element_type == "class":
                toRemove = driver.find_element(By.CLASS_NAME, value=element_value)
            elif element_type == "xpath":
                toRemove = driver.find_element(By.XPATH, value=element_value)
            elif element_type == "id":
                toRemove = driver.find_element(By.ID, value=element_value)
            driver.execute_script("arguments[0].remove();", toRemove)
        except NoSuchElementException:
            pass


# To get the current maximum block size that has been merged/achieved
# Requires the html inside the element with class "tile-container"
def get_max_size(html):
    # Parse the HTML using BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')

    # Find all tile elements
    tile_elements = soup.find_all(class_='tile')
    
    best_tile = 2
    for tile_element in tile_elements:
        tile_value = int(tile_element.find(class_='tile-inner').text)
        if tile_value > best_tile: best_tile = tile_value

    return best_tile


# To parse each current tile on the board and store it in a 2d list
# Requires the html inside the element with class "tile-container"
def parse_tiles(html):
    # Initialize a 4x4 grid as a list of lists (e.g., a nested list of 0 values)
    grid = [[0] * 4 for _ in range(4)]

    # Parse the HTML using BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')

    # Find all tile elements
    tile_elements = soup.find_all(class_='tile')

    # Store the positions of all merged tiles
    merged_tile_positions = set()
    for tile_element in tile_elements:
        if 'tile-merged' in tile_element.get('class'):
            # Extract the position (row, column) from the class list
            position = tuple(map(int, tile_element.get('class')[2].split('-')[2:]))
            merged_tile_positions.add(position)

    # Iterate through the tile elements and update the grid
    for tile_element in tile_elements:
        classes = tile_element.get('class')
        # Extract the position (row, column) from the class list
        position = tuple(map(int, classes[2].split('-')[2:]))
        # Skip tiles that are in the process of merging, unless it's the merged tile itself
        if position in merged_tile_positions and 'tile-merged' not in classes:
            continue

        # Once the position is determined, parse the tile value and update the grid
        tile_value = int(tile_element.find(class_='tile-inner').text)
        # Since the HTML uses 1-based indexing and our grid is 0-based, subtract 1 from each index
        grid_col_index = position[0] - 1
        grid_row_index = position[1] - 1
        grid[grid_row_index][grid_col_index] = tile_value

    return grid


# Main game loop function
def game_loop():
    # Restart game
    restart = driver.find_element(By.CLASS_NAME, value="restart-button")
    restart.click()
    # Check if an alert is present before switching to it
    try:
        alert = driver.switch_to.alert
        alert.accept()
    except NoAlertPresentException:
        pass

    game_container = driver.find_element(By.TAG_NAME, value="body")

    # Main loop
    playing_game = True
    while playing_game:
        # Check if the game is still going
        game_status = driver.find_element(By.CLASS_NAME, value="game-message")
        game_status_text = game_status.get_attribute("class")
        if "game-over" in game_status_text:
            playing_game = False

        tile_container = driver.find_element(By.CLASS_NAME, value="tile-container")
        tile_html = tile_container.get_attribute("innerHTML")

        # Parse the HTML and get the updated grid
        updated_grid = parse_tiles(tile_html)

        sim_arr = []

        # Simulate pressing the down arrow
        down_sim_grid = simulate_down_movement(updated_grid)
        if (down_sim_grid != updated_grid):
            # down_sim_grid = simulate_random_tile(down_sim_grid)
            down_sim_score = calculate_grid_score(down_sim_grid)
            sim_arr.append([down_sim_score, Keys.ARROW_DOWN])

        # Simulate pressing the up arrow
        up_sim_grid = simulate_up_movement(updated_grid)
        if (up_sim_grid != updated_grid):
            # up_sim_grid = simulate_random_tile(up_sim_grid)
            up_sim_score = calculate_grid_score(up_sim_grid)
            sim_arr.append([up_sim_score, Keys.ARROW_UP])

        # Simulate pressing the left arrow
        left_sim_grid = simulate_left_movement(updated_grid)
        if (left_sim_grid != updated_grid):
            # left_sim_grid = simulate_random_tile(left_sim_grid)
            left_sim_score = calculate_grid_score(left_sim_grid)
            sim_arr.append([left_sim_score, Keys.ARROW_LEFT])

        # Simulate pressing the right arrow
        right_sim_grid = simulate_right_movement(updated_grid)
        if (right_sim_grid != updated_grid):
            # right_sim_grid = simulate_random_tile(right_sim_grid)
            right_sim_score = calculate_grid_score(right_sim_grid)
            sim_arr.append([right_sim_score, Keys.ARROW_RIGHT])

        # Select a direction to move based on the stored simulation values
        if sim_arr == []: game_container.send_keys(pick_random_direction())
        else: game_container.send_keys(select_direction(sim_arr))

        # Main movements
        time.sleep(overall_delay)

    # Get the best tile achieved
    tile_html = tile_container.get_attribute("innerHTML")
    max_tile = get_max_size(tile_html)
    # Get the game score
    score_container = driver.find_element(By.CLASS_NAME, "score-container")
    score = score_container.get_attribute("innerText").split('\n')[0]
    # Print the score, wait, and restart the loop
    print(f"Game Over - Best tile achieved: {max_tile}, Score: {score}")
    time.sleep(3)
    game_loop()


# Remove unnecessary elements (ads and the like)
element_removal_array = [
    ["class", "game-explanation-container"],
    ["xpath", "/html/body/div[1]/p[1]"],
    ["class", "sharing"],
    ["class", "links"],
    ["xpath", "/html/body/div[1]/p"],
    ["xpath", "/html/body/div[1]/span[1]"],
    ["xpath", "/html/body/div[1]/span[1]"],
    ["id", "ezmobfooter"],
    ["class", "sidebar-left"],
    ["class", "sidebar-right"],
    ["id", "ez-video-outstream-wrap"],
    ["xpath", "/html/body/div[1]/span[1]"],
    ["xpath", "/html/body/div[1]/hr[1]"],
    ["xpath", "/html/body/div[1]/hr[1]"],
    ["xpath", "/html/body/div[1]/span[1]"]
]
remove_elements(element_removal_array)

game_loop()

driver.quit()