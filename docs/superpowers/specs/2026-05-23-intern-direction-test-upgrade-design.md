# Intern Direction Test Upgrade Design

## Context

The current project is a static HTML/CSS/JS page for an internship direction test. It has a home screen, a 15-question quiz, a loading state, a result page, and a copy-summary action.

This design upgrades the project into a more complete "互联网实习隐藏人格测试" while keeping the first phase static. Phase 1 does not add a backend, does not call AI APIs, does not upload resumes, and does not perform resume editing.

## Goals

- Make the quiz feel lighter, more fun, and less obviously mapped to job labels.
- Expand the result system from 6 directions to 9 directions.
- Improve result usefulness with concrete next steps, portfolio guidance, job search terms, and application keywords.
- Keep the language friendly to beginners who may not know internet-industry jargon.
- Upgrade the visual style to a restrained, polished, lively product page.
- Add animal sticker avatars for result identities.
- Leave clear UI placeholders for future AI follow-up, without pretending AI exists in Phase 1.

## Non-Goals

- No AI-generated advice at runtime.
- No resume upload, parsing, storage, or editing.
- No user accounts or persistence.
- No backend service.
- No analytics integration.
- No full share-image generation in Phase 1.

## Product Positioning

The test should balance playful discovery and practical job-search help.

The home page can feel like a light test, with a title such as "测测你的互联网实习隐藏人格". The result page should be more practical: it should help users decide what to try first, what roles to search for, and what kind of portfolio project to build.

The target users are both complete beginners and students already starting to apply for internships. The default language should assume the user does not know professional jargon.

## Result Directions

The quiz will produce results across 9 directions:

1. 用户体验 / C 端产品
2. 业务流程 / B 端产品
3. 数据增长 / 增长运营
4. 内容表达 / 内容运营
5. 活动转化 / 活动运营
6. 社群关系 / 用户运营
7. 用户研究 / 需求洞察
8. 商业分析 / 策略运营
9. 项目管理 / 执行推进

Each direction needs:

- A beginner-friendly name.
- A short plain-language description.
- Suitable product roles.
- Suitable operation roles.
- Application keywords.
- Common professional terms with plain-language explanations.
- A 3-step route.
- A 7-day action plan.
- An animal sticker avatar.

## Animal Avatar System

The result avatars should be cute but professional animal sticker portraits. The animals remain clearly animal-like, with only small work-related props. They should not become complex fully dressed anthropomorphic characters.

Mapping:

- 用户体验 / C 端产品: cat, detail-sensitive, focused on usage comfort.
- 业务流程 / B 端产品: beaver, structure-building and process-oriented.
- 数据增长 / 增长运营: fox, sharp at spotting patterns and opportunities.
- 内容表达 / 内容运营: parrot, expressive and communication-oriented.
- 活动转化 / 活动运营: rabbit, quick-moving and approachable.
- 社群关系 / 用户运营: otter, warm, connective, and companion-like.
- 用户研究 / 需求洞察: deer, observant and empathetic.
- 商业分析 / 策略运营: owl, calm and big-picture-oriented.
- 项目管理 / 执行推进: border collie, organized and good at coordination.

The avatar art direction should use a consistent sticker-avatar style: same composition, similar line weight, similar background shape, and controlled accent colors.

## Quiz Design

The quiz should change from 15 questions to 25 questions.

Question mix:

- 15 scenario questions.
- 5 work-preference questions.
- 3 pressure-source or aversion questions.
- 2 self-calibration questions.

Question writing rules:

- Use beginner-friendly, everyday language.
- Prefer campus, club, content-account, job-search, App usage, group-project, and event-signup scenarios.
- Avoid obvious option ordering where option A always maps to one direction, option B to another, and so on.
- Avoid professional terms such as "转化漏斗", "用户分层", "SOP", and "A/B 测试" inside quiz questions.
- Do not require the user to understand product or operation job categories before answering.
- Do not add "none of the above" or skip options in Phase 1.
- Make each option broad enough that users can choose the closest fit.
- Some questions may cover only 4-5 relevant tendencies instead of all 9 directions.

The quiz should feel like behavior diagnosis, not a transparent role poll. Instead of asking "which job do you want", questions should ask what the user would naturally do under constraints such as limited time, incomplete information, conflicting opinions, weak signup results, confusing feedback, or unclear goals.

## Scoring Design

Each answer can affect one or two directions with weights. This avoids the current pattern where one option maps directly to one visible direction.

Scoring requirements:

- Use weighted scores for all 9 directions.
- Allow one answer to add points to a primary direction and a smaller amount to a secondary direction.
- Pressure-source questions should reduce fit for a direction or lightly increase fit for an opposite working style.
- Sort directions by final score.
- Show one main direction and one supporting direction by default.
- If supporting directions are tied or very close, show up to two supporting directions.
- If several directions are close, describe the user as multi-sided rather than saying the result is uncertain.

Result language must avoid absolute identity claims. Use phrasing such as "你最值得优先尝试的是..." instead of "你就是...".

## Result Page Structure

The result page should prioritize a clear conclusion, then offer details progressively.

