// API service for backend communication
import {
  getEmployees as getEmployeesLocal,
  addEmployee as addEmployeeLocal,
  addEmployees as addEmployeesLocal,
  deleteEmployee as deleteEmployeeLocal,
  saveEmployees as saveEmployeesLocal,
  updateEmployeeStatus as updateEmployeeStatusLocal,
} from './storage';

const EMPLOYEE_API_BASE_URL =
  process.env.REACT_APP_EMPLOYEE_API_URL || 'http://localhost:8080/api/employees';
const TEAM_API_BASE_URL = process.env.REACT_APP_TEAM_API_URL || 'http://localhost:5000/api/team';
const ML_API_BASE_URL = process.env.REACT_APP_ML_API_URL || 'http://localhost:8080/api/ml';

const handleResponse = async (response) => {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'An error occurred' }));
    throw new Error(error.message || `HTTP error! status: ${response.status}`);
  }
  return response.json();
};

const isNetworkError = (error) =>
  String(error?.message || '').toLowerCase().includes('failed to fetch') ||
  String(error?.message || '').toLowerCase().includes('networkerror');

const employeeKey = (emp) =>
  String(emp?.employeeId || emp?.id || `${emp?.name || ''}-${emp?.role || ''}` || '').toLowerCase();

const mergeEmployees = (primary = [], secondary = []) => {
  const merged = [];
  const seen = new Set();
  [...primary, ...secondary].forEach((emp) => {
    const key = employeeKey(emp);
    if (!key || seen.has(key)) return;
    seen.add(key);
    merged.push(emp);
  });
  return merged;
};

// Employee APIs
export const getEmployees = async () => {
  try {
    const response = await fetch(EMPLOYEE_API_BASE_URL);
    const remote = await handleResponse(response);
    const local = getEmployeesLocal();
    const merged = mergeEmployees(remote, local);
    saveEmployeesLocal(merged);
    return merged;
  } catch (error) {
    if (isNetworkError(error)) {
      return getEmployeesLocal();
    }
    throw error;
  }
};

export const getEmployeeById = async (id) => {
  const response = await fetch(`${EMPLOYEE_API_BASE_URL}/${id}`);
  return handleResponse(response);
};

export const createEmployee = async (employeeData) => {
  try {
    const response = await fetch(EMPLOYEE_API_BASE_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(employeeData),
    });
    const created = await handleResponse(response);
    const local = getEmployeesLocal();
    const merged = mergeEmployees([created], local);
    saveEmployeesLocal(merged);
    return created;
  } catch (error) {
    if (isNetworkError(error)) {
      return addEmployeeLocal(employeeData);
    }
    throw error;
  }
};

export const createEmployees = async (employeesList) => {
  try {
    const results = await Promise.allSettled(employeesList.map((emp) => createEmployee(emp)));
    const successful = results.filter((r) => r.status === 'fulfilled').map((r) => r.value);
    const failed = results.filter((r) => r.status === 'rejected');

    if (failed.length > 0 && successful.length === 0) {
      const firstError = failed[0]?.reason?.message || 'Unable to create employees.';
      throw new Error(firstError);
    }

    if (failed.length > 0 && successful.length > 0) {
      console.warn(`${failed.length} employees failed to create`);
    }

    return successful;
  } catch (error) {
    if (isNetworkError(error)) {
      return addEmployeesLocal(employeesList);
    }
    throw error;
  }
};

export const updateEmployee = async (id, employeeData) => {
  try {
    const response = await fetch(`${EMPLOYEE_API_BASE_URL}/${id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(employeeData),
    });
    return handleResponse(response);
  } catch (error) {
    if (isNetworkError(error)) {
      const status = employeeData?.status || 'Present';
      const updated = updateEmployeeStatusLocal(id, status);
      return updated.find((emp) => emp.id === id) || { ...employeeData, id };
    }
    throw error;
  }
};

export const deleteEmployee = async (id) => {
  try {
    const response = await fetch(`${EMPLOYEE_API_BASE_URL}/${id}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: 'An error occurred' }));
      throw new Error(error.message || `HTTP error! status: ${response.status}`);
    }
    deleteEmployeeLocal(id);
    return true;
  } catch (error) {
    if (isNetworkError(error)) {
      deleteEmployeeLocal(id);
      return true;
    }
    throw error;
  }
};

// Team configuration + generation APIs (Python service)
export const getTeamConfig = async () => {
  const response = await fetch(`${TEAM_API_BASE_URL}/config`);
  return handleResponse(response);
};

export const saveTeamConfig = async (configData) => {
  const response = await fetch(`${TEAM_API_BASE_URL}/config`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(configData),
  });
  return handleResponse(response);
};

export const generateTeamWithAI = async (payload) => {
  const response = await fetch(`${ML_API_BASE_URL}/team-formation`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });
  return handleResponse(response);
};
