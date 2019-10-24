# -*- coding: utf-8 -*-
"""Untitled8.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1vyH0caGj7EuF1Lx98Iiq9YhiB1qiJ-5X
"""

!wget https://raw.githubusercontent.com/Waxpple/ML4NASA21SENSOR/master/train_FD001.txt
!wget https://raw.githubusercontent.com/Waxpple/ML4NASA21SENSOR/master/RUL_FD001.txt
!wget https://raw.githubusercontent.com/Waxpple/ML4NASA21SENSOR/master/test_FD001.txt

import pandas as pd
import numpy as np


import os
import keras
import keras.backend as K
from keras.layers.core import Activation
from keras.models import Sequential, load_model
from keras.layers import Dense, Dropout, LSTM
from keras.wrappers.scikit_learn import KerasClassifier

import scipy
from scipy.stats import norm

import boto3

# get rid of deprecated warnings
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

import sklearn
from sklearn import preprocessing
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, precision_score, recall_score, confusion_matrix
from sklearn import linear_model


import matplotlib as mlab
import matplotlib.pyplot as plt
mlab.rcParams['figure.figsize']=(17,10)

# get the training file and call its handler "train"
train = pd.read_csv('train_FD001.txt',sep=" " ,header = None)             
test = pd.read_csv('test_FD001.txt',sep =" ",header = None)


if train.empty:
    raise Exception('No data found!')
if test.empty:
    raise Exception('No test found!')
# remove some columns and add titles
train.drop(train.columns[[26,27]],axis=1,inplace=True)
test.drop(test.columns[[26,27]],axis=1,inplace=True)

operational_columns = ['setting1','setting2','setting3']
observational_columns = ['s1','s2','s3','s4','s5','s6','s7','s8','s9','s10','s11','s12','s13','s14','s15','s16','s17','s18','s19','s20','s21']

train.columns = ['id','cycle'] + operational_columns + observational_columns 
test.columns = ['id','cycle'] + operational_columns + observational_columns 

#test = train
print(train.head())
print(test.head())

#train or test2
#test = train

# draw the histogram with the average cycle of failure "mu" using:
# norm.fit and acipy.stats.norm.pdf
# plt.hist

##### TO BE COMPLETED #####                  
Data1= train.groupby(['id'], sort=False,as_index=False)['cycle'].max()
max_scatter = list(Data1['cycle'])
l_1 = np.linspace(0, 400, 25)
l_2 = np.linspace(0,400,400)

mu,std=scipy.stats.norm.fit(max_scatter)
plt.hist(max_scatter,bins=l_1,normed='true')

pdf = scipy.stats.norm.pdf
plt.plot(pdf(l_2, loc=mu, scale=std))

plt.xlabel('Value')
plt.ylabel('Density')
plt.title('Histogram of Engine Failures: mean failure cycle = %.1f ' %(mu))
plt.grid(True)
plt.show()

# prepare the dataset

LOOKBACK_LENGTH = 10 # number of cycles in the past to analyse on a rolling basis
DAYS_IN_ADVANCE = 30 # number of cycles we consider before the engine fail

# get the "truth" data file to be used as the test dataset and call it "truth"

##### TO BE COMPLETED #####                  
truth = pd.read_csv('RUL_FD001.txt',sep=" " ,header = None) 
truth.drop(truth.columns[[1]],axis=1,inplace=True)

# for a given engine, RUL = cycle at failure - current cycle
# we add this parameter as a column to the left of the training data table
# then we drop the max column that becomes useless
train.head()
rul = pd.DataFrame(train.groupby('id')['cycle'].max()).reset_index()
rul.columns = ['id','max']
train = train.merge(rul, on=['id'], how='left')

train['RUL'] = train['max'] - train['cycle']
train.drop('max', axis=1, inplace=True)

# normalize the data in settings and sensors columns

train['cycle_norm'] = train['cycle']
cols_normalize = train.columns.difference(['id','cycle','RUL'])
min_max_scaler = preprocessing.MinMaxScaler()
norm_train_df = pd.DataFrame(min_max_scaler.fit_transform(train[cols_normalize]),columns=cols_normalize,index=train.index)
join_df = train[train.columns.difference(cols_normalize)].join(norm_train_df)
train = join_df.reindex(columns = train.columns)

print(train.head(40))

# generate column max for test data

rul = pd.DataFrame(test.groupby('id')['cycle'].max()).reset_index()
rul.columns = ['id','max']
truth.columns = ['more']
truth['id'] = truth.index + 1
truth['max'] = rul['max'] + truth['more']
truth.drop('more',axis=1,inplace=True)

print(truth.info())

# generate test['RUL'] for test data using max and cycle

test = test.merge(truth, on=['id'], how='left')

test['RUL'] = test['max'] - test['cycle'] 
                 

test.drop('max', axis=1, inplace=True)

print(test.head(200))
print(truth.head())

# normalize test data with MinMax normalization as above

               
test['cycle_norm'] = test['cycle']
cols_normalize = test.columns.difference(['id','cycle','RUL'])
min_max_scaler = preprocessing.MinMaxScaler()
norm_test_df = pd.DataFrame(min_max_scaler.fit_transform(test[cols_normalize]),columns=cols_normalize,index=test.index)
join_df = test[test.columns.difference(cols_normalize)].join(norm_test_df)
test = join_df.reindex(columns = test.columns)

print(test.head(40))

# we want deux classes: 0 or 1 (no need for maintenance or maintenance needed)
train['Y'] = np.where(train['RUL'] <= DAYS_IN_ADVANCE, 1, 0)
test['Y'] = np.where(test['RUL'] <= DAYS_IN_ADVANCE, 1, 0)

