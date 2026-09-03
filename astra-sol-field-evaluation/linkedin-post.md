We got early access to OpenAI's GPT-6 Astra (codenamed Vega-alpha) at Eliza.

18.4 million tracked tokens across Astra and Sol later, here's what stood out.

I compared it with GPT-5.6 Sol through both the API and Codex, at matched reasoning effort. The slides focus on coding, constraint reasoning and repository workflows.

Three things I'm taking away:

→ The token win is real in some workloads. On three exact constraint-reasoning designs, run twice per model at high effort, the alpha used 64.2% fewer output tokens. Both models passed all six. That's a result I'm excited to test on more unseen problems.

→ Coding needs a wider lens. The savings didn't carry over to staged repository work, where the alpha used more output. Fewer tokens also didn't consistently mean faster completion. I want to measure how much review and repair the finished work needs.

→ Delegation is the behavior I'm most curious about. In Codex, Astra seems more willing to split scoped work across subagents. Colleagues are noticing this too. The next question is whether it reduces steering and rework on longer jobs; our benchmark didn't score that.

I kept API and Codex results separate, and kept the failures: the expanded campaign finished at 100/100 passes for Sol and 98/100 for the alpha.

The PDF has the charts, tradeoffs and test boundaries. These are early-access measurements, not a retest of released Astra. The 18.4M total counts input and output across both models, including cached context. Output includes reasoning.

Thanks to the OpenAI team, Syed A. and Matt Lewis for the early access.

The evaluation artifacts and methodology are on GitHub. Link in the comments.

Where are you seeing the biggest difference versus Sol—planning, implementation or longer tasks? And is more delegation actually saving you time?
