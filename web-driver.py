# Selenium imports
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoAlertPresentException

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
overall_delay=0.1

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


def pick_random_directon():
    random_num = random.randint(1, 4) 
    if random_num == 1: return Keys.ARROW_UP
    elif random_num == 2: return Keys.ARROW_RIGHT
    elif random_num == 3: return Keys.ARROW_DOWN
    else: return Keys.ARROW_LEFT


# To remove all elements included in an array by class, xpath, or id
def remove_elements(element_removal_array):
    for element_info in element_removal_array:
        element_type, element_value = element_info 
        if element_type == "class":
            toRemove = driver.find_element(By.CLASS_NAME, value=element_value)
        elif element_type == "xpath":
            toRemove = driver.find_element(By.XPATH, value=element_value)
        elif element_type == "id":
            toRemove = driver.find_element(By.ID, value=element_value)
        driver.execute_script("arguments[0].remove();", toRemove)


# To get the current maximum block size that has been merged/acheived
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
        tileHtml = tile_container.get_attribute("innerHTML")

        # Parse the HTML and get the updated grid
        updated_grid = parse_tiles(tileHtml)
    
        # Print the updated grid
        for row in updated_grid:
            print(row)

        # Print the highest current block size reached
        print(get_max_size(tileHtml))

        # Main movements
        time.sleep(overall_delay)
        game_container.send_keys(pick_random_directon())

    time.sleep(3)
    game_loop()

# Remove unecessary elements (ads and the like)
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
