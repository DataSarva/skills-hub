---
name: local-client-prospector
description: Use this skill to find and qualify local business prospects near a location, especially shops, gyms, restaurants, clinics, salons, and local services that may need a website. It uses the integrated browser for assisted research, checks whether each business has a real website or only social profiles, and returns a concise lead sheet in chat or CSV-style rows.
---

# Local Client Prospector

Use this skill when the user wants to discover nearby local businesses that could become website or digital-marketing clients.

The default output is a compact lead sheet in chat. Create a CSV or spreadsheet only when the user asks for a file or when the result set is large enough that chat would be hard to use.

## Inputs to Collect

If missing, infer reasonable defaults and continue:

- `base_location`: address, town, landmark, or area.
- `radius_km`: default 20 km.
- `categories`: default `negozi, palestre, ristoranti, parrucchieri, estetisti, studi professionali`.
- `max_leads`: default 15.
- `language`: match the user's language.
- `output`: default `chat table`; optional `CSV`.

Ask a concise clarification only if the base location is missing and cannot be inferred.

## Compliance Guardrails

- Use the integrated browser as an assisted research tool, not as a bulk scraper.
- Do not bypass CAPTCHAs, login walls, rate limits, bot protections, or paywalls.
- Do not extract or resell Google Maps data at scale.
- Prefer public business facts and official business contact channels.
- Avoid collecting personal emails or private personal data unless the user explicitly provides a lawful basis and the source is clearly public business contact information.
- If using Google Maps manually in the browser, treat it as a discovery aid. Cross-check important details with independent public web sources such as the business website, social pages, directory listings, or search results.

## Browser Research Workflow

1. Open the browser and search for the requested category near `base_location`.
2. Build a candidate list from visible local results, search results, public directories, or business pages.
3. For each candidate, inspect enough public sources to fill the lead fields.
4. Search the exact business name plus city/town to check whether a real website exists.
5. Classify website status:
   - `No site found`: no credible standalone website after cross-check.
   - `Social only`: Facebook, Instagram, WhatsApp, Linktree, booking portal, or marketplace page only.
   - `Weak site`: standalone site exists but looks outdated, broken, very thin, non-mobile-friendly, or missing clear contact/conversion flow.
   - `Has site`: credible standalone site exists.
6. Mark confidence:
   - `High`: confirmed by at least two sources or official page.
   - `Medium`: one credible source plus consistent search evidence.
   - `Low`: incomplete or ambiguous evidence.

When the user explicitly asks for subagents or parallel verification and subagents are available, split candidates into non-overlapping batches and ask each subagent to verify only website/social/contact status. Do not use subagents for the immediate browser search if it blocks progress.

## Lead Scoring

Use this simple score:

- `Hot`: no site found or social only, phone/contact present, active business, near the target area.
- `Warm`: weak site, poor online presentation, or only marketplace/booking page.
- `Low`: good website already present or low confidence.
- `Skip`: closed, duplicate, outside radius, irrelevant category, or not a business prospect.

## Output Format

For chat output, use a concise markdown table:

| Score | Business | Category | Area | Distance | Website status | Website/Social | Phone | Why it is a prospect | Confidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

Rules:

- Keep `Why it is a prospect` short and actionable.
- Use `Not found` instead of leaving blank fields.
- Include source links when possible, but do not overload the table with many URLs.
- After the table, add `Best first outreach targets` with the top 3 leads and one practical reason each.
- If confidence is low, state exactly what remains uncertain.

## CSV Columns

When returning CSV-style rows or creating a file, use these columns:

```csv
score,business,category,area,distance_km,website_status,website_url,social_urls,phone,source_urls,why_prospect,confidence,notes
```

## Quality Checks

Before finalizing:

- Remove duplicates.
- Do not label a lead `Hot` if a real standalone website was found.
- Do not claim a site is missing unless at least one exact-name web search was attempted.
- Prefer fewer verified leads over many weak guesses.
- Include the search location, radius, categories, and date in the final response.
