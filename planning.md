# TakeMeter Project Planning

This document outlines the design, label schema, collection plan, and evaluation metrics for **TakeMeter**: a classifier evaluating discourse quality in the `r/soccer` community.

---

## 1. Community Selection
*   **Chosen Community:** `r/soccer` (focusing on the 2026 FIFA World Cup and international football discourse).
*   **Why Chosen & Fit for Classification:** The community is massive, global, and highly active, making it a goldmine for text-based classification. Football discourse is notoriously multi-layered: it features deep tactical breakdowns (discussing formations, xG, and player spacing), highly reactionary emotional venting (referee complaints, match celebration, player critiques), and socio-cultural debates (broadcast logistics, player family ethics, national identity). This variety creates a high-contrast environment where a classifier is needed to help users separate signal (high-quality analysis) from noise (knee-jerk banter).

---

## 2. Labels & Definitions

### Label 1: `analytical_and_fact_based`
*   **Sentence Definition:** A comment that provides objective facts, tactical play/formation breakdowns, financial transfer metrics, or structured comparisons of player/manager systems.
*   **Example 1:** *"Dutch medium Telegraaf reports fee at €3.5M"*
*   **Example 2:** *"He's an excellent player but idk about 'one of the most complete in the world' - he's never going to be a tempo setter or controller like prime Rodri (or Kroos himself for that matter) who can dictate an entire game..."*

### Label 2: `subjective_opinion_and_banter`
*   **Sentence Definition:** A comment expressing personal feelings, immediate emotional reactions, jokes, memes, insults, or venting about matches, teams, or players.
*   **Example 1:** *"I hate time wasting and can’t respect anybody that does that bullshit."*
*   **Example 2:** *"Couldn't have happened to a more fitting person. Dude is a dirty, over exaggerating clown (cheat)."*

### Label 3: `social_and_cultural_meta`
*   **Sentence Definition:** A comment discussing broader topics surrounding the sport rather than the football matches themselves, such as media broadcasting, cultural/social values, fanbase demographics, or players' personal lives.
*   **Example 1:** *"I do agree. I think sometimes people try to hard to be inclusive that they end up in the next extreme. A lot of nations and people do like to share our culture. Not all do, but that's why blanket statements on cultural appropriation don't work"*
*   **Example 2:** *"You know what. I disagree. It used to be that way but over the past 5 years or so most people I meet now have a team they like in the prem..."*

---

## 3. Hard Edge Cases & Boundary Rules

*   **Case A: The "Decorated" Rant (Tactical salt)**
    *   *Ambiguity:* A user writes an analytical critique of a team's shape but wraps it in heavy emotional venting or toxic remarks (e.g. *"Our manager is an absolute clown for playing a low block against a mid-table side"*).
    *   *Resolution:* If the comment refers to a specific, verifiable tactical setup (e.g. "low block", "double pivot", "4-3-3"), it will be classified as `analytical_and_fact_based` despite the emotional wrapper. If it is general insults without tactical substance, it falls under `subjective_opinion_and_banter`.
*   **Case B: Sarcastic/Ironic Analysis**
    *   *Ambiguity:* A user uses detailed technical terms to ironically hype a poor player (e.g. *"Clearly he is the ultimate inverted wing-back who dictates our transitions"*).
    *   *Resolution:* We label this as `subjective_opinion_and_banter`. The model must recognize that the underlying intent is banter.
*   **Case C: On-Pitch Impact of Off-Pitch News**
    *   *Ambiguity:* A player leaves the World Cup squad due to the birth of a child (personal meta-discussion), but a user debates how this will force the team to change their starting lineup (on-pitch tactics).
    *   *Resolution:* If the core of the comment details the team lineup, tactics, or match implications, it is `analytical_and_fact_based`. If it debates the ethics or personal nature of the player's choice, it is `social_and_cultural_meta`.

---

## 4. Data Collection Plan
*   **Data Source:** Reddit's live RSS comment stream (`https://www.reddit.com/r/soccer/comments.rss`).
*   **Target Sample Size:** 226 unique comments have been scraped and saved in `data/raw_comments.json`. We will annotate these to yield a final training set of ~200+ samples.
*   **Handling Underrepresented Labels:** Factual analysis and meta-discussion are naturally rarer than raw banter. If any label has fewer than 40 annotated examples after the first pass:
    1.  We will run a keyword-filtering script on new RSS fetches (e.g. searching for "formation", "stats", "tactical" for analysis; or "broadcast", "journalist", "ethics" for meta).
    2.  We will target specialized threads (like "Tactics Tuesdays" or "Daily Discussion" stickies) to boost representation.

