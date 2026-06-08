"""
Audio Processing & Music Merger for Skating Programs
معالج الصوت ودامج الموسيقى لبرامج التزلج

Features:
- Cut and trim audio files
- Merge multiple songs
- Fade in/out effects
- Beat detection and sync
- Volume normalization
- Export for competition (ISU compliant)
"""

import os
from pathlib import Path
from typing import List, Optional, Tuple, Dict
from dataclasses import dataclass
import json

try:
    import numpy as np
except ImportError:
    np = None

try:
    from pydub import AudioSegment
    from pydub.effects import normalize, compress_dynamic_range
    from pydub.playback import play
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    AudioSegment = None

try:
    import librosa
    import numpy as np
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False


@dataclass
class AudioClip:
    """قطعة صوتية"""
    filepath: str
    start_time: float  # seconds - start in original file
    end_time: float    # seconds - end in original file
    duration: float    # seconds - duration of clip
    fade_in: float = 0.0   # seconds
    fade_out: float = 0.0  # seconds
    volume_db: float = 0.0  # volume adjustment in dB
    name: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            'filepath': self.filepath,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration': self.duration,
            'fade_in': self.fade_in,
            'fade_out': self.fade_out,
            'volume_db': self.volume_db,
            'name': self.name
        }


@dataclass
class ProgramMusic:
    """موسيقى البرنامج الكاملة"""
    program_type: str  # 'short' or 'free'
    target_duration: float  # seconds (ISU limits)
    clips: List[AudioClip]

    # ISU Time Limits
    SHORT_PROGRAM_LIMITS = {
        'senior_men': 170,     # 2:50
        'senior_ladies': 170,  # 2:50
        'junior': 150,         # 2:30
    }

    FREE_SKATE_LIMITS = {
        'senior_men': 270,     # 4:30
        'senior_ladies': 240,  # 4:00
        'junior': 210,         # 3:30
    }

    def to_dict(self) -> Dict:
        return {
            'program_type': self.program_type,
            'target_duration': self.target_duration,
            'clips': [clip.to_dict() for clip in self.clips]
        }


