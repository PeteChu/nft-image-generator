from PIL import Image 
import random
import json
from functools import reduce
import os
import glob
from multiprocessing import Process
import math
from time import perf_counter

# A recursive function to generate unique image combinations
def create_new_image(layer_config):
    
    new_image = {} #

    # For each trait category, select a random trait based on the weightings
    for layer in layer_config["layers"]:
        new_image[layer] = random.choices(layer_config["layers"][layer]["traits"], layer_config["layers"][layer]["weights"])[0]
    
    # Create new image if has incampatable trait
    for incompat in layer_config["incompatibilities"]:
        for attr in new_image:
            if new_image[incompat["layer"]] == incompat["value"] and new_image[attr] in incompat["incompatible_with"]:
                return create_new_image()
        
    if new_image in all_images:
        return create_new_image()
    else:
        return new_image
    
# Returns true if all images are unique
def all_images_unique(all_images):
    seen = list()
    return not any(i in seen or seen.append(i) for i in all_images)


def remove_metadata_images():
    ### Clear metadata and images folder
    image_files = glob.glob('./images/*.png')
    metadata_files = glob.glob('./metadata/*.json')
    files = image_files + metadata_files
    for f in files:
        try:
            os.unlink(f)
        except OSError as e:
            print("Error: %s : %s" % (f, e.strerror))

#### Generate Metadata for all Traits 
def generate_metadata_all():
    METADATA_FILE_NAME = './metadata/all-traits.json'; 
    with open(METADATA_FILE_NAME, 'w') as outfile:
        json.dump(all_images, outfile, indent=4)

def generate_images(image_combinations, layer_config):
    for items in image_combinations:        
        images = [Image.open(f'./trait-layers/{layer}/{items[layer]}').convert('RGBA') for layer in layer_config["layer_order"] if layer != 'tokenId']

        # Create each composite
        comp = reduce(lambda pre, cur: Image.alpha_composite(pre, cur), images)

        #Convert to RGB
        rgb_im = comp.convert('RGB')
        file_name = str(items["tokenId"]) + ".png"
        rgb_im.save("./images/" + file_name)

        
def chunk_image(images, chunk_num = 1):
    result_imgs = []
    mov_slice = math.floor(len(images) / chunk_num)
    print(f"mov_slice {mov_slice}")
    for i in range(chunk_num):
        if i != chunk_num -1:
            result_imgs.append(images[i*mov_slice :(i+1)*mov_slice])
        else:
            result_imgs.append(images[i*mov_slice:])

    return result_imgs

# collection_imgs(all_images, 3)

def generate_image_multiprocessing(chunks, layer_config):
    
    processes = [Process(target=generate_images, args=(chunk, layer_config)) for chunk in chunks]
    
    for process in processes:
        process.start()
        
    for process in processes:
        process.join()


#### Generate Metadata for each Image    
def getAttribute(key, value):
    return {
        "trait_type": key,
        "value": value
    }

def generate_metadata():
    f = open('./metadata/all-traits.json',) 
    data = json.load(f)

    IMAGES_BASE_URI = "ADD_IMAGES_BASE_URI_HERE"
    PROJECT_NAME = "ADD_PROJECT_NAME_HERE"
    for items in data:
        token_id = items['tokenId']
        token = {
            "image": IMAGES_BASE_URI + str(token_id) + '.png',
            "tokenId": token_id,
            "name": PROJECT_NAME + ' ' + str(token_id),
            "attributes": [items[layer] for layer in items if layer != 'tokenId']
        }

        with open(f'./metadata/{str(token_id)}.json', 'w') as outfile:
            json.dump(token, outfile, indent=4)
            
    f.close()

if __name__ == '__main__':

    ## Generate Traits
    TOTAL_IMAGES = 4 # Number of random unique images we want to generate

    all_images = []
    layers = []

    # Load config file
    layer_config = {}
    try:
        with open('layer_config.json', 'r') as json_file:
            layer_config = json.load(json_file)
    except FileNotFoundError:
        raise Exception('layer_config.json is not found.')

    # Generate the unique combinations based on trait weightings
    for i in range(TOTAL_IMAGES): 
        new_trait_image = create_new_image(layer_config)
        all_images.append(new_trait_image)

    print("Are all images unique?", all_images_unique(all_images))

    # Add token Id to each image
    tokenId = 0
    for item in all_images:
        item["tokenId"] = tokenId
        tokenId = tokenId + 1

    remove_metadata_images()

    generate_metadata_all()

    start_time = perf_counter()
    generate_image_multiprocessing(chunk_image(all_images, 4), layer_config)
    end_time = perf_counter()
    print(f'Image generator took {end_time - start_time: 0.2f} seconds to complete.')

    generate_metadata()