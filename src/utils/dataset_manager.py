"""
Dataset Management and Annotation Tools
نظام إدارة قاعدة بيانات التدريب وأدوات التعليق
"""
import os
import json
import cv2
import shutil
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import pandas as pd


@dataclass
class ElementAnnotation:
    """تعليق على عنصر واحد"""
    element_id: str
    element_type: str  # jump, spin, step_sequence, etc.
    isu_code: str  # e.g., "3A", "CCoSp4", "StSq3"

    # Timing
    start_frame: int
    end_frame: int
    start_time: float
    end_time: float

    # ISU scoring (ground truth from judges)
    base_value: float
    goe: int  # -5 to +5
    goe_value: float
    total_score: float

    # Detailed info
    rotations: Optional[float] = None  # for jumps
    level: Optional[int] = None  # for spins/steps (1-4)

    # Quality notes
    errors: List[str] = None
    bullet_points: List[str] = None  # GOE bullet points

    # Annotator info
    annotated_by: str = ""
    annotation_date: str = ""
    verified: bool = False

    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.bullet_points is None:
            self.bullet_points = []


@dataclass
class VideoAnnotation:
    """تعليقات فيديو كامل"""
    video_id: str
    video_path: str
    skater_name: str
    competition: str
    program_type: str  # short, free
    season: str

    # Video info
    fps: float
    total_frames: int
    duration: float
    resolution: tuple  # (width, height)

    # Elements
    elements: List[ElementAnnotation]

    # Overall scores (ground truth)
    technical_score: float
    components_score: float
    total_score: float

    # Metadata
    created_date: str
    last_modified: str
    status: str  # draft, in_progress, completed, verified

    def to_dict(self) -> Dict:
        data = asdict(self)
        data['elements'] = [asdict(e) for e in self.elements]
        return data

    @classmethod
    def from_dict(cls, data: Dict) -> 'VideoAnnotation':
        elements = [ElementAnnotation(**e) for e in data.pop('elements', [])]
        return cls(**data, elements=elements)