feature_columns = operational_columns + ['cycle_norm'] + observational_columns
train.to_csv(r'train.csv')
test.to_csv(r'test.csv')
# train and test the model
# First method: Logistic regression


#train_Y=ans
train_Y = train['Y']
#train_rolling = train.groupby('id').apply(pd.DataFrame.rolling,LOOKBACK_LENGTH, min_periods=1)
train_rolling = train.groupby('id')
train_rolling = train_rolling.rolling(window=LOOKBACK_LENGTH, min_periods=1).mean()
train_rolling.to_csv(r'train_rolling.csv')
#print(train_rolling['Y'].tail(40))

train_rolling = train_rolling.drop('cycle', axis=1)
#train_rolling['Y'] = train_Y

# Y is the variable to predict according to X
train_rolling.to_csv(r'rolling.csv')
X = train_rolling.drop(['Y','RUL'], axis=1)
Y = train_rolling['Y'].fillna(0)
Y = Y.astype('int')
print(Y)
Y.to_csv(r'fitting.csv')

# create and "fit" or train the model with the training data using linear_model.LogisticRegression
# call the model "lr_model"

from sklearn.linear_model import LinearRegression
from sklearn.feature_selection import f_regression
from sklearn import preprocessing, linear_model

lr_model =  linear_model.LogisticRegression()
lr_model.fit(X, Y)

# print Coef of fitting
print(lr_model.coef_)

# print intercept
print(lr_model.intercept_ )
predicted_classes = lr_model.predict(X)
np.savetxt("predict_train.csv", predicted_classes, delimiter=",")
accuracy = accuracy_score(Y,predicted_classes)
prec = precision_score(Y, predicted_classes)
recall = recall_score(Y, predicted_classes)
cm_1 = confusion_matrix(Y, predicted_classes)
print(cm_1)
print(accuracy,prec,recall)

from google.colab import files
files.download('train.csv')
files.download('test.csv')
files.download('fitting.csv')
files.download('predict_train.csv')

files.download('train_rolling.csv')

# prepare test data for prediction
test_y = test['Y']
#test or train?
all_test = test.groupby('id')
all_test = all_test.rolling(window=LOOKBACK_LENGTH, min_periods=1).mean()
all_test = all_test.drop('cycle', axis=1)
#all_test['Y'] = test_y

# define features to predict

X_test_lr = all_test.drop(['Y','RUL'], axis=1)
Y_test_lr = all_test['Y'].fillna(0)
Y_test_lr = Y_test_lr.astype('int')

# run the model for prediction
predictions = lr_model.predict(X_test_lr)

# return model evaluation metrics using accuracy_score
logistic_acc = accuracy_score(Y_test_lr, predictions)
logistic_prec = precision_score(Y_test_lr, predictions)
logistic_recall = recall_score(Y_test_lr, predictions)
print(accuracy_score(Y_test_lr, predictions),logistic_prec)
#=====acc in test is 92.753%??======

cm = confusion_matrix(Y_test_lr,predictions)
tn, fp, fn, tp = confusion_matrix(Y_test_lr,predictions).ravel()
print(tp,fp,fn,tn)
print('\nConfusion Matrix for LR:\n', cm)
print('\nAccuracy: {}'.format(logistic_acc))
print('\nPrecision: {}'.format(logistic_prec))
print('\nRecall: {}'.format(logistic_recall))

# Applying the model to a new data point

print("\n\nApplying LR to engine #31...\n")
engine_number = 31
new_engine = test[test['id'] == engine_number]
#X_new_engine, Y_new_engine = flip_data(df=new_engine, feature_columns=feature_columns, lookback_length=LOOKBACK_LENGTH )

Y_predicted_new_engine_lr = lr_model.predict(X_test_lr[X_test_lr['id'] == engine_number])

max_cycles = new_engine.shape[0]
cycles = range(LOOKBACK_LENGTH,(max_cycles-1),1)

new_engine_results = pd.DataFrame({'Cycle':cycles, 'LogisticR' : Y_predicted_new_engine_lr[(LOOKBACK_LENGTH+1):]})


print(new_engine_results.tail(30))

# print the predicted failure day

##### TO BE COMPLETED #####                  
result=new_engine_results[new_engine_results['LogisticR']==1].iloc[0]
if(result.empty):
  print('error')
else:
  print('it will failed at ',result['Cycle']+30,'day')

# make the user enter which engine number is to be predicted
input_1 = input('in put a engine-number for prediction')

#
engine_number = int(input_1)
new_engine = test[test['id'] == engine_number]
#X_new_engine, Y_new_engine = flip_data(df=new_engine, feature_columns=feature_columns, lookback_length=LOOKBACK_LENGTH )

Y_predicted_new_engine_lr = lr_model.predict(X_test_lr[X_test_lr['id'] == engine_number])

max_cycles = new_engine.shape[0]
cycles = range(LOOKBACK_LENGTH,(max_cycles-1),1)

new_engine_results = pd.DataFrame({'Cycle':cycles, 'LogisticR' : Y_predicted_new_engine_lr[(LOOKBACK_LENGTH+1):]})


print(new_engine_results.tail(30))

# print the predicted failure day

##### TO BE COMPLETED #####             
try:
  result=new_engine_results[new_engine_results['LogisticR']==1].iloc[0]
  
  print('it will failed at ',result['Cycle']+30,'day')
except:
  print('it will not failed at least within 30days')