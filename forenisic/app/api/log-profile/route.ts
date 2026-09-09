import { NextResponse } from "next/server";

/**
 * Logs face profile + generated prompt to the **server terminal**
 * (the same window where `npm run dev` is running).
 */
export async function POST(req: Request) {
  try {
    const body = await req.json();
    const { event, profile, prompt } = body as {
      event?: string;
      profile?: unknown;
      prompt?: { positive?: string; negative?: string };
    };

    const line = "═".repeat(72);
    console.log("\n" + line);
    console.log(`[Forensic] ${event ?? "profile_update"}  @ ${new Date().toISOString()}`);
    console.log(line);

    if (prompt?.positive) {
      console.log("\n>>> POSITIVE PROMPT\n");
      console.log(prompt.positive);
    }
    if (prompt?.negative) {
      console.log("\n>>> NEGATIVE PROMPT\n");
      console.log(prompt.negative);
    }

    if (profile) {
      console.log("\n>>> FACE PROFILE JSON\n");
      console.log(JSON.stringify(profile, null, 2));
    }

    console.log("\n" + line + "\n");

    return NextResponse.json({ ok: true });
  } catch (err) {
    console.error("[Forensic] log-profile failed", err);
    return NextResponse.json({ ok: false }, { status: 400 });
  }
}
