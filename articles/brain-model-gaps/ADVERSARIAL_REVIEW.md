# Adversarial review: We Can Map a Brain. Why Can't We Build One?

**Date:** 2026-11-24
**Scope:** Claims, primary sources, counterevidence, conceptual necessity, experiment, research roadmap, and publication.
**Verdict:** Publish with corrections. This is a literature-grounded engineering analysis, not a biological-emulation experiment.

## Executive assessment

**Initial editorial rating: 7/10.** The central claim—that a fully validated human brain emulation has not been established—is defensible. Its first version, however, risks making ten missing areas sound like ten universal prerequisites. It also underweights successful partial biological emulations and overstates what a toy network demonstrates.

## High-priority findings and disposition

### Critical: not every gap blocks every goal — Corrected

The original list mixed brain-inspired AI, local neural prediction, whole-organism modeling, mechanistic emulation, and emulation of a particular person. A given mechanism is necessary only to the extent that its absence causes prediction errors for a clearly defined goal.

**Fix:** Add a goal-specific section distinguishing five targets. Avoid claiming all ten gaps must be solved for useful intelligence.

### High: strong counterevidence was missing — Corrected

The 2024 fly connectome-constrained model (Shiu et al.) made experimentally testable predictions with simplified dynamics, connectivity weights and neurotransmitter predictions. A new *Nature* paper published on **October 28, 2026** (Pugliese et al.) used fly nerve-cord connectome simulations to isolate a candidate three-interneuron rhythm-generating walking circuit and experimentally tested a prediction about a separate descending input.

**Fix:** Add both studies and clarify that success at the circuit level is not complete brain emulation.

**Sources:** https://www.nature.com/articles/s41586-024-07763-9 ; https://www.nature.com/articles/s41586-026-11195-y

### High: the toy is not evidence about biological inferability — Partially mitigated

Same graph plus different gains giving different outputs is a basic algebraic fact. It is not a demonstration of the actual unknowns in a biological brain.

**Fix:** Add zero-stimulus observational equivalence as an intentionally trivial example of why measurement design matters, and add a regression test.

**Residual limitation:** No biological data, no fitted parameters, no spiking, no learning, no physiology, no embodied behavior. The demonstration cannot tell us whether real neural dynamics are identifiable from sufficiently informative data.

### High: no clear study baselines or kill criteria — Corrected

A claim of progress must beat an activity-only predictor and a simpler connectome-constrained model on frozen, held-out interventions. It must not rely on qualitative visual resemblance.

**Fix:** Add reproducible starting datasets/code, simple and richer model baselines, held-out conditions, uncertainty, runtime, memory, and failure criteria.

**Residual limitation:** No independent circuit prediction has been replicated in the Articles repo.

### Medium: external-memory removal is not a definition of learning — Corrected

A full agent can adapt through persistent external memory without changing base-model weights. Removal of the store is a causal ablation, not a universal proof of failed learning.

**Fix:** Test complete-system retention and transfer, alongside targeted retrieval ablations and false-memory sensitivity.

### Medium: embodiment was framed too absolutely — Corrected

For whole-organism behavior, body mechanics and sensory feedback are central. Isolated circuit-response modeling does not always require a physics simulation.

**Fix:** Scope the need to whole-organism tasks and note that the 2025 fly-body simulator's controller was trained using reinforcement learning, not a reconstructed complete connectome.

**Source:** https://www.nature.com/articles/s41586-025-09029-4

### Medium: identifiability versus observability — Corrected

Lack of an inferred parameter does not prove that parameter could never be identified. Some data-collection protocols fail to excite the relevant states; designed interventions may distinguish candidate models.

**Fix:** Explain the difference and demonstrate a trivially uninformative stimulus in the toy.

### Medium: source-count precision and uncertainty — Corrected

- FlyWire: **139,255 neurons and 54.5 million chemical synapses**. https://www.nature.com/articles/s41586-024-07558-y
- 2024 human cortex fragment: **approximately 57,000 cells**, not specifically neurons; approximately 150 million synapses and 1.4 PB. https://pubmed.ncbi.nlm.nih.gov/38723085/
- MICrONS: **over 200,000 reconstructed cells**, approximately half a billion automatically detected synapses, around 75,000 imaged neurons; segmentation and matching have errors. https://pmc.ncbi.nlm.nih.gov/articles/PMC11981939/
- 2026 fly brain-and-cord connectome: genuine anatomical reconstruction, not complete functional emulation. https://www.nature.com/articles/s41586-026-10735-w
- **Around 86 billion human neurons** is a useful estimate with biological variation and methodological uncertainties, not a fixed exact count. Debate: https://academic.oup.com/brain/article/148/3/689/7909879 and https://academic.oup.com/brain/article/148/5/e37/8003626

## Strongest unresolved objections

1. **A faithful computational model might need far fewer details than a biological replica.** Correct. The sufficient level is prediction-dependent, not known a priori.
2. **Local validated models already work.** Correct. Avoid describing partial successes as failures.
3. **Modern ML could infer effective dynamics directly without describing every cell process.** Possible. Compare data-driven and biological baselines under matched constraints.
4. **A structural graph is not all-or-nothing information.** Correct. Synapse count, transmitter type and inferred cell type add useful constraints even if they do not uniquely fix activity.
5. **A model's behavior may depend on unobserved internal state or history.** Correct. Report uncertainty and detect when data are insufficient.
6. **Human-person emulation raises identity questions outside ordinary ML metrics.** Correct. Do not imply they are resolved by passing behavior tests.

## What evidence could falsify this perspective?

- A cross-organism or cross-circuit reconstruction method that predicts new neural and behavioral interventions with only measured connectivity and a small general parameterization.
- Empirical demonstrations that more detailed biology adds no out-of-distribution predictive accuracy for a specified emulation task.
- A validated pathway from structural measurements to faithful real-time dynamics at the claimed scale, with replicated uncertainty bounds.

These outcomes would narrow or eliminate practical barriers without changing the trivial fact that network parameters affect outputs.

## Reproduction and publication gate

- [x] Separate task-specific goals and necessary biological fidelity.
- [x] Cite both positive and negative evidence.
- [x] Check primary-source figures and limitations.
- [x] Qualify the toy's inferential scope.
- [x] Propose baselines, held-out interventions, and stop conditions.
- [x] Add a targeted synthetic test for uninformative observations.
- [ ] Independently reproduce a published biological circuit: **not done**.
- [ ] Observe Medium's actual imported draft on every client: static HTML checks cannot guarantee its appearance.

## Final recommendation

Publish the corrected analysis. Do **not** describe it as a result in neuroscience, proof that digital brains are impossible, evidence of AGI, or evidence that consciousness could be reproduced.
