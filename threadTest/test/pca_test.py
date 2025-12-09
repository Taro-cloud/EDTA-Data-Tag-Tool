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

#fix,axes =plt.subplots(2,5,figsize=(15,8),subplot_kw={"xticks":(),"yticks":()})

#for target, image, ax in zip(people.target, people.images, axes.ravel() ):
#    ax.imshow(image)
#    ax.set_title(people.target_names[target])
  
#plt.show()
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

pca=sk.decomposition.PCA(n_components=100,whiten=True,random_state=0).fit(X_train)
X_train_pca=pca.transform(X_train)
X_test_pca=pca.transform(X_test)

print("x_train_pca_shape{}".format(X_train.shape))

#fix,axes =plt.subplots(3,5,figsize=(15,12),subplot_kw={"xticks":(),"yticks":()})

#for i,(component,ax) in enumerate( zip(pca.components_, axes.ravel() )):
#    ax.imshow( component.reshape(image_shape),cmap="viridis")
#    ax.set_title( "{}.component".format(i+1) ) 
#plt.show()

mglearn.discrete_scatter(X_train_pca[:,0],X_train_pca[:,1],y_train)
plt.xlabel("first")
plt.xlabel("second")
plt.show()
#?? mglearn.plots.plot_pca_whitening()

#print("people.imasgs.shape:{}".format(people.images.shape))
#print("number of classes: {}".format(len(people.target_names)))

#print("aaa")