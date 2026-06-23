# Shared categories and dropdown selections for SAT Tracker

TOPICS = [
    "Algebra", "Advanced Math", "Problem Solving & Data Analysis", "Geometry & Trigonometry",
    "Information & Ideas", "Craft & Structure", "Expression of Ideas", "Standard English Conventions"
]

QUESTION_TYPES = [
    "Math MCQ (Algebra)", "Math SPR (Algebra)", "Math MCQ (Advanced Math)", "Math SPR (Advanced Math)",
    "Math MCQ (Problem Solving & Data Analysis)", "Math SPR (Problem Solving & Data Analysis)",
    "Math MCQ (Geometry & Trigonometry)", "Math SPR (Geometry & Trigonometry)",
    "Reading MCQ (Central Ideas & Details)", "Reading MCQ (Command of Evidence - Textual)",
    "Reading MCQ (Command of Evidence - Quantitative)", "Reading MCQ (Inferences)",
    "Reading MCQ (Words in Context)", "Reading MCQ (Text Structure & Purpose)",
    "Reading MCQ (Cross-Text Connections)", "Writing MCQ (Transitions)",
    "Writing MCQ (Rhetorical Synthesis)", "Writing MCQ (Standard English Conventions)"
]

SUBTOPICS = [
    # Math - Algebra
    "Linear Equations (1 Variable)", "Linear Equations (2 Variables)", "Linear Functions & Graphs",
    "Systems of Linear Equations (No/Infinite Solutions)", "Systems of Linear Equations (Solving)",
    "Linear Inequalities (1 Variable)", "Linear Inequalities (2 Variables & Systems)",
    "Linear Equations (Word Problems)", "Linear Functions (Slope & Intercept Interpretations)",
    "Systems of Linear Equations (Word Problems)", "Graphing Linear Inequalities (Shaded Regions)",
    "Absolute Value Equations (Linear)", "Absolute Value Inequalities (Linear)",
    # Math - Advanced Math
    "Quadratic Equations (Solving by Factoring/Formula)", "Quadratic Functions & Parabolas (Vertex & Axis)",
    "Exponential Growth & Decay (Word Problems)", "Exponential Graphs & Percent Rates",
    "Polynomials & Factoring (Remainder Theorem)", "Radical & Rational Equations",
    "Systems of Non-Linear Equations", "Function Notation & Transformations",
    "Quadratic Equations (Discriminant & Number of Solutions)",
    "Quadratic Functions (Vertex Form vs Standard Form vs Factored Form)",
    "Exponents & Radicals (Rules of Exponents)", "Dividing Polynomials (Synthetic/Long Division)",
    "Rational Functions & Asymptotes", "Composite Functions (f(g(x)))",
    "Absolute Value Functions (Non-Linear)", "Graphing Nonlinear Functions (Intercepts & End Behavior)",
    # Math - Problem Solving & Data Analysis
    "Ratios, Rates, & Proportions", "Scale Drawings & Unit Conversions", "Percents & Percent Change",
    "Mean, Median, Mode & Range", "Standard Deviation & Spread", "Probability & Conditional Probability",
    "Scatterplots & Line of Best Fit", "Linear vs. Exponential Models", "Margin of Error & Confidence Intervals",
    "Observational Studies & Experiments", "Density & Complex Ratios",
    "Multi-step Percent Word Problems (e.g. interest, discounts, tax)",
    "Analyzing Distributions (Dot plots, Histograms, Box plots)", "Two-way Tables & Joint Frequency",
    "Evaluating Experimental Design (Random Assignment vs Selection)", "Estimating Population Parameters from Samples",
    "Outliers and their Effect on Mean & Median",
    # Math - Geometry & Trigonometry
    "Lines, Angles, & Transversals", "Congruent & Similar Triangles", "Right Triangle Trigonometry (SohCahToa)",
    "Sine-Cosine Complementary Relationship", "Arc Length & Sector Area in Circles",
    "Circle Theorems (Tangents, Inscribed Angles)", "Circle Equations in Coordinate Plane",
    "2D Area & Perimeter (Triangles/Polygons)", "3D Volume & Surface Area (Prisms/Cylinders)",
    "Special Right Triangles (30-60-90 & 45-45-90)", "Pythagorean Theorem & Distance Formula",
    "Radian-Degree Conversions", "Trigonometric Identities (e.g., sin^2 + cos^2 = 1)",
    "Coordinate Geometry: Midpoint & Slope", "Circle Equations: Completing the Square to Find Center/Radius",
    "Area and Volume Scaling (Effects of resizing dimensions)", "Angles in Polygons (Interior & Exterior Angles)",
    # Reading & Writing - Information & Ideas
    "Central Ideas & Themes", "Details & Direct Comprehension", "Command of Evidence (Textual)",
    "Command of Evidence (Quantitative)", "Inferences & Logical Completion", "Text Evidence Support & Refutation",
    "Summarizing Key Arguments", "Data Graphic/Table interpretation in Context", "Analyzing Logical Hypotheses in Passages",
    # Reading & Writing - Craft & Structure
    "Words in Context (Vocabulary Fill-in)", "Text Structure & Author's Purpose", "Cross-Text Connections",
    "Analyzing Tone, Style, & Perspective", "Part of Speech Context Clues",
    "Meaning of Words in Literary vs. Scientific Texts", "Relationship between Paired Passages",
    # Reading & Writing - Expression of Ideas
    "Rhetorical Synthesis (Bullet Notes)", "Transitions (Contrast)", "Transitions (Cause/Effect)",
    "Transitions (Addition/Example)", "Rhetorical Synthesis: Minimizing/Emphasizing Information",
    "Rhetorical Synthesis: Introducing a Topic/Book/Author", "Rhetorical Synthesis: Summarizing a Study or Trend",
    "Transitions (Time & Sequence)", "Transitions (Alternative/Similarity)",
    # Reading & Writing - Standard English Conventions
    "Punctuation (Commas/Semicolons/Colons/Dashes)", "Subject-Verb Agreement", "Pronoun-Antecedent Agreement",
    "Verb Tense, Mood, & Aspects", "Parallel Structure (Lists/Comparisons)", "Dangling & Misplaced Modifiers",
    "Noun Clauses (Appositives)", "Idioms & Prepositional Idioms", "Sentence Structure: Run-on Sentences & Fragments",
    "Sentence Structure: Comma Splices & Conjunctions", "Plural vs. Possessive Nouns (e.g., cats' vs cat's)",
    "Pronoun Case (Subjective, Objective, Possessive)",
    "Ambiguous Pronouns (e.g., this, that, it, they without clear reference)",
    "Relative Pronouns (Who vs Whom, Which vs That)", "Semicolons vs Colons for Lists and Explanations",
    "Dashes vs Parentheses for Parenthetical Elements",
    "Correlative Conjunctions (Either/Or, Neither/Nor, Not Only/But Also)"
]

