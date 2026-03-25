import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { createEmployee, createEmployees } from '../utils/api';
import { parseCSV, downloadCSV } from '../utils/csvParser';
import { toast } from '../utils/toast';

const AddEmployee = () => {
  const navigate = useNavigate();
  const fileInputRef = useRef(null);

  const [formData, setFormData] = useState({
    employeeId: '',
    name: '',
    department: '',
    role: '',
    skills: '',
    skillLevel: 1,
    experience: 0,
    category: 'Full-time',
    availability: 'Available',
    performanceRating: 0,
  });

  const [showSuccess, setShowSuccess] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');
  const [csvError, setCsvError] = useState('');
  const [csvSuccess, setCsvSuccess] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const departments = ['Engineering', 'Marketing', 'Sales', 'HR', 'Finance', 'Operations', 'IT', 'Design'];
  const categories = ['Full-time', 'Part-time', 'Contract', 'Intern', 'Freelance'];
  const availabilityOptions = ['Available', 'Busy', 'On Leave', 'Unavailable'];

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]:
        name === 'skillLevel' || name === 'experience' || name === 'performanceRating'
          ? parseFloat(value) || 0
          : value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    if (!formData.name || !formData.department || !formData.role) {
      setError('Please fill in required fields (Name, Department, Role)');
      setLoading(false);
      return;
    }

    try {
      await createEmployee(formData);
      toast.success('Employee added successfully');
      setShowSuccess(true);
      setSuccessMessage('Employee added successfully. Redirecting to employee list...');
      setFormData({
        employeeId: '',
        name: '',
        department: '',
        role: '',
        skills: '',
        skillLevel: 1,
        experience: 0,
        category: 'Full-time',
        availability: 'Available',
        performanceRating: 0,
      });

      setTimeout(() => {
        setShowSuccess(false);
        navigate('/employees');
      }, 2000);
    } catch (submitError) {
      const errorMsg = submitError.message || 'Failed to add employee. Please try again.';
      setError(errorMsg);
      toast.error(errorMsg);
      console.error('Error adding employee:', submitError);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    if (!file.name.endsWith('.csv')) {
      setCsvError('Please upload a CSV file');
      setCsvSuccess('');
      return;
    }

    setCsvError('');
    setCsvSuccess('');
    setLoading(true);

    const reader = new FileReader();
    reader.onload = async (event) => {
      try {
        const csvText = event.target.result;
        const employees = parseCSV(csvText);

        if (employees.length === 0) {
          setCsvError('No valid employee data found in CSV file');
          setLoading(false);
          return;
        }

        const created = await createEmployees(employees);
        const successMsg = `Successfully imported ${created.length} employee(s)`;
        setCsvSuccess(successMsg);
        toast.success(successMsg);

        if (fileInputRef.current) {
          fileInputRef.current.value = '';
        }

        setTimeout(() => navigate('/employees'), 2000);
      } catch (uploadError) {
        const errorMsg = `Error importing CSV: ${uploadError.message}`;
        setCsvError(errorMsg);
        toast.error(errorMsg);
        console.error('Error importing CSV:', uploadError);
      } finally {
        setLoading(false);
      }
    };

    reader.onerror = () => {
      setCsvError('Error reading file');
      setLoading(false);
    };

    reader.readAsText(file);
  };

  return (
    <>
      <header className="header">
        <h1>Add New Employee</h1>
        <div className="user">Admin Portal</div>
      </header>

      <section className="panel">
        <h2>Import Employee Data (CSV)</h2>
        <p>
          Expected columns: Employee ID, Name, Skills, Skill Level, Experience (years), Category,
          Availability, Performance Rating, Department, Role.
        </p>
        <div className="table-toolbar" style={{ padding: '12px 0 0', borderBottom: 'none' }}>
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv"
            onChange={handleFileUpload}
            className="input-control"
          />
          <button
            type="button"
            className="btn"
            onClick={() => {
              const template =
                'Employee ID,Name,Skills,Skill Level,Experience (years),Category,Availability,Performance Rating,Department,Role\nEMP001,John Doe,JavaScript React Node.js,8,5,Full-time,Available,8.5,Engineering,Software Engineer\nEMP002,Jane Smith,Python Django SQL,7,3,Full-time,Available,7.8,Engineering,Backend Developer';
              downloadCSV(template, 'employee_template.csv');
            }}
          >
            Download Template
          </button>
        </div>

        {csvError && <div className="message error">{csvError}</div>}
        {csvSuccess && <div className="message success">{csvSuccess}</div>}
      </section>

      <div className="divider-label">Or add one employee manually</div>

      {showSuccess && <div className="success-message">{successMessage}</div>}
      {error && <div className="message error">{error}</div>}

      <form className="employee-form" onSubmit={handleSubmit}>
        <h2>Add Employee Manually</h2>

        <label htmlFor="employeeId">Employee ID</label>
        <input
          type="text"
          id="employeeId"
          name="employeeId"
          value={formData.employeeId}
          onChange={handleChange}
          placeholder="Optional"
        />

        <div className="form-row">
          <div>
            <label htmlFor="name">Full Name *</label>
            <input
              type="text"
              id="name"
              name="name"
              value={formData.name}
              onChange={handleChange}
              required
            />
          </div>
          <div>
            <label htmlFor="department">Department *</label>
            <select
              id="department"
              name="department"
              value={formData.department}
              onChange={handleChange}
              required
            >
              <option value="">Select Department</option>
              {departments.map((dept) => (
                <option key={dept} value={dept}>
                  {dept}
                </option>
              ))}
            </select>
          </div>
        </div>

        <label htmlFor="role">Role *</label>
        <input type="text" id="role" name="role" value={formData.role} onChange={handleChange} required />

        <label htmlFor="skills">Skills</label>
        <input
          type="text"
          id="skills"
          name="skills"
          value={formData.skills}
          onChange={handleChange}
          placeholder="Comma-separated skills"
        />

        <div className="form-row">
          <div>
            <label htmlFor="skillLevel">Skill Level (1-10)</label>
            <input
              type="number"
              id="skillLevel"
              name="skillLevel"
              value={formData.skillLevel}
              onChange={handleChange}
              min="1"
              max="10"
            />
          </div>
          <div>
            <label htmlFor="experience">Experience (years)</label>
            <input
              type="number"
              id="experience"
              name="experience"
              value={formData.experience}
              onChange={handleChange}
              min="0"
              step="0.5"
            />
          </div>
        </div>

        <div className="form-row">
          <div>
            <label htmlFor="category">Category</label>
            <select id="category" name="category" value={formData.category} onChange={handleChange}>
              {categories.map((cat) => (
                <option key={cat} value={cat}>
                  {cat}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="availability">Availability</label>
            <select
              id="availability"
              name="availability"
              value={formData.availability}
              onChange={handleChange}
            >
              {availabilityOptions.map((avail) => (
                <option key={avail} value={avail}>
                  {avail}
                </option>
              ))}
            </select>
          </div>
        </div>

        <label htmlFor="performanceRating">Performance Rating (0-10)</label>
        <input
          type="number"
          id="performanceRating"
          name="performanceRating"
          value={formData.performanceRating}
          onChange={handleChange}
          min="0"
          max="10"
          step="0.1"
        />

        <button type="submit" disabled={loading}>
          {loading ? (
            <>
              <span className="loading-spinner" />
              Saving...
            </>
          ) : (
            'Add Employee'
          )}
        </button>
      </form>
    </>
  );
};

export default AddEmployee;
