import { Navigate, Route, Routes } from 'react-router-dom';
import { AppShell } from './app/AppShell';
import { RunsLayout } from './routes/RunsLayout';
import { RunsIndex } from './routes/RunsIndex';
import { RunDetail } from './routes/RunDetail';

export default function App() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route path="/" element={<RunsLayout />}>
          <Route index element={<RunsIndex />} />
          <Route path="runs/:id" element={<RunDetail />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
