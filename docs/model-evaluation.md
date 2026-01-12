# Model Evaluation (Representative)

This document summarizes how a sepsis risk model can be evaluated in a clinical analytics pipeline.
The purpose is to document **evaluation methodology and engineering assumptions**, not to claim a
production-certified medical model.

> This system is intended for **decision support** and pipeline demonstration only.  
> It is not a diagnostic tool and is not validated for clinical deployment.

---

## What Was Evaluated

The scoring system produces a risk score per ICU observation timestamp using:
- validated vitals and lab inputs
- derived physiological signals (e.g., MAP, shock index)
- interpretable flags for explanation

In a production setting, the scoring layer would typically wrap a trained model (logistic regression,
gradient boosting, or neural network) and apply calibration + thresholds.

---

## Data Assumptions (Non-PHI)

This repository does not include patient data. Evaluation is described at a **method level** only.

A realistic evaluation setup would use one of:
- a de-identified institutional dataset under governance controls, or
- a public ICU dataset (e.g., MIMIC-style data) with appropriate preprocessing

Key requirement: labels must be defined consistently (e.g., sepsis onset window), and leakage must be avoided.

---

## Split Strategy

Recommended split strategy to avoid optimistic bias:
- split by **patient_id** (not by rows) to prevent information leakage
- keep temporal order within admissions
- evaluate on a held-out set that reflects ICU distribution shifts (units, acuity, missingness patterns)

---

## Metrics

Primary metric:
- **AUC-ROC** to measure ranking quality across thresholds

Additional metrics recommended in clinical workflows:
- precision/recall at alert thresholds
- sensitivity for early warning windows
- calibration metrics (reliability curve, Brier score)
- alert burden (alerts per patient-day)

---

## Representative Performance

In prior implementations of similar ICU risk scoring pipelines, an AUC-ROC in the range of **~0.87**
can be achieved depending on:
- label definition (onset window)
- feature set and missingness handling
- patient population and unit type
- evaluation split strategy

This repository does **not** ship training code or datasets, so the numeric value above should be treated
as representative context rather than a reproducible benchmark from this codebase.

---

## How This Repo Supports Evaluation

Even without training artifacts, this repository supports evaluation-oriented engineering by providing:
- deterministic preprocessing and validation
- explicit feature contracts and derived signals
- transparent scoring thresholds and explainability hooks
- an end-to-end runnable pipeline using synthetic inputs (`examples/`)

These components are the foundation required to run real evaluations in governed environments.
