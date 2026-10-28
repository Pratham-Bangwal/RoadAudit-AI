# RoadAudit AI model pipeline

These training and inference scripts came from the RoadAudit AI final handoff. The trained checkpoint used by the main application is `../models/road_damage.pt` (the later 90-epoch run's epoch-15 checkpoint). The earlier CPU MVP checkpoint remains at `model/best.pt` for comparison.

The model predicts four RDD2022 classes: longitudinal crack, transverse crack, alligator crack, and pothole. Its detections feed the main app's separate priority, route, and repair workflows. Severity and Road Health Index values are image-based heuristics, not engineering measurements.

## Run inference

Install the root `requirements.txt`, then run from this directory:

```powershell
python ai\inference.py --image "test_images\test image.webp" --conf 0.05
python ai\video_inference.py --video path\to\road_video.mp4 --conf 0.05
```

Inference outputs go under the ignored `outputs/` directory. Both commands use the checkpoint in `../models/road_damage.pt` by default; pass `--model model\best.pt` to compare with the earlier MVP checkpoint.

## Prepare data and train

The preprocessing scripts in `ai/preprocess/` convert Pascal VOC XML labels to YOLO format, combine country data, and create deterministic train/validation splits. The RDD2022 dataset is not included. Place prepared data at `dataset/processed/` and its configuration at `dataset/processed/dataset.yaml` before training.

```powershell
python ai\train.py --data dataset\processed\dataset.yaml
```

Training starts from the included later checkpoint by default. Use `--model path\to\yolo11n.pt` to start from a base model. Outputs go to the ignored `runs/` directory. See `python ai\train.py --help` for other options.

The handoff reported mAP50 0.23565 and mAP50-95 0.09816 for the later checkpoint. These figures come from the source handoff; they were not independently reproduced during consolidation.
