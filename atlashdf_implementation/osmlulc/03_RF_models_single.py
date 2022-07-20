from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix
from sklearn.metrics import accuracy_score
from sklearn.metrics import cohen_kappa_score
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import classification_report
from sklearn.metrics import f1_score
from sklearn.metrics import matthews_corrcoef
from sklearn.metrics import recall_score
from sklearn.metrics import precision_score

from sklearn import svm
import os
import math 
import numpy as np
from hsi_io import *
import os
import time

###########  Hyperparameters #############
num_classes = 12


###########  Data Import #############
Train = r"./data_RF/DE_std_train_samples_RF_5k.npy"
Test = r"./data_RF/DE_valid_RF.npy"
Train = np.load(Train, allow_pickle=True)
Test = np.load(Test, allow_pickle=True)
X_train, y_train, X_test, y_test = train_test_preprocess(Train, Test)
X_train = X_train.astype('float16')
X_test = X_test.astype('float16')
print('Data Pratation is ready.')

#################  RF Model ###########################

classifier = RandomForestClassifier(n_estimators=500, min_samples_split=4)

classifier.fit(X_train, y_train)
print("model is ready!")
# classifying validation data
y_test_pre = classifier.predict(X_test)

#################  SVM Model ###########################

#classifier_svm =  svm.SVC(C=4, kernel = 'rbf',gamma= 0.25) 
#classifier_svm.fit(X_train, y_train)
#print("model is ready!")
## classifying validation data
#y_test_pre = classifier_svm.predict(X_test)

#################  Evaluation ###########################

y_test = [1 if x==5 else 0 for x in y_test]
#y_test_pre = [1 if x==12 else 0 for x in y_test_pre] 
y_test_pre = [1 if x==12 else 0 for x in y_test_pre] 
y_test = y_test[:4600]
y_test_pre = y_test_pre[:4600]

tn, fp, fn, tp = confusion_matrix(y_test, y_test_pre).ravel()
tn = tn
tp = tp
fp = fp
fn = fn
mcc = (tp*tn-fp*fn)/math.sqrt((tp+fp)*(tp+fn)*(tn+fn)*(tn+fp))
overall = (tp+tn)/(tp+tn+fp+fn)
producer_accuracy = tp/(tp+fn)
user_accuracy = tp/(tp+fp)
f1 = 2*tp/(2*tp+fp+fn)


report = classification_report(y_test, y_test_pre)
print(report)
cm = confusion_matrix(y_test, y_test_pre)
#overall = accuracy_score(y_test, y_test_pre)
#f1 = f1_score(y_test, y_test_pre)
#mcc = matthews_corrcoef(y_test, y_test_pre)
#user_accuracy = precision_score(y_test, y_test_pre)
#producer_accuracy = recall_score(y_test, y_test_pre)
print("\noverall:" + str(overall) + "\nf1:" + str(f1) + "\nmcc:" + str(mcc) + "\nuser accuracy:"
      + str(user_accuracy) + "\nproducer accuracy:" + str(producer_accuracy) + "\nconfusion matrix: \n" + str(cm))


assert 0



#print('classification accuracy', accuracy_score(y_test, y_test_pre))
#print('cohen kappa', cohen_kappa_score(y_test, y_test_pre))
#cm = confusion_matrix(y_test, y_test_pre)

#cm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
#classes_indi = cm.diagonal()
#print('classes individual accuracy', classes_indi)
#print('average accuracy', sum(classes_indi) / 12)
