Code
All code is at 
https://colab.research.google.com/drive/1vyH0caGj7EuF1Lx98Iiq9YhiB1qiJ-5X

It is my collar file.
What I have done
I find the file at NASA open data site. And download the data TEST_001 and RUL_001 and Train_001 and I use train to fit the model and find use TEST to predict and TEST max cycle+RUL = real failure cycle.
This is the data description of nasa:
https://gallery.azure.ai/Experiment/Predictive-Maintenance-Step-1-of-3-data-preparation-and-feature-engineering-2

This is from train data: 
Confusion matrix:
[[18186   245]
 [  344  1856]]

accuracy, precision, recall
0.971450729484756 
0.8833888624464541 
0.8436363636363636

And my test result
Confusion Matrix for LR:
 [[12006   948]
 [    1   141]]

Accuracy: 0.9275351252290776

Precision: 0.12947658402203857

Recall: 0.9929577464788732

And predict about engine #100

it will failed at  212 day

Which means after 181 cycle should be maintain.
And the truth value it fail is 218(198+RUL 100row 20 = 218) day.

Which successfully predict the failure before it happened.
