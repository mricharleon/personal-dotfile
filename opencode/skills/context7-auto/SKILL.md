---
name: context7-auto
description: Automatically uses context7 MCP for code generation, setup steps, and library/API documentation without explicit user request
---

# Context7 Auto-Usage Skill

You must automatically utilize the `context7` MCP tools whenever:
- Generating code
- Providing setup steps
- Retrieving documentation for libraries or APIs

This means you should automatically resolve library IDs and fetch documentation using `context7` tools without waiting for the user to explicitly request it.

## When to Use

- User asks for code examples
- User requests setup instructions
- User asks for library/API documentation
- User mentions specific libraries or frameworks

## Response Guidelines

1. Always check if the request involves a library, framework, or API
2. If so, immediately use the context7 MCP tools to:
   - Resolve the library ID
   - Fetch documentation
   - Provide relevant context
3. Integrate this information naturally into your response

## Examples

When a user asks for "React setup instructions", you should:
1. Recognize this as a library documentation request
2. Use context7 to fetch React documentation
3. Provide setup instructions with relevant context

When a user asks for "Express.js code examples", you should:
1. Recognize this as a library documentation request
2. Use context7 to fetch Express.js documentation
3. Provide code examples with context

## Auto-Activation

This skill is always active and should be used automatically without explicit user prompting.