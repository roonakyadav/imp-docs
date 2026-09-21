# Classical Machine Learning — Complete MCQ Notes
## Sessions 1–8 | Optimized for Part A (8 × 1 mark)

**Purpose:** These notes are built around the exact eight MCQ areas in the Quiz Guide, then expanded using the corresponding Session 1–8 study material. The goal is not to teach every possible ML detail; it is to make the concepts recognizable under exam pressure.

---

# 0. How to use these notes

For every MCQ, learn four things:

1. **Definition** — what the term literally means.
2. **Difference** — how it differs from the closest confusing term.
3. **Direction** — what goes up/down, helps/hurts, or train/test only.
4. **Trap** — the answer option designed to fool you.

When revising immediately before the quiz, read only the **Quick Recall**, **MCQ Traps**, and **Final 8-line Sheet** sections.

---

# Q1 — Supervised Learning & Regression

The quiz guide explicitly tests supervised vs. unsupervised learning, regression vs. classification, the target `y`, hypothesis `h(x)`, and the train/test split. [Guide Q1]

## 1. Machine Learning

### Traditional programming

**Rules + Data → Output**

A programmer writes the rules manually.

### Machine learning

**Data + Output → Rules (model)**

The model learns the relationship between inputs and correct outputs from examples.

### One-sentence definition

Machine learning learns a rule/model from experience so that performance on a task improves according to a chosen performance measure.

The course uses Mitchell's framing:

- **E = Experience**
- **T = Task**
- **P = Performance measure**

Think: **E-T-P = Experience, Task, Performance.**

---

## 2. Supervised vs. Unsupervised Learning

| Feature | Supervised | Unsupervised |
|---|---|---|
| Features `X` | Yes | Yes |
| Target/label `y` | **Yes** | **No** |
| Goal | Learn `X → y` | Discover structure in `X` |
| Example | House price prediction | Customer segmentation |

### Supervised learning

The dataset contains:

**X = features/input**

**y = labelled target/output**

The model learns how `X` maps to `y`.

Examples:

- House price → regression
- Spam / not-spam → classification
- Customer churn → classification

### Unsupervised learning

There is **no labelled target**.

The model looks for structure already present in the features.

Examples mentioned in the session:

- Customer segmentation
- Document grouping
- Clustering
- PCA / dimensionality reduction

### MCQ trigger

If the question says **"labelled data" / "known correct output" / "target y"** → think **supervised**.

If it says **"no target" / "discover groups" / "find structure"** → think **unsupervised**.

---

# 3. Regression vs. Classification

## Regression

Predicts a **continuous numerical value**.

Examples:

- Price
- Revenue
- Temperature
- Demand

Think: **number**.

## Classification

Predicts a **category/class**.

Examples:

- Spam / not-spam
- Fraud / legitimate
- Disease / healthy

Think: **label/category**.

### Fast memory trick

**Regression = Real number**

**Classification = Class**

### Important trap: 1–5 star rating

The session explicitly says predicting a 1–5 star rating can be framed as either regression or classification.

Why?

Because **problem framing determines the task**. You can model the rating as a numerical quantity or as a set of categories.

Do not assume every number-valued target automatically makes the problem regression.

---

# 4. What is the target `y`?

`y` is the **target/output/thing the model is trying to predict**.

`X` = input features

`y` = target

Example:

```text
House size, bedrooms, location  → X
House price                    → y
```

### Critical point

The target is **chosen when the problem is framed**. It is not some magical field that the data automatically declares to be the target.

---

# 5. What is the hypothesis `h(x)`?

The hypothesis is the model/function that maps input features to a prediction.

Conceptually:

```text
h(x) = model's prediction from x
```

For linear regression, the model can look like:

```text
h(x) = β₀ + β₁x
```

For multiple features:

```text
h(x) = β₀ + β₁x₁ + β₂x₂ + ... + βₚxₚ
```

The model learns the parameters so that predictions are good.

---

# 6. Generalization

The actual goal of ML is **not** to memorize the training examples.

The goal is to perform well on **unseen data** drawn from the same underlying problem distribution.

This is called **generalization**.

### Training error vs. true error

**Training error:** error measured on the training sample you actually have.

**True error:** expected error over the underlying data distribution.

The session's key idea is:

> We can measure training error; what we actually care about is true error.

### MCQ trap

A model getting 99% on the exact data it trained on does **not** prove that it generalizes well.

---

# 7. Train/Test Split

We split the dataset so that the model is trained on one part and evaluated on **unseen** data.

Example:

```python
train_test_split(X, y, test_size=0.2)
```

`test_size=0.2` means approximately 20% is held out for testing.

## Golden rule

**The test set is for the final evaluation.**

The session states that it should be touched **exactly once, at the very end**.

Looking at test performance and repeatedly making modelling decisions based on it contaminates the test estimate.

### Recognition question

> "I trained on all 1000 rows and got 99% accuracy on those same 1000 rows."

This is training performance, not an honest estimate of performance on unseen data.

---

## Q1 Quick Recall

```text
Supervised       = X + labelled y
Unsupervised     = X, no target y
Regression       = continuous number
Classification   = category/class
y                = target/output
h(x)             = model/hypothesis mapping input → prediction
Generalization   = good performance on unseen data
Train/test split = reserve unseen data for evaluation
Test set         = final evaluation; don't tune on it
```

### Q1 MCQ Traps

- **"No target" → unsupervised**, not supervised.
- **"Predict a category" → classification**, even if labels are written as numbers.
- **"Predict a number" → usually regression**, but problem framing matters.
- **High training accuracy ≠ high generalization.**
- `y` is what you predict; `X` is what you use to predict it.

---

# Q2 — Data Leakage & Preprocessing

