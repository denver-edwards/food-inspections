# Commented out IPython magic to ensure Python compatibility.
# %%capture
# import sys
# 
# if 'google.colab' in sys.modules:
#     !pip install category_encoders
#     !pip install matplotlib==3.7.1
#     !pip install pdpbox

"""# Predict Chicago Food Inspections 🍕

In this challenge, you'll use data from the [Chicago Department of Public Health](https://www.chicago.gov/city/en/depts/cdph/provdrs/healthy_restaurants/svcs/food-protection-services.html) to build a model to predict whether a food establishment passed inspection or not.

The purpose of this model is to help inspectors use their time more efficiently by identifying establishments that will likely fail inspection. In other words, this model should be able to predict whether an establishment will fail inspection *before* the inspector arrives at the establishment.

# Directions

This notebook contains 12 tasks, which cover the material we've learned in this sprint. Here's a summary:

- **Task 1:** Importing data.
- **Task 2:** Identifying data leakage.
- **Task 3:** Writing a wrangle function.
- **Task 4:** Splitting data into a feature matrix and target vector.
- **Task 5:** Splitting data into training and validation sets.
- **Task 6:** Establishing baseline accuracy.
- **Task 7:** Building model with bagging predictor.
- **Task 8:** Building model with boosting predictor.
- **Task 9 (`stretch goal`):** Plotting ROC curves.
- **Task 10:** Generating classification report.
- **Task 11:** Calculating permutation importances.
- **Task 12 (`stretch goal`):** Creating PDP interaction plot.

For each task you should do the following:

- Read the task instructions.
- Write your code in the cell below the task. Delete the `raise NotImplementedError` before your start.
- Run the testing cell below the task. If you get an error, read the error message and re-evaluate your code.

**You should limit your code to the following libraries:**

- `category_encoders`
- `numpy`
- `matplotlib`
- `pandas`
- `pdpbox`
- `sklearn`
- `xgboost`

**A word of warning:** The virtual machine that will check your answers is small. So, where applicable, don't use huge values for `n_estimators` (`>100`) or `n_jobs` (keep at `-1`).

If you'd like to import all your libraries at the start of your notebook, you can do so in the code block below 👇
"""

# YOUR CODE HERE
import pandas as pd
from sklearn.pipeline import make_pipeline
from sklearn.ensemble import RandomForestClassifier
from category_encoders import OneHotEncoder
from sklearn.impute import SimpleImputer
from xgboost import XGBClassifier as xgb
import matplotlib.pyplot as plt
from pdpbox.pdp import PDPInteract
from pdpbox.info_plots import InteractPredictPlot
from sklearn.metrics import roc_curve

"""# I. Wrangle Data

**Task 1:** Change the code below to import your dataset. Be sure to examine the columns carefully and determine if one of them should be set as the index.
"""

'''T1. Import data file.'''
url = "https://raw.githubusercontent.com/denver-edwards/sprint3/main/chicago-inspections-train.csv"
df = pd.read_csv(url)
# YOUR CODE HERE
df['Inspection Date'] = pd.to_datetime(df['Inspection Date'])
df.set_index('Inspection Date', inplace=True)

df.head(1)

"""**Task 1 Test**"""

'''T1 Test'''
assert isinstance(df, pd.DataFrame), 'Have you created a DataFrame named `df`?'
assert len(df) == 51916

"""**Task 2:** Given that this model is supposed to generate predictions *before* an inspection is conducted, identify the numerical feature that is an example of **data leakage.** Assign the column name to the variable `'leaky_col'`.

**Remember:** Leakage is when your feature matrix includes columns that will not be available to your model at the time it make predictions.


"""

'''T2. Identify data leakage column.'''
leaky_col = ''
# YOUR CODE HERE
leaky_col = 'Serious Violations Found'

"""**Task 2 Test**"""

'''T2 Test'''
# This is a hidden test.
# You'll see the result when you submit to Canvas.
assert isinstance(leaky_col, str), '`leaky_col` should be type `str`.'

"""**Task 3:** Add to the `wrangle` function below so that it does the following:

- Removes the "leaky" column.
- Removes high-cardinality categorical columns (more than `500` categories).
- Removes categorical columns that have only one category.
- Removes numerical columns that are unique identifiers for each observation, not features that would affect the target.
"""

