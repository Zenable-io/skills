---
name: diagram
description: Draw a flow, lifecycle, state machine, or sequence from the code as a Mermaid diagram a person can read at a glance — labelled in the reader's words, small enough to follow, with problem states marked and every node traceable to code. Can also show how a branch or pull request changes a flow, so a reviewer can approve an agent's change by its behaviour. Use when the user asks to "draw", "diagram", "chart", "sketch", or "visualize" how a flow, request path, job, or lifecycle works, asks what a branch or PR does to a flow, wants to review an agent's change without reading every line, when another skill needs a diagram, or invokes `/z:diagram`.
---

# Draw a diagram from the code

A diagram is for the person who decides whether the behaviour is right. When agents
write most of the code, that person is often approving work they did not write and will
not read line by line. They read the diagram once, at a glance, often without the code
open. Every choice below serves that reader.

The user's request, or the skill that called this one, names what to draw. If it is
vague, draw the one flow a user of the product goes through most, and say which.

## Read the code first

Build the diagram from the code, not from names, comments, or docs. For each node and
arrow, find the code that makes it true: the function that handles a step, the write
that changes a state, the call that sends a message. Keep a list of those locations.
Anything you cannot point to in the code is a guess; leave it out or mark it as one.

## Pick the form

Pick the form by the question the reader is asking:

- **How does this thing move between states?** `stateDiagram-v2`. Orders, uploads,
  sessions, jobs, forms.
- **What happens in what order between parts?** `sequenceDiagram`. Requests between
  services, a login handshake, an agent calling tools.
- **What are the steps and decisions?** `flowchart`. A pipeline, a decision process,
  where a request goes.

Use Mermaid, since most code hosts, editors, and docs tools render it.

## Write it in the reader's words

- **States and nodes** are named by what the reader can see or cares about: "Waiting
  for payment", "Upload failed". Never variable names, function names, or enum values.
- **Arrows** say what happens, as the reader sees it: "you press pay", "the card is
  declined", "the retry timer fires". Never the function or handler name.
- **Conditions** go in brackets at the end of the arrow: "you press play [while the
  file loads]".
- **Two causes with the same result** share one arrow: "the track ends or you press stop".
- **The title** names the flow, in a few words.

The reader's words are what make the diagram checkable by someone who doesn't know the
code. Compare:

- From the code: `PENDING --> READY: promote_pending()`
- For the reader: `Waiting for a machine --> Ready to connect: a spare machine frees up`

The second one lets a product owner say "that's wrong, it should time out after ten
minutes" without asking what `promote_pending` does.

## Keep it small

Aim for about 12 nodes and 20 arrows or fewer. A bigger diagram is hard to read, so cut
before you draw:

- Merge states or steps that behave the same for this reader.
- Leave out detail the reader does not need, such as a call in flight whose result
  changes nothing.
- Drop an arrow that every state has, such as "you sign out", and say so under the
  diagram.
- Split one large flow into a few diagrams, one per phase, rather than drawing it all.

Never merge or drop a state on a problem path, and never merge two states with
different problems, because the reader then cannot see which problem happens where.
Every node you keep must stay reachable from the start, and every node that is not
meant to be final must keep an arrow out.

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

When the request is about a branch, a pull request, or a merge request, draw the flow
as it is on the base branch and as it is with the change, from the code at each commit.
Draw one diagram with the same layout for both, and mark each state and arrow the change
adds, removes, or alters, with a legend. Under it, list each difference in one sentence
in the reader's words ("you can now cancel while the payment is pending"), with the file
and function that makes it. A change with no effect on the flow gets one sentence saying
so, not a diagram.

## Check it before you hand it over

- Render it if a Mermaid renderer is already available, and fix every parse error. Don't
  install one without asking. If none is available, keep to basic syntax: give each
  state a short ID and put its label after it (`s1: Waiting for payment`), quote
  flowchart labels that contain punctuation, and don't use reserved words such as `end`
  as IDs.
- Walk each arrow against your list of code locations and confirm it.
- Read it as the reader would: can someone who has never seen the code say what happens
  and where it goes wrong?

## Hand off

Give the diagram as a `mermaid` code block, followed by:

- the code locations behind each node and arrow, as a short table or list;
- what the diagram leaves out (dropped arrows, merged states, code you did not read);
- each problem's path as numbered steps, when there are any.

If the diagram will live in the repository, record the commit it was drawn from beside
it, so the next reader can tell whether the code has moved on since.