The guide specifically lists train/test split, preprocessing leakage, `StandardScaler`, fitting only on training data, transforming train/test using the same fitted transformer, and imputation leakage. [Guide Q2]

## 1. Data Leakage

### Definition

**Data leakage = information reaches the model that would not actually be available at prediction time.**

Result:

```text
Development score looks excellent
              ↓
Model appears amazing
              ↓
Production performance collapses
```

### Core idea

Leakage means **information crossed a boundary it should not have crossed**.

The session gives three major patterns:

1. Preprocessing leakage
2. Target leakage
3. Temporal leakage

---

# 2. Preprocessing Leakage

### Wrong order

```text
Entire dataset
      ↓
Fit scaler on everything
      ↓
Train/test split
```

### Correct order

```text
Train/test split
      ↓
Fit scaler on TRAIN only
      ↓
Transform TRAIN and TEST
```

Why is the first version leakage?

Because the scaler learns parameters such as:

- mean `μ`
- standard deviation `σ`

If those are calculated using test rows, the test set has influenced the transformation used during training.

---

# 3. StandardScaler

Standardization is:

```text
z = (x - μ) / σ
```

It produces approximately:

- Mean = 0
- Standard deviation = 1

### The most important rule

**Fit on training data only.**

Then use the same fitted transformer to transform both training and test data.

Conceptually:

```python
scaler.fit(X_train)
X_train_scaled = scaler.transform(X_train)
X_test_scaled  = scaler.transform(X_test)
```

NOT:

```python
scaler.fit(X)
```

before the split.

---

# 4. Imputation Leakage

Imputation fills missing values.

For numerical data, the session lists:

- Mean
- Median
- Constant

For categorical data:

- Mode
- Explicit `Unknown`

### Important leakage rule

Any learned imputation statistic must also be learned from **training data only**.

If the test-set mean/median is used while training, information from the test set has leaked into preprocessing.

### Mean vs. Median

The session's rule:

**Use median when outliers are present.**

Reason: an extreme value can pull the mean strongly.

Example idea:

```text
Normal values: 10, 11, 12, 13
One extreme:   1,000,000
```

The mean gets dragged toward the extreme value; the median is much more resistant.

---

# 5. Target Leakage

A feature contains information that becomes known **after the outcome**.

Session example:

Trying to predict `will_default` using `total_amount_recovered`, when the recovery amount is only known after the default process has happened.

That gives the model information that would not exist at prediction time.

### MCQ trigger

If a feature is only available **after the thing you are trying to predict**, think **target leakage**.

---

# 6. Temporal Leakage

For time-ordered data, a random split can allow the model to use **future information to predict the past**.

Correct idea:

```text
Past → train
Future → validation/test
```

For time-dependent problems, respect chronological order.

### MCQ trigger

Words like:

- future
- past
- timeline
- time-ordered
- predicting earlier events using later information

→ **temporal leakage**.

---

# 7. Three Leakage Patterns — One Table

| Leakage | What crosses the boundary? | Example |
|---|---|---|
| Preprocessing | Test/validation information enters preprocessing | Fit scaler on entire dataset |
| Target | Information available after outcome enters features | Recovery amount used to predict default |
| Temporal | Future information enters past prediction | Random split of time-ordered data |

Memory trick:

**Pre → Test contamination**

**Target → After-the-answer information**

**Temporal → Future leaks backward**

---

# Q2 Quick Recall

```text
Leakage = unavailable information reaches the model
StandardScaler = (x - μ) / σ
fit            = learn parameters
transform      = apply learned parameters
Correct order  = split → fit on train → transform train/test
Median         = preferred over mean when outliers exist
Target leak    = after-the-outcome information
Temporal leak  = future information used for past prediction
```

### Q2 MCQ Traps

- `fit` is the dangerous step because it **learns** parameters.
- `transform` applies parameters already learned.
- Test data can be **transformed** using the training-fitted scaler; it must not be used to **fit** the scaler.
- Scaling before splitting is leakage.
- Imputer statistics also must be fit on training data only.
- A feature known after the outcome is target leakage.

---

# Q3 — Categorical Encoding

The guide targets categorical variables, ordinal vs. nominal categories, ordinal encoding, one-hot encoding, and avoiding artificial ordering. [Guide Q3]

## 1. Categorical Variables

A categorical variable contains categories rather than a naturally continuous numerical measurement.

Examples:

```text
City     = Delhi / Mumbai / Bangalore
Size     = Small / Medium / Large
```

But not all categories behave the same way.

---

# 2. Nominal vs. Ordinal

## Nominal

Categories have **no natural order**.

Example:

```text
Delhi
Mumbai
Bangalore
```

There is no meaningful:

```text
Delhi < Mumbai < Bangalore
```

relationship.

## Ordinal

Categories have a **real order**.

Example:

```text
Low < Medium < High
```

The order itself contains information.

### Memory trick

**Nominal = Name only**

**Ordinal = Order exists**

---

# 3. One-Hot Encoding

Best mental model for a nominal categorical feature:

> Make one 0/1 column for each category.

Example:

| City | Delhi | Mumbai | Bangalore |
|---|---:|---:|---:|
| Delhi | 1 | 0 | 0 |
| Mumbai | 0 | 1 | 0 |
| Bangalore | 0 | 0 | 1 |

### Key benefit

It does **not invent an order** among categories.

---

# 4. Ordinal Encoding

Use ordinal encoding when categories genuinely have order.

Example:

```text
Low    → 0
Medium → 1
High   → 2
```

The numeric values communicate the intended order.

---

# 5. Why Label Encoding a Nominal Feature Is Dangerous

Suppose:

```text
Delhi     → 0
Mumbai    → 1
Bangalore → 2
```

