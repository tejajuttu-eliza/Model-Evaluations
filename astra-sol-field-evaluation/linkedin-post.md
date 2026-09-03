GPT-6 Astra vs Sol: 64% fewer output tokens on exact reasoning. 41% more on staged coding.

At Eliza, we had early access to the model behind today's Astra launch. I tested that early build against GPT-5.6 Sol on synthetic tasks drawn from the work I do as an FDE: coding, constraint reasoning, source reconciliation and delivery decisions.

Three results from matched high-effort API tests:

• Exact constraint reasoning: 64.2% fewer output tokens. Three designs, each run twice per model; both passed all six.
• Staged repository changes: 40.7% more output tokens. Three workflows; both passed all three.
• A broader set of 15 objective API tasks: 1.7% more output tokens.

Across all effort settings in the expanded campaign, Sol passed 100/100 attempts; the early alpha passed 98/100.

The efficiency gain on exact reasoning is worth paying attention to. So is where it disappears.

I also tested through Codex and kept those results separate. The surrounding instructions, tools and cache behavior are part of what you're measuring there.

For FDE teams, the useful decision is which model and effort level produce work we can accept—with the least total cost and rework.

That's the standard I want us to keep at Eliza as models improve: test the workflow, preserve the failures, and measure the whole task.

The attached slides show the gains, reversals and API/Codex split. Output tokens include reasoning; these are early-access Vega-alpha measurements, not a retest of production Astra or a claim about actual dollar savings.

Thanks to the OpenAI team for the early access and opportunity to put it through its paces.
