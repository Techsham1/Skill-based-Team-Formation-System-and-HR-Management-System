import React, { useRef, useState } from 'react';
import { createEmployees, getEmployees } from '../utils/api';
import { downloadCSV, parseCSV } from '../utils/csvParser';
import { toast } from '../utils/toast';

const REQUIRED_HEADERS = [
  'Employee ID',
  'Name',
  'Skills',
  'Skill Level',
  'Experience (years)',
  'Category',
  'Availability',
  'Performance Rating',
  'Department',
  'Role',
];

const normalizeHeader = (value) => value.trim().toLowerCase().replace(/\s+/g, ' ');

const validateHeaderFormat = (headerLine) => {
  const actualHeaders = headerLine.split(',').map((h) => h.trim());
  if (actualHeaders.length !== REQUIRED_HEADERS.length) {
    return `Invalid column count. Expected ${REQUIRED_HEADERS.length} columns.`;
  }

  for (let i = 0; i < REQUIRED_HEADERS.length; i += 1) {
    if (normalizeHeader(actualHeaders[i]) !== normalizeHeader(REQUIRED_HEADERS[i])) {
      return `Header mismatch at column ${i + 1}. Expected "${REQUIRED_HEADERS[i]}" but got "${actualHeaders[i]}".`;
    }
  }

  return '';
};

const CandidateImport = () => {
  const fileInputRef = useRef(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const handleDownloadTemplate = () => {
    const templateRows = [
      REQUIRED_HEADERS.join(','),
      'EMP001,John Doe,"React,Node.js,SQL",8,4,Full-time,Available,8.6,Engineering,Frontend Developer',
      'EMP002,Jane Smith,"Python,ML,Statistics",9,5,Full-time,Available,9.1,Data,ML Engineer',
    ];
    downloadCSV(templateRows.join('\n'), 'candidate_import_template.csv');
  };

  const handleFileUpload = (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    if (!file.name.toLowerCase().endsWith('.csv')) {
      setError('Please upload a .csv file only.');
      setMessage('');
      return;
    }

    setLoading(true);
    setError('');
    setMessage('');

    const reader = new FileReader();
    reader.onload = async (e) => {
      try {
        const content = String(e.target?.result || '');
        const lines = content.split('\n').filter((line) => line.trim());
        if (lines.length < 2) {
          throw new Error('CSV must contain header and at least one data row.');
        }

        const headerError = validateHeaderFormat(lines[0]);
        if (headerError) {
          throw new Error(headerError);
        }

        const candidates = parseCSV(content);
        if (candidates.length === 0) {
          throw new Error('No valid candidate records found in CSV.');
        }

        const before = await getEmployees();
        const existingIds = new Set(
          before
            .map((emp) => String(emp?.employeeId || emp?.id || '').toLowerCase())
            .filter(Boolean)
        );

        const seenInFile = new Set();
        const deduped = candidates.filter((candidate) => {
          const candidateId = String(candidate?.employeeId || '').toLowerCase();
          if (!candidateId) return true;
          if (seenInFile.has(candidateId)) return false;
          seenInFile.add(candidateId);
          return !existingIds.has(candidateId);
        });

        if (deduped.length === 0) {
          setMessage('All candidates in the file already exist. Nothing to import.');
          toast.success('All candidates already exist. Nothing imported.');
          if (fileInputRef.current) {
            fileInputRef.current.value = '';
          }
          return;
        }

        const created = await createEmployees(deduped);
        const after = await getEmployees();
        const createdCount = Math.max(created.length, after.length - before.length);
        if (createdCount <= 0) {
          throw new Error('Candidates were not saved. Please check employee backend connection.');
        }
        const skipped = candidates.length - deduped.length;
        const successText =
          skipped > 0
            ? `Imported ${createdCount} candidate(s). Skipped ${skipped} duplicate(s).`
            : `Imported ${createdCount} candidate(s) successfully.`;
        setMessage(successText);
        toast.success(successText);
        if (fileInputRef.current) {
          fileInputRef.current.value = '';
        }
      } catch (uploadError) {
        const errText = uploadError.message || 'Import failed.';
        setError(errText);
        toast.error(errText);
      } finally {
        setLoading(false);
      }
    };

    reader.onerror = () => {
      setLoading(false);
      setError('Failed to read the selected file.');
    };

    reader.readAsText(file);
  };

  return (
    <>
      <header className="header">
        <h1>Candidate Import</h1>
        <div className="user">Admin User</div>
      </header>

      <section className="config-grid">
        <article className="panel panel-strong">
          <h2>CSV Upload</h2>
          <p>Import candidates using the exact format shown on the right panel.</p>
          <div className="import-actions">
            <input
              ref={fileInputRef}
              className="input-control"
              type="file"
              accept=".csv"
              onChange={handleFileUpload}
              disabled={loading}
            />
            <button type="button" className="btn btn-neutral" onClick={handleDownloadTemplate}>
              Download Template
            </button>
          </div>
          {loading && <div className="message success">Uploading and validating CSV...</div>}
          {message && <div className="message success">{message}</div>}
          {error && <div className="message error">{error}</div>}
        </article>

        <article className="panel panel-strong">
          <h2>Required Format</h2>
          <p>Headers must match exactly in this same order:</p>
          <div className="format-list">
            {REQUIRED_HEADERS.map((header, index) => (
              <div className="format-item" key={header}>
                <span>{index + 1}.</span>
                <strong>{header}</strong>
              </div>
            ))}
          </div>
        </article>
      </section>
    </>
  );
};

export default CandidateImport;
