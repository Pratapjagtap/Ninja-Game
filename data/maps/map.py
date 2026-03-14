import random
import json

def generate_map(level_id):
    random.seed(level_id * 12345)
    tilemap_data = {"tilemap": {}, "tile_size": 16, "offgrid": []}
    width = 40 + level_id * 2
    height = 20
    enemy_count = min(3 + level_id, 15)
    platform_count = 5 + level_id // 2
    
    # generate terrain - create a more stable ground level
    base_ground_y = 15  # closer to bottom
    current_ground = base_ground_y
    
    # First pass: determine ground heights
    ground_heights = {}
    for x in range(-5, width + 5):
        if random.random() < 0.3:  # chance to vary height
            current_ground += random.randint(-1, 1)
            current_ground = max(10, min(height - 2, current_ground))  # keep reasonable bounds
        ground_heights[x] = current_ground
    
    # Second pass: place tiles
    for x in range(-5, width + 5):
        ground_y = ground_heights[x]
        for y in range(ground_y, height + 3):  # fill from ground down
            if y == ground_y:
                tile_type = "grass"
                variant = random.choice([0, 1, 2, 3, 4, 5, 6, 7, 8])
            else:
                tile_type = "stone"
                variant = random.choice([0, 1, 2, 3, 4, 5, 6, 7, 8])
            key = f"{x};{y}"
            tilemap_data["tilemap"][key] = {"type": tile_type, "variant": variant, "pos": [x, y]}
    
    # add platforms - make sure they're above ground
    for _ in range(platform_count):
        plat_length = random.randint(3, 8)
        plat_x = random.randint(5, width - plat_length - 5)
        
        # Find ground level at this x position for reference
        ref_ground = ground_heights.get(plat_x, base_ground_y)
        plat_y = random.randint(5, ref_ground - 3)  # platform above ground
        
        for px in range(plat_length):
            x = plat_x + px
            y = plat_y
            key = f"{x};{y}"
            
            # Platform tile variants: 0=left, 1=middle, 2=right
            if px == 0:
                variant = 0  # left edge
            elif px == plat_length - 1:
                variant = 2  # right edge
            else:
                variant = 1  # middle
                
            tilemap_data["tilemap"][key] = {"type": "grass", "variant": variant, "pos": [x, y]}
            
            # add some stone support below platforms
            for dy in range(1, random.randint(2, 4)):
                below_key = f"{x};{y+dy}"
                if below_key not in tilemap_data["tilemap"]:
                    tilemap_data["tilemap"][below_key] = {"type": "stone", "variant": random.randint(0, 8), "pos": [x, y + dy]}
    
    # add decorations - replace some grass tiles with decor
    grass_tiles = [(k, v) for k, v in tilemap_data["tilemap"].items() if v["type"] == "grass"]
    decor_count = max(1, len(grass_tiles) // 20)  # about 5% of grass tiles
    
    for _ in range(decor_count):
        if grass_tiles:
            key, tile = random.choice(grass_tiles)
            grass_tiles.remove((key, tile))  # don't reuse
            decor_variant = random.randint(0, 3)
            tilemap_data["tilemap"][key] = {"type": "decor", "variant": decor_variant, "pos": tile["pos"]}
    
    # add large decor offgrid
    for _ in range(5 + level_id):
        type_ = "large_decor"
        variant = random.randint(0, 2)
        pos_x = random.uniform(0, width * 16)
        pos_y = random.uniform(0, height * 16)
        tilemap_data["offgrid"].append({"type": type_, "variant": variant, "pos": [pos_x, pos_y]})
    
    # add spawners
    # player spawner - place above ground level
    spawn_ground = ground_heights.get(3, base_ground_y)
    player_spawn_y = (spawn_ground - 2) * 16  # 2 tiles above ground
    tilemap_data["offgrid"].append({"type": "spawners", "variant": 0, "pos": [50.0, float(player_spawn_y)]})
    
    # enemy spawners
    for _ in range(enemy_count):
        spawn_x = random.randint(10, width - 5)
        ref_ground = ground_heights.get(spawn_x, base_ground_y)
        pos_x = spawn_x * 16 + random.uniform(-8, 8)
        pos_y = (ref_ground - random.randint(1, 3)) * 16  # above ground level
        variant = random.choice([1, 2])  # enemy variants
        tilemap_data["offgrid"].append({"type": "spawners", "variant": variant, "pos": [pos_x, pos_y]})
    
    return tilemap_data

# generate for levels 3,4,5
for level in [3, 4, 5]:
    map_data = generate_map(level)
    filename = f"{level}.json"
    with open(filename, 'w') as f:
        json.dump(map_data, f, indent=2)
    print(f"Generated {filename}")