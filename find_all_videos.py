"""
Quick Video Finder - Python Script
يبحث عن كل الفيديوهات في الكمبيوتر
"""

import os
from pathlib import Path
import string

print("=" * 60)
print("  🔍 SEARCHING FOR ALL VIDEOS ON YOUR COMPUTER")
print("=" * 60)
print()

VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm', '.m4v'}

def search_drive(drive_letter):
    """Search a specific drive for video files"""
    drive_path = f"{drive_letter}:\\"

    if not os.path.exists(drive_path):
        return None

    print(f"📀 Scanning drive {drive_letter}:...")

    video_folders = {}
    video_count = 0

    try:
        for root, dirs, files in os.walk(drive_path):
            # Skip system folders
            dirs[:] = [d for d in dirs if d not in [
                'Windows', 'Program Files', 'Program Files (x86)',
                'System Volume Information', '$RECYCLE.BIN',
                'ProgramData', 'AppData'
            ]]

            # Count videos in this folder
            videos_here = [f for f in files if Path(f).suffix.lower() in VIDEO_EXTENSIONS]

            if videos_here:
                folder = Path(root)
                video_folders[str(folder)] = len(videos_here)
                video_count += len(videos_here)

                # Print folders with many videos
                if len(videos_here) >= 5:
                    print(f"  ✅ Found {len(videos_here)} videos in: {folder}")

    except PermissionError:
        pass
    except Exception as e:
        print(f"  ⚠️ Error scanning {drive_letter}: {e}")

    return video_folders, video_count

# Search all drives
print("Searching all drives (this may take a few minutes)...")
print()

all_results = {}
total_videos = 0

for letter in string.ascii_uppercase:
    result = search_drive(letter)
    if result:
        folders, count = result
        if count > 0:
            all_results[letter] = folders
            total_videos += count
            print(f"  🎯 Drive {letter}: - {count} videos found")
            print()

print("=" * 60)
print(f"  📊 SUMMARY: Found {total_videos} total videos")
print("=" * 60)
print()

# Show top folders with most videos
print("📁 TOP FOLDERS WITH MOST VIDEOS:")
print("-" * 60)

all_folders = []
for drive, folders in all_results.items():
    for folder, count in folders.items():
        all_folders.append((folder, count))

# Sort by count
all_folders.sort(key=lambda x: x[1], reverse=True)

# Show top 20
for i, (folder, count) in enumerate(all_folders[:20], 1):
    print(f"{i}. [{count} videos] {folder}")

print()
print("=" * 60)
print("  💡 USE ONE OF THESE PATHS IN THE ANNOTATION TOOL")
print("=" * 60)

# Check for "Off Ice" specifically
print()
print("🔍 Searching specifically for 'Off Ice' folder...")
print()

for drive, folders in all_results.items():
    for folder in folders.keys():
        if 'off ice' in folder.lower() or 'off_ice' in folder.lower():
            print(f"  ✅ FOUND: {folder}")
            print(f"     Videos: {folders[folder]}")
            print()

print()
print("=" * 60)
print("DONE! Copy one of the paths above and use it in the app.")
print("=" * 60)

input("\nPress Enter to exit...")
