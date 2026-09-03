We got early access to OpenAI's GPT-6 Astra (codenamed Vega-alpha) at Eliza.

18.4 million tracked tokens across Astra and Sol later, here's what has me excited.

I compared it with GPT-5.6 Sol through both the API and Codex, at matched reasoning effort. A few highlights:

→ Less output to solve the same reasoning problems. On three exact constraint-reasoning designs, run twice per model at high effort, Astra used 64.2% fewer output tokens. Each model passed all six runs.

→ Promising efficiency in Codex too. In small high-effort tests, Astra used 16.2% fewer output tokens on coding and 25.8% fewer on reasoning. Both models passed all three tasks in each group.

→ More natural delegation. In day-to-day Codex use, Astra seems more willing to split scoped work across subagents. Colleagues are noticing this too. That's a practitioner observation; next I want to measure whether it reduces steering and rework on longer jobs.

The exciting part for me is completing useful work with fewer output tokens. I want to see how far that carries into more demanding workflows.

The PDF shows these selected early-access highlights, including the long-context results. API and Codex are reported separately. Output includes reasoning; the 18.4M total includes input and output across both models, including cached context. These runs predate the released Astra version.

Thanks to the OpenAI team, Syed Ahmed and Matt Lewis for the early access.

The full results, methodology and supporting artifacts are on GitHub. Link in the comments.

Where are you seeing the biggest difference versus Sol: planning, coding or longer tasks? Is delegation changing how you work with it?
