import { agentLabel } from "../lib/agents";
import { CREW_STAGES, stageIndex, type CrewStageId } from "../lib/crewStages";

interface Props {
  activeAgent: string | null;
}

export function ProgressRail({ activeAgent }: Props) {
  const current = stageIndex(activeAgent);

  return (
    <ol className="progress-rail" aria-label="Crew progress">
      {CREW_STAGES.map((stage: CrewStageId, index) => {
        const done = current > index;
        const active = current === index;
        return (
          <li
            key={stage}
            className={`progress-node${done ? " is-done" : ""}${active ? " is-active" : ""}`}
          >
            <span className="progress-dot" aria-hidden="true" />
            <span className="progress-label">{agentLabel(stage)}</span>
          </li>
        );
      })}
    </ol>
  );
}
