import ProjectPage from "./client";

export function generateStaticParams() {
  return [
    { id: "d1a2b3c4-5678-90ab-cdef-111111111111" },
    { id: "e5f6a7b8-5678-90ab-cdef-444444444444" },
  ];
}

export default function Page() {
  return <ProjectPage />;
}
