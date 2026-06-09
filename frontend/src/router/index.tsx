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
import ModelDetailPage from "../pages/models/ModelDetailPage";
import ModelEvaluationPage from "../pages/models/ModelEvaluationPage";
import ModelListPage from "../pages/models/ModelListPage";
import ModelTrainPage from "../pages/models/ModelTrainPage";
import AIAnalysisPage from "../pages/ai/AIAnalysisPage";
import ReportGeneratorPage from "../pages/ai/ReportGeneratorPage";
import BatchPredictionPage from "../pages/prediction/BatchPredictionPage";
import IganSinglePredictionPage from "../pages/prediction/IganSinglePredictionPage";
import PredictionHistoryPage from "../pages/prediction/PredictionHistoryPage";
import RegressionBatchPredictionPage from "../pages/prediction/RegressionBatchPredictionPage";
import RegressionSinglePredictionPage from "../pages/prediction/RegressionSinglePredictionPage";
import ReportListPage from "../pages/reports/ReportListPage";
import AIConfigPage from "../pages/settings/AIConfigPage";
import SettingsPage from "../pages/settings/SettingsPage";
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
          { path: "models/:id", element: <ModelDetailPage /> },
          { path: "models/:id/evaluation", element: <ModelEvaluationPage /> },
          { path: "prediction/igan/single", element: <IganSinglePredictionPage /> },
          { path: "prediction/batch", element: <BatchPredictionPage /> },
          { path: "prediction/regression/single", element: <RegressionSinglePredictionPage /> },
          { path: "prediction/regression/batch", element: <RegressionBatchPredictionPage /> },
          { path: "prediction/history", element: <PredictionHistoryPage /> },
          { path: "ai/dataset-analysis", element: <AIAnalysisPage /> },
          { path: "ai/model-analysis", element: <AIAnalysisPage /> },
          { path: "ai/report-generator", element: <ReportGeneratorPage /> },
          { path: "reports", element: <ReportListPage /> },
          { path: "settings", element: <SettingsPage /> },
          { path: "settings/ai", element: <AIConfigPage /> },
        ],
      },
    ],
  },
]);
