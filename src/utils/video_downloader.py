"""
Professional Video Downloader
نظام تحميل الفيديوهات الاحترافي

Supports 1000+ websites including:
- YouTube, Vimeo, Dailymotion
- Facebook, Instagram, Twitter, TikTok
- Sports sites, news sites, and more

Features:
- Single video download
- Playlist download
- Quality selection
- Progress tracking
- Metadata extraction
"""

import os
import json
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import subprocess
import re

try:
    import yt_dlp
    YT_DLP_AVAILABLE = True
except ImportError:
    YT_DLP_AVAILABLE = False
    print("⚠️ yt-dlp not installed. Install with: pip install yt-dlp")


@dataclass
class VideoInfo:
    """Video information"""
    id: str
    title: str
    url: str
    duration: int  # seconds
    thumbnail: str
    uploader: str
    upload_date: str
    view_count: Optional[int] = None
    like_count: Optional[int] = None
    description: Optional[str] = None
    format_id: Optional[str] = None
    ext: str = 'mp4'
    filesize: Optional[int] = None

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class DownloadResult:
    """Download result"""
    success: bool
    video_id: str
    title: str
    filepath: Optional[str] = None
    error: Optional[str] = None
    duration: Optional[float] = None  # download time in seconds

    def to_dict(self) -> Dict:
        return asdict(self)


