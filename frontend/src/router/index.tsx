import { createBrowserRouter, Navigate } from "react-router-dom";

import AppLayout from "../layouts/AppLayout";
import PlaceholderPage from "../pages/PlaceholderPage";
import DashboardPage from "../pages/dashboard/DashboardPage";


export const router = createBrowserRouter([
  {
    path: "/",
    element: <AppLayout />,
    children: [
      { index: true, element: <Navigate to="/dashboard" replace /> },
      { path: "dashboard", element: <DashboardPage /> },
      { path: "datasets", element: <PlaceholderPage title="数据集" /> },
      { path: "models", element: <PlaceholderPage title="模型训练" /> },
      { path: "reports", element: <PlaceholderPage title="分析报告" /> },
    ],
  },
]);
