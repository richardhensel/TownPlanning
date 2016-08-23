clear all;
clc;
close all;

%% Load Training Data
%t = cputime;
fprintf('Loading and Visualizing Data')

X = [1,-1,0;
    -1, 0, -1;
    0, -1, 0;
    -1, 0, -1];
    

y = [1; 2; 3; 2];
    
 XTest = [-1, 0, 0; 1, 0, 0 ];

 yTest = [2;1];


%% Initialize parameters
fprintf('Initializing parameters');
m = size(X, 1); % number of examples
lambda = 0.1; % regularization parameter
numLabels = size(unique(y),1); % number of labels
fprintf('...done\n');

%% Training Logistic Regression classifier
fprintf('Training One-vs-All Logistic Regression');

% theta = LRClassifier(XTrain, yTrain, numLabels, lambda);
theta = LRClassifier(X, y, numLabels, lambda)
fprintf('...done\n');

%% Predict numbers 
prediction = predict(theta, XTest)

%% Calculate Accuracy over the training data
fprintf('\nTest Set Accuracy: %f\n', mean(double(prediction == yTest)) * 100);

%fprintf('Program executed in %f seconds or %f minutes\n', cputime-t, (cputime-t)/60);
