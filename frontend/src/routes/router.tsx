import { createBrowserRouter } from "react-router-dom";

import { AuthProvider } from "../auth/AuthProvider.tsx";
import { RouteError } from "../components/RouteError.tsx";
import { AppLayout } from "../layouts/AppLayout.tsx";
import { DashboardPage } from "../pages/DashboardPage.tsx";
import { EmployeesPage } from "../pages/EmployeesPage.tsx";
import { LoginPage } from "../pages/LoginPage.tsx";
import { MessagesPage } from "../pages/MessagesPage.tsx";
import { NotFoundPage } from "../pages/NotFoundPage.tsx";
import { ReviewsPage } from "../pages/ReviewsPage.tsx";
import { ShiftsPage } from "../pages/ShiftsPage.tsx";
import { TelegramGroupsPage } from "../pages/TelegramGroupsPage.tsx";
import { UsersPage } from "../pages/UsersPage.tsx";
import { WorkObjectsPage } from "../pages/WorkObjectsPage.tsx";
import { AdminRoute } from "./AdminRoute.tsx";
import { ProtectedRoute } from "./ProtectedRoute.tsx";
import { RootRedirect } from "./RootRedirect.tsx";

export const router = createBrowserRouter([
  {
    element: <AuthProvider />,
    errorElement: <RouteError />,
    children: [
      { index: true, element: <RootRedirect /> },
      { path: "login", element: <LoginPage /> },
      {
        element: <ProtectedRoute />,
        children: [
          {
            element: <AppLayout />,
            children: [
              { path: "dashboard", element: <DashboardPage /> },
              { path: "reviews", element: <ReviewsPage /> },
              { path: "messages", element: <MessagesPage /> },
              { path: "shifts", element: <ShiftsPage /> },
              { path: "employees", element: <EmployeesPage /> },
              { path: "work-objects", element: <WorkObjectsPage /> },
              { path: "telegram-groups", element: <TelegramGroupsPage /> },
              {
                element: <AdminRoute />,
                children: [{ path: "users", element: <UsersPage /> }],
              },
            ],
          },
        ],
      },
      { path: "*", element: <NotFoundPage /> },
    ],
  },
]);
