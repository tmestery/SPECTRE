import type { ReportSection } from "../types/events";

interface Props {
  sections: ReportSection[];
}

export function LiveReportPanel({ sections }: Props) {
  return (
    <div className="panel report-panel">
      <h2>Live Report</h2>
      <div className="report-scroll">
        {sections.length === 0 ? (
          <p className="placeholder">Report sections stream in when Reporter runs.</p>
        ) : (
          sections.map((section) => (
            <section key={section.section_id} className="report-section">
              <h3>{section.title}</h3>
              <pre>{section.markdown}</pre>
            </section>
          ))
        )}
      </div>
    </div>
  );
}