class DatasetManager:
    """
    Dataset Manager
    إدارة قاعدة بيانات التدريب
    """

    def __init__(self, dataset_root: str = "data/skating_dataset"):
        self.dataset_root = Path(dataset_root)
        self.dataset_root.mkdir(parents=True, exist_ok=True)

        # Directory structure
        self.videos_dir = self.dataset_root / "videos"
        self.annotations_dir = self.dataset_root / "annotations"
        self.features_dir = self.dataset_root / "features"
        self.splits_dir = self.dataset_root / "splits"

        # Create directories
        for dir_path in [self.videos_dir, self.annotations_dir,
                         self.features_dir, self.splits_dir]:
            dir_path.mkdir(exist_ok=True)

        # Load index
        self.index_file = self.dataset_root / "index.json"
        self.index = self._load_index()

    def _load_index(self) -> Dict:
        """Load dataset index"""
        if self.index_file.exists():
            with open(self.index_file, 'r') as f:
                return json.load(f)
        return {
            'videos': {},
            'statistics': {
                'total_videos': 0,
                'total_elements': 0,
                'elements_by_type': {},
                'last_updated': datetime.now().isoformat()
            }
        }

    def _save_index(self):
        """Save dataset index"""
        self.index['statistics']['last_updated'] = datetime.now().isoformat()

        with open(self.index_file, 'w') as f:
            json.dump(self.index, f, indent=2)

    def add_video(
        self,
        video_path: str,
        video_id: Optional[str] = None,
        copy_video: bool = True
    ) -> str:
        """
        Add new video to dataset

        Args:
            video_path: path to video file
            video_id: unique ID (auto-generated if None)
            copy_video: copy video to dataset folder

        Returns:
            video_id
        """
        if video_id is None:
            video_id = self._generate_video_id()

        # Copy or link video
        if copy_video:
            dest_path = self.videos_dir / f"{video_id}.mp4"
            shutil.copy2(video_path, dest_path)
            stored_path = dest_path
        else:
            stored_path = Path(video_path)

        # Get video info
        cap = cv2.VideoCapture(str(stored_path))
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = total_frames / fps if fps > 0 else 0
        cap.release()

        # Create annotation
        annotation = VideoAnnotation(
            video_id=video_id,
            video_path=str(stored_path),
            skater_name="",
            competition="",
            program_type="",
            season="",
            fps=fps,
            total_frames=total_frames,
            duration=duration,
            resolution=(width, height),
            elements=[],
            technical_score=0.0,
            components_score=0.0,
            total_score=0.0,
            created_date=datetime.now().isoformat(),
            last_modified=datetime.now().isoformat(),
            status="draft"
        )

        # Save annotation
        self._save_annotation(video_id, annotation)

        # Update index
        self.index['videos'][video_id] = {
            'path': str(stored_path),
            'added_date': datetime.now().isoformat(),
            'status': 'draft'
        }
        self.index['statistics']['total_videos'] += 1
        self._save_index()

        print(f"✅ Added video: {video_id}")
        return video_id

    def _generate_video_id(self) -> str:
        """Generate unique video ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"video_{timestamp}"

    def get_annotation(self, video_id: str) -> Optional[VideoAnnotation]:
        """Load annotation for video"""
        annotation_file = self.annotations_dir / f"{video_id}.json"

        if not annotation_file.exists():
            return None

        with open(annotation_file, 'r') as f:
            data = json.load(f)

        return VideoAnnotation.from_dict(data)

    def _save_annotation(self, video_id: str, annotation: VideoAnnotation):
        """Save annotation"""
        annotation.last_modified = datetime.now().isoformat()

        annotation_file = self.annotations_dir / f"{video_id}.json"

        with open(annotation_file, 'w') as f:
            json.dump(annotation.to_dict(), f, indent=2)

    def add_element_annotation(
        self,
        video_id: str,
        element: ElementAnnotation
    ):
        """Add element annotation to video"""
        annotation = self.get_annotation(video_id)

        if annotation is None:
            raise ValueError(f"Video {video_id} not found")

        # Add element
        annotation.elements.append(element)

        # Update statistics
        self._update_element_statistics(element.element_type)

        # Save
        self._save_annotation(video_id, annotation)
        self._save_index()

        print(f"✅ Added element: {element.isu_code} to {video_id}")

    def _update_element_statistics(self, element_type: str):
        """Update element type statistics"""
        stats = self.index['statistics']
        stats['total_elements'] = stats.get('total_elements', 0) + 1

        if 'elements_by_type' not in stats:
            stats['elements_by_type'] = {}

        stats['elements_by_type'][element_type] = \
            stats['elements_by_type'].get(element_type, 0) + 1

    def create_train_test_split(
        self,
        test_ratio: float = 0.2,
        random_seed: int = 42
    ):
        """
        Create train/test split

        Args:
            test_ratio: ratio of test set (0-1)
            random_seed: random seed for reproducibility
        """
        import numpy as np

        video_ids = list(self.index['videos'].keys())

        # Shuffle
        np.random.seed(random_seed)
        np.random.shuffle(video_ids)

        # Split
        split_idx = int(len(video_ids) * (1 - test_ratio))
        train_ids = video_ids[:split_idx]
        test_ids = video_ids[split_idx:]

        # Save splits
        splits = {
            'train': train_ids,
            'test': test_ids,
            'test_ratio': test_ratio,
            'random_seed': random_seed,
            'created_date': datetime.now().isoformat()
        }

        split_file = self.splits_dir / "train_test_split.json"
        with open(split_file, 'w') as f:
            json.dump(splits, f, indent=2)

        print(f"✅ Created split:")
        print(f"   Train: {len(train_ids)} videos")
        print(f"   Test: {len(test_ids)} videos")

    def get_split(self, split_name: str = "train") -> List[str]:
        """Get video IDs for split"""
        split_file = self.splits_dir / "train_test_split.json"

        if not split_file.exists():
            raise ValueError("Split not created yet. Run create_train_test_split()")

        with open(split_file, 'r') as f:
            splits = json.load(f)

        return splits.get(split_name, [])

    def export_to_dataframe(self) -> pd.DataFrame:
        """Export all annotations to pandas DataFrame"""
        rows = []

        for video_id in self.index['videos'].keys():
            annotation = self.get_annotation(video_id)

            if annotation is None:
                continue

            for element in annotation.elements:
                row = {
                    'video_id': video_id,
                    'skater': annotation.skater_name,
                    'competition': annotation.competition,
                    'program_type': annotation.program_type,
                    'element_type': element.element_type,
                    'isu_code': element.isu_code,
                    'start_frame': element.start_frame,
                    'end_frame': element.end_frame,
                    'base_value': element.base_value,
                    'goe': element.goe,
                    'total_score': element.total_score,
                    'rotations': element.rotations,
                    'level': element.level,
                    'verified': element.verified
                }
                rows.append(row)

        df = pd.DataFrame(rows)
        return df

    def get_statistics(self) -> Dict:
        """Get dataset statistics"""
        stats = {
            'total_videos': self.index['statistics']['total_videos'],
            'total_elements': self.index['statistics']['total_elements'],
            'elements_by_type': self.index['statistics']['elements_by_type'],
            'videos_by_status': {}
        }

        # Count videos by status
        for video_info in self.index['videos'].values():
            status = video_info.get('status', 'unknown')
            stats['videos_by_status'][status] = \
                stats['videos_by_status'].get(status, 0) + 1

        return stats

    def print_statistics(self):
        """Print dataset statistics"""
        stats = self.get_statistics()

        print("\n📊 Dataset Statistics:")
        print(f"   Total videos: {stats['total_videos']}")
        print(f"   Total elements: {stats['total_elements']}")

        print("\n   Elements by type:")
        for elem_type, count in stats['elements_by_type'].items():
            print(f"      {elem_type}: {count}")

        print("\n   Videos by status:")
        for status, count in stats['videos_by_status'].items():
            print(f"      {status}: {count}")


class AnnotationTool:
    """
    Interactive Annotation Tool
    أداة تعليق تفاعلية للفيديوهات
    """

    def __init__(self, dataset_manager: DatasetManager):
        self.dataset = dataset_manager
        self.current_video_id = None
        self.current_annotation = None
        self.current_frame = 0
        self.cap = None

    def load_video(self, video_id: str):
        """Load video for annotation"""
        self.current_video_id = video_id
        self.current_annotation = self.dataset.get_annotation(video_id)

        if self.current_annotation is None:
            raise ValueError(f"Video {video_id} not found")

        # Open video
        if self.cap:
            self.cap.release()

        self.cap = cv2.VideoCapture(self.current_annotation.video_path)
        self.current_frame = 0

        print(f"✅ Loaded video: {video_id}")
        print(f"   Duration: {self.current_annotation.duration:.1f}s")
        print(f"   Elements: {len(self.current_annotation.elements)}")

    def annotate_element(
        self,
        element_type: str,
        isu_code: str,
        start_frame: int,
        end_frame: int,
        base_value: float,
        goe: int,
        annotator_name: str = "Manual"
    ):
        """
        Annotate an element

        Args:
            element_type: jump, spin, step_sequence, etc.
            isu_code: ISU code (e.g., "3A")
            start_frame: start frame
            end_frame: end frame
            base_value: ISU base value
            goe: GOE (-5 to +5)
            annotator_name: name of annotator
        """
        if self.current_annotation is None:
            raise ValueError("No video loaded")

        # Calculate times
        fps = self.current_annotation.fps
        start_time = start_frame / fps
        end_time = end_frame / fps

        # Calculate GOE value (simplified - real calc uses base value)
        goe_value = goe * (base_value * 0.1)  # approximation
        total_score = base_value + goe_value

        # Create annotation
        element = ElementAnnotation(
            element_id=f"{self.current_video_id}_{len(self.current_annotation.elements)}",
            element_type=element_type,
            isu_code=isu_code,
            start_frame=start_frame,
            end_frame=end_frame,
            start_time=start_time,
            end_time=end_time,
            base_value=base_value,
            goe=goe,
            goe_value=goe_value,
            total_score=total_score,
            annotated_by=annotator_name,
            annotation_date=datetime.now().isoformat(),
            verified=False
        )

        # Add to dataset
        self.dataset.add_element_annotation(self.current_video_id, element)

        # Reload annotation
        self.current_annotation = self.dataset.get_annotation(self.current_video_id)

        print(f"✅ Annotated: {isu_code} ({start_frame}-{end_frame})")

    def show_frame(self, frame_number: Optional[int] = None):
        """Show specific frame"""
        if self.cap is None:
            raise ValueError("No video loaded")

        if frame_number is not None:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            self.current_frame = frame_number

        ret, frame = self.cap.read()

        if ret:
            # Draw elements
            annotated_frame = self._draw_elements(frame)

            cv2.imshow("Annotation Tool", annotated_frame)
            cv2.waitKey(0)

    def _draw_elements(self, frame: np.ndarray) -> np.ndarray:
        """Draw element annotations on frame"""
        annotated = frame.copy()

        if self.current_annotation is None:
            return annotated

        # Draw each element
        for element in self.current_annotation.elements:
            if element.start_frame <= self.current_frame <= element.end_frame:
                # Draw bounding box
                color = (0, 255, 0) if element.verified else (0, 165, 255)
                cv2.rectangle(
                    annotated,
                    (50, 50),
                    (300, 150),
                    color,
                    3
                )

                # Draw text
                text = f"{element.isu_code} (GOE: {element.goe:+d})"
                cv2.putText(
                    annotated,
                    text,
                    (60, 90),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1.0,
                    color,
                    2
                )

        # Draw frame info
        cv2.putText(
            annotated,
            f"Frame: {self.current_frame}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2
        )

        return annotated

    def close(self):
        """Close video"""
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()


def demo_dataset_manager():
    """Demo of dataset manager"""
    # Create dataset manager
    dm = DatasetManager("data/skating_dataset")

    # Add a video (example)
    # video_id = dm.add_video("path/to/video.mp4")

    # Create annotation
    # annotation_tool = AnnotationTool(dm)
    # annotation_tool.load_video(video_id)

    # Annotate element
    # annotation_tool.annotate_element(
    #     element_type="jump",
    #     isu_code="3A",
    #     start_frame=100,
    #     end_frame=150,
    #     base_value=8.0,
    #     goe=2,
    #     annotator_name="Coach Ahmed"
    # )

    # Create split
    # dm.create_train_test_split(test_ratio=0.2)

    # Print stats
    dm.print_statistics()

    # Export to DataFrame
    # df = dm.export_to_dataframe()
    # print(df.head())


if __name__ == "__main__":
    demo_dataset_manager()