For a linear or distance-based model, this can create the fake interpretation:

```text
Bangalore is "more" than Mumbai
Mumbai is "more" than Delhi
```

The numbers imply an order that never existed.

### Session rule

**Never label-encode a nominal feature.**

The session describes label encoding as reserved for the **target**, not feature columns.

---

# 6. Dummy-Variable Trap

If there are `k` one-hot columns for a categorical variable, and an intercept is also included, all `k` dummy columns are perfectly collinear because exactly one category is active.

Conceptually:

```text
Dummy₁ + Dummy₂ + ... + Dummyₖ = 1
```

With an intercept, this creates perfect linear dependence.

For linear models, the session's fix is:

```python
drop_first=True
```

This drops one reference category.

### Important distinction

**Nominal encoding problem:** artificial ordering.

**Dummy trap:** perfect collinearity caused by redundant one-hot columns plus intercept.

Do not confuse them.

---

# 7. Unknown Categories

A test set may contain a category that the training set never saw.

The session points to:

```python
handle_unknown='ignore'
```

inside the encoding/Pipeline setup.

Mental model:

> "Do not crash just because a new category appears at prediction time."

---

# Q3 Quick Recall

```text
Nominal = no natural order
Ordinal = natural order exists
One-hot = separate 0/1 column per category
Ordinal encoding = ordered categories
Label encoding = target, not nominal features
Nominal + 0/1/2 = artificial ordering trap
Dummy trap = all k dummies + intercept are perfectly collinear
```

### Q3 MCQ Traps

- **City names → nominal → one-hot.**
- **Low/Medium/High → ordinal encoding can make sense.**
- Turning arbitrary city names into `0,1,2` invents an order.
- One-hot encoding does not mean the categories are ordered.
- Dummy-variable trap is about **collinearity**, not categorical ordering.

---

# Q4 — Mean Squared Error (MSE)

The guide tests residuals, squared error, the MSE formula, manual calculation, and interpretation of prediction error. [Guide Q4]

## 1. Prediction

For observation `i`:

```text
Actual value     = yᵢ
Predicted value  = ŷᵢ
```

---

# 2. Residual

The residual is:

```text
residual = actual - predicted
```

Formula:

```text
eᵢ = yᵢ - ŷᵢ
```

### Example

Actual = 10

Predicted = 7

```text
residual = 10 - 7 = +3
```

If actual = 7 and predicted = 10:

```text
residual = 7 - 10 = -3
```

So:

**Residual sign tells the direction of the error.**

---

# 3. Squared Error

The squared error for one observation is:

```text
(yᵢ - ŷᵢ)²
```

Squaring makes the error non-negative.

It also gives large errors disproportionately more influence than small errors.

---

# 4. Mean Squared Error

The formula is:

```text
                 1
MSE = ───────────────── Σ (yᵢ - ŷᵢ)²
                 n
```

or:

```text
MSE = (1/n) Σ eᵢ²
```

### Procedure for manual MSE

Always do these steps in order:

1. Calculate each residual.
2. Square each residual.
3. Add all squared errors.
4. Divide by the number of observations.

### Quick example

Actual:

```text
[3, 5, 7]
```

Predicted:

```text
[2, 6, 8]
```

Residuals:

```text
[1, -1, -1]
```

Squared errors:

```text
[1, 1, 1]
```

Sum:

```text
3
```

MSE:

```text
3 / 3 = 1
```

---

# 5. Why Squared Error Is Used

The session gives three reasons:

### Practical

Squared error is differentiable everywhere, which makes calculus-based optimization convenient.

### Statistical

With Gaussian noise, least squares corresponds to maximum likelihood estimation.

### Decision-theoretic

The function that minimizes expected squared error is the conditional mean:

```text
f*(x) = E[y | x]
```

The session contrasts this with absolute error, whose minimizer is the conditional median.

For MCQs, the important association is:

**Squared error ↔ conditional mean**

**Absolute error ↔ conditional median**

---

# Q4 Quick Recall

```text
Residual      = y - ŷ
Squared error = (y - ŷ)²
MSE           = average of squared errors
MSE           = (1/n) Σ(yᵢ - ŷᵢ)²
```

### MSE MCQ Traps

- Do not forget the **square**.
- Do not forget the **mean** — divide by `n`.
- `y - ŷ` and `ŷ - y` give opposite residual signs, but the squared error is the same.
- MSE cannot be negative.
- A large residual becomes especially important after squaring.

---

# Q5 — Linear Regression Assumptions

The guide focuses specifically on residual analysis, residual-vs-fitted plots, homoscedasticity, heteroscedasticity, variance stabilization, and log transformation. [Guide Q5]

## 1. Residuals Again

```text
eᵢ = yᵢ - ŷᵢ
```

Residual analysis asks:

> Do the errors look like random noise, or is there a pattern the model has failed to capture?

---

# 2. Residual vs. Fitted Plot

Plot residuals against fitted/predicted values.

### Healthy-looking pattern

Random scatter around zero.

Think:

```text
•  •   •
  • •
•   •  •
──────────── 0
```

There should not be a systematic pattern.

---

# 3. The Four Most Important Residual Patterns

| Residual pattern | What it suggests |
|---|---|
| U-shape / curve | Non-linearity |
| Funnel / cone | Heteroscedasticity |
| Clusters | Missing variable / structure |
| Trend over index | Autocorrelation / dependence |

For Q5, remember especially:

**Funnel → heteroscedasticity**

---

# 4. Homoscedasticity

**Homoscedasticity = residuals have approximately constant variance across the fitted values.**

Meaning:

```text
small fitted value → similar spread
large fitted value → similar spread
```

The error cloud has roughly the same vertical width.

---

# 5. Heteroscedasticity

