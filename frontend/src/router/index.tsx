import { createBrowserRouter, Navigate } from "react-router-dom";

import AppLayout from "../layouts/AppLayout";
import LoginPage from "../pages/auth/LoginPage";
import RegisterPage from "../pages/auth/RegisterPage";
import DashboardPage from "../pages/dashboard/DashboardPage";
import DatasetCreatePage from "../pages/datasets/DatasetCreatePage";
import DatasetDetailPage from "../pages/datasets/DatasetDetailPage";
import DatasetListPage from "../pages/datasets/DatasetListPage";
import DatasetPreviewPage from "../pages/datasets/DatasetPreviewPage";
import DatasetProfilePage from "../pages/datasets/DatasetProfilePage";
import ModelEvaluationPage from "../pages/models/ModelEvaluationPage";
import ModelListPage from "../pages/models/ModelListPage";
import ModelTrainPage from "../pages/models/ModelTrainPage";
import PlaceholderPage from "../pages/PlaceholderPage";
import ProtectedRoute from "./ProtectedRoute";


export const router = createBrowserRouter([
  { path: "/login", element: <LoginPage /> },
  { path: "/register", element: <RegisterPage /> },
  {
    path: "/",
    element: <ProtectedRoute />,
    children: [
      {
        element: <AppLayout />,
        children: [
          { index: true, element: <Navigate to="/dashboard" replace /> },
          { path: "dashboard", element: <DashboardPage /> },
          { path: "datasets", element: <DatasetListPage /> },
          { path: "datasets/create", element: <DatasetCreatePage /> },
          { path: "datasets/:id", element: <DatasetDetailPage /> },
          { path: "datasets/:id/preview", element: <DatasetPreviewPage /> },
          { path: "datasets/:id/profile", element: <DatasetProfilePage /> },
          { path: "models", element: <ModelListPage /> },
          { path: "models/train", element: <ModelTrainPage /> },
          { path: "models/:id/evaluation", element: <ModelEvaluationPage /> },
          { path: "reports", element: <PlaceholderPage title="分析报告" /> },
        ],
      },
    ],
  },
]);
