# Module 2: Large Deviations

## 1. Intuition
CLT gives fluctuations (Gaussian). LDP gives rare events (Exponential decay).

## 2. Cramer Theorem
P(mean ~ x) ~ exp(-n * I(x))
I(x) is the Rate Function.
Rare events become impossible exponentially fast.

## 3. Rate Function I(x)
For coins (mean 0.5):
I(x) = x ln(2x) + (1-x) ln(2(1-x))
At x=0.5, I(x)=0.
At x=0.8, I(x)>0.