**Heteroscedasticity = residual variance changes with the level of the fitted value/predictor.**

Typical visual signature:

```text
small x:  ••
medium x: ••••
large x:  •••••••••
```

This looks like a **funnel/cone**.

### Memory trick

**Hetero = different** variance.

**Homo = same** variance.

---

# 6. Variance-Stabilizing Transformation

When the variance changes systematically, a transformation can make the spread more stable.

The session specifically highlights **log transformation**.

The remedy listed for heteroscedasticity includes:

- log-transform `y`
- weighted least squares

For an MCQ, if you see:

> "Funnel-shaped residual plot; variance increases with fitted value"

Think:

**Heteroscedasticity → log transformation can help stabilize variance.**

---

# 7. Full Six-Assumption Picture from the Session

Even though Q5 emphasizes only part of this, know the full checklist:

1. **Linearity** — relationship is approximately linear.
2. **Independence** — errors are independent.
3. **Homoscedasticity** — residual variance is constant.
4. **Normality of residuals** — mainly important for inference.
5. **No/low multicollinearity** — predictors are not near-duplicates.
6. **No influential extreme points** — one row should not dominate the fit.

### Important session distinction

Normality violations mainly affect **inference** such as p-values and confidence intervals; they do not necessarily destroy point prediction.

The session also emphasizes that multicollinearity can make coefficients unstable/uninterpretable while predictions may still be acceptable.

---

# Q5 Quick Recall

```text
Residual        = actual - fitted
Homoscedastic   = constant residual variance
Heteroscedastic = changing residual variance
Funnel plot     = heteroscedasticity
U-shape         = non-linearity
Log transform   = possible variance-stabilizing remedy
```

### Q5 MCQ Traps

- Funnel ≠ overfitting automatically. It specifically signals changing residual variance.
- **Homo = same**, **hetero = different**.
- A good `R²` alone does not prove that regression assumptions are valid.
- Non-normal residuals are mainly an inference issue in the session, not automatically a prediction failure.

---

# Q6 — Gradient Descent

The guide specifically lists Batch Gradient Descent, cost `J(θ)`, gradient, learning rate `α`, too-large vs. too-small learning rates, convergence/divergence, and Batch GD vs. SGD. [Guide Q6]

## 1. Why Gradient Descent?

For linear regression, the closed-form solution can become expensive or fail with singular matrices.

For logistic regression, the session says a closed form does not exist.

Gradient descent provides a general-purpose iterative optimization method for differentiable costs.

---

# 2. Intuition

Imagine standing on a foggy hillside and trying to reach the valley floor.

You cannot see the entire landscape.

You can feel the **slope**.

So you:

```text
measure slope → step downhill → repeat
```

Mapping:

| Hill analogy | ML symbol |
|---|---|
| Hillside | Cost `J(θ)` |
| Current position | Parameters `θ` |
| Slope | Gradient `∇J` |
| Step size | Learning rate `α` |
| Valley floor | Minimum |

---

# 3. Cost Function

The session uses the cost:

```text
          1
J(θ) = ─────── Σ(ŷᵢ - yᵢ)²
          2m
```

The factor `1/2` is mainly a convenience because the 2 from differentiating the square cancels it.

Important idea:

**Training = choose parameters that minimize the cost.**

---

# 4. Gradient

The gradient tells you the direction of **steepest increase** of the cost.

Therefore, to minimize the cost, move in the opposite direction.

This produces the famous minus sign.

### Update rule

```text
θ := θ - α ∇J(θ)
```

This is one of the most important formulas in the whole course.

### Memory trick

**Gradient says UP → minus says DOWN.**

---

# 5. Gradient Pattern

For the linear-regression setup in the session:

```text
gradient = average(error × feature)
```

More explicitly:

```text
∂J/∂θ₁ = (1/m) Σ(ŷᵢ - yᵢ)xᵢ
```

The intercept term is the feature value `1`, giving:

```text
∂J/∂θ₀ = (1/m) Σ(ŷᵢ - yᵢ)
```

### Memory trick

**Gradient = error × feature, then average.**

---

# 6. Learning Rate `α`

The learning rate controls **how big the step is**.

### Too small

```text
Correct direction
but tiny steps
→ very slow
```

### About right

```text
Smooth, fast descent
→ convergence
```

### Too large

```text
Huge steps
→ overshoot
→ oscillation/divergence
→ loss can explode / NaN
```

### Fast exam rule

**Loss rising repeatedly → learning rate is too high.**

**Loss nearly flat for hundreds of iterations → learning rate may be too low.**

---

# 7. Convergence vs. Divergence

## Convergence

The optimization settles toward the minimum.

For linear regression, the cost surface is convex, so there is one global minimum.

## Divergence

The updates move away instead of settling.

A common reason in this session:

**learning rate too large.**

---

# 8. Batch vs. Stochastic vs. Mini-Batch

| Method | Samples per update | Character |
|---|---:|---|
| Batch GD | All `m` | Smooth, stable, exact gradient |
| SGD | 1 | Very noisy, frequent updates |
| Mini-batch | Typically 32–256 in the session | Practical default |

### Batch Gradient Descent

Uses **all training examples** to calculate a gradient for one update.

Pros:

- Smooth
- Stable
- Exact gradient for the current dataset

Cons:

- Can be slow on large datasets

### Stochastic Gradient Descent (SGD)

Uses **one example** per update.

Pros:

- Very fast per update
- Noisy movement can help explore the surface

Cons:

- Jittery/noisy path

### Mini-Batch GD

Uses a small batch, not the entire dataset and not just one point.

The session calls this the **practical default**.

---

# 9. Why Scaling Helps Gradient Descent

Unscaled features can make the cost surface look like a long, thin valley.