### Limitations & Drawbacks of RSS Scraping
*   **Strict Rate Limits:** Reddit limits unauthenticated RSS feeds to roughly 1 request per minute, preventing fast or high-volume multithreaded fetching.
*   **No Historical Access:** RSS only returns the 25 most recent posts or comments at the time of request. We cannot target specific games or query historical discussion threads.
*   **Loss of Thread Context:** Comments are served standalone without the parent comments they reply to, making generic statements (e.g., *"I agree," "No way"* ) hard to categorize.
*   **Selection Bias:** The dataset is a narrow time-slice snapshot representing whatever matches or news are active at the exact hour of scraping.

### Context Loss Mitigation Strategies
1.  **Programmatic Filtering:** The scraper auto-discards comments containing fewer than 10 characters or consisting only of simple generic agreement phrases.
2.  **Fallback Categorization:** Standalone assertions or emotional disagreements without factual backing (e.g., *"No way that was clean"*) are systematically classified as `subjective_opinion_and_banter` by default.
3.  **Buffer and Skip Option:** We scraped 226 comments (a 26-comment buffer above the required 200). Truly unclassifiable comments will be discarded via the `[s] -> Skip` action in the annotation tool.
4.  **Permalink Verification:** The CLI tool preserves and displays the permalink for each comment, enabling the annotator to paste the URL in a browser and check parent threads if context is critical.


---

## 5. Evaluation Metrics
*   **Macro-Averaged F1-Score:** Since the dataset will naturally skew toward `subjective_opinion_and_banter` (which represents the majority of Reddit comments), standard accuracy is highly deceptive. Macro-averaged F1-score treats all classes equally, ensuring the model performs well on the rarer, higher-quality categories like analysis.
*   **Precision for `analytical_and_fact_based`:** If this classifier is deployed to filter or highlight high-quality takes for a user interface, False Positives (labeling noise/banter as analysis) must be minimized. High precision on this class is paramount.
*   **Confusion Matrix:** We will inspect the confusion matrix during training to identify where boundaries blur (e.g., determining if the model struggles to differentiate between "decorated" rants and pure subjective opinions).

---

## 6. Definition of Success
*   **Success Metric:** Achieving a **Macro F1-Score of >= 0.75** on the validation set.
*   **Real-World Utility:** In a live community tool (e.g., a browser extension that highlights tactical summaries or auto-filters banter), a 75% macro F1-score is "good enough" to significantly clean up thread feeds. It acts as an automated filter that aggregates high-quality tactical comments or segments off-topic debates, saving users substantial scrolling time without needing absolute perfection.

---

## 7. AI Tool Plan

This section outlines how AI tools will be leveraged throughout the TakeMeter workflow to improve dataset quality, accelerate annotation, and analyze model failures.

### 1. Label Stress-Testing
*   **Methodology:** We will feed our current label definitions and edge case guidelines to the AI. We will instruct it to generate 5–10 synthetic boundary comments that sit precisely on the fence between `analytical_and_fact_based` and `subjective_opinion_and_banter`, or between `analytical_and_fact_based` and `social_and_cultural_meta`.
*   **Stress-Test Assessment:** If we find ourselves unable to confidently assign any AI-generated synthetic comment to exactly one label, we will refine our boundary rules and update the `planning.md` guidelines before starting the annotation phase.

### 2. Annotation Assistance
*   **Pre-labeling Approach:** Yes, we will use Gemini 3.5 Flash to generate preliminary labels for our raw dataset of 226 comments.
*   **Tracking & Verification:** 
    *   We will introduce a boolean column `pre_labeled` (True/False) in `data/labeled_comments.csv` to track which rows were initially suggested by the LLM.
    *   A human annotator will review 100% of these suggestions using `annotate.py`. The CLI tool will show the AI's suggested label, and the human will either confirm it (by pressing Enter) or override it. Only the final human-verified label will be exported for model training.

### 3. Failure Analysis
*   **Pattern Identification:** After fine-tuning, we will collect all misclassified instances (validation/test examples where the model prediction disagrees with the human ground truth). We will format these as a structured markdown table and prompt the AI to identify semantic or structural patterns (e.g., *Is the model consistently confused by sarcasm? Does it fail on short, single-word tactical labels? Is it misclassifying rants containing positional numbers?*).
*   **Manual Verification:** We will check the AI's hypothesized failure modes against the raw data by reviewing specific examples of the flagged pattern. If the pattern is real, we will document it in our final evaluation report and suggest specific adjustments (e.g. data augmentation or rule adjustments) to resolve it.

