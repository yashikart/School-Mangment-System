import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
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

// School Admin Components
import SchoolAdminDashboard from './admin/SchoolAdminDashboard';
import TeachersManagement from './admin/TeachersManagement';
import StudentsManagement from './admin/StudentsManagement';
import ParentsManagement from './admin/ParentsManagement';
import ClassesManagement from './admin/ClassesManagement';
import TimetableManagement from './admin/TimetableManagement';
import HolidaysEvents from './admin/HolidaysEvents';
import Announcements from './admin/Announcements';
import LessonsView from './admin/LessonsView';
import Analytics from './admin/Analytics';

// Teacher Components
import TeacherDashboard from './teacher/TeacherDashboard';
import MyClasses from './teacher/MyClasses';
import MyStudents from './teacher/MyStudents';
import Attendance from './teacher/Attendance';

const Dashboard = () => {
  const { user } = useAuth();
  const isAdmin = user?.role === 'ADMIN';
  const isTeacher = user?.role === 'TEACHER';

  return (
    <Layout>
      <Routes>
        {isAdmin ? (
          // School Admin Routes
          <>
            <Route index element={<SchoolAdminDashboard />} />
            <Route path="/teachers" element={<TeachersManagement />} />
            <Route path="/students" element={<StudentsManagement />} />
            <Route path="/parents" element={<ParentsManagement />} />
            <Route path="/classes" element={<ClassesManagement />} />
            <Route path="/timetable" element={<TimetableManagement />} />
            <Route path="/holidays-events" element={<HolidaysEvents />} />
            <Route path="/announcements" element={<Announcements />} />
            <Route path="/lessons" element={<LessonsView />} />
            <Route path="/analytics" element={<Analytics />} />
          </>
        ) : isTeacher ? (
          // Teacher Routes
          <>
            <Route index element={<TeacherDashboard />} />
            <Route path="/classes" element={<MyClasses />} />
            <Route path="/classes/:classId/students" element={<MyStudents />} />
            <Route path="/students" element={<MyStudents />} />
            <Route path="/attendance" element={<Attendance />} />
          </>
        ) : (
          // Super Admin Routes
          <>
            <Route index element={<DashboardOverview />} />
            <Route path="/schools/:id/edit" element={<EditSchool />} />
            <Route path="/schools/:id" element={<SchoolDetails />} />
            <Route path="/schools" element={<SchoolList />} />
            <Route path="/create-school" element={<CreateSchool />} />
            <Route path="/admins/:id/edit" element={<EditAdmin />} />
            <Route path="/admins" element={<AdminList />} />
            <Route path="/create-admin" element={<CreateAdmin />} />
            <Route path="/users" element={<ViewAllUsers />} />
          </>
        )}
      </Routes>
    </Layout>
  );
};

export default Dashboard;