The gradient then tends to zig-zag across the valley.

Scaled features produce a more rounded surface, allowing descent to move more directly toward the minimum.

### Memory image

```text
Unscaled → long/thin valley → zig-zag → slow
Scaled   → round bowl        → direct → faster
```

---

# Q6 Quick Recall

```text
θ := θ - α∇J
Gradient          = steepest increase
Minus sign        = move downhill
α too small       = slow
α too large       = overshoot/diverge
Batch             = all samples/update
SGD               = 1 sample/update
Mini-batch        = small batch/update
Scaling           = makes optimization geometry easier
Linear regression = convex → one global minimum
```

### Q6 MCQ Traps

- The gradient itself points toward **increase**, not decrease.
- The minus sign is what moves opposite the gradient.
- Increasing `α` does not always make training faster; too much causes instability.
- Batch GD does **not** mean one sample.
- SGD does **not** mean all samples.
- Mini-batch is neither 1 nor all; it is a small subset.

---

# Q7 — Bias, Variance & Polynomial Regression

The guide explicitly tests underfitting, overfitting, bias, variance, polynomial degree, train vs. test error, regularization, and the bias-variance tradeoff. [Guide Q7]

## 1. The Three Main Error Patterns

| Situation | Train error | Test error | Diagnosis |
|---|---|---|---|
| Underfit | High | High | High bias |
| Good fit | Low | Low | Balanced |
| Overfit | Very low | High | High variance |

### The biggest pattern to memorize

**High train + high test → underfitting / high bias.**

**Very low train + high test → overfitting / high variance.**

---

# 2. Bias

Bias is systematic error caused by a model being too restricted or too simple to capture the underlying relationship.

High-bias model:

- Pays too little attention to the real structure in the data.
- Produces systematically wrong predictions.
- Often underfits.

### Example intuition

Trying to fit a strongly curved relationship with a straight line.

---

# 3. Variance

Variance measures how much the fitted model/prediction changes when the training sample changes.

High variance:

- Model is very sensitive to the particular training sample.
- It can chase noise.
- Often overfits.

### Human memory trick from the session

**High bias:** one simple rule applied everywhere.

**High variance:** memorized the past exactly, struggles on new data.

---

# 4. Bias-Variance Decomposition

The session gives:

```text
Total prediction error
= irreducible noise + variance + bias²
```

or, in the session's shorthand:

```text
Error = noise + variance + bias²
```

### The three terms

#### Irreducible noise

Randomness inherent in the target given the features.

**Cannot be removed simply by choosing a better model.**

It is the error floor.

#### Variance

How much the prediction changes when the training data changes.

**Can be reduced** by methods such as:

- simpler models
- more data
- ensembling

#### Bias²

How far the average model prediction is from the true conditional mean.

**Can be reduced** by:

- more expressive models
- better features

---

# 5. Complexity and the Bias-Variance Tradeoff

As model complexity increases:

```text
Bias ↓
Variance ↑
```

Total error is therefore often U-shaped against complexity.

The best region is usually somewhere between:

```text
Too simple ← balanced → too complex
```

### One-line memory

**More complexity: less bias, more variance.**

---

# 6. Polynomial Regression

Example:

```text
y = β₀ + β₁x + β₂x² + β₃x³ + ...
```

It is nonlinear in `x`, but it is **linear in the parameters `β`**.

That is why the session still treats it as linear regression.

### Extremely important MCQ wording

Question:

> "Is polynomial regression linear?"

Correct interpretation:

**Yes, it is linear in the parameters. It is not linear in the original input `x`.**

---

# 7. Polynomial Degree

Increasing polynomial degree increases model flexibility/complexity.

Higher degree can capture more complicated shapes.

But:

```text
Higher degree → more columns/parameters → more variance risk
```

The session also warns that very high powers such as `x^15` can create huge numerical ranges on unscaled data.

Therefore:

**Polynomial features and scaling should travel together.**

---

# 8. Learning Curves

A learning curve shows error/performance as training-set size changes.

### High bias pattern

Training and validation/test curves tend to converge to a **high error**.

More data will not solve the underlying lack of model expressiveness.

Possible direction:

**Use a better/more expressive model.**

### High variance pattern

A **large persistent gap** exists between training and validation/test performance.

More data can help reduce variance.

Other fixes include:

- simplify the model
- regularize

---

# 9. More Data — Which Problem Does It Help?

The session explicitly connects:

**More data → can reduce variance.**

It does not generally solve a high-bias model whose training and validation errors are both high and close together.

### MCQ pattern

> Training and validation error are both high and close.

Think:

**High bias / underfitting. More data alone is not the main fix.**

> Training error is tiny and test error is much larger.

Think:

**High variance / overfitting. More data can help.**

---

# Q7 Quick Recall

```text
Underfit       = high train error + high test error
Overfit        = very low train error + high test error
High bias      = model too simple
High variance  = model sensitive to data/noise
Error          = noise + variance + bias²
Complexity ↑   = bias ↓, variance ↑
Polynomial     = linear in parameters, nonlinear in x
More data      = mainly helps high variance
Learning curve = diagnose bias/variance from train/validation behavior
```

### Q7 MCQ Traps

- Overfitting is **not** high training error; it is usually very low training error with worse test performance.
- Underfitting is not "variance is too high"; it is high bias.
- Polynomial regression is not "nonlinear regression" in the parameter sense used in the session.
- More features or higher degree can reduce bias but increase variance.
- Irreducible noise is not something regularization can simply remove.

---

# Q8 — Regularization + Classification Metrics

The guide combines Lasso/L1, Ridge/L2, feature selection, class imbalance, the accuracy trap, precision, recall, F1, ROC-AUC, and classification threshold. [Guide Q8]

