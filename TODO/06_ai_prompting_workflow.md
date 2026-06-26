# AI Prompting Workflow

Use this folder to keep future AI assistance consistent.

## When asking an AI to modify this repository

Paste or attach:

1. `PROJECT_CONTEXT.md`
2. The relevant folder `README.md`
3. The file or files to be changed
4. The relevant TODO item
5. Any hardware datasheets or decisions already made

## Required AI instruction for future changes

```text
You are modifying the Buddy ROS 2 robot repository. Treat PROJECT_CONTEXT.md as the current architecture contract. If you add, delete, rename, or promote any file, update PROJECT_CONTEXT.md and the affected folder README. Files that are incomplete must end with (_IP). Keep hard real-time motor safety on the MCU, and keep ROS 2 as the high-level integration layer.
```

## Promotion checklist for `(_IP)` files

- [ ] The file is usable or intentionally official.
- [ ] The filename no longer contains `(_IP)`.
- [ ] Build/launch references are updated.
- [ ] Folder README is updated.
- [ ] `PROJECT_CONTEXT.md` is updated.
- [ ] Relevant TODO item is checked or replaced.
- [ ] Decision is captured in an ADR if it changes architecture.
