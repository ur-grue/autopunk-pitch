import SubtitleEditorPage from "./client";

export function generateStaticParams() {
  return [
    { id: "a1b2c3d4-5678-90ab-cdef-222222222222", language: "fr" },
    { id: "a1b2c3d4-5678-90ab-cdef-222222222222", language: "es" },
    { id: "a1b2c3d4-5678-90ab-cdef-222222222222", language: "de" },
  ];
}

export default function Page() {
  return <SubtitleEditorPage />;
}
