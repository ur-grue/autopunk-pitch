import JobPage from "./client";

export function generateStaticParams() {
  return [
    { id: "a1b2c3d4-5678-90ab-cdef-222222222222" },
    { id: "b2c3d4e5-5678-90ab-cdef-333333333333" },
  ];
}

export default function Page() {
  return <JobPage />;
}
