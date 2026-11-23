# We Can Map a Brain. Why Can't We Build One?

**The scientific and engineering gaps between a neural wiring diagram and a working digital brain.**

Suppose we could map every neuron and every synapse in a human brain tomorrow. Could we load that map into a computer, press Run, and recreate a mind?

Not yet. A wiring diagram can reveal which cells connect, but it does not contain every variable that determines how those cells behave, how they learn, or how they interact with a body. Even the conditions under which a simulation should count as a successful brain emulation remain contested.

The deeper problem is not simply that a brain contains many neurons. **We do not yet know which biological details are essential, which can be approximated, and how to validate a simulation against a living nervous system.**

In my open-source [Brain project](https://github.com/faheemkhaskheli9/Brain), I investigate sparse neural architectures, local learning, persistent memory, and embodied control. That work is exploratory engineering—not evidence that a complete digital brain or AGI has been achieved. The useful question is which missing mechanisms can be turned into falsifiable research experiments.

## First, define what a digital brain means

There are three different goals that are often conflated.

- **Brain-inspired AI:** A system that borrows ideas such as sparse connectivity, memory consolidation, local learning, and sensorimotor feedback. It may operate very differently from a biological brain.
- **Biological brain emulation:** A model that reproduces selected neural and behavioral dynamics of a particular nervous system within defined tolerances and conditions.
- **Individual-person emulation:** A much stronger proposal requiring a person's individual neural structure, functional state, acquired memories, and history, as well as a defensible definition of fidelity and identity.

A system can be intelligent without being biologically faithful. A simulation can reproduce neural responses without being generally intelligent. And human-like conversation is not evidence that a person's mind has been reproduced.

No scientific theorem establishes that digital brain emulation is impossible. The evidence supports a narrower conclusion: **today's data and models are insufficient to demonstrate a complete, validated human-brain emulation.**

## The progress is real: what we have already mapped

In 2024, FlyWire researchers published a neuron-level wiring map of an adult fruit-fly brain: **139,255 neurons and roughly 50 million annotated chemical synapses**. In another 2024 study, a connectome-constrained fly-brain model predicted particular sensorimotor circuit responses that researchers tested experimentally. This is evidence that wiring can help predict function—not proof of a complete emulated fly.

In the same year, researchers reconstructed a fragment of human temporal cortex just over **one cubic millimeter** in volume. It contained approximately **57,000 cells and 150 million synapses**. The imaging dataset was about **1.4 petabytes**. This was a fragment, not a human brain, and the cell count must not be mistaken for a neuron count.

In 2025, the MICrONS project combined mouse visual-cortex connectomics with functional measurements: a reconstruction containing around **200,000 cells and 523 million synapses**, alongside calcium-imaging recordings of around **75,000 neurons** in the living animal. These are different kinds of measurements, not continuous recordings of every reconstructed synapse.

In 2026, researchers reported a densely reconstructed adult fly **brain-and-ventral-nerve-cord** connectome, extending mapping toward motor-control pathways.

These achievements make the limitations clearer. **A structure map is a constraint on a model, not the model's complete state or behavior.**

## Gap 1: We still lack a complete, individualized structural map

The often-quoted figure of 86 billion neurons in the human brain is an estimate, with meaningful uncertainty. A complete, synapse-resolved map of one living human brain remains beyond current methods.

High-resolution electron microscopy typically uses prepared tissue. That means the same individual brain cannot be continuously observed while behaving, learning, and subsequently mapped at that resolution without major gaps between measurements.

What is needed: scalable connectomics, reliable long-range reconstruction, uncertainty estimates for inferred connections, and methods to align anatomical maps with functional recordings.

**Test:** Can the reconstructed circuit predict unseen synaptic and functional measurements, not merely fit the material from which its map was created?

## Gap 2: Wiring does not specify neural dynamics

A connection tells us that communication is possible. It does not fully specify synaptic strength, short-term facilitation or depression, membrane conductance, dendritic processing, or current biochemical state.

Two networks can have the same edges but respond differently to the same input because their effective weights or internal states differ. This is a problem of **identifiability**: multiple hidden models can agree with the observed anatomy while generating distinct predictions.

What is needed: recordings across timescales, joint estimation of structure and dynamics, causal perturbations, and uncertainty-calibrated predictions.

**Test:** Freeze the connectivity, vary plausible unmeasured parameters, and quantify variation in neural and behavioral predictions.

## Gap 3: We do not have a complete account of neural coding

Neural systems combine spike timing, firing rates, population activity, oscillations, and context-dependent representations. Different circuits may encode information differently.

Successfully decoding an experimental label from recorded activity does not establish a general translation between neural signals and memory, planning, perception, or intention.

What is needed: mechanistic models that predict unseen stimuli, states, and interventions rather than only classifying familiar recordings.

**Test:** Predict the neural response to a new stimulus or targeted perturbation before collecting the corresponding biological measurement.

## Gap 4: Artificial neurons are often too simple

Many artificial neural networks use a single activation per unit. Real neurons can integrate inputs across dendritic branches, express different channels, and operate across many timescales. The brain contains many cell classes and non-neuronal cells.

Astrocytes and other glia contribute to neuronal support, excitability, metabolism, synaptic function, development, and plasticity. Their roles differ across circuits; not every model needs the same biological detail.

What is needed: modular models that can add dendritic compartments, synaptic dynamics, neuromodulation, or glial processes when those details improve predictions.

**Test:** Compare a simple point-neuron baseline against more detailed alternatives using the same held-out experimental outcomes. Additional realism must earn its computational cost.

## Gap 5: We do not know the complete learning algorithm

Brains learn while acting. Their plasticity involves local changes, delayed modulatory signals, replay, structural remodeling, and stability mechanisms. No single accepted learning rule explains all forms of biological adaptation.

A fixed neural circuit can produce an accurate response but fail to learn. A trained AI agent may learn effectively while relying on a mechanism unlike that used by the biological circuit.

What is needed: explicitly competing hypotheses for spike-timing-dependent plasticity, eligibility traces, reinforcement signals, replay, and homeostatic regulation.

**Test:** Measure acquisition, reversal learning, retention, transfer, and recovery after disruption on independent tasks. Separate training gains from test-time leakage.

## Gap 6: Adult structure does not explain development

The mature brain results from development: growth, genetic regulation, sensory experience, activity-dependent refinement, and interactions among neurons and glia.

Copying the final network does not explain how it acquired its capabilities. Replaying development may be unnecessary for a useful AI system, but it could be essential for mechanistic explanations of some biological functions.

What is needed: developmental simulations whose predicted circuit changes can be tested under altered early experiences.

**Test:** Change a defined developmental condition and predict the later changes in anatomy and behavior.

## Gap 7: A brain cannot be fully understood in isolation from its body

The nervous system acts within an ongoing sensory–motor loop. Muscles, sensory organs, proprioception, body mechanics, and internal physiological signals affect what is learned and which actions succeed.

An agent that performs well against prerecorded observations may fail when its own actions change the environment. Physics-based fly-body models are useful here because they permit controlled tests of closed-loop behavior.

What is needed: embodied simulations that include sensing, actuation, time delays, physiological constraints, and realistic disturbances.

**Test:** Measure actual navigation, reaching, locomotion, and recovery under unseen changes—not only proxy reward.

## Gap 8: Persistent memory remains fragmented

Biological memory operates across short-term neural dynamics, synaptic changes, systems-level consolidation, replay, sleep, interference, and forgetting.

Putting examples in a vector database changes what information an AI application can retrieve. It does not, by itself, show that the model has acquired a skill, reorganized representations, or learned like a brain.

What is needed: explicit distinctions among episodic retrieval, skill acquisition, policy updates, consolidation, generalization, and adaptive forgetting.

**Test:** Remove the retrieval store after training and evaluate held-out skills. Measure whether earlier capabilities survive later learning.

## Gap 9: Computing scale is difficult, but more GPUs are not enough

Detailed simulations may need many coupled variables, fast time steps, communication across large sparse graphs, and large amounts of state. Storage, communication, energy, and numerical stability can be limiting even when arithmetic is available.

But a faster simulation of the wrong model is still the wrong model. A claim about biological fidelity requires measurements and validation, not just throughput.

What is needed: multiscale approaches that spend computation only where necessary, sparse execution, reproducible benchmarks, and explicit error budgets.

**Test:** Can a cheaper approximation retain the neural and behavioral predictions that matter for the scientific question?

## Gap 10: We do not have a universal validation standard

What would count as building a brain? Matching the anatomy? Fitting neural recordings? Learning new skills? Behaving like a person?

These are different claims. A model may fit known recordings but fail on new perturbations. Another may behave convincingly without reproducing neural mechanisms. Both can be useful; neither should be mislabeled.

What is needed: preregistered, held-out tests at anatomical, physiological, behavioral, and learning levels, with independent replication and published negative results.

**Test:** Require the model to predict neural responses, lesion effects, changing internal states, and adaptive behavior **before** those experiments are conducted.

## A runnable experiment: identical wiring, different outcomes

A short [Python companion experiment](https://github.com/faheemkhaskheli9/Articles/tree/main/examples/brain-model-gaps) demonstrates a narrow version of Gap 2.

It defines three artificial nodes—sensory, intermediate, and motor—with fixed recurrent connectivity. Two versions use **exactly the same directed edges and the same signs**, but different connection strengths. The same input produces different motor outputs.

This is a synthetic teaching example, **not** a brain simulation, empirical neuroscience result, or proof that connectomics is unhelpful. Its only demonstrated lesson is that graph topology alone does not uniquely determine network dynamics.

The repository includes setup instructions, tests, a VS Code launch configuration, and an import-friendly Medium edition of this article.

## A practical research roadmap

Instead of immediately attempting a model of tens of billions of neurons, I would use five evidence gates:

1. **Validate a small circuit.** Reproduce held-out neural time series and causal interventions from a published dataset.
2. **Add learning.** Compare different plasticity and memory mechanisms under fixed data and compute budgets.
3. **Add a body.** Test sensorimotor feedback under unseen disturbances, realistic delays, and altered physics.
4. **Integrate circuits.** Combine independently validated components, measure compounded error, and test interfaces.
5. **Demand replication.** Publish seeds, code, data provenance, ablations, uncertainty, failures, and predeclared success criteria.

For my [Brain research repository](https://github.com/faheemkhaskheli9/Brain), this suggests a simple priority: **predictive biological grounding before larger network size or more impressive animations**.

A small circuit that correctly predicts the effects of a new intervention is stronger scientific evidence than a million-node simulation that merely runs.

## Adversarial review: tempting claims that are wrong or overstated

- **“We just need more computing power.”** Compute matters, but missing dynamics, parameters, measurements, and validation matter too.
- **“A connectome is the entire brain.”** The graph is important but does not specify all functional states and plasticity.
- **“We must model every molecule.”** Not established. Necessary detail depends on the behavior being predicted; simple effective models may suffice.
- **“If an AI behaves like a human, it is a human brain emulation.”** Behavioral performance and biological fidelity are different criteria.
- **“We have not simulated meaningful biological circuits.”** False. Connectome-constrained fly models have generated experimentally tested circuit-level predictions.

The strongest counterargument is also the most useful: **brain-inspired intelligence might not require complete biological emulation**. The converse is equally important: achieving strong AI benchmarks does not validate a biological theory of the brain.

## Conclusion

We are not missing one magic algorithm. We face interconnected gaps in **measurement, hidden dynamics, neural computation, learning, development, embodiment, scaling, and validation**.

The next decisive step may not be adding neurons to a computer. It may be building a much smaller model that predicts what a real nervous system will do under a new stimulus, a new injury, or a new learning experience.

**Before asking whether a computer can run a human brain, we should ask whether our models can reliably predict how a small biological circuit will behave tomorrow.**

## Research sources

- [Dorkenwald et al., Neuronal wiring diagram of an adult brain, Nature (2024)](https://www.nature.com/articles/s41586-024-07558-y).
- [Shiu et al., A Drosophila computational brain model reveals sensorimotor processing, Nature (2024)](https://www.nature.com/articles/s41586-024-07763-9).
- [Shapson-Coe et al., A petavoxel fragment of human cerebral cortex reconstructed at nanoscale resolution, Science (2024)](https://pubmed.ncbi.nlm.nih.gov/38723085/).
- [MICrONS Consortium, Functional connectomics spanning multiple areas of mouse visual cortex, Nature (2025)](https://www.nature.com/articles/s41586-025-08790-w).
- [Distributed control circuits across a brain-and-cord connectome, Nature (2026)](https://www.nature.com/articles/s41586-026-10735-w).
- [Goriely, Eighty-six billion and counting: do we know the number of neurons in the human brain?, Brain (2025)](https://academic.oup.com/brain/article/148/3/689/7909879).
- [Neuron–Glial Interactions: Implications for Plasticity, Behavior, and Cognition (2024)](https://pmc.ncbi.nlm.nih.gov/articles/PMC11450529/).
- [Whole-body physics simulation of fruit fly locomotion, Nature (2025)](https://www.nature.com/articles/s41586-025-09029-4).
