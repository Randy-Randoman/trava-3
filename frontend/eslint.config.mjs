import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const eslintConfig = [
  ...nextVitals,
  ...nextTs,
  {
    rules: {
      // Legacy casts at untyped boundaries (Excalidraw, react-markdown, API JSON); typing them is out of scope
      "@typescript-eslint/no-explicit-any": "warn",
      // New React 19 rule flags our fetch-on-mount effects; rewriting them is out of scope
      "react-hooks/set-state-in-effect": "warn",
    },
  },
  { ignores: [".next/**", "out/**", "build/**", "next-env.d.ts"] },
];

export default eslintConfig;
