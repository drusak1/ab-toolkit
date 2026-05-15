import { NavLink, Outlet } from "react-router-dom";

type Item = { to: string; label: string; icon: string; end?: boolean };

const SECTIONS: { label?: string; items: Item[] }[] = [
  {
    items: [
      { to: "/", label: "Главная", icon: "🏠", end: true },
    ],
  },
  {
    label: "Данные",
    items: [
      { to: "/datasources", label: "Источники", icon: "🗂" },
      { to: "/metrics", label: "Метрики", icon: "📊" },
    ],
  },
  {
    label: "Эксперименты",
    items: [
      { to: "/design", label: "Дизайн", icon: "🧪" },
      { to: "/launch", label: "Запуск", icon: "🚀" },
      { to: "/results", label: "Результаты", icon: "📈" },
    ],
  },
];

export default function Layout() {
  return (
    <div className="shell">
      <aside className="sidebar-nav">
        <div className="brand">AB Calc</div>
        {SECTIONS.map((s, i) => (
          <div key={i}>
            {s.label && <div className="section-label">{s.label}</div>}
            {s.items.map((it) => (
              <NavLink key={it.to} to={it.to} end={it.end} className={({ isActive }) => (isActive ? "active" : "")}>
                <span className="icon">{it.icon}</span>
                {it.label}
              </NavLink>
            ))}
          </div>
        ))}
      </aside>
      <div className="main">
        <header className="topbar2">
          <div className="muted">DuckDB datasource engine</div>
          <div className="right">
            <span className="muted" style={{ fontSize: 13 }}>v0.1.0</span>
            <div className="avatar">DR</div>
          </div>
        </header>
        <main className="page">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