'''T3. Write wrangle function.'''
def wrangle(df):
    # Drop leaky col
    df.drop(columns=leaky_col, inplace=True)

    # Drop high cardinality col
    for col in df.columns:
      if (df[col].nunique() > 500):
        if (col == "Latitude") | (col == "Longitude"):
          continue
        df.drop(columns=col, inplace=True)

    # Drop categorical col w/ 1 category
    df.drop(columns=['State'], inplace=True)
    return df
# YOUR CODE HERE
df = wrangle(df)

df.head(1)

"""**Task 3 Test**"""

'''T3 Test'''
assert df.select_dtypes('object').nunique().max() < 500, 'Have you dropped the high-cardinality columns?'
assert df.select_dtypes('object').nunique().min() > 1, 'Have you dropped the column with only one category?'

"""# II. Split Data

**Task 4:** Split the DataFrame `df` into the feature matrix `X` and the target vector `y`. Your target is `'Fail'`.
"""

'''T4. Split feature matrix and target vector.'''
target = 'Fail'
# YOUR CODE HERE
X = df.drop(columns=target)
y = df[target]

print(X)
print(y)

"""**Task 4 Test**"""

'''T4 Test'''
assert y.shape == (51916,), '`y` either has the wrong number of rows, or is two-dimentional.'
assert len(X) == 51916, '`X` has the wrong number of rows.'

"""**Task 5:** Split your dataset into training and validation sets.

- Your training set (`X_train`, `y_train`) should contain inspections conducted before 2017.
- Your validation set (`X_val`, `y_val`) should contain inspections conducted during or after 2017.
"""

'''T5. Split dataset into training and validation sets.'''
# YOUR CODE HERE
offset = df.index < "2017"

X_train, y_train = X[offset], y[offset]
X_val, y_val = X[~offset], y[~offset]

print(y.unique())
print(y_val.unique())

"""**Task 5 Testing**"""

'''T5 Test'''
assert len(X_train) == len(y_train) == 41827, 'Your training set has the wrong number of observations.'
assert len(X_val) == len(y_val) == 10089, 'Your validation set has the wrong number of observations.'

"""# III. Establish Baseline

**Task 6:** Establish the baseline accuracy score for this classification problem using your training set. Save the score to the variable `baseline_acc`.
"""

'''T6. Establish baseline accuracy.'''
# YOUR CODE HERE
baseline_acc = y_train.value_counts(normalize=True).max()
print('Baseline accuracy:', baseline_acc)

"""**Task 6 Testing**"""

'''T6 Test'''
assert isinstance(baseline_acc, float), '`baseline_acc` should be type float. Have you defined the variable?'
assert 0.0 <= baseline_acc <= 1.0

"""# IV. Build Model

In this section, you want to answer the question: Which ensemble method performs better with this data — bagging or boosting?

**Task 7:** Build a model that includes a bagging predictor (`RandomForest`). Your predictor should be part of a pipeline named `model_bag` that includes any transformers that you think are necessary.
"""

'''T7. Build model with bagging predictor.'''
# YOUR CODE HERE
model_bag = make_pipeline(
    OneHotEncoder(use_cat_names=True),
    SimpleImputer(strategy="mean"),
    RandomForestClassifier(random_state=42, n_jobs=-1, n_estimators = 25)
)
model_bag.fit(X_train, y_train);

"""**Tast 7 Testing**"""

'''T7 Testing'''
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
assert isinstance(model_bag, Pipeline), '`model_bag` is the wrong data type. Have you assigned your pipeline to the correct variable name?'
assert isinstance(model_bag[-1], RandomForestClassifier), 'Your predictor should be a `RandomForestClassifier`.'
assert hasattr(model_bag[-1], 'feature_importances_'), 'Have you trained your model?'

"""**Task 8:** Build a model that includes a boosting predictor (`GradientBoostingClassifier` from `sklearn` or `XGBClassifier` from `xgboost`). Your predictor should be part of a pipeline named `model_boost` that includes any transformers that you think are necessary."""

'''T8. Build model with boosting predictor.'''
# YOUR CODE HERE
model_boost = make_pipeline(
    OneHotEncoder(use_cat_names=True),
    xgb(
    random_state=42,
    n_estimators=25,
    n_job=-1)
)
model_boost.fit(X_train, y_train);

"""**Task 8 Testing**"""

'''T8 Testing'''
from xgboost import XGBClassifier
from sklearn.ensemble import GradientBoostingClassifier
assert isinstance(model_boost, Pipeline), '`model_boost` is the wrong data type. Have you assigned your pipeline to the correct variable name?'
assert any([isinstance(model_boost[-1], XGBClassifier),
            isinstance(model_boost[-1], GradientBoostingClassifier)]), 'Your predictor should be `XGBClassifier` or `GradientBoostingClassifier`.'

