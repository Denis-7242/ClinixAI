# ClinixAI Mathematical Model

For a disease \(D\), the illustrative symptom weight \(w_i\) is interpreted as
\(\Pr(S_i=\text{present}\mid D)\). It is clipped to
\([\epsilon,1-\epsilon]\), with default \(\epsilon=0.01\). A symptom not listed
for a disease has a documented illustrative background probability of 0.05.
This is Laplace-style smoothing.

The log posterior is:

\[
\log P(D\mid S) \propto \log P(D) +
\sum_{i:\text{present}}\log P(S_i\mid D)
+ \sum_{i:\text{absent}}\log(1-P(S_i\mid D)).
\]

Unknown answers add no term. Posterior probabilities are normalized with
log-sum-exp. The per-symptom contribution is a log-likelihood ratio compared
with the 0.05 background probability.

## Worked example

For a two-disease example with equal priors, a fever weight of 0.75 and a
background 0.05, and only fever present:

- Disease A log unnormalized score: \(\log(0.5)+\log(0.75)\)
- Disease B log unnormalized score: \(\log(0.5)+\log(0.05)\)
- Relative weight: \(0.75/0.05=15\)
- Normalized posterior for A: \(15/(15+1)=0.9375\), B: \(0.0625\).

## Limitations

This is a closed-world model: it ranks only conditions present in the bundled
knowledge base. Priors and weights are illustrative and not clinically
calibrated. It does not establish a diagnosis.