ERROR_TYPES = [
    "Knowledge Gap (Concept Untrained)", "Knowledge Gap (Forgotten Details)", "Formula Misrecall / Incorrect Usage",
    "Grammar Rule Misrecall / Confusion", "Desmos Over-Reliance (Inefficient Method)", "Desmos Input Error (Syntax / Typo)",
    "Desmos Window / Scale Misinterpretation", "Desmos Mode Error (Radians vs. Degrees)", "Careless Arithmetic (Simple Addition/Subtraction)",
    "Careless Arithmetic (Sign Error +/-)", "Careless Arithmetic (Multiplication/Division)", "Algebraic Manipulation Slip (Distribution/Signs)",
    "Exponent / Power Rule Error", "Misread Question Constraint (e.g. integer vs constant)", "Solved for Wrong Variable (e.g. x instead of 2x)",
    "Misread Units (e.g. hours vs. minutes)", "Misread Scale / Axis Labels", "Trap Answer distractor choice",
    "Second-Guessing (Changed correct to incorrect)", "Overthinking (Read too deep into passage)", "Underthinking (Skimmed too quickly / Rushed)",
    "Pacing: spent too long on one question", "Time Pressure: rushed choice at the end", "Educated Guess (Eliminated 2 options)",
    "Blind Guessing", "Reading: Text Evidence Misinterpretation", "Reading: Data Table / Graph Misread",
    "Reading: Vocabulary definition misunderstanding", "Reading: Main idea vs Supporting detail confusion",
    "Reading: Cross-text perspective misattribution", "Reading: Tone / Attitude misinterpretation",
    "Reading: Transition logic choice error", "Reading: Rhetorical synthesis goal mismatch",
    "Writing: Sentence structure error (Run-on/Fragment)", "Writing: Punctuation misinterpretation",
    "Scratchpad / Copy-paste transcription error", "Fatigue / Lack of Concentration", "Process Error / Methodology Slip"
]

