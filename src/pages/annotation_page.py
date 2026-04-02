"""
Quick Video Annotation Interface
واجهة التعليق السريع على الفيديوهات

For labeling videos with categories and elements
"""

import streamlit as st
import sys
import os
from pathlib import Path
import json
import cv2
import numpy as np
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    from src.utils.video_scanner import VideoScanner, VideoFile
except ImportError:
    VideoScanner = None
    VideoFile = None


# Element categories for figure skating
CATEGORIES = {
    'jumps': {
        'name': 'القفزات',
        'subcategories': [
            'Axel', 'Lutz', 'Flip', 'Loop', 'Salchow', 'Toe Loop',
            'Single', 'Double', 'Triple', 'Quad', 'Other'
        ]
    },
    'spins': {
        'name': 'الدورانات',
        'subcategories': [
            'Upright Spin', 'Sit Spin', 'Camel Spin', 'Layback Spin',
            'Combination Spin', 'Flying Spin', 'Other'
        ]
    },
    'sequences': {
        'name': 'المتتاليات',
        'subcategories': [
            'Step Sequence', 'Spiral Sequence', 'Choreographic Sequence',
            'Footwork', 'Other'
        ]
    },
    'full_program': {
        'name': 'برنامج كامل',
        'subcategories': [
            'Short Program', 'Free Skate', 'Exhibition', 'Practice'
        ]
    },
    'tutorial': {
        'name': 'شرح تعليمي',
        'subcategories': [
            'Technique', 'Tips', 'Training', 'Analysis'
        ]
    },
    'other': {
        'name': 'أخرى',
        'subcategories': ['Mixed', 'Unknown', 'Not Skating']
    }
}

SKILL_LEVELS = ['Beginner', 'Intermediate', 'Advanced', 'Elite', 'Unknown']


