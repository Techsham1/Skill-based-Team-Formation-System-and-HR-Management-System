import React, { useEffect, useState } from 'react';
import { createEmployee, deleteEmployee, getEmployees } from '../utils/api';
import { toast } from '../utils/toast';

const CandidateManagement = () => {
  const [candidates, setCandidates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');
  const [form, setForm] = useState({
    name: '',
    skills: '',
    experience: '',
    role: '',
    score: '',
  });

  const loadCandidates = async () => {
    try {
      setLoading(true);
      setLoadError('');
      const data = await getEmployees();
      setCandidates(data);
    } catch (error) {
      console.error('Error loading candidates:', error);
      setLoadError(error.message || 'Unable to load candidates');
      setCandidates([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCandidates();
  }, []);

  const handleChange = (e) => {
    setForm((prev) => ({
      ...prev,
      [e.target.name]: e.target.value,
    }));
  };

  const handleAddCandidate = async (e) => {
    e.preventDefault();
    if (!form.name || !form.skills || !form.role) {
      toast.error('Please fill Name, Skills and Role');
      return;
    }

    try {
      const score = Number(form.score || 0);
      const generatedId = `CAND-${Date.now()}`;
      await createEmployee({
        employeeId: generatedId,
        name: form.name,
        skills: form.skills,
        experience: Number(form.experience || 0),
        role: form.role,
        score,
        performanceRating: Math.min(10, Math.max(0, score / 10)),
        skillLevel: Math.min(10, Math.max(1, Math.round(score || 1))),
        department: 'General',
        availability: 'Available',
        category: 'Full-time',
        status: 'Present',
      });
      toast.success('Candidate added');
      setForm({ name: '', skills: '', experience: '', role: '', score: '' });
      await loadCandidates();
    } catch (error) {
      toast.error(`Failed to add candidate: ${error.message}`);
    }
  };

  const handleDelete = async (id) => {
    try {
      await deleteEmployee(id);
      toast.success('Candidate removed');
      await loadCandidates();
    } catch (error) {
      toast.error(`Failed to remove candidate: ${error.message}`);
    }
  };

  return (
    <>
      <header className="header">
        <h1>Candidate Management</h1>
        <div className="user">Talent Pool</div>
      </header>

      <form className="employee-form" onSubmit={handleAddCandidate}>
        <h2>Add Candidate</h2>
        <div className="form-row">
          <div>
            <label htmlFor="name">Name</label>
            <input id="name" name="name" value={form.name} onChange={handleChange} placeholder="Candidate name" />
          </div>
          <div>
            <label htmlFor="role">Role</label>
            <input id="role" name="role" value={form.role} onChange={handleChange} placeholder="Frontend Engineer" />
          </div>
        </div>

        <label htmlFor="skills">Skills</label>
        <input id="skills" name="skills" value={form.skills} onChange={handleChange} placeholder="React, Node, SQL" />

        <div className="form-row">
          <div>
            <label htmlFor="experience">Experience</label>
            <input
              id="experience"
              name="experience"
              type="number"
              min="0"
              step="0.5"
              value={form.experience}
              onChange={handleChange}
              placeholder="3"
            />
          </div>
          <div>
            <label htmlFor="score">Score</label>
            <input
              id="score"
              name="score"
              type="number"
              min="0"
              max="100"
              value={form.score}
              onChange={handleChange}
              placeholder="82"
            />
          </div>
        </div>
        <button type="submit">Add Candidate</button>
      </form>

      <section className="table-container">
        <div className="table-toolbar">
          <strong>Candidate Table</strong>
        </div>
        {loading ? (
          <div className="empty-state">
            <h3>Loading candidates...</h3>
          </div>
        ) : loadError ? (
          <div className="empty-state">
            <h3>Could not load candidates</h3>
            <p>{loadError}</p>
            <button className="btn" onClick={loadCandidates}>
              Retry
            </button>
          </div>
        ) : candidates.length === 0 ? (
          <div className="empty-state">
            <h3>No candidates</h3>
            <p>Add candidates from the form above.</p>
          </div>
        ) : (
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Skills</th>
                  <th>Experience</th>
                  <th>Role</th>
                  <th>Score</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {candidates.map((candidate) => {
                  const candidateId = candidate.id || candidate.employeeId;
                  return (
                  <tr key={candidateId || `${candidate.name}-${candidate.role}`}>
                    <td>{candidate.name || '-'}</td>
                    <td className="truncate">{candidate.skills || '-'}</td>
                    <td>{candidate.experience || 0} yrs</td>
                    <td>{candidate.role || '-'}</td>
                    <td>{candidate.score || candidate.performanceRating || 0}</td>
                    <td>
                      <button className="delete-btn" onClick={() => handleDelete(candidateId)}>
                        Delete
                      </button>
                    </td>
                  </tr>
                )})}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </>
  );
};

export default CandidateManagement;
