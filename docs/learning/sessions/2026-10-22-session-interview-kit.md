# Interview Kit for Arabic NLP / RAG hiring

### Context

Repo: Burhan (Arabic Islamic QA). Session task was NOT code work: building a reusable hiring kit to evaluate an Arabic NLP / RAG candidate (public GitHub + Hugging Face profile: Athar, Baligh, OCR/KYC, Egyptian function-calling). Deliverable lives outside the repo at C:\Users\Kandil\Downloads\artifacts (2)\.

### Explanation

Eight files produced, in Arabic for the interviewer and English for the candidate-facing text:
1) README.md - index, philosophy, thresholds, live-scoring rubric.
2) hiring_plan.md - 7 working-day path (outreach, 45-min call, paid 3-4h task, review call, reference, decision), EN outreach/offer/decline templates, payment policy, failure handling per stage, ~8 hours of team time per candidate.
3) candidate_brief.md - what the public profile proves and does not prove, the four questions the call must answer, 45-minute GitHub review checklist, strong signals, red flags, role tracks.
4) interview_guide.md - 45-minute script, 0-5 live scoring scale, question blocks (RAG, OCR, LLM/fine-tuning, production), adaptive question tree, red flags, code-review questions, project-specific appendix.
5) interview_scorecard.csv - 15 weighted rows on a 50-point scale split CALL 20 / TASK 18 / REVIEW 6 / REFERENCE 6, each row with score 0-5, evidence and notes.
6) practical_task.md - candidate brief for an Arabic RAG Evaluation Sprint (corpus assembly, normalization, chunking, hybrid retrieval, Recall@5 + MRR, citation correctness, EVALUATION.md), plus interviewer-only hidden-holdout design and 45-minute review checklist.
7) reference_check.md - 10 questions, consent and legal guardrails, recording template, decision impact table.
8) decision_template.md - 50-point decision form, evidence requirement, conditions per role track, calibration rules.
Decision thresholds: 42-50 Strong Hire, 35-41 Hire, 28-34 No Hire for this role, below 28 Reject.

### Alternatives

Kept a single 40-point technical scorecard from the earlier draft, but rejected it because the final decision must span four stages; the 50-point cross-stage scale captures that. Rejected a generic take-home in favour of one that forces measurement. Rejected a free take-home, since unpaid production-grade work filters out strong candidates and creates a wrong expectation. Kept the kit outside the Burhan repo so hiring material does not pollute the product git tree.

### Rationale (Why this?)

The user decided the interview is for verification, not rejection or hiring from the profile. That required separating the profile screen from the decision, making every stage produce evidence rather than impressions, and binding each score to a written evidence field. The 50-point scale matches the cross-stage path (call, paid task, review, reference) that the user actually chose. Storing it in Downloads keeps the Burhan repository clean.

### Exercises

1. Run the 45-minute call against the guide and check that every scored row got an evidence note. 2. Build the hidden holdout (10 questions) before sending the task, then compare the candidate's reported Recall@5 against it. 3. Reuse the kit unchanged for the next candidate and confirm the scorecard still discriminates. 4. Tighten the task rubric if the first review round produces indistinguishable scores.

### Next Steps

Send the outreach message from hiring_plan.md. Prepare the hidden holdout corpus before the take-home goes out. If the role is Senior rather than applied, the reference check must carry the scale evidence since the profile alone cannot decide it.

---

## Interview practice: current project answer and rehearsal plan (2026-10-22)

### Context

Same session as the Interview Kit build (Burhan repo, no source code changed). The user asked how to answer "tell me about your current project" when they are the candidate, so the kit gained two answer-focused files.

### Explanation

Added two files to C:\Users\Kandil\Downloads\artifacts (2)\:
- current_project.md - verified answer script for the current project (Burhan): 60-second version in Arabic and English, 2-minute version (problem, data, architecture, decisions, measurement, failure, next), 10-minute walkthrough table, a table of numbers measured from the repo rather than from docs/README.md (golden set 20 items with 15 strictly scored, 4 eval sets totalling 2140, dense P@5 0.853 / R@10 1.000 / MRR 0.942 against keyword+rerank 0.653 / 0.830 / 0.911, routing 0.75 to 1.00, islamic_history topic hit rate 0.0, 10 collection agents, 12 verification checks, 5 tools, 7 route modules, 240 source files, 45 test files, 654 commits), expected follow-up questions with answers, and a traps list.
- interview_practice.md - candidate-side practice package: what an interviewer is actually scoring, the 60-90 second answer, the 5-minute structure, 10 likely follow-ups with answers, the three projects as case studies (Burhan, Athar 15-stage pipeline with checkpoints/DLQ/ES+Qdrant+FAISS fallback, Baligh Qwen3-1.7B with an 8-category Sunni benchmark and 283 tests at 82.39 percent coverage), a 3-session rehearsal plan with pass criteria, and a one-page cheat sheet.

### Rationale (Why this?)

The user is preparing to be the candidate, not only the interviewer, so the answer had to be built from measurements that exist in the repos rather than from the older README claims. Stating the weak collection first buys more credibility than listing features, and stating sample size with every number is the single highest-leverage habit in a technical interview.

### Next Steps

Rehearse the 30-second version until it is recallable, then the 90-second version with a recording. If an interviewer asks for Athar retrieval numbers, run a golden-set evaluation first - the pipeline is verified but published recall results are not. Consider updating docs/README.md, whose agent, file, and coverage numbers are stale.

---
