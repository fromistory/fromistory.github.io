import os
import argparse
from PIL import Image

import twitter_utils as utils

# --- Configuration (as requested) ---
ROOT_DIRECTORY = './media/events'
OUTPUT_DIRECTORY = './docs/assets/thumb'
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif'}
ASPECT_RATIO_TOLERANCE = 0.25

# --- Aspect Ratio Configuration ---
ASPECT_RATIOS = {
    "Landscape_3_2": 3 / 2,
    "Landscape_4_3": 4 / 3,
    "Landscape_16_9": 16 / 9,
    "Square_1_1": 1 / 1,
    "Portrait_2_3": 2 / 3,
    "Portrait_3_4": 3 / 4,
}

# *** CHOOSE YOUR TARGET ASPECT RATIO HERE ***
TARGET_ASPECT_RATIO = ASPECT_RATIOS["Portrait_3_4"]

# --- Thumbnail Generation Settings ---
THUMBNAIL_HEIGHT = 400
THUMBNAIL_QUALITY = 60


# --- Helper Functions ---
def find_image_files(directory, posts):
    """Finds all image files in a given directory (not recursive)."""
    image_ids = []
    for p in posts:
        image_ids += p.get_img_ids()

    # print(image_ids)

    def is_valid_img(i):
        print(f'{directory}/{i}')
        return os.path.exists(f'{directory}/{i}')

    return [f'{directory}/{i}' for i in image_ids if is_valid_img(i)]

    # try:
    #     # for file in os.listdir(directory):
    #     #     if os.path.splitext(file)[1].lower() in IMAGE_EXTENSIONS:
    #     #         image_files.append(os.path.join(directory, file))
    # except FileNotFoundError:
    #     return []
    # return image_files


def create_thumbnail(source_path, dest_path, dry_run=False):
    """Opens, resizes, and saves a single thumbnail image."""
    try:
        with Image.open(source_path) as img:
            aspect_ratio = img.width / img.height
            new_width = int(THUMBNAIL_HEIGHT * aspect_ratio)

            if not dry_run:
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')

                resized_img = img.resize((new_width, THUMBNAIL_HEIGHT), Image.Resampling.LANCZOS)

                resized_img.save(
                    dest_path,
                    'jpeg',
                    quality=THUMBNAIL_QUALITY,
                    optimize=True,
                    progressive=True
                )
                print(f"   -> Saved {new_width}x{THUMBNAIL_HEIGHT} thumbnail to {dest_path}")
            else:
                print(f"   -> [DRY RUN] Would resize to {new_width}x{THUMBNAIL_HEIGHT} and save to {dest_path}")
    except Exception as e:
        print(f"   Error: Failed to process and save thumbnail. Error: {e}")


# --- Main Logic Functions ---
def process_all_events(root_dir, output_dir, target_aspect_ratio, dry_run=False):
    """Automatically selects the best image from each event folder."""
    print("--- Mode: Auto-selecting from all events ---")

    try:
        event_folders = [d for d in os.listdir(root_dir) if os.path.isdir(os.path.join(root_dir, d))]
    except FileNotFoundError:
        print(f"Error: The root directory '{root_dir}' was not found.")
        return

    events_dict = utils.get_events_dict()
    posts_by_event = utils.gather_posts_by_event([], events_dict)

    for event_name, posts in posts_by_event.items():
        safe_event_name = "".join(c for c in event_name if c.isalnum() or c in (' ', '_', '-')).rstrip()
        dest_path = os.path.join(output_dir, f"{safe_event_name}.jpg")
        if os.path.exists(dest_path):
            continue

        event_path = os.path.join(root_dir, event_name)
        images_in_event = find_image_files(event_path, posts)

        if not images_in_event:
            print(f"\nEvent '{event_name}': No images found, skipping.")
            continue

        matching_images = []
        for img_path in images_in_event:
            if os.path.basename(img_path) == 'thumb':
                matching_images = [{'path': img_path, 'size': 999999}]
                break

            try:
                with Image.open(img_path) as img:
                    if img.height > 0:
                        ratio = img.width / img.height
                        if abs(ratio - target_aspect_ratio) <= ASPECT_RATIO_TOLERANCE:
                            file_size = os.path.getsize(img_path)
                            matching_images.append({'path': img_path, 'size': file_size})
            except Exception:
                continue  # Skip unreadable images

        if not matching_images:
            print(f"\nEvent '{event_name}': No images matched the target aspect ratio. Skipping.")
            continue

        best_image = max(matching_images, key=lambda x: x['size'])
        best_image_path = best_image['path']

        print(f"\nEvent '{event_name}': Found {len(matching_images)} matching images.")
        print(f"   Selected: {os.path.basename(best_image_path)}")

        create_thumbnail(best_image_path, dest_path, dry_run)


def process_single_image(event_name, file_name, root_dir, output_dir, dry_run=False):
    """Processes a single, manually specified image."""
    print(f"--- Mode: Manual selection for event '{event_name}' ---")

    source_path = os.path.join(root_dir, event_name, file_name)

    if not os.path.isfile(source_path):
        print(f"Error: The specified image file was not found.")
        print(f"       Checked path: {source_path}")
        return

    print(f"   Selected: {file_name}")

    safe_event_name = "".join(c for c in event_name if c.isalnum() or c in (' ', '_', '-')).rstrip()
    dest_path = os.path.join(output_dir, f"{safe_event_name}.jpg")

    create_thumbnail(source_path, dest_path, dry_run)


# --- Script Entry Point ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Selects, resizes, and saves thumbnails for event folders.")

    parser.add_argument("--dry-run", action="store_true",
                        help="Perform a test run without creating/modifying any files.")
    parser.add_argument("--event", type=str, help="The name of a specific event folder to process.")
    parser.add_argument("--file", type=str,
                        help="The specific filename to use for the given event. Must be used with --event.")

    args = parser.parse_args()

    # Validate that --event and --file are used together
    if (args.event and not args.file) or (not args.event and args.file):
        parser.error("--event and --file must be used together.")

    run_mode = "(DRY RUN)" if args.dry_run else "(LIVE RUN)"
    print(f"--- Thumbnail Generator Initialized {run_mode} ---")

    if not args.dry_run:
        os.makedirs(OUTPUT_DIRECTORY, exist_ok=True)
    else:
        print(f"[DRY RUN] Would ensure output directory '{OUTPUT_DIRECTORY}' exists.")

    if args.event and args.file:
        # Manual Override Mode
        process_single_image(args.event, args.file, ROOT_DIRECTORY, OUTPUT_DIRECTORY, dry_run=args.dry_run)
    else:
        # Automatic Mode
        process_all_events(ROOT_DIRECTORY, OUTPUT_DIRECTORY, TARGET_ASPECT_RATIO, dry_run=args.dry_run)

    print("\n--- Process complete! ---")