"""# V. Check Metrics

Here are the accuracy scores for your two models. Did you beat the baseline? Which of your two models appears to perform better on your validation set?
"""

print('Bagging Model')
print('Training accuracy:', model_bag.score(X_train, y_train))
print('Validation accuracy:', model_bag.score(X_val, y_val))
print()
print('Boosting Model')
print('Training accuracy:', model_boost.score(X_train, y_train))
print('Validation accuracy:', model_boost.score(X_val, y_val))

"""**Task 9 (`stretch_goal`):** Plot the ROC-curve for both of your models (you can plot them one-at-a-time, side-by-side, or in the same plot)."""

'''T9. Plot ROC-curve.'''
# YOUR CODE HERE
y_pred_prob_bag = model_bag.predict_proba(X_val)[:, 1]
y_pred_prob_boost = model_boost.predict_proba(X_val)[:, 1]

fpr_bag, tpr_bag, thresholds_bag = roc_curve(y_val, y_pred_prob_bag)
fpr_boost, tpr_boost, thresholds_boost = roc_curve(y_val, y_pred_prob_boost)

plt.plot(fpr_bag, tpr_bag, label=f'Bagging Model')
plt.plot(fpr_boost, tpr_boost, label=f'Boosting Model')

plt.plot([0,1], ls='--')

plt.xlabel('False Positive Rate')
plt.ylabel('True Positive Rate')
plt.title('ROC Curve')
plt.legend()
plt.show()

"""**Task 10:** Choose one of your models based on your validation accuracy score or your ROC curves. Then create a classification report for that model using your validation data. Save the text of the report to the variable name `model_cr`."""

'''T10. Generate classification report for one model.'''
from sklearn.metrics import classification_report
# YOUR CODE HERE
y_pred_boost = model_boost.predict(X_val)

model_cr = classification_report(y_val, y_pred_boost)
print(model_cr)

"""**Task 10 Testing**"""

assert isinstance(model_cr, str), '`model_cr` should be type `str`.'
assert all(term in model_cr for term in ['precision', 'recall', 'f1-score', 'support']), 'Is this a classification report?'

"""**Task 11:** Using your best model, create a DataFrame `permutation_importances` with the model's permutation importances based on your validation data.

- The index of the DataFrame should be your feature names.
- The first column should be the mean importance.
- The second column should be the importance standard deviation.
"""

'''T11. Create DataFrame of permutation importances.'''
# YOUR CODE HERE
from sklearn.inspection import permutation_importance

perm_data = permutation_importance(model_boost, X_val, y_val, random_state=42, n_jobs=-1)

permutation_importances = pd.DataFrame(index=X_val.columns,
                                       data={"mean_importance": perm_data.importances_mean,
                                             "std_importance": perm_data.importances_std})

permutation_importances

"""**Task 11 Testing**"""

'''Task 11 Test'''
assert isinstance(permutation_importances, pd.DataFrame), '`permutation_importances` should be type `DataFrame`.'
assert permutation_importances.shape == (7,2)

"""**Task 12 (`stretch goal`):** Using your best model, create a PDP interaction plot to examine how `'Latitude'` and `'Longitude'` inform predictions. Remember to user your validation data.

**Note:** Because of the way that `pdp_interact` works, it will throw an error if there are `NaN` values in your validation set. To avoid this problem, be sure to set `dataset` to `X_val.dropna()`.
"""

df

'''T12. Create PDP interaction plot for "Latitude" and "Longitude".'''
features = ['Longitude', 'Latitude']
# YOUR CODE HERE
X_val = X_val.dropna()

X_val_pdp = X_val

# interact = PDPInteract(model=model_boost,
#                           n_classes = 2,
#                           df=X_val_pdp,
#                           model_features=X_val.columns,
#                           features=features,
#                           feature_names=features)

interact_plot = InteractPredictPlot(model=model_boost,
                          n_classes = 2,
                          df=X_val_pdp,
                          model_features=X_val_pdp.columns,
                          features=features,
                          feature_names=features,
                          )
fig, axes, summary = interact_plot.plot()
fig.show()

"""What do you think? Is there a relationship between location and failing a food saftey inspection? Answer below.

This task will not be autograded - but it is part of completing the challenge.

There is not a relationship between the two
"""
