from PIL import Image
import os
import glob

# Rutas
src_dir = r'C:\Users\Personal\.gemini\antigravity\brain\553e80d4-2ff2-4f65-bb3b-1288444f1762'
dst_dir = r'c:\Users\Personal\Downloads\GIT\RelojMundial\assets'

# Imagen original subida
orig_img = r'C:\Users\Personal\.gemini\antigravity\brain\553e80d4-2ff2-4f65-bb3b-1288444f1762\.user_uploaded\media_1789366202347.jpg'

images = {
    'avatar_count.png': orig_img,
    'avatar_work.png': glob.glob(os.path.join(src_dir, 'avatar_work*.jpg'))[0],
    'avatar_lunch.png': glob.glob(os.path.join(src_dir, 'avatar_lunch*.jpg'))[0],
    'avatar_preclose.png': glob.glob(os.path.join(src_dir, 'avatar_preclose*.jpg'))[0],
    'avatar_rest.png': glob.glob(os.path.join(src_dir, 'avatar_rest*.jpg'))[0],
}

def remove_bg(img):
    img = img.convert('RGBA')
    data = img.getdata()
    new_data = []
    # threshold for white
    for item in data:
        if item[0] > 235 and item[1] > 235 and item[2] > 235:
            new_data.append((255, 255, 255, 0))
        else:
            new_data.append(item)
    img.putdata(new_data)
    return img

for name, path in images.items():
    print(f'Processing {name} from {path}...')
    img = Image.open(path)
    
    # Original user image might already have transparency but it's a jpg, let's treat it same
    img = remove_bg(img)
    
    # Resize to max 300x300 to keep it light
    img.thumbnail((300, 300), Image.LANCZOS)
    
    out_path = os.path.join(dst_dir, name)
    img.save(out_path, 'PNG')
    print(f'Saved {out_path}')

print('Done!')
