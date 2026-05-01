#!/usr/bin/env python3
"""Modify AnalysisPage.tsx for Phase 3 Frontend implementation"""

import re

# Read the current file
with open('src/web/frontend/src/pages/AnalysisPage.tsx', 'r') as f:
    content = f.read()

# 1. Add ProgressWindow import after other imports
import_section = content[:content.find('interface ScanRegion')]
import_section = import_section.replace(
    'import { AnalysisProgressPanel } from "../components/AnalysisProgressPanel";',
    'import { AnalysisProgressPanel } from "../components/AnalysisProgressPanel";\nimport { ProgressWindow } from "../components/ProgressWindow";'
)
content = import_section + content[content.find('interface ScanRegion'):]

# 2. Add new state variables after startError
start_error_match = re.search(r"const \[startError, setStartError\] = useState<string \| null>\(null\);", content)
if start_error_match:
    after_start_error = start_error_match.end()
    new_state = '''
  const [analysisId, setAnalysisId] = useState<string | null>(null);
  const [videoId, setVideoId] = useState<string | null>(null);
  const [progressStatus, setProgressStatus] = useState<"in_progress" | "completed" | "failed" | null>(null);
  const [progressMessage, setProgressMessage] = useState("");
  const [projectStatus, setProjectStatus] = useState<"creating" | "merging" | null>(null);
  const [progressPercent, setProgressPercent] = useState(0);'''
    content = content[:after_start_error] + new_state + content[after_start_error:]

# 3. Replace handleStart function
handlestart_pattern = r'const handleStart = async \(\) => \{[\s\S]*?\n  \};'
new_handlestart = '''const handleStart = async () => {
    setStartError(null);
    setAnalysisId(null);
    setVideoId(null);
    setProgressStatus(null);
    setProgressMessage("");
    setProjectStatus(null);
    setProgressPercent(0);

    const payload = {
      video_url: sourceValue.trim(),
    };

    try {
      const resp = await fetch("/api/analysis/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (resp.status === 202) {
        const data = await resp.json() as {
          analysis_id: string;
          video_id: string;
          project_status: "creating" | "merging";
          message: string;
        };
        setAnalysisId(data.analysis_id);
        setVideoId(data.video_id);
        setProjectStatus(data.project_status);
        setProgressMessage(data.message);
        setProgressStatus("in_progress");
        setIsRunning(true);
      } else {
        const err = await resp.json().catch(() => ({ message: "Unknown error" })) as { message?: string };
        setStartError(err.message ?? "Start failed");
      }
    } catch (error) {
      setStartError(error instanceof Error ? error.message : "Network error");
    }
  };'''

content = re.sub(handlestart_pattern, new_handlestart, content)

# 4. Add progress polling effect before return statement
# Find the point just before "return ("
return_pattern = r'(const handlePointerUp = \(\) => \{[\s\S]*?\n  \};)\n\n  return \('
progress_effect = r'''\1

  // Poll for progress when analysis is running
  useEffect(() => {
    if (!analysisId || progressStatus === "completed" || progressStatus === "failed") {
      return;
    }

    const interval = setInterval(async () => {
      try {
        const resp = await fetch(`/api/analysis/progress?analysis_id=${encodeURIComponent(analysisId)}`);
        if (!resp.ok) {
          setProgressStatus("failed");
          setProgressMessage("Failed to fetch progress");
          return;
        }
        const data = await resp.json() as {
          status: "in_progress" | "completed" | "failed";
          progress_percent: number;
          project_status: "creating" | "merging";
          message: string;
          video_id?: string;
        };
        setProgressStatus(data.status);
        setProgressPercent(data.progress_percent);
        setProgressMessage(data.message);
        setProjectStatus(data.project_status);
        if (data.video_id) {
          setVideoId(data.video_id);
        }
        if (data.status === "completed") {
          setIsRunning(false);
          // Navigate to ReviewPage after a short delay
          setTimeout(() => {
            const vidId = data.video_id || videoId || "";
            window.location.hash = `#/review?video_id=${encodeURIComponent(vidId)}`;
          }, 500);
        } else if (data.status === "failed") {
          setIsRunning(false);
        }
      } catch (error) {
        setProgressStatus("failed");
        setProgressMessage(error instanceof Error ? error.message : "Network error");
      }
    }, 1500);

    return () => clearInterval(interval);
  }, [analysisId, progressStatus, videoId]);

  return ('''

content = re.sub(return_pattern, progress_effect, content)

# 5. Replace AnalysisProgressPanel with ProgressWindow in JSX
old_jsx = r'''\{isRunning && runId && \(
        <AnalysisProgressPanel
          runId={runId}
          onCompleted=\{\(csvPath\) => \{
            setIsRunning\(false\);
            setRunId\(null\);
            window\.dispatchEvent\(new CustomEvent\("scyt:open-review", \{ detail: \{ csvPath \} \}\)\);
          \}\}
          onStopped=\{\(\) => \{
            setIsRunning\(false\);
            setRunId\(null\);
          \}\}
        />
      \)\}'''

new_jsx = '''{isRunning && analysisId ? (
        <ProgressWindow 
          visible={true}
          statusText={`${projectStatus === "creating" ? "Creating" : "Merging"} project... ${progressMessage} (${progressPercent}%)`}
        />
      ) : isRunning && runId ? (
        <AnalysisProgressPanel
          runId={runId}
          onCompleted={(csvPath) => {
            setIsRunning(false);
            setRunId(null);
            window.dispatchEvent(new CustomEvent("scyt:open-review", { detail: { csvPath } }));
          }}
          onStopped={() => {
            setIsRunning(false);
            setRunId(null);
          }}
        />
      ) : null}'''

content = re.sub(old_jsx, new_jsx, content)

# Write the modified file
with open('src/web/frontend/src/pages/AnalysisPage.tsx', 'w') as f:
    f.write(content)

print("Modified AnalysisPage.tsx successfully")