---

# PART A — Regularization

## 1. Why Regularization?

Overly flexible models can have large coefficients and high variance.

Regularization adds a complexity penalty to the loss.

Core pattern:

```text
Regularized loss = data-fit loss + λ × complexity penalty
```

The session expresses it as:

```text
loss = MSE + λ × Penalty(β)
```

The tradeoff is deliberate:

```text
accept some bias
        ↓
reduce variance
        ↓
better generalization
```

---

# 2. Ridge Regression — L2

Penalty:

```text
Σ βⱼ²
```

So:

```text
Ridge = L2 regularization
```

### Effect

Ridge **shrinks coefficients toward zero**.

The session emphasizes:

**Ridge generally does not make coefficients exactly zero.**

Therefore it does not perform automatic feature selection in the way Lasso does.

### Best association

**Ridge ↔ multicollinearity**

The session describes Ridge's `λI` term as a direct repair for the singular/ill-conditioned matrix problem.

---

# 3. Lasso Regression — L1

Penalty:

```text
Σ |βⱼ|
```

So:

```text
Lasso = L1 regularization
```

### Effect

Lasso can force coefficients to become **exactly zero**.

Therefore:

**Lasso performs automatic feature selection.**

Irrelevant features can disappear because their coefficients become zero.

The session says Lasso is solved using **coordinate descent**, not a simple normal-equation closed form.

---

# 4. Ridge vs. Lasso — Memorize This Table

| Property | Ridge | Lasso |
|---|---|---|
| Penalty | L2: `Σβ²` | L1: `Σ|β|` |
| Shrinks coefficients | Yes | Yes |
| Can make coefficient exactly 0 | Generally no | **Yes** |
| Automatic feature selection | No | **Yes** |
| Strong association | Multicollinearity | Feature selection |

### Memory trick

**Lasso = Leaves features at zero.**

**Ridge = Reduces coefficient size.**

---

# 5. Elastic Net

Elastic Net combines L1 and L2 penalties:

```text
RSS + λ₁Σ|βⱼ| + λ₂Σβⱼ²
```

The session associates it with:

- correlated groups of features
- situations such as `p > n`

The grouping effect is important:

**Lasso may arbitrarily keep one feature from a correlated group and zero others. Elastic Net can keep the correlated group together.**

---

# 6. What Happens as `λ` Changes?

### `λ = 0`

No regularization penalty.

→ ordinary least squares.

### Larger `λ`

Stronger penalty.

→ coefficients shrink more.

### Very large `λ`

Coefficients are driven toward zero.

For Ridge, the session describes the limit as the flat-line model with very high bias and near-zero variance.

### Memory

```text
λ ↑ → penalty ↑ → coefficient sizes ↓
```

---

# 7. Important Ridge Rules

### Scale first

Regularization penalties depend on coefficient magnitude, so feature scale matters.

The session says to **scale before Ridge/Lasso**.

### Do not penalize the intercept

The intercept is treated separately; shrinking it can undesirably pull predictions toward zero rather than toward the target mean.

---

# PART B — Classification Metrics

## 8. Confusion Matrix

For binary classification:

| | Actual Positive | Actual Negative |
|---|---:|---:|
| Predicted Positive | TP | FP |
| Predicted Negative | FN | TN |

Memorize the four:

- **TP = True Positive**
- **FP = False Positive**
- **FN = False Negative**
- **TN = True Negative**

---

# 9. Precision

Formula:

```text
Precision = TP / (TP + FP)
```

Plain English:

> Of the examples I predicted as positive, how many were actually positive?

Think:

**Precision = "Can I trust my positive predictions?"**

### Precision is hurt by

**False positives.**

---

# 10. Recall

Formula:

```text
Recall = TP / (TP + FN)
```

Plain English:

> Of all the actual positives that existed, how many did I successfully catch?

Think:

**Recall = "How many real positives did I find?"**

### Recall is hurt by

**False negatives.**

---

# 11. Precision vs. Recall

| Metric | Question |
|---|---|
| Precision | Of predicted positives, how many were correct? |
| Recall | Of actual positives, how many did we catch? |

### Session examples

**Spam:** precision can matter strongly because you do not want many legitimate emails flagged as spam.

**Cancer/fraud:** recall can matter strongly because missing a true positive can be costly.

The exact desired balance depends on the application's error costs.

---

# 12. F1 Score

Formula:

```text
              2 × Precision × Recall
F1 = ─────────────────────────────────────
              Precision + Recall
```

F1 is the **harmonic mean** of precision and recall.

Why harmonic mean matters:

If one metric is very high and the other is very low, F1 does not let the high metric hide the weakness of the low metric.

### Session example

If:

```text
Precision = 1.0
Recall    = 0.1
```

the arithmetic mean is 0.55, while F1 is much lower (about 0.18).

### Memory

**F1 wants both precision and recall to be good.**

---

# 13. Accuracy

Accuracy is:

```text
(TP + TN) / (TP + TN + FP + FN)
```

It measures the fraction of all predictions that were correct.

Accuracy is simple, but the session strongly warns about the **accuracy trap under class imbalance**.

---

# 14. Class Imbalance

Suppose:

```text
99% = legitimate
1%  = fraud
```

A useless model that always predicts:

```text
legitimate
```

gets:

```text
99% accuracy
```

but catches:

```text
0 fraud cases
```

Therefore:

**High accuracy does not automatically mean a useful classifier when classes are highly imbalanced.**

### Base-rate trick

When you see a statement like:

> "99% accuracy!"

Immediately ask:

> "What percentage belongs to the majority class?"

Then compare against the naive majority-class baseline.

---

# 15. ROC Curve

The session defines:

```text
TPR = TP / (TP + FN)
```

