interface SessionFile {
  display_name: string;
  csv_path: string;
}

interface Props {
  files: SessionFile[];
  onLoad: (csvPath: string) => void;
}

export function SessionPicker({ files, onLoad }: Props) {
  return (
    <div className="session-picker">
      <h4>Session picker</h4>
      {files.length === 0 ? (
        <p>No CSV files found.</p>
      ) : (
        files.map((file) => (
          <button
            key={file.csv_path}
            type="button"
            className="session-pick-item"
            onClick={() => onLoad(file.csv_path)}
          >
            {file.display_name}
          </button>
        ))
      )}
    </div>
  );
}
