from __future__ import print_function, absolute_import

import glob
import pickle
import re
from os import path as osp


class Market1501Dataset(object):
    """
    Market1501
    Reference:
    Zheng et al. Scalable Person Re-identification: A Benchmark. ICCV 2015.
    URL: http://www.liangzheng.org/Project/project_reid.html

    Dataset statistics:
    # identities: 1501 (+1 for background)
    # images: 12936 (train) + 3368 (query) + 15913 (gallery)
    """
    # dataset_dir = '/unsullied/sharefs/wangjian02/isilon-home/datasets/Market1501/data'
    # pose_dataset_dir = '/unsullied/sharefs/zhongyunshan/isilon-home/datasets/Texture/market-pose/'

    pkl_path = 'dataset/market1501split.pkl'

    def __init__(self, dataset_dir, render_tensors_dir):

        self.dataset_dir = dataset_dir
        self.render_tensors_dir = render_tensors_dir

        self.train_dir = osp.join(self.dataset_dir, 'bounding_box_train')
        self.query_dir = osp.join(self.dataset_dir, 'query')
        self.gallery_dir = osp.join(self.dataset_dir, 'bounding_box_test')

        self.pose_train_dir = osp.join(self.render_tensors_dir, 'bounding_box_train')
        self.pose_query_dir = osp.join(self.render_tensors_dir, 'query')
        self.pose_gallery_dir = osp.join(self.render_tensors_dir, 'bounding_box_test')

        self._check_before_run()

        train, num_train_pids, num_train_imgs = self._process_dir(self.train_dir, self.pose_train_dir, relabel=True,
                                                                  pkl_path=self.pkl_path)
        query, num_query_pids, num_query_imgs = self._process_dir(self.query_dir, self.pose_query_dir, relabel=False)
        gallery, num_gallery_pids, num_gallery_imgs = self._process_dir(self.gallery_dir, self.pose_gallery_dir,
                                                                        relabel=False)
        num_total_pids = num_train_pids + num_query_pids
        num_total_imgs = num_train_imgs + num_query_imgs + num_gallery_imgs

        print("=> Market1501 loaded")
        print("Dataset statistics:")
        print("  ------------------------------")
        print("  subset   | # ids | # images")
        print("  ------------------------------")
        print("  train    | {:5d} | {:8d}".format(num_train_pids, num_train_imgs))
        print("  query    | {:5d} | {:8d}".format(num_query_pids, num_query_imgs))
        print("  gallery  | {:5d} | {:8d}".format(num_gallery_pids, num_gallery_imgs))
        print("  ------------------------------")
        print("  total    | {:5d} | {:8d}".format(num_total_pids, num_total_imgs))
        print("  ------------------------------")

        self.train = train
        self.query = query
        self.gallery = gallery

        self.num_train_pids = num_train_pids
        self.num_query_pids = num_query_pids
        self.num_gallery_pids = num_gallery_pids

    def _check_before_run(self):
        """Check if all files are available before going deeper"""
        if not osp.exists(self.dataset_dir):
            raise RuntimeError("'{}' is not available".format(self.dataset_dir))
        if not osp.exists(self.train_dir):
            raise RuntimeError("'{}' is not available".format(self.train_dir))
        if not osp.exists(self.query_dir):
            raise RuntimeError("'{}' is not available".format(self.query_dir))
        if not osp.exists(self.gallery_dir):
            raise RuntimeError("'{}' is not available".format(self.gallery_dir))

    def _process_dir(self, dir_path, pose_dir_path, relabel=False, pkl_path=None):

        if pkl_path is not None:
            with open(pkl_path, 'rb') as f:
                saveForTest = pickle.load(f)
        else:
            saveForTest = []

        img_paths = glob.glob(osp.join(dir_path, '*.jpg'))

        pattern = re.compile(r'([-\d]+)_c(\d)')

        pid_container = set()
        for img_path in img_paths:

            # 对每一个 pattern.search(img_path).groups() 使用map函数
            pid, _ = map(int, pattern.search(img_path).groups())
            if pid == -1 or pid in saveForTest:
                continue  # junk images are just ignored
            pid_container.add(pid)
        pid2label = {pid: label for label, pid in enumerate(pid_container)}

        dataset = []
        for img_path in img_paths:

            img_name = osp.split(img_path)[1]
            pose_path = osp.join(pose_dir_path, img_name + '.npy')

            pid, camid = map(int, pattern.search(img_path).groups())
            if pid == -1 or pid in saveForTest:
                continue  # junk images are just ignored
            assert 0 <= pid <= 1501  # pid == 0 means background
            assert 1 <= camid <= 6
            camid -= 1  # index starts from 0
            if relabel:
                pid = pid2label[pid]
            dataset.append((img_path, pose_path, pid, camid))

        num_pids = len(pid_container)
        num_imgs = len(dataset)
        return dataset, num_pids, num_imgs
