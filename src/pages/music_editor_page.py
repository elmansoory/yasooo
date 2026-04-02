"""
Music Editor & Merger Page for Skating Programs
صفحة محرر ودامج الموسيقى لبرامج التزلج

Features:
- Upload and manage music files
- Cut and trim songs
- Merge multiple clips
- Add fade effects
- Preview and export
- ISU time limit compliance
"""

import streamlit as st
import sys
from pathlib import Path
from typing import List, Optional
import json

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    from src.utils.audio_processor import (
        AudioProcessor, AudioClip, ProgramMusic,
        PYDUB_AVAILABLE, LIBROSA_AVAILABLE
    )
except ImportError:
    AudioProcessor = None
    PYDUB_AVAILABLE = False


def show_music_editor_page():
    """صفحة محرر الموسيقى الرئيسية"""

    st.title("🎵 محرر ودامج الموسيقى - Music Editor & Merger")

    # Check dependencies
    if not PYDUB_AVAILABLE:
        show_installation_instructions()
        return

    # Initialize session state
    if 'audio_processor' not in st.session_state:
        st.session_state.audio_processor = AudioProcessor()
        st.session_state.clips = []
        st.session_state.program_type = 'short'
        st.session_state.skater_category = 'senior_ladies'

    processor = st.session_state.audio_processor

    # Sidebar - Program Settings
    with st.sidebar:
        st.subheader("⚙️ إعدادات البرنامج")

        program_type = st.selectbox(
            "نوع البرنامج",
            ['short', 'free'],
            format_func=lambda x: {
                'short': '🎯 Short Program (برنامج قصير)',
                'free': '🎭 Free Skate (برنامج حر)'
            }[x]
        )
        st.session_state.program_type = program_type

        if program_type == 'short':
            category_options = {
                'senior_men': 'Senior Men (2:50)',
                'senior_ladies': 'Senior Ladies (2:50)',
                'junior': 'Junior (2:30)'
            }
            limits = ProgramMusic.SHORT_PROGRAM_LIMITS
        else:
            category_options = {
                'senior_men': 'Senior Men (4:30)',
                'senior_ladies': 'Senior Ladies (4:00)',
                'junior': 'Junior (3:30)'
            }
            limits = ProgramMusic.FREE_SKATE_LIMITS

        category = st.selectbox(
            "الفئة",
            list(category_options.keys()),
            format_func=lambda x: category_options[x]
        )
        st.session_state.skater_category = category

        target_duration = limits[category]
        st.info(f"⏱️ ISU Limit: {target_duration // 60}:{target_duration % 60:02d}")

        st.markdown("---")

        # Current program status
        total_duration = sum(clip.duration for clip in st.session_state.clips)
        st.metric(
            "Total Duration",
            f"{int(total_duration // 60)}:{int(total_duration % 60):02d}",
            delta=f"{total_duration - target_duration:+.1f}s"
        )

        if total_duration > target_duration + 10:
            st.error("⚠️ Exceeds ISU limit!")
        elif total_duration < target_duration - 10:
            st.warning(f"⚠️ {target_duration - total_duration:.0f}s short")
        else:
            st.success("✅ Within limits!")

        st.markdown("---")

        # Quick actions
        st.subheader("⚡ Quick Actions")

        if st.button("🗑️ Clear All", use_container_width=True):
            st.session_state.clips = []
            st.rerun()

        if st.button("💾 Save Config", use_container_width=True):
            save_program_config()

        if st.button("📂 Load Config", use_container_width=True):
            load_program_config()

    # Main content
    tabs = st.tabs([
        "📁 Upload & Manage",
        "✂️ Add Clips",
        "🎬 Timeline",
        "🎵 Preview & Export"
    ])

    with tabs[0]:
        show_upload_section(processor)

    with tabs[1]:
        show_add_clip_section(processor)

    with tabs[2]:
        show_timeline_section()

    with tabs[3]:
        show_export_section(processor, target_duration)


def show_upload_section(processor):
    """قسم رفع الملفات"""

    st.subheader("📁 Upload Music Files")

    uploaded_files = st.file_uploader(
        "Upload audio files (MP3, WAV, FLAC, etc.)",
        type=['mp3', 'wav', 'flac', 'm4a', 'ogg'],
        accept_multiple_files=True
    )

    if uploaded_files:
        st.success(f"✅ Uploaded {len(uploaded_files)} file(s)")

        for file in uploaded_files:
            # Save to temp directory
            upload_dir = Path('data/audio_uploads')
            upload_dir.mkdir(parents=True, exist_ok=True)

            filepath = upload_dir / file.name

            with open(filepath, 'wb') as f:
                f.write(file.getbuffer())

            # Get info
            try:
                info = processor.get_audio_info(str(filepath))

                with st.expander(f"🎵 {file.name}"):
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.metric("Duration", info['duration_formatted'])
                    with col2:
                        st.metric("Channels", info['channels'])
                    with col3:
                        st.metric("Sample Rate", f"{info['frame_rate']} Hz")

                    st.audio(str(filepath))

                    # Beat detection (if librosa available)
                    if LIBROSA_AVAILABLE:
                        if st.button(f"🎵 Detect Beats", key=f"beats_{file.name}"):
                            with st.spinner("Detecting beats..."):
                                beats = processor.detect_beats(str(filepath))
                                st.success(f"Found {len(beats)} beats")
                                st.write("First 10 beat times:", beats[:10])

            except Exception as e:
                st.error(f"❌ Error loading {file.name}: {e}")


