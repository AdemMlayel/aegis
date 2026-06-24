import type { ReactNode } from "react";

type DiffKind = "same" | "added" | "removed";

type DiffLine = {
  kind: DiffKind;
  text: string;
  oldLine: number | null;
  newLine: number | null;
};

export function RobotCodeView({ content }: { content: string }) {
  return (
    <div className="robot-code-view" role="region" aria-label="Robot Framework source">
      {sourceLines(content).map((line, index) => (
        <div className="robot-code-line" key={`${index}-${line}`}>
          <span className="robot-line-number">{index + 1}</span>
          <code>{highlightRobotLine(line)}</code>
        </div>
      ))}
    </div>
  );
}

export function RobotDiffView({
  before,
  after
}: {
  before: string;
  after: string;
}) {
  const lines = buildLineDiff(before, after);
  const changed = lines.some((line) => line.kind !== "same");

  return (
    <div className="robot-diff-view" role="region" aria-label="Robot Framework changes">
      {!changed ? (
        <div className="robot-diff-empty">No content changes in this comparison.</div>
      ) : lines.map((line, index) => (
        <div className={`robot-diff-line ${line.kind}`} key={`${index}-${line.kind}-${line.text}`}>
          <span className="diff-marker">
            {line.kind === "added" ? "+" : line.kind === "removed" ? "-" : " "}
          </span>
          <span className="robot-line-number">{line.oldLine ?? ""}</span>
          <span className="robot-line-number">{line.newLine ?? ""}</span>
          <code>{highlightRobotLine(line.text)}</code>
        </div>
      ))}
    </div>
  );
}

export function lineDiffSummary(
  before: string,
  after: string
): { added: number; removed: number } {
  return buildLineDiff(before, after).reduce(
    (summary, line) => {
      if (line.kind === "added") summary.added += 1;
      if (line.kind === "removed") summary.removed += 1;
      return summary;
    },
    { added: 0, removed: 0 }
  );
}

function sourceLines(content: string): string[] {
  const lines = content.replaceAll("\r\n", "\n").split("\n");
  return lines.length ? lines : [""];
}

function highlightRobotLine(line: string): ReactNode {
  if (!line) return " ";
  if (/^\s*#/.test(line)) {
    return <span className="robot-token comment">{line}</span>;
  }
  if (/^\s*\*{3}.+\*{3}\s*$/.test(line)) {
    return <span className="robot-token section">{line}</span>;
  }

  const cells = line.split(/(\s{2,}|\t+)/);
  let contentCell = 0;
  return cells.map((cell, index) => {
    if (!cell) return null;
    if (/^(\s{2,}|\t+)$/.test(cell)) {
      return <span key={index}>{cell}</span>;
    }
    contentCell += 1;
    const className = contentCell === 1 && !/^[${@&%]/.test(cell)
      ? "robot-token keyword"
      : undefined;
    return (
      <span className={className} key={index}>
        {highlightRobotTokens(cell)}
      </span>
    );
  });
}

function highlightRobotTokens(value: string): ReactNode[] {
  return value
    .split(/(\$\{[^}]+\}|@\{[^}]+\}|&\{[^}]+\}|%\{[^}]+\}|\[[A-Za-z][^\]]*\])/g)
    .filter(Boolean)
    .map((token, index) => {
      const className = /^[${@&%]\{/.test(token)
        ? "robot-token variable"
        : /^\[.+\]$/.test(token)
          ? "robot-token setting"
          : undefined;
      return <span className={className} key={`${index}-${token}`}>{token}</span>;
    });
}

function buildLineDiff(before: string, after: string): DiffLine[] {
  const oldLines = sourceLines(before);
  const newLines = sourceLines(after);
  const table = Array.from(
    { length: oldLines.length + 1 },
    () => Array<number>(newLines.length + 1).fill(0)
  );

  for (let oldIndex = oldLines.length - 1; oldIndex >= 0; oldIndex -= 1) {
    for (let newIndex = newLines.length - 1; newIndex >= 0; newIndex -= 1) {
      table[oldIndex][newIndex] = oldLines[oldIndex] === newLines[newIndex]
        ? table[oldIndex + 1][newIndex + 1] + 1
        : Math.max(table[oldIndex + 1][newIndex], table[oldIndex][newIndex + 1]);
    }
  }

  const result: DiffLine[] = [];
  let oldIndex = 0;
  let newIndex = 0;
  while (oldIndex < oldLines.length && newIndex < newLines.length) {
    if (oldLines[oldIndex] === newLines[newIndex]) {
      result.push({
        kind: "same",
        text: oldLines[oldIndex],
        oldLine: oldIndex + 1,
        newLine: newIndex + 1
      });
      oldIndex += 1;
      newIndex += 1;
    } else if (table[oldIndex + 1][newIndex] >= table[oldIndex][newIndex + 1]) {
      result.push({
        kind: "removed",
        text: oldLines[oldIndex],
        oldLine: oldIndex + 1,
        newLine: null
      });
      oldIndex += 1;
    } else {
      result.push({
        kind: "added",
        text: newLines[newIndex],
        oldLine: null,
        newLine: newIndex + 1
      });
      newIndex += 1;
    }
  }
  while (oldIndex < oldLines.length) {
    result.push({
      kind: "removed",
      text: oldLines[oldIndex],
      oldLine: oldIndex + 1,
      newLine: null
    });
    oldIndex += 1;
  }
  while (newIndex < newLines.length) {
    result.push({
      kind: "added",
      text: newLines[newIndex],
      oldLine: null,
      newLine: newIndex + 1
    });
    newIndex += 1;
  }
  return result;
}