Required sections:

1. Result hero
   - Animal avatar.
   - Main direction.
   - One-sentence plain-language summary.
   - A short note if the result is multi-sided or has tied supporting directions.

2. Supporting direction
   - Show one supporting direction by default.
   - Show two only when the scores are tied or extremely close.
   - Explain it as an add-on strength, not a second main identity.

3. Ability distribution
   - Show all 9 direction scores as lightweight bars.
   - Keep this visually secondary to the main result.

4. Three-step route
   - Step 1: understand what this direction actually does in internships.
   - Step 2: build a small portfolio project.
   - Step 3: use job search terms and application keywords to start applying.

5. Seven-day action plan
   - Show seven short daily tasks by default.
   - Each day can expand to show "today's goal", "how to do it", and "today's output".
   - Include a disabled or clearly marked "继续追问 AI" placeholder inside the expanded detail.

6. Portfolio suggestion
   - Generate the suggestion from main direction plus supporting direction.
   - The main direction decides the project theme.
   - The supporting direction decides the project's highlight.
   - Do not hardcode all 9 x 8 combinations. Use a rule-based composition.

7. Role and application terms
   - Suitable job search terms.
   - Application keywords that users can use in portfolio and resume wording.
   - This is not resume editing.

8. Inline jargon explanations
   - Professional terms inside the result text should be highlighted.
   - Clicking or tapping a highlighted term shows a small plain-language explanation.
   - On desktop, use a small popover near the term.
   - On mobile, use a bottom sheet or centered lightweight popup so the explanation remains readable.
   - Keep a small "查看本结果里的全部岗位词" entry for users who want to review all terms at once.

9. Copy result summary
   - Copy a concise summary including main direction, supporting direction, portfolio suggestion, and role keywords.

## Interaction Rules

Question flow:

- Keep one question per screen.
- Show progress clearly.
- Allow going back to the previous question.
- Advance after selecting an answer, with enough delay that the selection feels acknowledged.

Seven-day plan:

- Default view shows compact rows or cards.
- Tapping one day expands that day's details.
- Expanding one day should not force all days open.
- The expanded content should be structured, not a long paragraph.

Jargon popovers:

- Highlight only useful professional terms, not every noun.
- Explain terms in one or two short sentences.
- Allow closing by clicking outside, tapping the same term again, or pressing Escape.
- On mobile, avoid tiny hover-only interactions.

AI placeholder:

- The UI can include "继续追问 AI" but must make clear this is reserved for a future version.
- It should not look like a working feature in Phase 1.

## Visual Direction

Use a balanced style between campus notebook friendliness and a mature product interface.

Visual rules:

- Use white and light neutral backgrounds as the base.
- Use only 2-3 main accent colors.
- Avoid visual clutter, excessive stickers, or too many competing colors.
- Keep the interface organized and readable.
- Use animal avatars as the main memorable visual element.
- Cards should feel clean and functional, not nested or overly decorative.
- Result pages should feel like useful reports, not decorative posters.
- Text density should be controlled with progressive disclosure.

## Code Organization Design

The current app is a three-file static project. Phase 1 can remain static, but the JavaScript should be organized into clearer data and rendering sections.

Recommended internal units:

- `directions`: metadata for 9 directions.
- `questions`: 25 quiz questions and weighted answer data.
- `jargonTerms`: term definitions keyed by term id.
- `actionPlans`: 7-day plans by main direction.
- `portfolioThemes`: main-direction project themes.
- `portfolioHighlights`: supporting-direction highlights.
- scoring functions: answer aggregation, sorting, tie detection, and result selection.
- rendering functions: screen switching, quiz rendering, result rendering, accordions, popovers, copy summary.

If the implementation grows too large, split JavaScript into separate files without introducing a build tool.

## Error And Edge Cases

- If the user reaches the result page with incomplete answers, unanswered questions should contribute no score and the UI should still produce a result if enough answers exist.
- If all scores are equal or too close, show a multi-sided result with a recommended first project path.
- If clipboard copy fails, show the summary text in a selectable fallback area or display a clear message.
- If avatar images fail to load, show direction initials or a simple fallback sticker shape.
- Popovers must be accessible by keyboard and usable on mobile.

## Testing And Review

Manual checks:

- Complete the quiz from start to finish.
- Use back navigation during the quiz.
- Verify 25 questions render correctly.
- Verify scoring returns a main direction and supporting direction.
- Verify tied supporting directions show at most two.
- Verify multi-sided copy appears when scores are close.
- Expand and collapse seven-day plan items.
- Open and close jargon explanations on desktop and mobile widths.
- Copy result summary.
- Confirm the result page remains readable on mobile.

Visual checks:

- Home page should feel playful but not childish.
- Result page should feel practical and structured.
- Colors should remain restrained.
- Animal avatars should read as one consistent set.

## Phase 2 Notes

Potential future work:

- Real AI follow-up questions.
- AI-generated detailed explanations.
- Resume upload and resume editing.
- Save or share result cards.
- Persistent progress or result history.

These are intentionally out of scope for Phase 1.
