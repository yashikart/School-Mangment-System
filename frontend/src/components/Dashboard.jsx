import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Layout from './Layout';
import DashboardOverview from './DashboardOverview';
import SchoolList from './SchoolList';
import CreateSchool from './CreateSchool';
import EditSchool from './EditSchool';
import SchoolDetails from './SchoolDetails';
import AdminList from './AdminList';
import CreateAdmin from './CreateAdmin';
import EditAdmin from './EditAdmin';
import ViewAllUsers from './ViewAllUsers';

const Dashboard = () => {
  return (
    <Layout>
      <Routes>
        <Route index element={<DashboardOverview />} />
        <Route path="/schools/:id/edit" element={<EditSchool />} />
        <Route path="/schools/:id" element={<SchoolDetails />} />
        <Route path="/schools" element={<SchoolList />} />
        <Route path="/create-school" element={<CreateSchool />} />
        <Route path="/admins/:id/edit" element={<EditAdmin />} />
        <Route path="/admins" element={<AdminList />} />
        <Route path="/create-admin" element={<CreateAdmin />} />
        <Route path="/users" element={<ViewAllUsers />} />
      </Routes>
    </Layout>
  );
};

export default Dashboard;
