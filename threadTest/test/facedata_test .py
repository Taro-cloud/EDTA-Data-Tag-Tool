  #!/usr/bin/env python
# coding: utf-8
#

## https://qiita.com/montblanc18/items/0188ff680acf028d4b63

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import mglearn
from IPython.display import display
import sklearn as sk
##
from sklearn.datasets import fetch_lfw_people

people =fetch_lfw_people(min_faces_per_person=20,resize=0.7)
image_shape=people.images[0].shape

fix,axes =plt.subplots(2,5,figsize=(15,8),subplot_kw={"xticks":(),"yticks":()})

for target, image, ax in zip(people.target, people.images, axes.ravel() ):
    ax.imshow(image)
    print(people.target_names[target])
    print(image)
    ax.set_title(people.target_names[target])
  
plt.show()
mask=np.zeros(people.target.shape,dtype=np.bool)
for target in np.unique(people.target):
    mask[np.where(people.target==target)[0][:50] ]=True

#print(mask)

X_people=people.data[mask]
y_people=people.target[mask]

X_people= X_people/255.

print(X_people.shape) #Xは[[]]

X_train,X_test,y_train,y_test=sk.model_selection.train_test_split(X_people,y_people,stratify=y_people,random_state=0)
print(X_train.shape)
print(X_test.shape)
print(X_train[0])
print(len(X_train[0]))
print(image_shape)
plt.imshow(X_train[0].reshape(image_shape)) #1人分画像
plt.show()

