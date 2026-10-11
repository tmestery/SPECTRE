import type { ReportSection, ReportVerdict } from "../types/events";
import { VerdictBadge } from "../findings/VerdictBadge";

interface Props {
  sections: ReportSection[];
  reportVerdict?: ReportVerdict | null;
}

export function LiveReportPanel({ sections, reportVerdict = null }: Props) {
  return (
    <div className="panel report-panel">
      <div className="panel-heading">
        <h2>Live report</h2>
        {reportVerdict ? <VerdictBadge verdict={reportVerdict.verdict} kind="report" /> : null}
      </div>
      <div className="report-scroll">
        {sections.length === 0 ? (
          <p className="placeholder">Report sections stream in when Reporter runs.</p>
        ) : (
          sections.map((section) => (
            <section key={section.section_id} className="report-section">
              <div className="panel-heading">
                <h3>{section.title}</h3>
                {section.verdict ? (
                  <VerdictBadge verdict={section.verdict.verdict} kind="report" />
                ) : null}
              </div>
              <pre>{section.markdown}</pre>
            </section>
          ))
        )}
      </div>
    </div>
  );
}
