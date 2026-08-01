import { AppShell } from "./components/layout/AppShell";
import { LayoutProvider } from "./components/layout/LayoutProvider";

function App() {
  return (
    <LayoutProvider>
      <AppShell />
    </LayoutProvider>
  );
}

export default App;
