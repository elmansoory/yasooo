"""
Video Scanner & Organizer
ماسح ومنظم الفيديوهات

Scans computer for all video files and helps organize them
يبحث في الكمبيوتر عن جميع الفيديوهات ويساعد في تنظيمها
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, asdict
from datetime import datetime
import hashlib
import subprocess
import shutil

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False


@dataclass
class VideoFile:
    """Video file information"""
    filepath: str
    filename: str
    size_mb: float
    duration_seconds: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None
    fps: Optional[float] = None
    frame_count: Optional[int] = None
    codec: Optional[str] = None
    hash: Optional[str] = None
    created_date: Optional[str] = None
    modified_date: Optional[str] = None

    # Annotation fields
    category: Optional[str] = None  # jumps, spins, sequences, etc.
    subcategory: Optional[str] = None  # axel, lutz, upright, etc.
    skill_level: Optional[str] = None  # beginner, intermediate, advanced
    annotated: bool = False
    notes: Optional[str] = None

    def to_dict(self) -> Dict:
        return asdict(self)


class VideoScanner:
    """
    Scans directories for video files
    يبحث في المجلدات عن ملفات الفيديو
    """

    # Common video extensions
    VIDEO_EXTENSIONS = {
        '.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv',
        '.webm', '.m4v', '.mpg', '.mpeg', '.3gp', '.f4v'
    }

    def __init__(self, output_dir: str = 'data/scanned_videos'):
        """
        Initialize scanner

        Args:
            output_dir: Directory to save scan results
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.scanned_videos: List[VideoFile] = []
        self.scan_log = []
        self.last_error = None  # Store last error for UI display

    def scan_directory(
        self,
        directory: str,
        recursive: bool = True,
        max_depth: Optional[int] = None,
        skip_folders: Optional[Set[str]] = None
    ) -> List[VideoFile]:
        """
        Scan directory for video files

        Args:
            directory: Directory path to scan
            recursive: Scan subdirectories
            max_depth: Maximum depth for recursive scan
            skip_folders: Folder names to skip

        Returns:
            List of VideoFile objects
        """
        if skip_folders is None:
            skip_folders = {
                'node_modules', '.git', '__pycache__', 'venv',
                'AppData', 'Windows', 'System32', 'Program Files'
            }

        directory = Path(directory)
        if not directory.exists():
            error_msg = f"Directory not found: {directory}"
            print(f"❌ {error_msg}")
            self.last_error = error_msg
            return []

        # Clear last error on successful scan start
        self.last_error = None

        print(f"🔍 Scanning: {directory}")
        found_videos = []

        try:
            if recursive:
                for root, dirs, files in os.walk(directory):
                    # Skip certain folders
                    dirs[:] = [d for d in dirs if d not in skip_folders]

                    # Check depth
                    if max_depth is not None:
                        current_depth = len(Path(root).relative_to(directory).parts)
                        if current_depth >= max_depth:
                            dirs.clear()

                    # Check files
                    for file in files:
                        filepath = Path(root) / file
                        if filepath.suffix.lower() in self.VIDEO_EXTENSIONS:
                            video = self._process_video_file(filepath)
                            if video:
                                found_videos.append(video)
                                print(f"✅ Found: {file}")
            else:
                # Non-recursive scan
                for file in directory.iterdir():
                    if file.is_file() and file.suffix.lower() in self.VIDEO_EXTENSIONS:
                        video = self._process_video_file(file)
                        if video:
                            found_videos.append(video)
                            print(f"✅ Found: {file.name}")

        except PermissionError as e:
            print(f"⚠️ Permission denied: {directory}")
        except Exception as e:
            print(f"❌ Error scanning {directory}: {e}")

        self.scanned_videos.extend(found_videos)
        print(f"\n📊 Total found: {len(found_videos)} videos")

        return found_videos

    def _process_video_file(self, filepath: Path) -> Optional[VideoFile]:
        """
        Extract information from video file

        Args:
            filepath: Path to video file

        Returns:
            VideoFile object or None if failed
        """
        try:
            # Basic file info
            stats = filepath.stat()
            size_mb = stats.st_size / (1024 * 1024)

            video = VideoFile(
                filepath=str(filepath.absolute()),
                filename=filepath.name,
                size_mb=round(size_mb, 2),
                created_date=datetime.fromtimestamp(stats.st_ctime).isoformat(),
                modified_date=datetime.fromtimestamp(stats.st_mtime).isoformat()
            )

            # Extract video metadata using OpenCV
            if CV2_AVAILABLE:
                try:
                    cap = cv2.VideoCapture(str(filepath))

                    if cap.isOpened():
                        video.width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                        video.height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                        video.fps = cap.get(cv2.CAP_PROP_FPS)
                        video.frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

                        if video.fps and video.fps > 0:
                            video.duration_seconds = video.frame_count / video.fps

                        # Get codec
                        fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))
                        video.codec = "".join([chr((fourcc >> 8 * i) & 0xFF) for i in range(4)])

                    cap.release()
                except Exception as e:
                    print(f"⚠️ Could not read video metadata: {filepath.name}")

            # Calculate file hash for duplicate detection
            video.hash = self._calculate_file_hash(filepath)

            return video

        except Exception as e:
            print(f"❌ Error processing {filepath}: {e}")
            return None

    def _calculate_file_hash(self, filepath: Path, chunk_size: int = 8192) -> str:
        """Calculate MD5 hash of file"""
        hasher = hashlib.md5()
        try:
            with open(filepath, 'rb') as f:
                while chunk := f.read(chunk_size):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except:
            return None

    def find_duplicates(self) -> Dict[str, List[VideoFile]]:
        """
        Find duplicate videos based on hash

        Returns:
            Dict mapping hash to list of duplicate videos
        """
        hash_map = {}

        for video in self.scanned_videos:
            if video.hash:
                if video.hash not in hash_map:
                    hash_map[video.hash] = []
                hash_map[video.hash].append(video)

        # Filter to only duplicates
        duplicates = {h: vids for h, vids in hash_map.items() if len(vids) > 1}

        return duplicates

    def filter_by_duration(
        self,
        min_seconds: Optional[float] = None,
        max_seconds: Optional[float] = None
    ) -> List[VideoFile]:
        """
        Filter videos by duration

        Args:
            min_seconds: Minimum duration
            max_seconds: Maximum duration

        Returns:
            Filtered list of videos
        """
        filtered = []

        for video in self.scanned_videos:
            if video.duration_seconds is None:
                continue

            if min_seconds and video.duration_seconds < min_seconds:
                continue

            if max_seconds and video.duration_seconds > max_seconds:
                continue

            filtered.append(video)

        return filtered

    def filter_by_resolution(
        self,
        min_width: Optional[int] = None,
        min_height: Optional[int] = None
    ) -> List[VideoFile]:
        """
        Filter videos by resolution

        Args:
            min_width: Minimum width
            min_height: Minimum height

        Returns:
            Filtered list of videos
        """
        filtered = []

        for video in self.scanned_videos:
            if video.width is None or video.height is None:
                continue

            if min_width and video.width < min_width:
                continue

            if min_height and video.height < min_height:
                continue

            filtered.append(video)

        return filtered

    def organize_videos(
        self,
        destination_dir: str,
        copy_files: bool = True,
        by_category: bool = True
    ) -> Dict[str, int]:
        """
        Organize videos into structured folders

        Args:
            destination_dir: Destination directory
            copy_files: Copy files (True) or move (False)
            by_category: Organize by category/subcategory

        Returns:
            Statistics dict
        """
        destination = Path(destination_dir)
        destination.mkdir(parents=True, exist_ok=True)

        stats = {
            'total': len(self.scanned_videos),
            'organized': 0,
            'skipped': 0,
            'failed': 0
        }

        for video in self.scanned_videos:
            try:
                # Determine target folder
                if by_category and video.category:
                    if video.subcategory:
                        target_folder = destination / video.category / video.subcategory
                    else:
                        target_folder = destination / video.category
                else:
                    target_folder = destination / 'uncategorized'

                target_folder.mkdir(parents=True, exist_ok=True)

                # Target filepath
                target_path = target_folder / video.filename

                # Check if already exists
                if target_path.exists():
                    print(f"⚠️ Already exists: {video.filename}")
                    stats['skipped'] += 1
                    continue

                # Copy or move
                source_path = Path(video.filepath)
                if copy_files:
                    shutil.copy2(source_path, target_path)
                else:
                    shutil.move(source_path, target_path)

                print(f"✅ Organized: {video.filename} → {target_folder.name}")
                stats['organized'] += 1

            except Exception as e:
                print(f"❌ Failed: {video.filename} - {e}")
                stats['failed'] += 1

        return stats

    def save_scan_results(self, filename: str = 'scan_results.json'):
        """
        Save scan results to JSON file

        Args:
            filename: Output filename
        """
        output_path = self.output_dir / filename

        data = {
            'scan_date': datetime.now().isoformat(),
            'total_videos': len(self.scanned_videos),
            'videos': [video.to_dict() for video in self.scanned_videos]
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"💾 Saved results to: {output_path}")

    def load_scan_results(self, filename: str = 'scan_results.json'):
        """
        Load previously saved scan results

        Args:
            filename: Input filename
        """
        input_path = self.output_dir / filename

        if not input_path.exists():
            print(f"❌ File not found: {input_path}")
            return

        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.scanned_videos = [
            VideoFile(**video_data) for video_data in data['videos']
        ]

        print(f"✅ Loaded {len(self.scanned_videos)} videos from: {input_path}")

    def get_statistics(self) -> Dict:
        """Get statistics about scanned videos"""
        if not self.scanned_videos:
            return {}

        total_size_mb = sum(v.size_mb for v in self.scanned_videos)
        total_duration = sum(v.duration_seconds or 0 for v in self.scanned_videos)

        videos_with_duration = [v for v in self.scanned_videos if v.duration_seconds]
        avg_duration = (
            sum(v.duration_seconds for v in videos_with_duration) / len(videos_with_duration)
            if videos_with_duration else 0
        )

        # Category breakdown
        categories = {}
        for video in self.scanned_videos:
            cat = video.category or 'uncategorized'
            categories[cat] = categories.get(cat, 0) + 1

        return {
            'total_videos': len(self.scanned_videos),
            'total_size_gb': round(total_size_mb / 1024, 2),
            'total_duration_hours': round(total_duration / 3600, 2),
            'avg_duration_seconds': round(avg_duration, 2),
            'annotated': sum(1 for v in self.scanned_videos if v.annotated),
            'categories': categories,
        }

    def export_to_csv(self, filename: str = 'videos.csv'):
        """Export video list to CSV"""
        import csv

        output_path = self.output_dir / filename

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            if self.scanned_videos:
                writer = csv.DictWriter(f, fieldnames=self.scanned_videos[0].to_dict().keys())
                writer.writeheader()
                for video in self.scanned_videos:
                    writer.writerow(video.to_dict())

        print(f"💾 Exported to CSV: {output_path}")


def quick_scan(directory: str = None) -> VideoScanner:
    """Quick scan utility function"""
    scanner = VideoScanner()

    if directory is None:
        # Scan common video directories
        common_dirs = [
            str(Path.home() / 'Videos'),
            str(Path.home() / 'Downloads'),
            str(Path.home() / 'Desktop'),
            str(Path.home() / 'Documents'),
        ]

        for dir_path in common_dirs:
            if Path(dir_path).exists():
                print(f"\n📁 Scanning {dir_path}...")
                scanner.scan_directory(dir_path, recursive=True, max_depth=3)
    else:
        scanner.scan_directory(directory, recursive=True)

    # Save results
    scanner.save_scan_results()

    # Show statistics
    stats = scanner.get_statistics()
    print("\n📊 Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")

    return scanner


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        directory = sys.argv[1]
        scanner = quick_scan(directory)
    else:
        print("Usage: python video_scanner.py [directory]")
        print("Or run quick_scan() to scan common video folders")