ROOT_CAUSES = [
    "Concept was never learned or studied", "Concept was studied but not practiced enough", "Forgot specific math formula or identity",
    "Forgot specific grammar/punctuation rule", "Misread keyword in question (e.g., 'not', 'except', 'must')",
    "Ignored constraint (e.g., 'x > 0', 'integer', 'positive')", "Solved for x but question asked for another expression (e.g., y, 2x, x+3)",
    "Basic arithmetic slip (addition, subtraction, multiplication, division)", "Positive/negative sign flip during algebraic step",
    "Fraction or decimal calculation/conversion error", "Exponent or radical simplification rule applied incorrectly",
    "Incorrect factoring or distribution of algebraic terms", "Desmos typo: entered numbers or variables incorrectly",
    "Desmos setting: calculator was in wrong angle mode (Radian/Degree)", "Desmos window: did not zoom out far enough to see intersections",
    "Desmos reading: clicked wrong point or misread coordinate value", "Did not write down intermediate steps (tried to do it all mentally)",
    "Scratchpad work was too messy to follow, causing copy error", "Fell for a common SAT distractor answer trap",
    "Eliminated the correct answer choice too early", "Overthought the passage (imported external assumptions)",
    "Under-read the passage (missed transition word or tone shift)", "Confused the perspective of Author 1 vs Author 2",
    "Misread numerical values or labels in data table/graph", "Misidentified the specific goal of the rhetorical synthesis bullets",
    "Confused logical transitions (e.g., 'however' vs 'furthermore')", "Misidentified subject or verb in complex sentence structure",
    "Ambiguous pronoun reference or incorrect pronoun case", "Misplaced apostrophe for singular vs plural possessives",
    "Dangling modifier describing the wrong noun", "Lack of parallel structure in list or comparison",
    "Semicolon/colon punctuation rule misapplied", "Spent too much time on a difficult question (Sunk Cost Fallacy)",
    "Panicked due to time pressure in the second module", "Rushed through easy questions and made silly slips",
    "Second-guessed original correct choice and changed it", "Mental fatigue or brain fog near the end of a module",
    "Unfamiliar vocabulary word in the context passage", "Assumed incorrect definition for a vocabulary word",
    "Did not plug in answers or test numbers to double check"
]

FIX_STRATEGIES = [
    "Study/Review the core mathematical concept from scratch", "Memorize formula/rule (create physical or digital flashcard)",
    "Review standard English grammar and punctuation rules", "Add word and definition to personal SAT vocabulary log",
    "Complete 20+ practice questions on this specific subtopic", "Do a timed drill (10-15 questions) for this domain",
    "Do an untimed drill to focus on step-by-step accuracy", "Practice solving this algebraic problem type without Desmos",
    "Practice Desmos shortcuts (regression, graphing intersections, systems)", "Verify Desmos settings (Radian/Degree mode) before starting",
    "Practice grid-zoom calibration in Desmos for graphs", "Practice writing clear, organized scratchpad steps",
    "Implement 'Read the Question Twice' rule for word problems", "Underline/circle the final variable or expression being asked for",
    "Write down all constraints explicitly before solving", "Practice the Process of Elimination: write down why wrong choices are wrong",
    "Read passages with focus on main idea/tone, ignoring minor details", "Annotate the passage briefly to track arguments",
    "Read all four answer choices fully before selecting one", "Set a strict 90-second limit per question (flag and skip if exceeded)",
    "Retake this exact question in 7 days (spaced repetition)", "Retake this exact question in 14 days",
    "Explain the solution out loud to verify understanding (Feynman Technique)", "Backsolve by plugging in answer choices",
    "Test algebraic equivalence by plugging in simple numbers (0, 1, -1)", "Double-check units and scale conversions (e.g. minutes to hours)",
    "Review common trap answer patterns in prep book / online resources", "Take a 30-second breathing break between modules to reset focus",
    "Do a full-length practice section to build mental endurance", "Compare my solution step-by-step with the official explanation",
    "Analyze why the trap answer was tempting and how to spot it next time", "Verify that my selected choice matches all constraints in the question"
]