class AudioProcessor:
    """
    معالج الصوت الشامل
    Complete audio processor for skating programs
    """

    # Supported formats
    AUDIO_FORMATS = {'.mp3', '.wav', '.flac', '.m4a', '.ogg', '.wma'}

    def __init__(self, output_dir: str = 'data/audio_output'):
        """Initialize audio processor"""
        if not PYDUB_AVAILABLE:
            raise ImportError(
                "pydub is required for audio processing. "
                "Install with: pip install pydub"
            )

        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.sample_rate = 44100  # Standard audio sample rate

    def load_audio(self, filepath: str) -> AudioSegment:
        """
        Load audio file

        Args:
            filepath: Path to audio file

        Returns:
            AudioSegment object
        """
        filepath = Path(filepath)

        if not filepath.exists():
            raise FileNotFoundError(f"Audio file not found: {filepath}")

        if filepath.suffix.lower() not in self.AUDIO_FORMATS:
            raise ValueError(f"Unsupported audio format: {filepath.suffix}")

        # Load audio
        audio = AudioSegment.from_file(str(filepath))

        return audio

    def cut_audio(
        self,
        filepath: str,
        start_time: float,
        end_time: float
    ) -> AudioSegment:
        """
        Cut/trim audio file

        Args:
            filepath: Path to audio file
            start_time: Start time in seconds
            end_time: End time in seconds

        Returns:
            Trimmed AudioSegment
        """
        audio = self.load_audio(filepath)

        # Convert seconds to milliseconds
        start_ms = int(start_time * 1000)
        end_ms = int(end_time * 1000)

        # Cut
        trimmed = audio[start_ms:end_ms]

        return trimmed

    def apply_fade(
        self,
        audio: AudioSegment,
        fade_in: float = 0.0,
        fade_out: float = 0.0
    ) -> AudioSegment:
        """
        Apply fade in/out effects

        Args:
            audio: AudioSegment
            fade_in: Fade in duration in seconds
            fade_out: Fade out duration in seconds

        Returns:
            Audio with fades applied
        """
        result = audio

        if fade_in > 0:
            fade_in_ms = int(fade_in * 1000)
            result = result.fade_in(fade_in_ms)

        if fade_out > 0:
            fade_out_ms = int(fade_out * 1000)
            result = result.fade_out(fade_out_ms)

        return result

    def adjust_volume(
        self,
        audio: AudioSegment,
        volume_db: float
    ) -> AudioSegment:
        """
        Adjust volume

        Args:
            audio: AudioSegment
            volume_db: Volume change in dB (positive = louder, negative = quieter)

        Returns:
            Audio with adjusted volume
        """
        return audio + volume_db

    def normalize_audio(self, audio: AudioSegment) -> AudioSegment:
        """
        Normalize audio levels

        Args:
            audio: AudioSegment

        Returns:
            Normalized audio
        """
        return normalize(audio)

    def merge_clips(
        self,
        clips: List[AudioClip],
        crossfade: float = 0.0
    ) -> AudioSegment:
        """
        Merge multiple audio clips

        Args:
            clips: List of AudioClip objects
            crossfade: Crossfade duration between clips in seconds

        Returns:
            Merged AudioSegment
        """
        if not clips:
            raise ValueError("No clips to merge")

        # Process first clip
        first_clip = clips[0]
        audio = self.cut_audio(
            first_clip.filepath,
            first_clip.start_time,
            first_clip.end_time
        )
        audio = self.apply_fade(audio, first_clip.fade_in, first_clip.fade_out)
        audio = self.adjust_volume(audio, first_clip.volume_db)

        # Merge remaining clips
        for clip in clips[1:]:
            next_audio = self.cut_audio(
                clip.filepath,
                clip.start_time,
                clip.end_time
            )
            next_audio = self.apply_fade(next_audio, clip.fade_in, clip.fade_out)
            next_audio = self.adjust_volume(next_audio, clip.volume_db)

            # Append with crossfade
            if crossfade > 0:
                crossfade_ms = int(crossfade * 1000)
                audio = audio.append(next_audio, crossfade=crossfade_ms)
            else:
                audio = audio + next_audio

        return audio

    def create_program_music(
        self,
        program: ProgramMusic,
        output_filename: str,
        normalize: bool = True
    ) -> str:
        """
        Create complete program music from clips

        Args:
            program: ProgramMusic object
            output_filename: Output filename
            normalize: Normalize audio levels

        Returns:
            Path to output file
        """
        # Merge clips
        merged = self.merge_clips(program.clips)

        # Normalize if requested
        if normalize:
            merged = self.normalize_audio(merged)

        # Check duration against ISU limits
        duration_sec = len(merged) / 1000.0

        if duration_sec > program.target_duration + 10:
            print(f"⚠️ Warning: Program duration ({duration_sec:.1f}s) exceeds target ({program.target_duration}s)")

        # Export
        output_path = self.output_dir / output_filename
        merged.export(
            str(output_path),
            format='mp3',
            bitrate='320k',
            tags={
                'title': f'Skating Program - {program.program_type.title()}',
                'comment': f'Duration: {duration_sec:.1f}s'
            }
        )

        print(f"✅ Created program music: {output_path}")
        print(f"   Duration: {duration_sec:.1f}s / {program.target_duration}s")

        return str(output_path)

    def detect_beats(self, filepath: str):
        """
        Detect beats in audio file (requires librosa)

        Args:
            filepath: Path to audio file

        Returns:
            Array of beat times in seconds
        """
        if not LIBROSA_AVAILABLE:
            raise ImportError(
                "librosa is required for beat detection. "
                "Install with: pip install librosa"
            )

        # Load audio with librosa
        y, sr = librosa.load(filepath, sr=self.sample_rate)

        # Detect beats
        tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)

        # Convert frames to times
        beat_times = librosa.frames_to_time(beat_frames, sr=sr)

        print(f"🎵 Detected tempo: {tempo:.1f} BPM")
        print(f"🎵 Found {len(beat_times)} beats")

        return beat_times

    def get_audio_info(self, filepath: str) -> Dict:
        """
        Get audio file information

        Args:
            filepath: Path to audio file

        Returns:
            Dict with audio info
        """
        audio = self.load_audio(filepath)

        duration_sec = len(audio) / 1000.0

        info = {
            'filepath': str(filepath),
            'duration_seconds': duration_sec,
            'duration_formatted': f"{int(duration_sec // 60)}:{int(duration_sec % 60):02d}",
            'channels': audio.channels,
            'sample_width': audio.sample_width,
            'frame_rate': audio.frame_rate,
            'frame_count': audio.frame_count(),
            'rms': audio.rms,  # Volume level
            'max_dBFS': audio.max_dBFS,  # Peak volume
        }

        return info

    def save_program_config(
        self,
        program: ProgramMusic,
        config_file: str = 'program_music_config.json'
    ):
        """
        Save program configuration to JSON

        Args:
            program: ProgramMusic object
            config_file: Output config filename
        """
        config_path = self.output_dir / config_file

        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(program.to_dict(), f, indent=2, ensure_ascii=False)

        print(f"💾 Saved program config: {config_path}")

    def load_program_config(
        self,
        config_file: str = 'program_music_config.json'
    ) -> ProgramMusic:
        """
        Load program configuration from JSON

        Args:
            config_file: Config filename

        Returns:
            ProgramMusic object
        """
        config_path = self.output_dir / config_file

        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(config_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        clips = [AudioClip(**clip_data) for clip_data in data['clips']]

        program = ProgramMusic(
            program_type=data['program_type'],
            target_duration=data['target_duration'],
            clips=clips
        )

        print(f"✅ Loaded program config: {config_path}")

        return program


def create_sample_program():
    """مثال على إنشاء برنامج موسيقي"""

    processor = AudioProcessor()

    # Create clips (example)
    clips = [
        AudioClip(
            filepath='song1.mp3',
            start_time=10.0,
            end_time=70.0,
            duration=60.0,
            fade_in=2.0,
            fade_out=1.0,
            volume_db=0.0,
            name='Opening'
        ),
        AudioClip(
            filepath='song2.mp3',
            start_time=30.0,
            end_time=90.0,
            duration=60.0,
            fade_in=1.0,
            fade_out=2.0,
            volume_db=-2.0,
            name='Middle section'
        ),
        AudioClip(
            filepath='song1.mp3',
            start_time=120.0,
            end_time=170.0,
            duration=50.0,
            fade_in=1.0,
            fade_out=3.0,
            volume_db=1.0,
            name='Finale'
        ),
    ]

    # Create program
    program = ProgramMusic(
        program_type='short',
        target_duration=170,  # 2:50 for senior
        clips=clips
    )

    # Save config
    processor.save_program_config(program)

    # Create merged music
    # output = processor.create_program_music(program, 'my_short_program.mp3')

    return program


if __name__ == "__main__":
    print("🎵 Audio Processor for Figure Skating Programs")
    print("=" * 60)
    print()
    print("Example usage:")
    print()
    print("from src.utils.audio_processor import AudioProcessor, AudioClip, ProgramMusic")
    print()
    print("processor = AudioProcessor()")
    print("info = processor.get_audio_info('my_song.mp3')")
    print("beats = processor.detect_beats('my_song.mp3')")
    print()
