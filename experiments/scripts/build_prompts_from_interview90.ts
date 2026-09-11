/**
 * Build draft prompts from interview_90.json using the same
 * normalizer + prompt-builder as the Next.js UI.
 *
 * Usage (from forenisic/):
 *   npx --yes tsx ../experiments/scripts/build_prompts_from_interview90.ts <interview_90.json> <out.json>
 */

import { readFileSync, writeFileSync } from "fs";
import { resolve } from "path";

import { buildProfileFromAnswers, type FlatAnswer } from "../../forenisic/lib/face-profile";
import { attachPrompt } from "../../forenisic/lib/prompt-builder";

type InterviewRow = {
  key: string;
  group: string;
  value: string;
  source: string;
};

function main() {
  const interviewPath = process.argv[2];
  const outPath = process.argv[3];
  if (!interviewPath || !outPath) {
    console.error(
      "Usage: npx tsx build_prompts_from_interview90.ts <interview_90.json> <out.json>",
    );
    process.exit(1);
  }

  const rows = JSON.parse(
    readFileSync(resolve(interviewPath), "utf-8"),
  ) as InterviewRow[];

  const answers: FlatAnswer[] = rows.map((r) => ({
    key: r.key,
    group: r.group,
    value: r.value,
    source: r.source === "celeba" ? "option" : "other",
  }));

  const profile = attachPrompt(
    buildProfileFromAnswers(
      answers,
      "experiment_1a_celeba",
      answers.length,
      true,
    ),
  );

  const payload = {
    structured: profile.structured,
    structured_values: profile.structured_values,
    draft_positive: profile.prompt!.draft_positive,
    draft_negative: profile.prompt!.draft_negative,
    answered_count: profile.session.answered_count,
    mapped_celeba: rows.filter((r) => r.source === "celeba").length,
    not_available: rows.filter((r) => r.source === "not_available").length,
  };

  writeFileSync(resolve(outPath), JSON.stringify(payload, null, 2), "utf-8");
  console.log(
    JSON.stringify(
      {
        ok: true,
        out: outPath,
        draft_chars: payload.draft_positive.length,
        mapped_celeba: payload.mapped_celeba,
        not_available: payload.not_available,
      },
      null,
      2,
    ),
  );
}

main();