def show_add_clip_section(processor):
    """قسم إضافة المقاطع"""

    st.subheader("✂️ Create Audio Clip")

    # List available files
    upload_dir = Path('data/audio_uploads')
    if upload_dir.exists():
        audio_files = list(upload_dir.glob('*'))
        audio_files = [f for f in audio_files if f.suffix.lower() in processor.AUDIO_FORMATS]
    else:
        audio_files = []

    if not audio_files:
        st.info("📁 Upload audio files first in the 'Upload & Manage' tab")
        return

    selected_file = st.selectbox(
        "Select audio file",
        audio_files,
        format_func=lambda x: x.name
    )

    # Get file info
    info = processor.get_audio_info(str(selected_file))
    max_duration = info['duration_seconds']

    st.audio(str(selected_file))

    col1, col2 = st.columns(2)

    with col1:
        start_time = st.number_input(
            "Start time (seconds)",
            min_value=0.0,
            max_value=max_duration,
            value=0.0,
            step=0.1
        )

    with col2:
        end_time = st.number_input(
            "End time (seconds)",
            min_value=start_time + 0.1,
            max_value=max_duration,
            value=min(start_time + 30.0, max_duration),
            step=0.1
        )

    clip_duration = end_time - start_time

    st.info(f"⏱️ Clip duration: {clip_duration:.1f} seconds")

    # Effects
    st.markdown("---")
    st.subheader("🎨 Effects")

    col1, col2, col3 = st.columns(3)

    with col1:
        fade_in = st.number_input("Fade In (sec)", 0.0, 10.0, 0.0, 0.5)

    with col2:
        fade_out = st.number_input("Fade Out (sec)", 0.0, 10.0, 0.0, 0.5)

    with col3:
        volume_db = st.slider("Volume (dB)", -10.0, 10.0, 0.0, 0.5)

    clip_name = st.text_input("Clip name (optional)", f"Clip {len(st.session_state.clips) + 1}")

    # Add clip button
    if st.button("➕ Add Clip to Timeline", type="primary", use_container_width=True):
        clip = AudioClip(
            filepath=str(selected_file),
            start_time=start_time,
            end_time=end_time,
            duration=clip_duration,
            fade_in=fade_in,
            fade_out=fade_out,
            volume_db=volume_db,
            name=clip_name
        )

        st.session_state.clips.append(clip)
        st.success(f"✅ Added clip: {clip_name}")
        st.rerun()


def show_timeline_section():
    """قسم الخط الزمني"""

    st.subheader("🎬 Program Timeline")

    clips = st.session_state.clips

    if not clips:
        st.info("📝 No clips added yet. Add clips in the 'Add Clips' tab.")
        return

    # Show clips
    total_time = 0.0

    for i, clip in enumerate(clips):
        with st.expander(f"🎵 {clip.name or f'Clip {i+1}'}", expanded=True):
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Start", f"{total_time:.1f}s")

            with col2:
                st.metric("Duration", f"{clip.duration:.1f}s")

            with col3:
                st.metric("End", f"{total_time + clip.duration:.1f}s")

            with col4:
                st.metric("Volume", f"{clip.volume_db:+.1f} dB")

            # Details
            st.text(f"📁 Source: {Path(clip.filepath).name}")
            st.text(f"✂️ Clip range: {clip.start_time:.1f}s - {clip.end_time:.1f}s")

            if clip.fade_in > 0 or clip.fade_out > 0:
                st.text(f"🎨 Fade In: {clip.fade_in:.1f}s, Fade Out: {clip.fade_out:.1f}s")

            # Actions
            col1, col2, col3 = st.columns(3)

            with col1:
                if i > 0:
                    if st.button("⬆️ Move Up", key=f"up_{i}"):
                        clips[i], clips[i-1] = clips[i-1], clips[i]
                        st.rerun()

            with col2:
                if i < len(clips) - 1:
                    if st.button("⬇️ Move Down", key=f"down_{i}"):
                        clips[i], clips[i+1] = clips[i+1], clips[i]
                        st.rerun()

            with col3:
                if st.button("🗑️ Delete", key=f"del_{i}"):
                    clips.pop(i)
                    st.rerun()

        total_time += clip.duration

    # Timeline visualization
    st.markdown("---")
    st.subheader("📊 Visual Timeline")

    target_duration = ProgramMusic.SHORT_PROGRAM_LIMITS.get(
        st.session_state.skater_category, 170
    ) if st.session_state.program_type == 'short' else ProgramMusic.FREE_SKATE_LIMITS.get(
        st.session_state.skater_category, 240
    )

    # Create visual timeline
    timeline_html = create_timeline_visualization(clips, target_duration)
    st.markdown(timeline_html, unsafe_allow_html=True)


