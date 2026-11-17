import { Fragment, type ReactNode } from "react";

/** **bold** → <strong>. Everything else is plain text (never parsed as HTML). */
function inline(text: string): ReactNode[] {
  return text.split(/(\*\*[^*]+\*\*)/g).map((piece, index) =>
    piece.startsWith("**") && piece.endsWith("**") && piece.length > 4 ? (
      <strong key={index} className="font-semibold text-ink">
        {piece.slice(2, -2)}
      </strong>
    ) : (
      <Fragment key={index}>{piece}</Fragment>
    ),
  );
}

/** The model's short answer: paragraphs, "- " bullet lists and bold. */
export function AnswerText({ text }: { text: string }) {
  const blocks = text.trim().split(/\n{2,}/);
  return (
    <div className="space-y-2 text-[15px] leading-relaxed text-ink">
      {blocks.map((block, index) => {
        const lines = block.split("\n");
        if (lines.every((line) => /^\s*[-*•]\s+/.test(line))) {
          return (
            <ul key={index} className="list-disc space-y-1 pl-5">
              {lines.map((line, i) => (
                <li key={i}>{inline(line.replace(/^\s*[-*•]\s+/, ""))}</li>
              ))}
            </ul>
          );
        }
        return <p key={index}>{inline(lines.join(" "))}</p>;
      })}
    </div>
  );
}
