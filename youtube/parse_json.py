from collections import defaultdict

import json
from pathlib import Path

# --- Configuration ---
INPUT_FOLDER = Path("json/youtube")
OUTPUT_FOLDER = Path("json/parsed")
OUTPUT_FILENAME = "youtube_events.json"
# MINIMUM_VIDEO_LENGTH_SECONDS = 20


def parse_length_to_seconds(length_str: str) -> int:
    """
    Converts a time string like "1:05:12", "3:32", or "0:59" into total seconds.
    Returns 0 if the format is invalid (e.g., "N/A" or "Live").
    """
    try:
        parts = length_str.split(':')
        parts.reverse()
        total_seconds = 0
        for i, part in enumerate(parts):
            if i == 0:
                total_seconds += int(part)
            elif i == 1:
                total_seconds += int(part) * 60
            elif i == 2:
                total_seconds += int(part) * 3600
        return total_seconds
    except (ValueError, AttributeError):
        return 0


def extract_and_filter_videos(data, date_str_for_filtering, seen):
    """
    Parses the JSON structure, extracts all video details, and applies filters.
    """
    filtered_videos = []

    try:
        section_list = data.get('contents', {}) \
            .get('twoColumnSearchResultsRenderer', {}) \
            .get('primaryContents', {}) \
            .get('sectionListRenderer', {}) \
            .get('contents', [])

        for section in section_list:
            item_contents = section.get('itemSectionRenderer', {}).get('contents', [])

            for item in item_contents:
                if 'videoRenderer' in item:
                    video_renderer = item['videoRenderer']

                    video_id = video_renderer.get('videoId')
                    link = f'https://www.youtube.com/watch?v={video_id}'

                    title_runs = video_renderer.get('title', {}).get('runs', [])

                    if not (video_id and title_runs):
                        continue

                    video_title = title_runs[0].get('text', '')

                    length_obj = video_renderer.get('lengthText', {})
                    video_length_str = length_obj.get('simpleText', "0:00") if length_obj else "0:00"

                    length_sec = parse_length_to_seconds(video_length_str)
                    # if length_sec < MINIMUM_VIDEO_LENGTH_SECONDS:
                    #     continue

                    # --- If filters pass, extract all data ---
                    author_runs = video_renderer.get('longBylineText', {}).get('runs', [])
                    author_name = author_runs[0].get('text') if author_runs else "N/A"

                    view_count_obj = video_renderer.get('viewCountText', {})
                    view_count_text = view_count_obj.get('simpleText', "N/A") if view_count_obj else "N/A"

                    resolution = 'SD'
                    badges_list = video_renderer.get('badges', [])
                    for badge in badges_list:
                        label = badge.get('metadataBadgeRenderer', {}).get('label')
                        if label in ['4K', 'HD', '8K']:
                            resolution = label
                            break

                    # --- ADDED: Extract Description ---
                    description = "N/A"  # Default value
                    snippets = video_renderer.get('detailedMetadataSnippets', [])
                    if snippets:
                        snippet_text = snippets[0].get('snippetText', {})
                        runs = snippet_text.get('runs', [])
                        if runs:
                            # Join all text parts from the 'runs' list
                            description = "".join([part.get('text', '') for part in runs])

                    # --- APPLY FILTERS ---
                    title_and_desc = (video_title + ' ' + description).lower()

                    print('Parsing', title_and_desc, link)
                    if date_str_for_filtering not in title_and_desc.replace('.', ''):
                        print('\tSkip date', date_str_for_filtering, title_and_desc)
                        continue

                    names = ['fromis', 'formis', 'fromsi' '프로미스나인', '프미나', '프나', '프로미스', 'idol school', '아이돌 학교'
                             'saerom', 'hayoung', 'gyuri', 'jisun', 'jiwon', 'seoyeon', 'chaeyoung', 'nagyung', 'jiheon',
                             "새롬", "하영", "규리", "지선", "지원", "서연", "채영", "나경", "지헌"]

                    skip = True
                    for n in names:
                        if n in title_and_desc:
                            skip = False
                            break

                    if skip:
                        print('\tSkip missing terms', title_and_desc)
                        continue

                    if video_id in seen:
                        print('\tSkip dupe', video_id, video_title)
                        continue

                    ignored_ids = ['zPs2XsTDwnk']
                    if video_id in ignored_ids:
                        continue

                    ignored_authors = ['ThePingiiz', 'parrotsubs', 'papago_9']
                    if author_name.lower() in ignored_authors:
                        continue

                    if length_sec < 20:
                        continue

                    banned_terms = ['치어리더', 'cheerleader', '4x4crew', '버스킹', 'busking', 'dance cover']
                    if any(b.lower() in title_and_desc.lower() for b in banned_terms):
                        print(f'\tSkipping yt video banned terms', f'https://www.youtube.com/watch?v={video_id}, {video_title}')
                        continue
                    # for b in banned_terms:
                    #     if b.lower() in title_and_desc.lower():
                    #         print(f'Skipping yt video {b}', f'https://www.youtube.com/watch?v={video_id}, {video_title}')
                    #         continue

                    seen.add(video_id)

                    print('\tAdded!')

                    filtered_videos.append({
                        'id': video_id,
                        'title': video_title,
                        'author': author_name,
                        'views': view_count_text,
                        'length': length_sec,
                        'resolution': resolution,
                        'description': description,  # Add the new field
                    })

    except (KeyError, IndexError, TypeError) as e:
        print(f"  [Warning] Could not parse a section of the JSON data: {e}")

    return filtered_videos


def main():
    """
    Main function to read all JSON files, process and filter them, and save
    the aggregated results into a single new JSON file.
    """
    if not INPUT_FOLDER.is_dir():
        print(f"Error: Input directory '{INPUT_FOLDER}' not found.")
        return

    OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

    json_files = sorted(INPUT_FOLDER.glob('*.json'))
    if not json_files:
        print(f"No .json files found in the '{INPUT_FOLDER}' directory.")
        return

    all_filtered_videos = defaultdict(list)
    seen = set()

    print("Starting processing and filtering of JSON files...")
    for file_path in json_files:
        # print('Parsing', file_path)
        date_str = file_path.name.removesuffix("".join(file_path.suffixes))
        # print(date_str)
        # print(
        #     f" -> Processing {file_path.name} (filtering for title containing '{date_str}' and length >= {MINIMUM_VIDEO_LENGTH_SECONDS}s)")

        # if date_str != '181014':
        #     continue

        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                json_data = json.load(f)
                video_list = extract_and_filter_videos(json_data, date_str, seen)
                all_filtered_videos[date_str] += video_list
            except json.JSONDecodeError:
                print(f"  [Error] Could not decode JSON from file: {file_path.name}")

    output_path = OUTPUT_FOLDER / OUTPUT_FILENAME
    print(f"\nProcessing complete. Writing {len(all_filtered_videos)} filtered data to '{output_path}'...")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_filtered_videos, f, indent=4, ensure_ascii=False)

    print("Successfully saved filtered data.")


if __name__ == "__main__":
    main()