TPR is the same quantity as **Recall**.

False positive rate:

```text
FPR = FP / (FP + TN)
```

ROC examines the relationship between TPR and FPR as the classification threshold changes.

---

# 16. ROC-AUC

AUC summarizes the ranking quality represented by the ROC curve.

The session's interpretation:

> AUC is the probability that a randomly chosen positive is ranked above a randomly chosen negative.

Important values:

```text
AUC = 0.5 → roughly coin-flip ranking
AUC = 1.0 → perfect ranking
```

### Key property

**ROC-AUC is threshold-independent.**

It evaluates ranking across thresholds rather than one chosen cutoff.

---

# 17. When ROC-AUC Can Mislead

Under **extreme class imbalance**, the false-positive rate can look deceptively small because its denominator contains a very large number of true negatives.

The session therefore says to prefer:

**PR-AUC (Precision-Recall AUC)**

when positive cases are rare.

### Memory

```text
Rare positives → think Precision/Recall → PR-AUC
```

---

# 18. Classification Threshold

The model produces a probability/score.

A threshold converts that score into a final class decision.

Example from the session:

```text
Probability = 0.82
Threshold   = 0.50
Prediction  = class 1
```

### Critical concept

**The threshold is a decision rule, not the model itself.**

The session emphasizes that 0.5 is a default, not a universal law.

Threshold choice should reflect the cost of different errors.

Examples:

- Cancer screening → low threshold can be appropriate when missing a true case is very costly.
- Spam → higher threshold can be appropriate when falsely blocking a real email is costly.

---

# 19. Logistic Regression Basics — Lower Priority but Know It

The session includes logistic regression concepts even though the Quiz Guide's Q8 list is centered on regularization/classification metrics.

## Sigmoid

```text
σ(z) = 1 / (1 + e^(-z))
```

It maps any real-valued input into:

```text
(0, 1)
```

Important point:

```text
σ(0) = 0.5
```

Large negative `z` → probability near 0.

Large positive `z` → probability near 1.

## Odds

```text
odds = p / (1-p)
```

Log-odds are linear in the features:

```text
log(p/(1-p)) = β₀ + β₁x₁ + ...
```

## Log-loss

For one observation:

```text
-[y log(p̂) + (1-y)log(1-p̂)]
```

It heavily punishes **confident wrong predictions**.

Example from the session for `y=1`:

```text
Predict 0.99 → tiny loss ≈ 0.01
Predict 0.01 → large loss ≈ 4.6
```

### MCQ trigger

**Sigmoid → probability**

**Log-odds → linear combination of features**

**Log-loss → punishes confident wrong predictions**

---

# Q8 Quick Recall

## Regularization

```text
Regularization = fit + λ × complexity penalty
Ridge          = L2 = Σβ² = shrink
Lasso          = L1 = Σ|β| = can become exactly zero
Elastic Net    = L1 + L2
λ ↑            = stronger shrinkage
λ = 0          = ordinary least squares
Ridge          = multicollinearity
Lasso          = feature selection
```

## Metrics

```text
Precision = TP / (TP + FP)
Recall    = TP / (TP + FN)
F1        = harmonic mean of precision and recall
TPR       = Recall
FPR       = FP / (FP + TN)
AUC       = ranking quality across thresholds
AUC 0.5   = random/coin-flip
AUC 1.0   = perfect
```

## Imbalance

```text
High accuracy + extreme imbalance ≠ necessarily useful
Rare positives → PR-AUC is often preferred
```

## Threshold

```text
threshold = converts score/probability → class decision
0.5       = default, not law
```

### Q8 MCQ Traps

- **Ridge is L2. Lasso is L1.**
- Lasso can make coefficients exactly zero; Ridge generally shrinks without hitting zero.
- Lasso → feature selection.
- Precision denominator contains **FP**.
- Recall denominator contains **FN**.
- TPR = Recall.
- FPR is not `FP / all examples`; it is `FP / (FP + TN)`.
- AUC is about ranking and is threshold-independent.
- 99% accuracy can still mean zero usefulness on a 1% positive class.
- Threshold is not the same thing as the trained model.

---

# High-Yield Comparison Tables

## 1. The most important "X vs Y" table

| If the question contrasts... | Remember |
|---|---|
| Supervised vs unsupervised | `y` exists vs no `y` |
| Regression vs classification | Continuous number vs category |
| Training vs test | Seen data vs unseen data |
| Nominal vs ordinal | No order vs real order |
| One-hot vs ordinal encoding | No artificial order vs meaningful order |
| Homoscedastic vs heteroscedastic | Same variance vs changing variance |
| Underfit vs overfit | High bias vs high variance |
| Ridge vs Lasso | L2 shrinkage vs L1 zeroing |
| Precision vs recall | Predicted positives correctness vs actual positives caught |
| Batch GD vs SGD | All samples/update vs one sample/update |

---

# High-Yield Formula Sheet

## Regression / MSE

```text
Residual:
eᵢ = yᵢ - ŷᵢ

MSE:
MSE = (1/n) Σ(yᵢ - ŷᵢ)²
```

## Standardization

```text
z = (x - μ) / σ
```

## Gradient Descent

```text
θ := θ - α∇J(θ)
```

## Regularization

```text
Ridge penalty = λΣβ²
Lasso penalty = λΣ|β|
```

## Classification metrics

```text
Accuracy  = (TP + TN)/(TP + TN + FP + FN)
Precision = TP/(TP + FP)
Recall    = TP/(TP + FN)
F1        = 2PR/(P + R)
TPR       = TP/(TP + FN)
FPR       = FP/(FP + TN)
```

## Logistic regression

```text
σ(z) = 1/(1 + e^(-z))
```

---

