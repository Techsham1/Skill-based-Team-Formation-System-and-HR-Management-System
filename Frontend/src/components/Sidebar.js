import React from 'react';
import { Link } from 'react-router-dom';
import './Sidebar.css';

const Sidebar = ({ sidebarOpen, setSidebarOpen, currentPath, onLogout }) => {
  const menuItems = [
    { path: '/', icon: 'DB', label: 'Dashboard' },
    { path: '/candidates', icon: 'CM', label: 'Candidates' },
    { path: '/candidate-import', icon: 'IM', label: 'Candidate Import' },
    { path: '/team', icon: 'AI', label: 'Team Formation' },
    { path: '/results', icon: 'RS', label: 'Results' },
  ];

  const handleLinkClick = () => {
    if (window.innerWidth <= 900) {
      setSidebarOpen(false);
    }
  };

  return (
    <>
      {sidebarOpen && <div className="sidebar-overlay" onClick={() => setSidebarOpen(false)} />}
      <aside className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
        <h2>Skillbase AI</h2>
        <ul>
          {menuItems.map((item) => (
            <li key={item.path}>
              <Link
                to={item.path}
                className={currentPath === item.path ? 'active' : ''}
                onClick={handleLinkClick}
              >
                <span className="icon">{item.icon}</span>
                <span className="label">{item.label}</span>
              </Link>
            </li>
          ))}
        </ul>
        <button className="sidebar-logout" onClick={onLogout}>
          Logout
        </button>
      </aside>
    </>
  );
};

export default Sidebar;