def show_annotation_page():
    """Main annotation interface"""

    if VideoScanner is None:
        st.error("❌ Video Scanner not available")
        return

    st.title("🏷️ Quick Video Annotation - تعليق الفيديوهات")

    # Initialize scanner in session state
    if 'scanner' not in st.session_state:
        st.session_state.scanner = VideoScanner()
        st.session_state.current_video_idx = 0
        st.session_state.filter_mode = 'all'

    scanner = st.session_state.scanner

    # Sidebar - Scanner Controls
    with st.sidebar:
        st.subheader("🔍 Video Scanner")

        scan_dir = st.text_input(
            "📁 Scan Directory",
            value=str(Path.home() / 'Videos'),
            help=f"Enter a valid directory path. Current system: {os.name}. Example: {Path.home() / 'Videos'}"
        )

        col1, col2 = st.columns(2)
        with col1:
            recursive = st.checkbox("Recursive", value=True)
        with col2:
            max_depth = st.number_input("Max Depth", 1, 10, 3)

        if st.button("🔍 Scan Now", type="primary", use_container_width=True):
            # Validate directory exists
            scan_path = Path(scan_dir)
            if not scan_path.exists():
                st.error(f"""
                ❌ **Directory not found:**

                `{scan_dir}`

                **Possible issues:**
                - The path doesn't exist on this system
                - This looks like a Windows path (e.g., `C:\\`, `D:\\`) but you're on Linux/Mac
                - You don't have permission to access this directory

                **Suggested paths:**
                - Your Videos folder: `{Path.home() / 'Videos'}`
                - Your home folder: `{Path.home()}`
                - Downloads: `{Path.home() / 'Downloads'}`
                - Current directory: `{Path.cwd()}`
                """)
            else:
                with st.spinner("Scanning..."):
                    scanner.scanned_videos = []  # Clear previous
                    scanner.scan_directory(scan_dir, recursive=recursive, max_depth=max_depth)
                    st.session_state.current_video_idx = 0
                    if len(scanner.scanned_videos) > 0:
                        st.success(f"✅ Found {len(scanner.scanned_videos)} videos")
                    else:
                        st.warning(f"⚠️ No videos found in {scan_dir}")
                    st.rerun()

        st.markdown("---")

        # Load/Save buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Save", use_container_width=True):
                scanner.save_scan_results()
                st.success("✅ Saved!")

        with col2:
            if st.button("📂 Load", use_container_width=True):
                scanner.load_scan_results()
                st.success("✅ Loaded!")
                st.rerun()

        st.markdown("---")

        # Statistics
        if scanner.scanned_videos:
            st.subheader("📊 Statistics")
            stats = scanner.get_statistics()

            st.metric("Total Videos", stats.get('total_videos', 0))
            st.metric("Annotated", stats.get('annotated', 0))
            st.metric("Total Size (GB)", stats.get('total_size_gb', 0))
            st.metric("Total Hours", stats.get('total_duration_hours', 0))

            # Category breakdown
            if stats.get('categories'):
                st.markdown("**Categories:**")
                for cat, count in stats['categories'].items():
                    st.text(f"{cat}: {count}")

        st.markdown("---")

        # Filter controls
        st.subheader("🔎 Filter")
        filter_mode = st.selectbox(
            "Show",
            ['all', 'unannotated', 'annotated', 'by_category'],
            format_func=lambda x: {
                'all': 'All Videos',
                'unannotated': 'Not Annotated',
                'annotated': 'Annotated',
                'by_category': 'By Category'
            }[x]
        )

        if filter_mode == 'by_category':
            filter_category = st.selectbox(
                "Category",
                list(CATEGORIES.keys())
            )
        else:
            filter_category = None

        st.session_state.filter_mode = filter_mode

    # Main content
    if not scanner.scanned_videos:
        st.info("""
        ### 👋 Welcome to Video Annotation!

        **Steps:**
        1. 🔍 Enter directory path in sidebar
        2. 📁 Click "Scan Now"
        3. 🏷️ Start labeling videos

        **Purpose:**
        - Label videos for ML training
        - Organize your video collection
        - Build structured datasets
        """)
        return

    # Apply filters
    if filter_mode == 'all':
        filtered_videos = scanner.scanned_videos
    elif filter_mode == 'unannotated':
        filtered_videos = [v for v in scanner.scanned_videos if not v.annotated]
    elif filter_mode == 'annotated':
        filtered_videos = [v for v in scanner.scanned_videos if v.annotated]
    elif filter_mode == 'by_category':
        filtered_videos = [v for v in scanner.scanned_videos if v.category == filter_category]
    else:
        filtered_videos = scanner.scanned_videos

    if not filtered_videos:
        st.warning(f"No videos found with filter: {filter_mode}")
        return

    # Video navigation
    total_videos = len(filtered_videos)
    current_idx = st.session_state.current_video_idx

    # Ensure index is valid
    if current_idx >= total_videos:
        current_idx = 0
        st.session_state.current_video_idx = 0

    current_video = filtered_videos[current_idx]

    # Progress bar
    progress = (current_idx + 1) / total_videos
    st.progress(progress)

    # Navigation controls
    col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])

    with col1:
        if st.button("⬅️ Previous", use_container_width=True):
            if current_idx > 0:
                st.session_state.current_video_idx -= 1
                st.rerun()

    with col2:
        if st.button("➡️ Next", use_container_width=True):
            if current_idx < total_videos - 1:
                st.session_state.current_video_idx += 1
                st.rerun()

    with col3:
        st.markdown(f"<h3 style='text-align: center;'>Video {current_idx + 1} / {total_videos}</h3>",
                   unsafe_allow_html=True)

    with col4:
        if st.button("⏭️ Skip 10", use_container_width=True):
            new_idx = min(current_idx + 10, total_videos - 1)
            st.session_state.current_video_idx = new_idx
            st.rerun()

    with col5:
        jump_to = st.number_input("Go to", 1, total_videos, current_idx + 1, label_visibility="collapsed")
        if jump_to != current_idx + 1:
            st.session_state.current_video_idx = jump_to - 1
            st.rerun()

    st.markdown("---")

    # Video player and info
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("📹 Video Player")

        # Show video if exists
        if Path(current_video.filepath).exists():
            st.video(current_video.filepath)
        else:
            st.error(f"❌ File not found: {current_video.filepath}")

        # Video info
        with st.expander("ℹ️ Video Information"):
            st.text(f"Filename: {current_video.filename}")
            st.text(f"Path: {current_video.filepath}")
            st.text(f"Size: {current_video.size_mb:.2f} MB")
            if current_video.duration_seconds:
                minutes = int(current_video.duration_seconds // 60)
                seconds = int(current_video.duration_seconds % 60)
                st.text(f"Duration: {minutes}:{seconds:02d}")
            if current_video.width and current_video.height:
                st.text(f"Resolution: {current_video.width}x{current_video.height}")
            if current_video.fps:
                st.text(f"FPS: {current_video.fps:.2f}")

    with col2:
        st.subheader("🏷️ Annotation")

        # Category selection
        category = st.selectbox(
            "Category",
            options=list(CATEGORIES.keys()),
            index=list(CATEGORIES.keys()).index(current_video.category) if current_video.category else 0,
            format_func=lambda x: f"{CATEGORIES[x]['name']} ({x})"
        )

        # Subcategory selection
        subcategories = CATEGORIES[category]['subcategories']
        subcategory_idx = (
            subcategories.index(current_video.subcategory)
            if current_video.subcategory in subcategories else 0
        )

        subcategory = st.selectbox(
            "Subcategory",
            options=subcategories,
            index=subcategory_idx
        )

        # Skill level
        skill_idx = (
            SKILL_LEVELS.index(current_video.skill_level)
            if current_video.skill_level in SKILL_LEVELS else 4
        )

        skill_level = st.selectbox(
            "Skill Level",
            options=SKILL_LEVELS,
            index=skill_idx
        )

        # Notes
        notes = st.text_area(
            "Notes (optional)",
            value=current_video.notes or "",
            height=100
        )

        # Save annotation button
        st.markdown("---")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("💾 Save & Next", type="primary", use_container_width=True):
                # Update video annotation
                current_video.category = category
                current_video.subcategory = subcategory
                current_video.skill_level = skill_level
                current_video.notes = notes
                current_video.annotated = True

                # Save to file
                scanner.save_scan_results()

                # Move to next video
                if current_idx < total_videos - 1:
                    st.session_state.current_video_idx += 1

                st.success("✅ Saved!")
                st.rerun()

        with col2:
            if st.button("❌ Skip", use_container_width=True):
                if current_idx < total_videos - 1:
                    st.session_state.current_video_idx += 1
                    st.rerun()

    # Keyboard shortcuts hint
    st.markdown("---")
    st.info("""
    **💡 Tips:**
    - Use the video player controls to watch/review the video
    - Select the most appropriate category and subcategory
    - Add notes for special features or quality issues
    - Click "Save & Next" to annotate and move forward
    - Your progress is saved automatically
    """)

    # Bulk actions
    with st.expander("⚙️ Bulk Actions"):
        st.subheader("Apply to Multiple Videos")

        bulk_category = st.selectbox(
            "Bulk Category",
            options=list(CATEGORIES.keys()),
            format_func=lambda x: CATEGORIES[x]['name'],
            key='bulk_cat'
        )

        bulk_subcategory = st.selectbox(
            "Bulk Subcategory",
            options=CATEGORIES[bulk_category]['subcategories'],
            key='bulk_subcat'
        )

        col1, col2 = st.columns(2)

        with col1:
            start_idx = st.number_input("From video", 1, total_videos, 1)
        with col2:
            end_idx = st.number_input("To video", 1, total_videos, min(10, total_videos))

        if st.button("🔄 Apply to Range", type="secondary"):
            count = 0
            for i in range(start_idx - 1, end_idx):
                if i < len(filtered_videos):
                    video = filtered_videos[i]
                    video.category = bulk_category
                    video.subcategory = bulk_subcategory
                    video.annotated = True
                    count += 1

            scanner.save_scan_results()
            st.success(f"✅ Applied to {count} videos!")
            st.rerun()

    # Export options
    with st.expander("📤 Export"):
        st.subheader("Export Annotations")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("📄 Export JSON", use_container_width=True):
                scanner.save_scan_results(f'annotations_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
                st.success("✅ Exported to JSON!")

        with col2:
            if st.button("📊 Export CSV", use_container_width=True):
                scanner.export_to_csv(f'annotations_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
                st.success("✅ Exported to CSV!")

        # Organize button
        st.markdown("---")
        organize_dir = st.text_input(
            "Organize to directory",
            value="data/organized_videos"
        )

        copy_files = st.checkbox("Copy files (instead of move)", value=True)

        if st.button("📁 Organize Videos", type="primary", use_container_width=True):
            with st.spinner("Organizing videos..."):
                stats = scanner.organize_videos(
                    destination_dir=organize_dir,
                    copy_files=copy_files,
                    by_category=True
                )

                st.success(f"""
                ✅ Organization complete!
                - Total: {stats['total']}
                - Organized: {stats['organized']}
                - Skipped: {stats['skipped']}
                - Failed: {stats['failed']}
                """)


if __name__ == "__main__":
    show_annotation_page()