def show_export_section(processor, target_duration):
    """قسم التصدير"""

    st.subheader("🎵 Preview & Export")

    clips = st.session_state.clips

    if not clips:
        st.info("📝 Add clips to timeline first")
        return

    # Merge settings
    st.markdown("### ⚙️ Merge Settings")

    col1, col2 = st.columns(2)

    with col1:
        crossfade = st.number_input(
            "Crossfade between clips (seconds)",
            0.0, 5.0, 0.0, 0.1
        )

    with col2:
        normalize = st.checkbox("Normalize audio levels", value=True)

    # Output filename
    output_filename = st.text_input(
        "Output filename",
        f"{st.session_state.program_type}_program_{st.session_state.skater_category}.mp3"
    )

    # Export button
    if st.button("🎵 Create Program Music", type="primary", use_container_width=True):
        with st.spinner("Merging audio clips..."):
            try:
                # Create program
                program = ProgramMusic(
                    program_type=st.session_state.program_type,
                    target_duration=target_duration,
                    clips=clips
                )

                # Merge
                merged = processor.merge_clips(clips, crossfade=crossfade)

                if normalize:
                    merged = processor.normalize_audio(merged)

                # Export
                output_path = processor.output_dir / output_filename
                merged.export(str(output_path), format='mp3', bitrate='320k')

                duration = len(merged) / 1000.0

                st.success(f"✅ Created: {output_filename}")
                st.info(f"📊 Duration: {int(duration // 60)}:{int(duration % 60):02d}")

                # Play
                st.audio(str(output_path))

                # Download button
                with open(output_path, 'rb') as f:
                    st.download_button(
                        "⬇️ Download Program Music",
                        f,
                        file_name=output_filename,
                        mime='audio/mpeg',
                        use_container_width=True
                    )

            except Exception as e:
                st.error(f"❌ Error creating program: {e}")


def create_timeline_visualization(clips: List[AudioClip], target_duration: float) -> str:
    """Create HTML timeline visualization"""

    total_duration = sum(c.duration for c in clips)
    max_duration = max(total_duration, target_duration)

    html = """
    <div style="background: #f0f0f0; padding: 20px; border-radius: 10px;">
    """

    current_time = 0.0
    colors = ['#667eea', '#764ba2', '#f093fb', '#4facfe', '#43e97b']

    for i, clip in enumerate(clips):
        width_percent = (clip.duration / max_duration) * 100
        left_percent = (current_time / max_duration) * 100
        color = colors[i % len(colors)]

        html += f"""
        <div style="
            position: relative;
            background: {color};
            height: 60px;
            width: {width_percent}%;
            margin-left: {left_percent}%;
            margin-bottom: 10px;
            border-radius: 5px;
            display: inline-block;
            color: white;
            padding: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        ">
            <strong>{clip.name or f'Clip {i+1}'}</strong><br>
            <small>{clip.duration:.1f}s</small>
        </div>
        """

        current_time += clip.duration

    # Target duration marker
    if target_duration > 0:
        target_percent = (target_duration / max_duration) * 100
        html += f"""
        <div style="
            position: absolute;
            left: {target_percent}%;
            height: 80px;
            width: 2px;
            background: red;
            margin-top: -80px;
        "></div>
        <div style="
            position: absolute;
            left: {target_percent}%;
            margin-top: -100px;
            color: red;
            font-weight: bold;
        ">ISU Limit</div>
        """

    html += "</div>"

    return html


def save_program_config():
    """Save program configuration"""
    processor = st.session_state.audio_processor
    program = ProgramMusic(
        program_type=st.session_state.program_type,
        target_duration=ProgramMusic.SHORT_PROGRAM_LIMITS.get(
            st.session_state.skater_category, 170
        ) if st.session_state.program_type == 'short' else ProgramMusic.FREE_SKATE_LIMITS.get(
            st.session_state.skater_category, 240
        ),
        clips=st.session_state.clips
    )

    processor.save_program_config(program)
    st.success("✅ Configuration saved!")


def load_program_config():
    """Load program configuration"""
    try:
        processor = st.session_state.audio_processor
        program = processor.load_program_config()

        st.session_state.program_type = program.program_type
        st.session_state.clips = program.clips

        st.success(f"✅ Loaded configuration with {len(program.clips)} clips")
        st.rerun()

    except Exception as e:
        st.error(f"❌ Error loading configuration: {e}")


def show_installation_instructions():
    """Show installation instructions"""

    st.error("❌ Audio processing dependencies not installed")

    st.markdown("""
    ### 🔧 Installation Required

    To use the Music Editor, install the following dependencies:

    ```bash
    # Required for audio processing
    pip install pydub

    # Required for beat detection (optional)
    pip install librosa

    # FFmpeg (required by pydub)
    # On Ubuntu/Debian:
    sudo apt-get install ffmpeg

    # On Mac:
    brew install ffmpeg

    # On Windows:
    # Download from: https://ffmpeg.org/download.html
    ```

    ### 📦 Or install all at once:

    ```bash
    pip install pydub librosa soundfile
    ```

    After installation, restart the app.
    """)


if __name__ == "__main__":
    show_music_editor_page()
