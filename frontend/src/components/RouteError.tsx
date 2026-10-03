import { useEffect } from "react";
import { useRouteError } from "react-router-dom";

import { ErrorFallback } from "./ErrorFallback.tsx";

export function RouteError() {
  const error = useRouteError();

  useEffect(() => {
    console.error(error);
  }, [error]);

  return <ErrorFallback />;
}
