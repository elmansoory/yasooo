"""
Batch Processing System
نظام معالجة جماعية للفيديوهات
"""
import os
from pathlib import Path
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import time

from src.core.advanced_pose_detector import AdvancedPoseDetector
from src.analysis.jump_detector import JumpDetector
from src.analysis.spin_detector import SpinDetector
from src.utils.dataset_manager import DatasetManager


@dataclass
class BatchJob:
    """وظيفة معالجة جماعية"""
    job_id: str
    video_files: List[str]
    output_dir: str
    enable_pose: bool = True
    enable_jumps: bool = True
    enable_spins: bool = True
    save_videos: bool = True
    save_json: bool = True


@dataclass
class ProcessingResult:
    """نتيجة معالجة فيديو واحد"""
    video_path: str
    success: bool
    processing_time: float
    pose_frames_count: int = 0
    jumps_count: int = 0
    spins_count: int = 0
    error_message: Optional[str] = None


class BatchProcessor:
    """
    نظام معالجة جماعية
    """

    def __init__(
        self,
        max_workers: int = 2,
        verbose: bool = True
    ):
        self.max_workers = max_workers
        self.verbose = verbose

    def process_batch(
        self,
        job: BatchJob,
        progress_callback: Optional[Callable] = None
    ) -> List[ProcessingResult]:
        """
        معالجة مجموعة من الفيديوهات

        Args:
            job: وظيفة المعالجة
            progress_callback: دالة callback للتقدم

        Returns:
            قائمة النتائج
        """
        # Create output directory
        output_path = Path(job.output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        results = []

        if self.verbose:
            print(f"🚀 Starting batch processing...")
            print(f"   Videos: {len(job.video_files)}")
            print(f"   Workers: {self.max_workers}")

        # Process with thread pool
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all jobs
            future_to_video = {
                executor.submit(
                    self._process_single_video,
                    video_path,
                    job
                ): video_path
                for video_path in job.video_files
            }

            # Collect results with progress bar
            if self.verbose:
                pbar = tqdm(total=len(job.video_files), desc="Processing videos")

            for future in as_completed(future_to_video):
                result = future.result()
                results.append(result)

                if self.verbose:
                    pbar.update(1)
                    if result.success:
                        pbar.set_postfix({
                            'jumps': result.jumps_count,
                            'spins': result.spins_count
                        })

                if progress_callback:
                    progress_callback(result)

            if self.verbose:
                pbar.close()

        # Save summary
        self._save_batch_summary(job, results)

        if self.verbose:
            self._print_summary(results)

        return results

    def _process_single_video(
        self,
        video_path: str,
        job: BatchJob
    ) -> ProcessingResult:
        """معالجة فيديو واحد"""
        start_time = time.time()

        try:
            # Initialize detectors
            pose_detector = AdvancedPoseDetector(
                model_complexity=2,
                min_detection_confidence=0.7
            )

            # Process video
            pose_frames = []

            if job.enable_pose:
                # Output paths
                video_name = Path(video_path).stem
                output_video = None
                if job.save_videos:
                    output_video = str(Path(job.output_dir) / f"{video_name}_annotated.mp4")

                pose_frames = pose_detector.process_video(
                    video_path,
                    save_visualization=job.save_videos,
                    output_path=output_video
                )

                # Save JSON
                if job.save_json:
                    json_path = Path(job.output_dir) / f"{video_name}_pose.json"
                    pose_detector.export_to_json(pose_frames, str(json_path))

            pose_detector.close()

            # Detect jumps
            jumps = []
            if job.enable_jumps and pose_frames:
                jump_detector = JumpDetector(fps=30)
                jumps = jump_detector.detect_jumps(pose_frames)

                if job.save_json:
                    json_path = Path(job.output_dir) / f"{video_name}_jumps.json"
                    self._save_jumps_json(jumps, json_path)

            # Detect spins
            spins = []
            if job.enable_spins and pose_frames:
                spin_detector = SpinDetector(fps=30)
                spins = spin_detector.detect_spins(pose_frames)

                if job.save_json:
                    json_path = Path(job.output_dir) / f"{video_name}_spins.json"
                    self._save_spins_json(spins, json_path)

            processing_time = time.time() - start_time

            return ProcessingResult(
                video_path=video_path,
                success=True,
                processing_time=processing_time,
                pose_frames_count=len(pose_frames),
                jumps_count=len(jumps),
                spins_count=len(spins)
            )

        except Exception as e:
            processing_time = time.time() - start_time

            return ProcessingResult(
                video_path=video_path,
                success=False,
                processing_time=processing_time,
                error_message=str(e)
            )

    def _save_jumps_json(self, jumps: List, json_path: Path):
        """Save jumps to JSON"""
        data = {
            'total_jumps': len(jumps),
            'jumps': [jump.to_dict() for jump in jumps]
        }

        with open(json_path, 'w') as f:
            json.dump(data, f, indent=2)

    def _save_spins_json(self, spins: List, json_path: Path):
        """Save spins to JSON"""
        data = {
            'total_spins': len(spins),
            'spins': [
                {
                    'isu_code': spin.get_isu_code(),
                    'type': spin.spin_type.value,
                    'level': spin.level,
                    'duration': spin.duration,
                    'total_rotations': spin.total_rotations,
                    'average_rpm': spin.average_rpm,
                    'centering_score': spin.centering_score,
                    'estimated_goe': spin.estimated_goe
                }
                for spin in spins
            ]
        }

        with open(json_path, 'w') as f:
            json.dump(data, f, indent=2)

    def _save_batch_summary(
        self,
        job: BatchJob,
        results: List[ProcessingResult]
    ):
        """Save batch processing summary"""
        summary = {
            'job_id': job.job_id,
            'total_videos': len(job.video_files),
            'successful': sum(1 for r in results if r.success),
            'failed': sum(1 for r in results if not r.success),
            'total_processing_time': sum(r.processing_time for r in results),
            'total_jumps': sum(r.jumps_count for r in results),
            'total_spins': sum(r.spins_count for r in results),
            'results': [
                {
                    'video': r.video_path,
                    'success': r.success,
                    'time': r.processing_time,
                    'jumps': r.jumps_count,
                    'spins': r.spins_count,
                    'error': r.error_message
                }
                for r in results
            ]
        }

        summary_path = Path(job.output_dir) / "batch_summary.json"
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)

        print(f"\n✅ Summary saved to: {summary_path}")

    def _print_summary(self, results: List[ProcessingResult]):
        """Print batch processing summary"""
        successful = [r for r in results if r.success]
        failed = [r for r in results if not r.success]

        total_time = sum(r.processing_time for r in results)
        total_jumps = sum(r.jumps_count for r in successful)
        total_spins = sum(r.spins_count for r in successful)

        print(f"\n{'='*60}")
        print(f"📊 BATCH PROCESSING SUMMARY")
        print(f"{'='*60}")
        print(f"Total videos: {len(results)}")
        print(f"  ✅ Successful: {len(successful)}")
        print(f"  ❌ Failed: {len(failed)}")
        print(f"\nProcessing time:")
        print(f"  Total: {total_time:.1f}s")
        print(f"  Average: {total_time/len(results):.1f}s per video")
        print(f"\nElements detected:")
        print(f"  🦘 Jumps: {total_jumps}")
        print(f"  🌀 Spins: {total_spins}")
        print(f"{'='*60}\n")


def demo_batch_processor():
    """Demo batch processing"""
    # Create batch job
    job = BatchJob(
        job_id="batch_001",
        video_files=[
            "video1.mp4",
            "video2.mp4",
            "video3.mp4"
        ],
        output_dir="output/batch_001",
        enable_pose=True,
        enable_jumps=True,
        enable_spins=True,
        save_videos=True,
        save_json=True
    )

    # Process
    processor = BatchProcessor(max_workers=2)
    results = processor.process_batch(job)

    print(f"✅ Batch processing complete!")


if __name__ == "__main__":
    demo_batch_processor()
