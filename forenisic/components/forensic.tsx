"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import {
  ArrowUpIcon,
  Fingerprint,
  BrainCircuit,
  User,
  Loader2,
  ScanFace,
} from "lucide-react";
import bgImage from "@/assets/forensic-bg.jpg";
import {
  INTERVIEW_QUESTIONS,
  INTERVIEW_QUESTION_COUNT,
} from "@/lib/interview-questions";
import {
  buildProfileFromAnswers,
  type FlatAnswer,
} from "@/lib/face-profile";
import { attachPrompt } from "@/lib/prompt-builder";
import { refinePromptWithLLM } from "@/lib/prompt-refiner";
import {
  generateCompare,
  imageSrc,
  type CompareImage,
} from "@/lib/generate-compare";

interface AutoResizeProps {
  minHeight: number;
  maxHeight?: number;
}

function useAutoResizeTextarea({ minHeight, maxHeight }: AutoResizeProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const adjustHeight = useCallback(
    (reset?: boolean) => {
      const textarea = textareaRef.current;
      if (!textarea) return;
      if (reset) {
        textarea.style.height = `${minHeight}px`;
        return;
      }
      textarea.style.height = `${minHeight}px`;
      const newHeight = Math.max(
        minHeight,
        Math.min(textarea.scrollHeight, maxHeight ?? Infinity),
      );
      textarea.style.height = `${newHeight}px`;
    },
    [minHeight, maxHeight],
  );

  useEffect(() => {
    if (textareaRef.current) textareaRef.current.style.height = `${minHeight}px`;
  }, [minHeight]);

  return { textareaRef, adjustHeight };
}

type Message =
  | { role: "user"; text: string }
  | { role: "ai"; text: string; questionIndex?: number }
  | { role: "status"; text: string };

