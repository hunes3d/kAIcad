# Hierarchical Sheets

Support for multi-sheet schematics with automatic sub-sheet discovery.

## How to use (Web)

1. Set project path
2. Click Detect
3. Ask: "Show me the hierarchical sheets" / "Inspect the hierarchy"

## Data structure

```
{
  root: { components, nets, hierarchy, stats },
  subsheets: { SheetName: { components, nets, stats }, ... }
}
```

## Benefits

- Complete visibility across the design
- AI-aware hierarchy for better answers
