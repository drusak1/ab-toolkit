import { createBrowserRouter, RouterProvider } from "react-router-dom";
import Layout from "./components/Layout";
import HomePage from "./pages/HomePage";
import DatasourcesPage from "./pages/DatasourcesPage";
import MetricsPage from "./pages/MetricsPage";
import DesignPage from "./pages/DesignPage";
import LaunchPage from "./pages/LaunchPage";
import ResultsPage from "./pages/ResultsPage";

const router = createBrowserRouter([
  {
    path: "/",
    element: <Layout />,
    children: [
      { index: true, element: <HomePage /> },
      { path: "datasources", element: <DatasourcesPage /> },
      { path: "metrics", element: <MetricsPage /> },
      { path: "design", element: <DesignPage /> },
      { path: "launch", element: <LaunchPage /> },
      { path: "results", element: <ResultsPage /> },
    ],
  },
]);

export default function App() {
  return <RouterProvider router={router} />;
}