export default function ForensicIntake() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [started, setStarted] = useState(false);
  const [step, setStep] = useState(0);
  const [finished, setFinished] = useState(false);
  const [thinking, setThinking] = useState(false);
  const [otherMode, setOtherMode] = useState(false);
  const [otherText, setOtherText] = useState("");
  const [answers, setAnswers] = useState<FlatAnswer[]>([]);
  const [openedWith, setOpenedWith] = useState("");
  const [finalPrompt, setFinalPrompt] = useState<{
    positive: string;
    negative: string;
    draft_positive?: string;
    draft_negative?: string;
    refined_by?: string | null;
  } | null>(null);
  const [compareImages, setCompareImages] = useState<{
    draft: CompareImage;
    final: CompareImage;
  } | null>(null);
  const [generatingImages, setGeneratingImages] = useState(false);
  const [generateError, setGenerateError] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  const logToTerminal = async (
    event: string,
    profile: unknown,
    prompt?: { positive: string; negative: string },
  ) => {
    try {
      await fetch("/api/log-profile", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ event, profile, prompt }),
      });
    } catch {
      // browser console fallback
      console.info(`[Forensic:${event}]`, { profile, prompt });
    }
  };

  const { textareaRef, adjustHeight } = useAutoResizeTextarea({
    minHeight: 56,
    maxHeight: 160,
  });

  const scrollToBottom = () => {
    requestAnimationFrame(() => {
      scrollRef.current?.scrollTo({
        top: scrollRef.current.scrollHeight,
        behavior: "smooth",
      });
    });
  };

  const askQuestion = (index: number, prev: Message[]) => {
    const q = INTERVIEW_QUESTIONS[index];
    if (!q) return;
    setThinking(true);
    scrollToBottom();
    setTimeout(() => {
      setThinking(false);
      setMessages([
        ...prev,
        {
          role: "ai",
          text: q.question,
          questionIndex: index,
        },
      ]);
      scrollToBottom();
    }, 700);
  };

  const startInterview = () => {
    const text = input.trim();
    if (!text) return;
    const base: Message[] = [
      { role: "user", text },
      {
        role: "ai",
        text: "Understood. Pipeline: raw interview → normalizer → structured profile → draft prompt → LLM refine (OpenRouter). Pick an option or Other.",
      },
    ];
    setStarted(true);
    setOpenedWith(text);
    setMessages(base);
    setAnswers([]);
    setFinalPrompt(null);
    setInput("");
    adjustHeight(true);
    askQuestion(0, base);
  };

  const answer = (text: string, qIndex: number, source: "option" | "other") => {
    if (thinking || finished || qIndex !== step) return;
    const q = INTERVIEW_QUESTIONS[qIndex];
    if (!q) return;

    const nextAnswers: FlatAnswer[] = [
      ...answers,
      { key: q.key, group: q.group, value: text, source },
    ];
    setAnswers(nextAnswers);

    // Live: raw → normalizer → structured (NOT raw dump)
    const liveProfile = buildProfileFromAnswers(
      nextAnswers,
      openedWith || "interview",
      INTERVIEW_QUESTION_COUNT,
      false,
    );
    console.info("[pipeline] raw → normalized", {
      last_raw: text,
      last_key: q.key,
      structured_cell: (() => {
        const [g, f] = q.key.split(".");
        return g && f ? liveProfile.structured[g]?.[f] : null;
      })(),
      structured_values: liveProfile.structured_values,
    });

    const base: Message[] = [...messages, { role: "user", text }];
    setMessages(base);
    setOtherMode(false);
    setOtherText("");
    const next = step + 1;
    setStep(next);

    if (next < INTERVIEW_QUESTION_COUNT) {
      askQuestion(next, base);
    } else {
      setFinished(true);
      setThinking(true);
      scrollToBottom();

      void (async () => {
        const drafted = attachPrompt(
          buildProfileFromAnswers(
            nextAnswers,
            openedWith || "interview",
            INTERVIEW_QUESTION_COUNT,
            true,
          ),
        );

        console.info("[1 RAW INTERVIEW]", drafted.raw_interview);
        console.info("[2 STRUCTURED PROFILE]", drafted.structured_values);
        console.info("[3 DRAFT PROMPT]", drafted.prompt);

        setMessages([
          ...base,
          { role: "status", text: "Normalizing attributes → structured profile…" },
          { role: "status", text: "Building draft prompt…" },
          { role: "status", text: "Refining with LLM (OpenRouter)…" },
        ]);
        scrollToBottom();

        const refine = await refinePromptWithLLM({
          structured_values: drafted.structured_values,
          structured: drafted.structured,
          draft: {
            positive: drafted.prompt!.draft_positive,
            negative: drafted.prompt!.draft_negative,
          },
        });

        const completed = {
          ...drafted,
          prompt: {
            draft_positive: drafted.prompt!.draft_positive,
            draft_negative: drafted.prompt!.draft_negative,
            positive: refine.ok && refine.prompt
              ? refine.prompt.positive
              : drafted.prompt!.positive,
            negative: refine.ok && refine.prompt
              ? refine.prompt.negative
              : drafted.prompt!.negative,
            refined_by: refine.ok ? refine.model ?? "openrouter" : null,
          },
        };

        const prompt = completed.prompt!;
        void logToTerminal("interview_complete", completed, {
          positive: prompt.positive,
          negative: prompt.negative,
        });
        console.info("[4 FINAL LLM PROMPT]", prompt);

        setThinking(false);
        setFinalPrompt(prompt);
        setCompareImages(null);
        setGenerateError(null);
        setGeneratingImages(true);
        setMessages([
          ...base,
          { role: "status", text: "Normalizing attributes → structured profile…" },
          { role: "status", text: "Draft prompt → LLM refine…" },
          {
            role: "status",
            text: "Generating draft vs LLM faces (SD 1.5, same seed)…",
          },
          {
            role: "ai",
            text: refine.ok
              ? `Prompts ready (${prompt.refined_by}). Generating two faces with seed 42 (prompt is the only variable)…`
              : `LLM refine failed (${refine.error ?? "unknown"}) — comparing draft vs fallback faces…`,
          },
        ]);
        scrollToBottom();

        // Controlled A/B: same seed + same negative; only positive prompt differs.
        const sharedNegative =
          prompt.draft_negative ?? prompt.negative;
        const compare = await generateCompare({
          draft: {
            positive: prompt.draft_positive ?? prompt.positive,
            negative: sharedNegative,
          },
          final: {
            positive: prompt.positive,
            negative: sharedNegative,
          },
          draft_seed: 42,
          final_seed: 42,
        });

        setGeneratingImages(false);

        if (compare.ok) {
          setCompareImages({
            draft: compare.draft_image,
            final: compare.final_image,
          });
          console.info("[5 COMPARE IMAGES]", {
            draft_seed: compare.draft_image.seed,
            final_seed: compare.final_image.seed,
            shared_seed: 42,
          });
          setMessages((prev) => [
            ...prev.filter((m) => m.role !== "status"),
            {
              role: "ai",
              text: "Faces ready — Draft Prompt vs LLM Prompt (same seed) side by side below.",
            },
          ]);
        } else {
          setGenerateError(
            [compare.error, compare.hint].filter(Boolean).join(" — "),
          );
          setMessages((prev) => [
            ...prev.filter((m) => m.role !== "status"),
            {
              role: "ai",
              text: `Prompts are ready, but image generation failed: ${compare.error}. Start the Python worker (uvicorn api.main:app --port 8000) and try again.`,
            },
          ]);
        }
        scrollToBottom();
      })();
    }
  };

  const sendOther = () => {
    const text = otherText.trim();
    if (!text) return;
    answer(text, step, "other");
  };

  const sendCustom = () => {
    if (!started) {
      startInterview();
      return;
    }
    const text = input.trim();
    if (!text) return;
    setInput("");
    adjustHeight(true);
    answer(text, step, "other");
  };

  const activeQuestion =
    started && !finished && !thinking ? INTERVIEW_QUESTIONS[step] : null;

  return (
    <div
      className="relative flex min-h-screen w-full flex-col items-center bg-cover bg-center"
      style={{
        backgroundImage: `url(${typeof bgImage === "string" ? bgImage : bgImage.src})`,
      }}
    >
      <div className="absolute inset-0 bg-background/70" aria-hidden="true" />

      <div className="relative flex w-full flex-1 flex-col items-center px-4 pt-10">
        <div className="max-w-2xl text-center">
          <span className="inline-flex items-center gap-2 rounded-full border border-border bg-card/60 px-3 py-1 text-xs uppercase tracking-[0.2em] text-muted-foreground backdrop-blur">
            <Fingerprint className="size-3.5" />
            Case intake
          </span>
          <h1 className="mt-4 text-4xl font-semibold tracking-tight text-foreground md:text-5xl">
            Forensic Sketch Generator
          </h1>
          {!started && (
            <p className="mt-3 text-base text-muted-foreground">
              Tell the assistant you want to generate a suspect image. It will run a
              full facial taxonomy interview (artist-style), then prepare the composite.
            </p>
          )}
          {started && !finished && (
            <p className="mt-3 text-sm text-muted-foreground">
              Facial taxonomy interview · {step + 1} / {INTERVIEW_QUESTION_COUNT}
            </p>
          )}
        </div>

        {started && (
          <div
            ref={scrollRef}
            className="mt-6 flex w-full max-w-3xl flex-1 flex-col gap-3 overflow-y-auto pb-4"
            style={{ maxHeight: "48vh" }}
          >
            {messages.map((m, i) =>
              m.role === "status" ? (
                <div
                  key={i}
                  className="flex items-center gap-2 self-center text-xs text-muted-foreground"
                >
                  <Loader2 className="size-3.5 animate-spin" />
                  {m.text}
                </div>
              ) : (
                <div
                  key={i}
                  className={cn(
                    "flex max-w-[85%] items-start gap-2",
                    m.role === "user" ? "self-end flex-row-reverse" : "self-start",
                  )}
                >
                  <span className="mt-1 flex size-7 shrink-0 items-center justify-center rounded-full border border-border bg-card/80">
                    {m.role === "user" ? (
                      <User className="size-3.5" />
                    ) : (
                      <BrainCircuit className="size-3.5" />
                    )}
                  </span>
                  <div
                    className={cn(
                      "rounded-xl border px-3.5 py-2.5 text-sm leading-relaxed backdrop-blur",
                      m.role === "user"
                        ? "border-primary/40 bg-primary/20 text-foreground"
                        : "border-border bg-card/70 text-foreground",
                    )}
                  >
                    {m.text}
                  </div>
                </div>
              ),
            )}
            {thinking && (
              <div className="flex items-center gap-2 self-start text-sm text-muted-foreground">
                <span className="flex size-7 items-center justify-center rounded-full border border-border bg-card/80">
                  <BrainCircuit className="size-3.5" />
                </span>
                <Loader2 className="size-4 animate-spin" />
                Next question…
              </div>
            )}
          </div>
        )}
      </div>

      <div className={cn("relative w-full max-w-3xl px-4", started ? "mb-6" : "mb-[14vh]")}>
        {(generatingImages || compareImages || generateError) && (
          <div className="mb-3 space-y-3 rounded-xl border border-primary/40 bg-card/90 p-4 backdrop-blur-md">
            <div className="text-xs uppercase tracking-[0.2em] text-primary">
              Prompt compare · generated faces · seed 42
            </div>
            {generatingImages && (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="size-4 animate-spin" />
                Running Stable Diffusion worker (two jobs, same seed)…
              </div>
            )}
            {generateError && (
              <p className="text-sm text-destructive">{generateError}</p>
            )}
            {compareImages && (
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <figure className="space-y-2">
                  <figcaption className="text-xs font-semibold text-muted-foreground">
                    Draft Prompt → Generated Face · seed{" "}
                    {compareImages.draft.seed}
                  </figcaption>
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={imageSrc(compareImages.draft)}
                    alt="Generated face from draft prompt"
                    className="w-full rounded-lg border border-border bg-background object-contain"
                  />
                </figure>
                <figure className="space-y-2">
                  <figcaption className="text-xs font-semibold text-muted-foreground">
                    LLM Prompt → Generated Face · seed{" "}
                    {compareImages.final.seed}
                  </figcaption>
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={imageSrc(compareImages.final)}
                    alt="Generated face from LLM prompt"
                    className="w-full rounded-lg border border-border bg-background object-contain"
                  />
                </figure>
              </div>
            )}
          </div>
        )}

        {finalPrompt && (
          <div className="mb-3 space-y-3 rounded-xl border border-primary/40 bg-card/90 p-4 backdrop-blur-md">
            <div className="text-xs uppercase tracking-[0.2em] text-primary">
              {finalPrompt.refined_by
                ? `Final LLM prompt · ${finalPrompt.refined_by}`
                : "Draft prompt (LLM refine skipped / failed)"}
            </div>
            {finalPrompt.draft_positive && finalPrompt.refined_by && (
              <details className="rounded-lg border border-border bg-background/40 p-2 text-xs">
                <summary className="cursor-pointer text-muted-foreground">
                  Show mechanical draft (pre-LLM)
                </summary>
                <pre className="mt-2 max-h-28 overflow-auto whitespace-pre-wrap text-foreground">
                  {finalPrompt.draft_positive}
                </pre>
              </details>
            )}
            <div>
              <p className="mb-1 text-xs font-semibold text-muted-foreground">
                Positive (witness-style)
              </p>
              <pre className="max-h-40 overflow-auto whitespace-pre-wrap rounded-lg border border-border bg-background/60 p-3 text-xs leading-relaxed text-foreground">
                {finalPrompt.positive}
              </pre>
            </div>
            <div>
              <p className="mb-1 text-xs font-semibold text-muted-foreground">Negative</p>
              <pre className="max-h-24 overflow-auto whitespace-pre-wrap rounded-lg border border-border bg-background/60 p-3 text-xs leading-relaxed text-foreground">
                {finalPrompt.negative}
              </pre>
            </div>
            <p className="text-[11px] text-muted-foreground">
              Also printed in the terminal running{" "}
              <code className="rounded bg-muted px-1">npm run dev</code>.
            </p>
          </div>
        )}

        {activeQuestion && (
          <div className="mb-3 rounded-xl border border-border bg-card/80 p-4 backdrop-blur-md">
            <div className="mb-1 flex flex-wrap items-center gap-2 text-xs uppercase tracking-[0.15em] text-muted-foreground">
              <ScanFace className="size-3.5" />
              <span>
                Question {step + 1} of {INTERVIEW_QUESTION_COUNT}
              </span>
              <span className="rounded-full border border-border px-2 py-0.5 normal-case tracking-normal text-[11px]">
                {activeQuestion.group}
              </span>
            </div>
            <p className="mb-3 text-sm font-medium text-foreground">
              {activeQuestion.question}
            </p>
            <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
              {activeQuestion.options.map((opt) => (
                <Button
                  key={opt}
                  variant="outline"
                  onClick={() => answer(opt, step, "option")}
                  className="h-auto justify-start whitespace-normal rounded-lg border-border bg-background/50 px-3 py-2.5 text-left text-sm text-foreground hover:border-primary hover:bg-primary/10"
                >
                  {opt}
                </Button>
              ))}
              <Button
                variant="outline"
                onClick={() => {
                  setOtherMode(true);
                  setOtherText("");
                }}
                className={cn(
                  "h-auto justify-start whitespace-normal rounded-lg border-dashed border-border bg-background/30 px-3 py-2.5 text-left text-sm text-muted-foreground hover:border-primary hover:bg-primary/10 sm:col-span-2",
                  otherMode && "border-primary bg-primary/10 text-foreground",
                )}
              >
                Other… (type your own / not sure)
              </Button>
            </div>

            {otherMode && (
              <div className="mt-3 flex items-center gap-2 rounded-lg border border-border bg-background/50 p-2">
                <input
                  type="text"
                  value={otherText}
                  onChange={(e) => setOtherText(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      sendOther();
                    }
                  }}
                  placeholder="Describe what you remember…"
                  autoFocus
                  className="flex-1 bg-transparent px-2 py-1.5 text-sm text-foreground outline-none placeholder:text-muted-foreground"
                />
                <Button
                  onClick={sendOther}
                  disabled={!otherText.trim()}
                  size="sm"
                  aria-label="Send other answer"
                >
                  <ArrowUpIcon className="size-4" />
                </Button>
              </div>
            )}
          </div>
        )}

        <div className="rounded-xl border border-border bg-card/70 backdrop-blur-md">
          <Textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => {
              setInput(e.target.value);
              adjustHeight();
            }}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                sendCustom();
              }
            }}
            placeholder={
              !started
                ? "Type: I want to generate a suspect image…"
                : finished
                  ? "Interview finished — profile recorded"
                  : "Or type a free-text answer for this question…"
            }
            disabled={finished || thinking}
            className={cn(
              "w-full resize-none border-none bg-transparent px-4 py-3 text-sm",
              "min-h-[56px] focus-visible:ring-0 focus-visible:ring-offset-0",
            )}
            style={{ overflow: "hidden" }}
          />

          <div className="flex items-center justify-end p-3">
            <Button
              onClick={sendCustom}
              disabled={!input.trim() || finished || thinking}
              size="icon"
              aria-label="Send"
            >
              <ArrowUpIcon />
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
