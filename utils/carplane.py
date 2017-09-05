import os
import xml.etree.ElementTree as ET
import numpy as np
import cv2
import cPickle
import copy
import yolo.config as cfg
from GetFileFromDir import GetFileFromThisRootDir

##TODO(dingjian) all path need changes

class carplane(object):
    def __init__(self, phase, rebuild=False):
        ##self.devkil_path = os.path.join(cfg.CARPLANE_PATH, 'VOCdevkit')
        ##self.data_path = os.path.join(cfg.CARPLANE_PATH)
        print cfg.CARPLANE_PATH
        self.data_path = cfg.CARPLANE_PATH
        ##self.cache_path = cfg.CACHE_PATHf
        self.batch_size = cfg.BATCH_SIZE
        self.image_size = cfg.IMAGE_SIZE
        self.cell_size = cfg.CELL_SIZE
        self.classes = cfg.CARPLANE_CLASSES
        self.class_to_ind = dict(zip(self.classes, xrange(len(self.classes))))
        self.flipped = cfg.FLIPPED
        self.phase = phase  ## phase indicate if 'train' or 'test'
        self.rebuild = rebuild
        self.cursor = 0
        self.epoch = 1
        self.gt_labels = None
        self.prepare()

    def get(self):
        images = np.zeros((self.batch_size, self.image_size, self.image_size, 3))
        #labels = np.zeros((self.batch_size, self.cell_size, self.cell_size, 25))
        labels = np.zeros((self.batch_size, self.cell_size, self.cell_size, 9 + 2))
        imnames = []
        count = 0
        while count < self.batch_size:
            imname = self.gt_labels[self.cursor]['imname']
            imnames.append(imname)
            flipped = self.gt_labels[self.cursor]['flipped']
            images[count, :, :, :] = self.image_read(imname, flipped)
            labels[count, :, :, :] = self.gt_labels[self.cursor]['label']
            count += 1
            self.cursor += 1
            if self.cursor >= len(self.gt_labels):
                np.random.shuffle(self.gt_labels)
                self.cursor = 0
                self.epoch += 1
        return images, labels, imnames

    def image_read(self, imname, flipped=False):
        image = cv2.imread(imname)
        image = cv2.resize(image, (self.image_size, self.image_size))
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB).astype(np.float32)
        image = (image / 255.0) * 2.0 - 1.0
        if flipped:
            image = image[:, ::-1, :]
        return image

    def prepare(self):
        gt_labels = self.load_labels()
        if self.flipped:
            print('Appending horizontally-flipped training examples ...')
            gt_labels_cp = copy.deepcopy(gt_labels)
            for idx in range(len(gt_labels_cp)):
                gt_labels_cp[idx]['flipped'] = True
                gt_labels_cp[idx]['label'] = gt_labels_cp[idx]['label'][:, ::-1, :]
                for i in xrange(self.cell_size):
                    for j in xrange(self.cell_size):
                        if gt_labels_cp[idx]['label'][i, j, 0] == 1:
                            gt_labels_cp[idx]['label'][i, j, 1] = self.image_size - 1 - gt_labels_cp[idx]['label'][i, j, 1]
            gt_labels += gt_labels_cp
        np.random.shuffle(gt_labels)
        self.gt_labels = gt_labels
        return gt_labels

    def load_labels(self):
        ##cache_file = os.path.join(self.cache_path, 'pascal_' + self.phase + '_gt_labels.pkl')

        # if os.path.isfile(cache_file) and not self.rebuild:
        #     print('Loading gt_labels from: ' + cache_file)
        #     with open(cache_file, 'rb') as f:
        #         gt_labels = cPickle.load(f)
        #     return gt_labels

        print('Processing gt_labels from: ' + self.data_path)

        # if not os.path.exists(self.cache_path):
        #     os.makedirs(self.cache_path)

        if self.phase == 'train':
            txtname = os.path.join(self.data_path, 'trainval',
                                 'train.txt')

        else:
            txtname = os.path.join(self.data_path, 'test',
                                   'test.txt')
        with open(txtname, 'r') as f:
            self.image_index = [x.strip() for x in f.readlines()]

        gt_labels = []


        for index in self.image_index:
            label, num = self.load_pascal_annotation(index)
            if num == 0:
                continue
            imname = os.path.join(self.data_path, 'images', index + '.png')
            gt_labels.append({'imname': imname, 'label': label, 'flipped': False})
        # print('Saving gt_labels to: ' + cache_file)
        # with open(cache_file, 'wb') as f:
        #     cPickle.dump(gt_labels, f)
        return gt_labels

    def load_pascal_annotation(self, index):
        """
        Load image and bounding boxes info from XML file in the PASCAL VOC
        format.
        """
        imname = os.path.join(self.data_path, 'images', index + '.png')

        im = cv2.imread(imname)
        h_ratio = 1.0 * self.image_size / im.shape[0]
        w_ratio = 1.0 * self.image_size / im.shape[1]
        # im = cv2.resize(im, [self.image_size, self.image_size])

        label = np.zeros((self.cell_size, self.cell_size, 9 + 2))
        filename = os.path.join(self.data_path, 'labelTxt', index + '.txt')
        #tree = ET.parse(filename)
        #objs = tree.findall('object')

        f = open(filename, 'r')
        lines = f.readlines()
        lines = [x.strip() for x in lines]

        index1 = 0
        for obj in lines:

            #print obj
            split = obj.split('\t')
            ##bbox = obj.find('bndbox')
            # Make pixel indexes 0-based
            ## TODO(dingjian) figure out the max,min
            # x1 = max(min((float(bbox.find('xmin').text) - 1) * w_ratio, self.image_size - 1), 0)
            # y1 = max(min((float(bbox.find('ymin').text) - 1) * h_ratio, self.image_size - 1), 0)
            # x2 = max(min((float(bbox.find('xmax').text) - 1) * w_ratio, self.image_size - 1), 0)
            # y2 = max(min((float(bbox.find('ymax').text) - 1) * h_ratio, self.image_size - 1), 0)
            # if (index1 < 10):
            #     print split
            bbox = [float(x.split('e+')[0]) * pow(10, int(x.split('e+')[1]) ) if (len(x.split('e+')) == 2) else float(x) for x in split]
            # if (index1 < 10):
            #     print bbox
            index1 = index1 + 1
            x1 = max(min((float(bbox[9]) - 1) * w_ratio, self.image_size - 1), 0)
            y1 = max(min((float(bbox[10]) - 1) * h_ratio, self.image_size - 1), 0)
            w = max(min((float(bbox[11]) - 1) * w_ratio, self.image_size - 1), 0)
            h = max(min((float(bbox[12]) - 1) * h_ratio, self.image_size - 1), 0)

            x2 = x1 + w
            y2 = y1 + h

            classname = index.split('_')[1]
            cls_ind = self.class_to_ind[classname]
            #cls_ind = self.class_to_ind[obj.find('name').text.lower().strip()]
            ##boxes = [(x2 + x1) / 2.0, (y2 + y1) / 2.0, x2 - x1, y2 - y1]
            boxes = [(x2 + x1) / 2.0, (y2 + y1) / 2.0, x2 - x1, y2 - y1]
            x_ind = int(boxes[0] * self.cell_size / self.image_size)
            y_ind = int(boxes[1] * self.cell_size / self.image_size)
            if label[y_ind, x_ind, 0] == 1:
                continue
            label[y_ind, x_ind, 0] = 1
            label[y_ind, x_ind, 1:5] = boxes
            label[y_ind, x_ind, 5 + cls_ind] = 1

        return label, len(lines)