class VideoDownloader:
    """
    Professional Video Downloader using yt-dlp
    يدعم أكثر من 1000 موقع وتحميل Playlists
    """

    # Supported websites (most popular)
    SUPPORTED_SITES = [
        'youtube.com', 'youtu.be',
        'vimeo.com',
        'dailymotion.com',
        'facebook.com', 'fb.watch',
        'instagram.com',
        'twitter.com', 'x.com',
        'tiktok.com',
        'twitch.tv',
        'reddit.com',
        'streamable.com',
        'soundcloud.com',
        'mixcloud.com',
        # Sports
        'espn.com',
        'nhl.com',
        'nba.com',
        # News
        'cnn.com',
        'bbc.co.uk',
        # And 1000+ more via yt-dlp
    ]

    def __init__(
        self,
        output_dir: str = 'data/videos',
        quality: str = 'best',
        format: str = 'mp4',
        organize_by_source: bool = True
    ):
        """
        Initialize downloader

        Args:
            output_dir: Directory to save videos
            quality: Video quality ('best', 'worst', '720p', '1080p', etc.)
            format: Video format (mp4, webm, mkv, etc.)
            organize_by_source: Organize downloads by source website
        """
        if not YT_DLP_AVAILABLE:
            raise ImportError(
                "yt-dlp is required. Install with:\n"
                "  pip install yt-dlp"
            )

        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.quality = quality
        self.format = format
        self.organize_by_source = organize_by_source

        # Download statistics
        self.stats = {
            'total_downloads': 0,
            'successful': 0,
            'failed': 0,
            'total_size_mb': 0,
        }

    def get_video_info(self, url: str) -> Optional[VideoInfo]:
        """
        Get video information without downloading

        Args:
            url: Video URL

        Returns:
            VideoInfo object or None if failed
        """
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

                if info is None:
                    return None

                return VideoInfo(
                    id=info.get('id', 'unknown'),
                    title=info.get('title', 'Unknown'),
                    url=url,
                    duration=info.get('duration', 0),
                    thumbnail=info.get('thumbnail', ''),
                    uploader=info.get('uploader', 'Unknown'),
                    upload_date=info.get('upload_date', ''),
                    view_count=info.get('view_count'),
                    like_count=info.get('like_count'),
                    description=info.get('description'),
                    ext=info.get('ext', 'mp4'),
                    filesize=info.get('filesize'),
                )
        except Exception as e:
            print(f"Error getting video info: {e}")
            return None

    def get_playlist_info(self, url: str) -> Optional[Dict]:
        """
        Get playlist information

        Args:
            url: Playlist URL

        Returns:
            Dict with playlist info and video list
        """
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,  # Don't download, just get info
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

                if info is None:
                    return None

                if 'entries' not in info:
                    # Not a playlist, single video
                    return {
                        'is_playlist': False,
                        'title': info.get('title', 'Unknown'),
                        'video_count': 1,
                    }

                videos = []
                for entry in info['entries']:
                    if entry:
                        videos.append({
                            'id': entry.get('id', 'unknown'),
                            'title': entry.get('title', 'Unknown'),
                            'url': entry.get('url', ''),
                            'duration': entry.get('duration', 0),
                        })

                return {
                    'is_playlist': True,
                    'title': info.get('title', 'Unknown Playlist'),
                    'video_count': len(videos),
                    'uploader': info.get('uploader', 'Unknown'),
                    'videos': videos,
                }
        except Exception as e:
            print(f"Error getting playlist info: {e}")
            return None

    def download_video(
        self,
        url: str,
        output_filename: Optional[str] = None,
        progress_callback: Optional[Callable] = None
    ) -> DownloadResult:
        """
        Download single video

        Args:
            url: Video URL
            output_filename: Custom filename (without extension)
            progress_callback: Function to call with progress updates

        Returns:
            DownloadResult object
        """
        start_time = datetime.now()

        # Determine output directory
        if self.organize_by_source:
            # Extract domain from URL
            domain = self._extract_domain(url)
            output_path = self.output_dir / domain
        else:
            output_path = self.output_dir

        output_path.mkdir(parents=True, exist_ok=True)

        # Setup output template
        if output_filename:
            output_template = str(output_path / f"{output_filename}.%(ext)s")
        else:
            output_template = str(output_path / "%(title)s.%(ext)s")

        # Progress hook
        def progress_hook(d):
            if progress_callback and d['status'] == 'downloading':
                percent = d.get('_percent_str', '0%').strip()
                speed = d.get('_speed_str', 'N/A').strip()
                eta = d.get('_eta_str', 'N/A').strip()
                progress_callback({
                    'percent': percent,
                    'speed': speed,
                    'eta': eta,
                    'downloaded': d.get('downloaded_bytes', 0),
                    'total': d.get('total_bytes', 0),
                })

        # yt-dlp options
        ydl_opts = {
            'format': self._get_format_string(),
            'outtmpl': output_template,
            'progress_hooks': [progress_hook] if progress_callback else [],
            'quiet': False,
            'no_warnings': False,
            'extract_flat': False,
            'writethumbnail': True,  # Download thumbnail
            'writeinfojson': True,   # Save metadata
            'merge_output_format': self.format,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)

                if info is None:
                    return DownloadResult(
                        success=False,
                        video_id='unknown',
                        title='Unknown',
                        error='Failed to extract video info'
                    )

                # Get downloaded filepath
                if output_filename:
                    filepath = str(output_path / f"{output_filename}.{self.format}")
                else:
                    filepath = str(output_path / f"{info['title']}.{self.format}")

                # Update stats
                self.stats['total_downloads'] += 1
                self.stats['successful'] += 1
                if info.get('filesize'):
                    self.stats['total_size_mb'] += info['filesize'] / (1024 * 1024)

                duration = (datetime.now() - start_time).total_seconds()

                return DownloadResult(
                    success=True,
                    video_id=info.get('id', 'unknown'),
                    title=info.get('title', 'Unknown'),
                    filepath=filepath,
                    duration=duration
                )

        except Exception as e:
            self.stats['total_downloads'] += 1
            self.stats['failed'] += 1

            return DownloadResult(
                success=False,
                video_id='unknown',
                title='Unknown',
                error=str(e)
            )

    def download_playlist(
        self,
        url: str,
        max_videos: Optional[int] = None,
        progress_callback: Optional[Callable] = None
    ) -> List[DownloadResult]:
        """
        Download entire playlist

        Args:
            url: Playlist URL
            max_videos: Maximum number of videos to download (None = all)
            progress_callback: Function to call with progress updates

        Returns:
            List of DownloadResult objects
        """
        results = []

        # Get playlist info first
        playlist_info = self.get_playlist_info(url)
        if not playlist_info or not playlist_info['is_playlist']:
            # Single video, not playlist
            result = self.download_video(url, progress_callback=progress_callback)
            return [result]

        videos = playlist_info['videos']
        if max_videos:
            videos = videos[:max_videos]

        total = len(videos)

        for idx, video in enumerate(videos, 1):
            print(f"\nDownloading {idx}/{total}: {video['title']}")

            # Custom progress callback for playlist
            def playlist_progress(progress):
                if progress_callback:
                    progress['playlist_progress'] = f"{idx}/{total}"
                    progress_callback(progress)

            result = self.download_video(
                video['url'],
                progress_callback=playlist_progress
            )
            results.append(result)

            if not result.success:
                print(f"Failed to download: {video['title']}")

        return results

    def download_batch(
        self,
        urls: List[str],
        progress_callback: Optional[Callable] = None
    ) -> List[DownloadResult]:
        """
        Download multiple videos from different URLs

        Args:
            urls: List of video URLs
            progress_callback: Function to call with progress updates

        Returns:
            List of DownloadResult objects
        """
        results = []
        total = len(urls)

        for idx, url in enumerate(urls, 1):
            print(f"\nDownloading {idx}/{total}")

            def batch_progress(progress):
                if progress_callback:
                    progress['batch_progress'] = f"{idx}/{total}"
                    progress_callback(progress)

            result = self.download_video(url, progress_callback=batch_progress)
            results.append(result)

        return results

    def search_and_download(
        self,
        query: str,
        source: str = 'youtube',
        max_results: int = 10
    ) -> List[DownloadResult]:
        """
        Search for videos and download them

        Args:
            query: Search query
            source: Source website (youtube, vimeo, etc.)
            max_results: Maximum number of results to download

        Returns:
            List of DownloadResult objects
        """
        search_url = f"ytsearch{max_results}:{query}"

        results = []
        ydl_opts = {
            'quiet': True,
            'extract_flat': True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(search_url, download=False)

                if info and 'entries' in info:
                    for entry in info['entries']:
                        if entry:
                            video_url = f"https://www.youtube.com/watch?v={entry['id']}"
                            result = self.download_video(video_url)
                            results.append(result)
        except Exception as e:
            print(f"Search failed: {e}")

        return results

    def _get_format_string(self) -> str:
        """Get yt-dlp format string based on quality setting"""
        if self.quality == 'best':
            return 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
        elif self.quality == 'worst':
            return 'worst[ext=mp4]/worst'
        elif self.quality.endswith('p'):
            # Specific resolution (e.g., '720p', '1080p')
            height = self.quality[:-1]
            return f'bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]/best[height<={height}][ext=mp4]/best'
        else:
            return 'best[ext=mp4]/best'

    def _extract_domain(self, url: str) -> str:
        """Extract domain name from URL"""
        # Simple regex to extract domain
        match = re.search(r'(?:https?://)?(?:www\.)?([^/]+)', url)
        if match:
            domain = match.group(1)
            # Remove common TLDs for cleaner folder names
            domain = domain.split('.')[0]
            return domain
        return 'unknown'

    def get_stats(self) -> Dict:
        """Get download statistics"""
        return self.stats.copy()

    def supported_sites(self) -> List[str]:
        """Get list of some supported sites"""
        return self.SUPPORTED_SITES.copy()

    def check_url(self, url: str) -> bool:
        """
        Check if URL is supported

        Args:
            url: URL to check

        Returns:
            True if supported, False otherwise
        """
        try:
            ydl_opts = {'quiet': True, 'no_warnings': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.extract_info(url, download=False)
                return True
        except:
            return False


def test_downloader():
    """Test the downloader"""
    downloader = VideoDownloader(
        output_dir='data/test_videos',
        quality='720p',
        organize_by_source=True
    )

    # Test URL
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

    print("Getting video info...")
    info = downloader.get_video_info(test_url)
    if info:
        print(f"Title: {info.title}")
        print(f"Duration: {info.duration}s")
        print(f"Uploader: {info.uploader}")

    print("\nDownloading...")
    result = downloader.download_video(test_url)

    if result.success:
        print(f"✅ Downloaded: {result.title}")
        print(f"📁 Saved to: {result.filepath}")
    else:
        print(f"❌ Failed: {result.error}")

    print("\nStats:")
    print(downloader.get_stats())


if __name__ == "__main__":
    test_downloader()
