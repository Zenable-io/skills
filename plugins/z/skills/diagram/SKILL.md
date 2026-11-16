---
name: diagram
description: Explain a flow, design, or change with the smallest visual that makes the point — a Mermaid state, sequence, or flow diagram, or a text sketch such as pseudocode, a call tree, a file tree, or a shape diff — instead of prose. Labels fit the reader, diagrams stay small, problem states are marked, and every node traces to code. Can show what a branch or pull request changes in a flow, so a reviewer can approve an agent's change by its behaviour. Use when the user says "show me", "draw", "diagram", "sketch", "chart", or "visualize", asks how a flow, request path, job, or lifecycle works, asks what a branch or PR changes, wants to review an agent's change without reading every line, when a PR description or report needs a visual, when another skill needs a diagram, or invokes `/z:diagram`.
---

# Show it with a diagram

A visual is for the person who decides whether the behaviour is right. When agents write
most of the code, that person is often approving work they did not write and will not
read line by line. They look once, at a glance, often without the code open. A sketch of
the shape replaces a paragraph about the shape, so pick the smallest view that makes the
point, put it next to the one or two sentences it supports, and stop.

The user's request, or the skill that called this one, names what to show. If it is
vague, show the one flow a user of the product goes through most, and say which.

## Know the reader and the target

Two facts decide most of what follows. Take them from the request or the caller when
they are there. When one is missing and the answer would change what you draw, ask the
user one short question, such as "Is this for a teammate who knows the code, or for
someone deciding whether the behaviour is right?" Otherwise use the defaults below.

**The reader:**

- **A teammate who knows the code** reads labels at the layer they think in: services,
  packages, queues, topics, tables, pages, events, and settings a user can change. Name a
  function only when that function is the boundary being discussed. Never name fields,
  variables, or internal keys.
- **Someone deciding whether the behaviour is right** (a product owner, a reviewer of an
  agent's change, a customer) reads plain words only: what they can see, what they do,
  what happens. This is the default for state and flow diagrams.

**The target**, which decides which forms render:

| Target | Forms that work |
| --- | --- |
| Terminal or chat | Text forms only. Mermaid shows as raw source. |
| Pull request, issue, or docs page | Text forms and Mermaid. GitHub and GitLab render `mermaid` and `diff` fences. |
| HTML page | Anything, but only when the user asks for one or nothing else can carry the point. |

Default to the terminal unless the caller says where the output goes.

## Read the code first

Build the visual from the code, not from names, comments, or docs. For each node and
arrow, find the code that makes it true: the function that handles a step, the write
that changes a state, the call that sends a message, the setting that schedules a job.
Keep a list of those locations. Anything you cannot point to in the code is a guess;
leave it out or mark it as one.

## Pick the form

Pick one form per point, by the question the reader is asking:

| Question | Form |
| --- | --- |
| How does this thing move between states? | Mermaid `stateDiagram-v2` |
| What happens in what order between services or processes? | Mermaid `sequenceDiagram` |
| What are the steps and decisions? | Mermaid `flowchart`, or pseudocode in a terminal |
| What is the logic or the decision? | Pseudocode |
| Who calls whom, in what order, at run time? | Call tree |
| Where does each responsibility live? | File tree at package and service level |
| What did a change add, remove, or move? | Shape diff, or a before/after Mermaid diagram |
| How is a screen built, and where does its state live? | Component tree |

In a terminal, a state flow becomes a short list of `state --> state: what happens` lines.

Text forms look like this:

```text
on(order.paid)                      # pseudocode
  if every item is in stock
    reserve the items
  else
    hold the order and email the customer
```

```text
handle_checkout                     # call tree
  load_cart
  charge_card                       # one payment API call per order
  publish order.paid
```

```diff
 handle_checkout                    # shape diff
   load_cart
+  check_fraud_score                # new: blocks scores above 80
   charge_card
```

## Write it in the reader's words

For Mermaid diagrams, and for any label a decision-maker reads:

- **States and nodes** say what the reader can see or cares about: "Waiting for
  payment", "Upload failed". Not variable names, function names, or enum values.
- **Arrows** say what happens: "you press pay", "the card is declined", "the retry timer
  fires".
- **Conditions** go in brackets at the end of the arrow: "you press play [while the
  file loads]".
- **Two causes with the same result** share one arrow: "the track ends or you press stop".
- **The title** names the flow in a few words.

Compare:

- From the code: `AWAITING_STOCK --> PACKING: on_inventory_reserved()`
- For the reader: `Waiting for stock --> Being packed: the warehouse reserves the items`

The second one lets a product owner say "that's wrong, it should cancel after two
days" without asking what `on_inventory_reserved` does.

Add `#` comments to text forms where a node's reason isn't obvious from its name. Cost
and trigger notes are the most useful: `# one model call per file`, `# nightly 00:00 UTC`.

## Keep it small

- **One visual per point.** A visual replaces prose and never sits beside prose that says
  the same thing. The text under it is one or two sentences of consequence.
- **Only the nodes the question needs.** A call tree with every branch is a listing, not
  an explanation.
- **Aim for about 12 nodes and 20 arrows or fewer** in a diagram. Merge states that
  behave the same for this reader, leave out detail the reader doesn't need, drop an
  arrow every state has (such as "you sign out") and say so under the diagram, or split a
  large flow into one diagram per phase.
- **Sketches show shape; they don't compile.** Never paste real code as a visual.

Never merge or drop a state on a problem path, and never merge two states with
different problems, because the reader then can't see which problem happens where.
Every node you keep must stay reachable from the start, and every node that isn't meant
to be final must keep an arrow out.

## Mark the problems

When the caller gives you problems (a stuck state, an impossible combination, a broken
rule), or you find one while reading the code:

- Mark each problem state with a `classDef` that changes its fill and border, and add a
  short legend naming each mark.
- Mark the states on the shortest path to each problem with a second class.
- Under the diagram, give each problem's path as numbered steps in the same words as the
  arrows.

Keep the colour meanings to those two, and add a text label as well, so the diagram
still reads in black and white and to colour-blind readers.

## Show a change

When the request is about a branch, a pull request, or a merge request, draw the flow as
it is on the base branch and as it is with the change, from the code at each commit.
Draw one diagram with the same layout for both, and mark each state and arrow the change
adds, removes, or alters, with a legend. In a terminal, use a shape diff instead. Under
it, list each difference in one sentence in the reader's words ("you can now cancel
while the payment is pending"), with the file and function that makes it. A change with
no effect on the flow gets one sentence saying so, not a diagram.

## Check it before you hand it over

- Render Mermaid if a renderer is already available, and fix every parse error. Don't
  install one without asking. Without one, keep to basic syntax: give each state a short
  ID and put its label after it (`s1: Waiting for payment`), quote flowchart labels that
  contain punctuation, don't use reserved words such as `end` as IDs, and avoid `;`
  inside sequence diagram messages, where it ends the statement.
- Walk each node and arrow against your list of code locations and confirm it.
- Read it as the reader would: can someone who has never seen the code say what happens
  and where it goes wrong?

## Hand off

Give the visual in the right fence for its target, followed by:

- the code locations behind each node and arrow, as a short table or list;
- what the visual leaves out (dropped arrows, merged states, code you didn't read);
- each problem's path as numbered steps, when there are any.

If the visual will live in the repository, record the commit it was drawn from beside
it, so the next reader can tell whether the code has moved on since.
