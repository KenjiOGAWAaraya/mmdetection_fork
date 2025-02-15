# Copyright (c) OpenMMLab. All rights reserved.
import argparse
import pandas as pd
import cv2
import mmcv
from mmcv.transforms import Compose
from mmengine.utils import track_iter_progress
from loguru import logger
from pathlib import Path
import numpy as np

from mmdet.apis import inference_detector, init_detector
from mmdet.registry import VISUALIZERS


def parse_args():
    parser = argparse.ArgumentParser(description='MMDetection video demo')
    parser.add_argument('video', help='Video file')
    parser.add_argument('config', help='Config file')
    parser.add_argument('checkpoint', help='Checkpoint file')
    parser.add_argument(
        '--device', default='cuda:0', help='Device used for inference')
    parser.add_argument(
        '--score-thr', type=float, default=0.3, help='Bbox score threshold')
    parser.add_argument('--out', type=str, help='Output video file')
    parser.add_argument('--show', action='store_true', help='Show video')
    parser.add_argument(
        '--wait-time',
        type=float,
        default=1,
        help='The interval of show (s), 0 is block')
    args = parser.parse_args()
    return args


def main():
    args = parse_args()
    assert args.out or args.show, \
        ('Please specify at least one operation (save/show the '
         'video) with the argument "--out" or "--show"')

    # build the model from a config file and a checkpoint file
    model = init_detector(args.config, args.checkpoint, device=args.device)

    # build test pipeline
    model.cfg.test_dataloader.dataset.pipeline[
        0].type = 'mmdet.LoadImageFromNDArray'
    test_pipeline = Compose(model.cfg.test_dataloader.dataset.pipeline)

    # init visualizer
    visualizer = VISUALIZERS.build(model.cfg.visualizer)
    # the dataset_meta is loaded from the checkpoint and
    # then pass to the model in init_detector
    visualizer.dataset_meta = model.dataset_meta
    videofile = args.video
    video_reader = mmcv.VideoReader(args.video)
    video_writer = None
    if args.out:
        outputfilename = "pred-output/movie/pred-{}.mp4".format(Path(videofile).stem)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        video_writer = cv2.VideoWriter(
            outputfilename, fourcc, video_reader.fps,
            (video_reader.width, video_reader.height))
    datas = []
    max_frame_count = np.infty
    for frame_count, frame in enumerate(video_reader):
        logger.debug("frame_count {:d}".format(frame_count))
        if frame_count > max_frame_count:
            break
        if (frame_count % 3) != 0:
            continue
        logger.debug("inference: start")
        result = inference_detector(model, frame, test_pipeline=test_pipeline)
        result = result.cpu()
        pred_instances = result.pred_instances
        pred_score_thr = 0.3
        pred_instances = pred_instances[pred_instances.scores > pred_score_thr]
        logger.debug("inference: end")
        df = pd.DataFrame({"score": pred_instances.scores,
                           "y0": pred_instances.bboxes[:,0],
                           "y0": pred_instances.bboxes[:,1],
                           "x1": pred_instances.bboxes[:,2],
                           "y1": pred_instances.bboxes[:,3],
                           "category_id": pred_instances.labels,})
        df["frame_count"] = frame_count
        df["filename"] = Path(videofile).stem

        datas.append(df)

        visualizer.add_datasample(
            name='video',
            image=frame,
            data_sample=result,
            draw_gt=False,
            show=False,
            pred_score_thr=args.score_thr)
        frame = visualizer.get_image()

        if args.show:
            cv2.namedWindow('video', 0)
            mmcv.imshow(frame, 'video', args.wait_time)
        if args.out:
            video_writer.write(frame)

    if video_writer:
        video_writer.release()
    cv2.destroyAllWindows()
    df_all = pd.concat(datas)
    csvfilename = "pred-output/csv/pred-{}.csv".format(Path(videofile).stem)
    df_all.to_csv(csvfilename)


if __name__ == '__main__':
    main()
