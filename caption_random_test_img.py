"""
- Must be called in one of the following ways:
  $ caption_img.py LSTM [img_id] (for using the best LSTM model)
  $ caption_img.py LSTM_attention [img_id] (for using the best LSTM_attention model)
  $ caption_img.py GRU [img_id] (for using te best GRU model)
  $ caption_img.py GRU_attention [img_id] (for using the best GRU_attention model)

- ASSUMES: that preprocess_captions.py and extract_img_features.py has already
  been run. That the weights for the best LSTM/GRU/LSTM_attention/GRU_attention
  model has been placed in models/**model_type**/best_model with names
  model.filetype.

- DOES: generates a caption for the test img with img id img_id if specified,
  otherwise for a random test img. It also displays the img and its caption.
  For attention models, it also displays a figure visualizing the img attention
  at the time of prediciton for each word in the caption.
"""

import cPickle
import random
import numpy as np
import tensorflow as tf
import skimage.io as io
import skimage
import matplotlib.pyplot as plt

# add the "PythonAPI" dir to the path so that "pycocotools" can be found:
import sys
sys.path.append("/home/fregu856/CS224n/project/CS224n_project/coco/PythonAPI")
from pycocotools.coco import COCO

from GRU_model import GRU_Config, GRU_Model
from LSTM_model import LSTM_Config, LSTM_Model
from GRU_attention_model import GRU_attention_Config, GRU_attention_Model
from LSTM_attention_model import LSTM_attention_Config, LSTM_attention_Model
from extract_img_features_attention import extract_img_features_attention

# check that the script was called in a valid way:
if len(sys.argv) < 2:
    raise Exception("Must be called in one of the following ways: \n%s\n%s\n%s\n%s" %\
                ("$ caption_random_test_img.py LSTM [img_id]",
                "$ caption_random_test_img.py LSTM_attention [img_id]",
                "$ caption_random_test_img.py GRU [img_id]",
                "$ caption_random_test_img.py GRU_attention [img_id]"))

model_type = sys.argv[1]
if model_type not in ["LSTM", "GRU", "LSTM_attention", "GRU_attention"]:
    raise Exception("Must be called in one of the following ways: \n%s\n%s\n%s\n%s" %\
                ("$ caption_random_test_img.py LSTM [img_id]",
                "$ caption_random_test_img.py LSTM_attention [img_id]",
                "$ caption_random_test_img.py GRU [img_id]",
                "$ caption_random_test_img.py GRU_attention [img_id]"))

# load all needed data:
test_img_ids = cPickle.load(open("coco/data/test_img_ids"))
test_img_id_2_feature_vector =\
            cPickle.load(open("coco/data/test_img_id_2_feature_vector"))
vocabulary = cPickle.load(open("coco/data/vocabulary"))

if len(sys.argv) >= 3:
    # get the img id if one was specified:
    img_id = int(sys.argv[2])
else:
    # pick a random test img if no img id was specified:
    random.shuffle(test_img_ids)
    img_id = int(test_img_ids[0])

# get the img's file name:
true_captions_file = "coco/annotations/captions_val2014.json"
coco = COCO(true_captions_file)
img = coco.loadImgs(img_id)[0]
img_file_name = img["file_name"]

# get the img's features:
if model_type in ["LSTM", "GRU"]:
    img_features = test_img_id_2_feature_vector[img_id]
elif model_type in ["LSTM_attention", "GRU_attention"]:
    extract_img_features_attention(["coco/images/test/%s" % img_file_name], demo=True)
    img_features = cPickle.load(
                open("coco/data/img_features_attention/%d" % -1))

# initialize the model:
if model_type == "GRU":
    config = GRU_Config()
    dummy_embeddings = np.zeros((config.vocab_size, config.embed_dim),
                dtype=np.float32)
    model = GRU_Model(config, dummy_embeddings, mode="demo")
elif model_type == "LSTM":
    config = LSTM_Config()
    dummy_embeddings = np.zeros((config.vocab_size, config.embed_dim),
                dtype=np.float32)
    model = LSTM_Model(config, dummy_embeddings, mode="demo")
elif model_type == "LSTM_attention":
    config = LSTM_attention_Config()
    dummy_embeddings = np.zeros((config.vocab_size, config.embed_dim),
                dtype=np.float32)
    model = LSTM_attention_Model(config, dummy_embeddings, mode="demo")
elif model_type == "GRU_attention":
    config = GRU_attention_Config()
    dummy_embeddings = np.zeros((config.vocab_size, config.embed_dim),
                dtype=np.float32)
    model = GRU_attention_Model(config, dummy_embeddings, mode="demo")

# create the saver:
saver = tf.train.Saver()

with tf.Session() as sess:
    # restore the best model:
    if model_type == "GRU":
        saver.restore(sess, "models/GRUs/best_model/model")
    elif model_type == "LSTM":
        saver.restore(sess, "models/LSTMs/best_model/model")
    elif model_type == "LSTM_attention":
        saver.restore(sess, "models/LSTMs_attention/best_model/model")
    elif model_type == "GRU_attention":
        saver.restore(sess, "models/GRUs_attention/best_model/model")

    # caption the img (using the best model):
    if model_type in ["LSTM", "GRU"]:
        img_caption = model.generate_img_caption(sess, img_features, vocabulary)
    elif model_type in ["LSTM_attention", "GRU_attention"]:
        img_caption, attention_maps = model.generate_img_caption(sess,
                    img_features, vocabulary)

# display the img and its generated caption:
I = io.imread("coco/images/test/%s" % img_file_name)
plt.imshow(I)
plt.axis('off')
plt.title(img_caption, fontsize=15)
print "img id: %d" % img_id

# for attention models, also display a figure visualizing the img attention for
# each word in the caption:
if model_type in ["LSTM_attention", "GRU_attention"]:
    # get a gray scale version of the img:
    I_gray = skimage.color.rgb2gray(I)
    # get some img paramaters:
    height, width = I_gray.shape
    height_block = int(height/8.)
    width_block = int(width/8.)
    # turn the caption into a vector of the words:
    img_caption_vector = img_caption.split(" ")
    caption_length = len(img_caption_vector)

    plt.figure(2)

    # create a plot with an img for each word in the generated caption,
    # visualizing the img attention when the word was generated:
    if int(caption_length/3.) == caption_length/3.:
        no_of_rows = int(caption_length/3.)
    else:
        no_of_rows = int(caption_length/3.) + 1

    for step, (attention_probs, word) in\
                enumerate(zip(attention_maps, img_caption_vector)):
        plt.subplot(no_of_rows, 3, step+1)
        # flatten the attention_probs from shape [1, 64, 1] to [64, ]:
        attention_probs = attention_probs.flatten()
        # reshape the attention_probs to shape [8,8]:
        attention_probs = np.reshape(attention_probs, (8,8))

        # convert the 8x8 attention probs map to an img of the same size as the img:
        I_att = np.zeros((height, width))
        for i in range(8):
            for j in range(8):
                I_att[i*height_block:(i+1)*height_block, j*width_block:(j+1)*width_block] =\
                            np.ones((height_block, width_block))*attention_probs[i,j]

        # blend the grayscale img and the attention img:
        alpha = 0.97
        I_blend = alpha*I_att+(1-alpha)*I_gray
        # display the blended img:
        plt.imshow(I_blend, cmap="gray")
        plt.axis('off')
        plt.title(word, fontsize=15)

plt.show()