# The "Direction" Sheet

MCQs love changing one word like **increase**, **decrease**, **large**, **small**, or **only**.

Memorize these directions:

```text
Model complexity ↑  → bias ↓, variance ↑
λ ↑                 → coefficient magnitude ↓
α ↑ too much        → instability/divergence risk ↑
α ↓ too much        → convergence speed ↓
More data           → variance can ↓
Lasso               → some coefficients → exactly 0
Ridge               → coefficients → toward 0
Heteroscedasticity → residual variance changes
```

---

# The "What Does This Pattern Mean?" Sheet

| Pattern in question | Answer to think about |
|---|---|
| 99% train, 70% test | Overfitting / high variance |
| High train error, high test error | Underfitting / high bias |
| Funnel residual plot | Heteroscedasticity |
| U-shaped residual plot | Non-linearity |
| Future data used to predict past | Temporal leakage |
| Test mean used to scale training data | Preprocessing leakage |
| Feature known only after outcome | Target leakage |
| Nominal city → `0,1,2` | Artificial ordering |
| Low/Medium/High | Ordinal |
| Many false positives | Precision suffers |
| Many false negatives | Recall suffers |
| 99% accuracy with 1% fraud | Accuracy trap |
| Rare positives | PR-AUC becomes important |
| Huge learning rate | Overshoot/divergence |
| Tiny learning rate | Very slow descent |
| Coefficients exactly zero | Lasso |
| Coefficients smoothly shrink | Ridge |

---

# Common MCQ Wording Decoder

## "Seen during training"

→ Training data

## "Unseen data"

→ Test/generalization evaluation

## "Learns parameters/statistics"

→ `fit`

## "Applies already learned transformation"

→ `transform`

## "No target"

→ Unsupervised

## "Continuous numeric output"

→ Regression

## "Class/category output"

→ Classification

## "No natural ordering"

→ Nominal

## "Natural ordering"

→ Ordinal

## "Constant residual spread"

→ Homoscedasticity

## "Changing residual spread"

→ Heteroscedasticity

## "Predicted positives that are correct"

→ Precision

## "Actual positives successfully detected"

→ Recall

## "Harmonic mean of precision and recall"

→ F1

## "Positive ranked above negative"

→ ROC-AUC interpretation

## "Future information"

→ Temporal leakage

## "Information after outcome"

→ Target leakage

## "Exactly zero coefficients"

→ Lasso

## "Multicollinearity"

→ Ridge

---

# Mini Numerical Recognition

## MSE

Actual:

```text
[10, 20]
```

Prediction:

```text
[12, 18]
```

Residuals:

```text
[-2, 2]
```

Squared errors:

```text
[4, 4]
```

MSE:

```text
(4 + 4)/2 = 4
```

---

## Precision / Recall

Suppose:

```text
TP = 40
FP = 10
FN = 20
TN = 30
```

Precision:

```text
40/(40+10) = 0.80
```

Recall:

```text
40/(40+20) ≈ 0.67
```

F1:

```text
2 × 0.80 × 0.67 / (0.80 + 0.67) ≈ 0.73
```

Accuracy:

```text
(40 + 30)/100 = 0.70
```

Interpretation:

```text
80% of predicted positives were truly positive.
67% of actual positives were successfully caught.
70% of all predictions were correct.
```

The session uses this exact style of interpretation.

---

# Final 8-Line Sheet — Read This Right Before the Quiz

```text
1. Supervised = X + labelled y; regression = number; classification = category.
2. Test/validation information must NOT be used to fit preprocessing; fit on train, transform train + test.
3. Nominal → one-hot; ordinal → ordered encoding; never invent order for nominal features.
4. Residual = y - ŷ; MSE = average squared residual.
5. Funnel residuals = heteroscedasticity; log transformation can stabilize variance.
6. Gradient descent: θ := θ - α∇J; α too small = slow, α too large = diverge.
7. Underfit = high bias; overfit = high variance; complexity ↑ → bias ↓, variance ↑.
8. Ridge = L2 shrink; Lasso = L1 zeroes/features; Precision=TP/(TP+FP), Recall=TP/(TP+FN), F1 balances both; imbalance makes accuracy dangerous.
```

---

# Last-Minute Memory Tricks

### 1. Supervised

**SUPERVISED has a supervisor → someone gives the correct `y`.**

### 2. Nominal vs ordinal

**Nominal = Name**

**Ordinal = Order**

### 3. Homo vs hetero

**Homo = same**

**Hetero = different**

### 4. Ridge vs Lasso

**Ridge reduces.**

**Lasso leaves some at zero.**

### 5. Precision vs Recall

**Precision = predicted positives → were they right?**

**Recall = real positives → did I catch them?**

### 6. Bias vs Variance

**Bias = too simple.**

**Variance = too sensitive.**

### 7. Gradient descent

**Gradient points UP; minus makes it go DOWN.**

### 8. Leakage

**Train first, learn second, test last.**

---

# Exam Strategy for the 8 MCQs

When reading an MCQ, do not start by calculating. First identify the **concept keyword**.

```text
"labelled"       → supervised
"continuous"     → regression
"category"       → classification
"future"         → temporal leakage
"after outcome"  → target leakage
"scale"          → preprocessing leakage
"no order"       → nominal / one-hot
"order"          → ordinal
"funnel"         → heteroscedasticity
"high train + high test error" → high bias
"low train + high test error"  → high variance
"exactly zero"   → Lasso
"multicollinearity" → Ridge
"predicted positives" → Precision
"actual positives"    → Recall
"rare positive class" → PR-AUC / accuracy trap
"learning rate"  → gradient descent
```

Then check whether the option reverses a direction or swaps a denominator.

That is where many one-mark MCQs are won or lost.
