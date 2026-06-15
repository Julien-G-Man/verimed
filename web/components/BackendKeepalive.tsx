"use client";

import { useEffect } from "react";

import { pingBackendHealth } from "../lib/api";

const FIVE_MINUTES_MS = 5 * 60 * 1000;

export default function BackendKeepalive() {
  useEffect(() => {
    void pingBackendHealth();

    const intervalId = window.setInterval(() => {
      void pingBackendHealth();
    }, FIVE_MINUTES_MS);

    return () => {
      window.clearInterval(intervalId);
    };
  }, []);

  return null;
}
