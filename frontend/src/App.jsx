import { useEffect, useState } from 'react'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const navItems = [
  { label: 'Обзор', icon: '◈' },
  { label: 'Футболисты', icon: '◉' },
  { label: 'Клубы', icon: '▣' },
  { label: 'Трансферы', icon: '↗' },
  { label: 'Аналитика', icon: '⌁' },
  { label: 'Избранное', icon: '☆' },
]

const recentTransfers = [
  { player: 'Kylian Mbappe', from: 'Paris Saint-Germain', to: 'Real Madrid', fee: '€180m', date: '01.07.2024' },
  { player: 'Jude Bellingham', from: 'Borussia Dortmund', to: 'Real Madrid', fee: '€103m', date: '14.06.2023' },
  { player: 'Declan Rice', from: 'West Ham United', to: 'Arsenal', fee: '€116m', date: '15.07.2023' },
]

function App() {
  const [activeSection, setActiveSection] = useState('Обзор')
  const [apiStatus, setApiStatus] = useState('Проверка связи')
  const [session, setSession] = useState(() => JSON.parse(localStorage.getItem('transfer-session') || 'null'))
  const [authOpen, setAuthOpen] = useState(false)
  const [clubToOpen, setClubToOpen] = useState(null)

  useEffect(() => {
    fetch(`${API_URL}/health`)
      .then((response) => {
        if (!response.ok) throw new Error('Backend unavailable')
        return response.json()
      })
      .then(() => setApiStatus('Система онлайн'))
      .catch(() => setApiStatus('Backend не подключен'))
  }, [])

  const logout = () => { localStorage.removeItem('transfer-session'); setSession(null) }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-mark">
          <span className="brand-symbol">TR</span>
          <div>
            <strong>Transfer Room</strong>
            <small>FOOTBALL INTELLIGENCE</small>
          </div>
        </div>

        <nav className="navigation" aria-label="Основная навигация">
          <span className="nav-caption">Рабочее пространство</span>
          {navItems.map((item) => (
            <button
              className={`nav-item ${activeSection === item.label ? 'active' : ''}`}
              key={item.label}
              onClick={() => setActiveSection(item.label)}
            >
              <span className="nav-icon">{item.icon}</span>
              {item.label}
            </button>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="connection-state"><span className="status-dot" /> {apiStatus}</div>
          <div className="profile-chip"><span className="avatar">{session ? session.user.username[0].toUpperCase() : 'Г'}</span><span><b>{session ? session.user.username : 'Гость'}</b><small>{session ? 'Авторизован' : 'Только просмотр'}</small></span></div>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div>
            <p className="eyebrow">СЕЗОН 2024 / 25</p>
            <h1>{activeSection}</h1>
          </div>
          <div className="header-actions">
            <a className="icon-button" aria-label="Открыть BetBoom" href="https://app.betboom.ru/QZMezjNa67" target="_blank" rel="noreferrer">♧</a>
            {session ? <button className="login-button" onClick={logout}>Выйти <span>↗</span></button> : <button className="login-button" onClick={() => setAuthOpen(true)}>Войти <span>→</span></button>}
          </div>
        </header>

        {activeSection === 'Обзор' && <Dashboard />}
        {activeSection === 'Футболисты' && <PlayersSection session={session} onRequireAuth={() => setAuthOpen(true)} onClubSelect={(id) => { setClubToOpen(id); setActiveSection('Клубы') }} />}
        {activeSection === 'Клубы' && <ClubsSection initialSelectedId={clubToOpen} onOpened={() => setClubToOpen(null)} />}
        {activeSection === 'Трансферы' && <TransfersSection onClubSelect={(id) => { setClubToOpen(id); setActiveSection('Клубы') }} />}
        {activeSection === 'Аналитика' && <AnalyticsSection />}
        {activeSection === 'Избранное' && <FavoritesSection session={session} onRequireAuth={() => setAuthOpen(true)} />}
      </main>
      {authOpen && <AuthModal onClose={() => setAuthOpen(false)} onSuccess={(nextSession) => { setSession(nextSession); setAuthOpen(false) }} />}
    </div>
  )
}

function Dashboard() {
  return (
    <div className="dashboard-content">
      <section className="welcome-band">
        <div>
          <p className="eyebrow warm">ЦЕНТР ДАННЫХ</p>
          <h2>Трансферный рынок<br /><em>в одном месте.</em></h2>
          <p className="welcome-copy">Отслеживайте переходы, изучайте составы и находите главное в цифрах.</p>
        </div>
        <div className="orbital-mark" aria-hidden="true"><span>24/25</span></div>
      </section>

      <section className="stats-grid" aria-label="Основные показатели">
        <StatCard label="Футболисты" value="1 248" detail="+12% к прошлому месяцу" trend="up" />
        <StatCard label="Клубы" value="86" detail="14 лиг в базе" />
        <StatCard label="Трансферы" value="3 691" detail="За текущий сезон" />
        <StatCard label="Общая стоимость" value="€2.8B" detail="По известным суммам" trend="up" />
      </section>

      <section className="content-grid">
        <div className="panel transfers-panel">
          <div className="panel-heading"><div><p className="eyebrow">ПОСЛЕДНИЕ СОБЫТИЯ</p><h3>Свежие трансферы</h3></div><button className="text-button">Все трансферы <span>→</span></button></div>
          <div className="transfer-list">
            {recentTransfers.map((transfer) => <TransferRow key={transfer.player} {...transfer} />)}
          </div>
        </div>
        <div className="panel insight-panel">
          <div className="panel-heading"><div><p className="eyebrow">РЫНОК</p><h3>Активность по месяцам</h3></div><span className="period-label">2024</span></div>
          <div className="chart-wrap"><div className="chart-y"><span>€1.2B</span><span>€800M</span><span>€400M</span><span>€0</span></div><div className="chart"><div className="chart-line" /><div className="chart-area" />{['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 'Июл'].map((month, index) => <span className="chart-label" style={{ left: `${index * 16.5}%` }} key={month}>{month}</span>)}</div></div>
          <div className="chart-note"><span className="legend-dot" /> Общая стоимость переходов <strong>€486M</strong></div>
        </div>
      </section>
    </div>
  )
}

function StatCard({ label, value, detail, trend }) {
  return <article className="stat-card"><p>{label}</p><strong>{value}</strong><span className={trend ? 'positive' : ''}>{trend && '↗ '}{detail}</span></article>
}

function TransferRow({ player, from, to, fee, date }) {
  return <div className="transfer-row"><div className="player-badge">{player.split(' ').map((word) => word[0]).join('')}</div><div className="transfer-player"><strong>{player}</strong><span>{date}</span></div><div className="club-route"><span>{from}</span><b>→</b><span>{to}</span></div><strong className="fee">{fee}</strong></div>
}

function ComingSoon({ title }) {
  return <section className="empty-state"><span className="empty-icon">⌁</span><p className="eyebrow">РАЗДЕЛ В РАЗРАБОТКЕ</p><h2>{title}</h2><p>Здесь появится рабочий раздел проекта после подключения соответствующих REST endpoints.</p></section>
}

function useCatalog(endpoint, params) {
  const [state, setState] = useState({ data: [], loading: true })
  const query = new URLSearchParams(Object.entries(params).filter(([, value]) => value !== '' && value !== null && value !== undefined)).toString()
  useEffect(() => {
    let active = true
    setState((current) => ({ ...current, loading: true }))
    fetch(`${API_URL}${endpoint}?${query}`)
      .then((response) => response.json())
      .then((data) => active && setState({ data: Array.isArray(data) ? data : [], loading: false }))
      .catch(() => active && setState({ data: [], loading: false }))
    return () => { active = false }
  }, [endpoint, query])
  return state
}

function PlayersSection({ session, onRequireAuth, onClubSelect }) {
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [selected, setSelected] = useState(null)
  const [filters, setFilters] = useState({ position: '', nationality: '', sort: 'name_asc' })
  const { data, loading } = useCatalog('/players', { search, ...filters, page, limit: 6 })
  const update = (key, value) => { setFilters((current) => ({ ...current, [key]: value })); setPage(1) }
  if (selected) return <PlayerDetails player={selected} onBack={() => setSelected(null)} onClubSelect={onClubSelect} />
  return <section className="data-section"><CatalogHeader eyebrow="КАТАЛОГ / ФУТБОЛИСТЫ" title="Футболисты" count={data.length} search={search} onSearch={(value) => { setSearch(value); setPage(1) }} placeholder="Поиск по имени..." /><div className="filter-row"><select value={filters.position} onChange={(event) => update('position', event.target.value)}><option value="">Все позиции</option><option value="Forward">Нападающие</option><option value="Midfielder">Полузащитники</option><option value="Defender">Защитники</option><option value="Goalkeeper">Вратари</option></select><input placeholder="Гражданство" value={filters.nationality} onChange={(event) => update('nationality', event.target.value)} /><select value={filters.sort} onChange={(event) => update('sort', event.target.value)}><option value="name_asc">Имя: А → Я</option><option value="name_desc">Имя: Я → А</option><option value="value_desc">Стоимость: сначала выше</option><option value="value_asc">Стоимость: сначала ниже</option></select></div><PlayerTable data={data} loading={loading} session={session} onRequireAuth={onRequireAuth} onSelect={(id) => fetch(`${API_URL}/players/${id}`).then((response) => response.json()).then(setSelected)} /><Pager page={page} hasNext={data.length === 6} onPage={setPage} /></section>
}

function ClubsSection({ initialSelectedId, onOpened }) {
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [selected, setSelected] = useState(null)
  const [filters, setFilters] = useState({ country: '', league: '', sort: 'name_asc' })
  const { data, loading } = useCatalog('/clubs', { search, ...filters, page, limit: 6 })
  const update = (key, value) => { setFilters((current) => ({ ...current, [key]: value })); setPage(1) }
  useEffect(() => { if (initialSelectedId) fetch(`${API_URL}/clubs/${initialSelectedId}`).then((response) => response.json()).then(setSelected).finally(onOpened) }, [initialSelectedId, onOpened])
  if (selected) return <ClubDetails club={selected} onBack={() => setSelected(null)} />
  return <section className="data-section"><CatalogHeader eyebrow="КАТАЛОГ / КЛУБЫ" title="Клубы" count={data.length} search={search} onSearch={(value) => { setSearch(value); setPage(1) }} placeholder="Поиск по названию..." /><div className="filter-row"><input placeholder="Страна" value={filters.country} onChange={(event) => update('country', event.target.value)} /><input placeholder="Лига" value={filters.league} onChange={(event) => update('league', event.target.value)} /><select value={filters.sort} onChange={(event) => update('sort', event.target.value)}><option value="name_asc">Название: А → Я</option><option value="name_desc">Название: Я → А</option><option value="country_asc">По стране</option><option value="squad_desc">По размеру состава</option></select></div><ClubTable data={data} loading={loading} onSelect={(id) => fetch(`${API_URL}/clubs/${id}`).then((response) => response.json()).then(setSelected)} /><Pager page={page} hasNext={data.length === 6} onPage={setPage} /></section>
}

function TransfersSection({ onClubSelect }) {
  const [filters, setFilters] = useState({ player_id: '', club_id: '', fee_min: '', fee_max: '', sort: 'date_desc', page: 1 })
  const [selected, setSelected] = useState(null)
  const { data, loading } = useCatalog('/transfers', { ...filters, limit: 6 })
  const update = (key, value) => setFilters((current) => ({ ...current, [key]: value, page: 1 }))
  if (selected) return <TransferDetails transfer={selected} onBack={() => setSelected(null)} onClubSelect={onClubSelect} />
  return <section className="data-section"><CatalogHeader eyebrow="РЫНОК / ТРАНСФЕРЫ" title="Трансферы" count={data.length} /><div className="filter-row transfer-filters"><input placeholder="ID игрока" value={filters.player_id} onChange={(event) => update('player_id', event.target.value)} /><input placeholder="ID клуба" value={filters.club_id} onChange={(event) => update('club_id', event.target.value)} /><input type="number" placeholder="Сумма от" value={filters.fee_min} onChange={(event) => update('fee_min', event.target.value)} /><input type="number" placeholder="Сумма до" value={filters.fee_max} onChange={(event) => update('fee_max', event.target.value)} /><select value={filters.sort} onChange={(event) => update('sort', event.target.value)}><option value="date_desc">Сначала новые</option><option value="date_asc">Сначала старые</option><option value="fee_desc">Сначала дорогие</option><option value="fee_asc">Сначала дешёвые</option></select></div><TransferTable data={data} loading={loading} onClubSelect={onClubSelect} onSelect={(id) => fetch(`${API_URL}/transfers/${id}`).then((response) => response.json()).then(setSelected)} /><Pager page={filters.page} hasNext={data.length === 6} onPage={(page) => setFilters((current) => ({ ...current, page }))} /></section>
}

function CatalogHeader({ eyebrow, title, count, search, onSearch, placeholder }) { return <div className="section-intro"><div><p className="eyebrow">{eyebrow}</p><h2>{title}</h2></div><div className="header-controls">{onSearch && <input className="catalog-search" value={search} onChange={(event) => onSearch(event.target.value)} placeholder={placeholder} />}<span className="record-count">{count} на странице</span></div></div> }
function Pager({ page, hasNext, onPage }) { return <div className="pager"><button disabled={page === 1} onClick={() => onPage(page - 1)}>← Назад</button><span>Страница {page}</span><button disabled={!hasNext} onClick={() => onPage(page + 1)}>Вперёд →</button></div> }
function PlayerTable({ data, loading, session, onRequireAuth, onSelect }) { const toggleFavorite = (event, playerId) => { event.stopPropagation(); if (!session) { onRequireAuth(); return } fetch(`${API_URL}/favorites/${playerId}`, { method: 'POST', headers: { Authorization: `Bearer ${session.access_token}` } }) }; return <DataState loading={loading} empty={!data.length}>{<table><thead><tr><th>Футболист</th><th>Позиция</th><th>Текущий клуб</th><th>Гражданство</th><th>Описание</th><th aria-label="Избранное" /></tr></thead><tbody>{data.map((item) => <tr className="clickable-row" key={item.id} onClick={() => onSelect(item.id)}><td><span className="table-player"><span className="mini-photo">{item.photo_url ? <img src={item.photo_url} alt="" /> : item.name.split(' ').map((word) => word[0]).join('')}</span>{item.name}</span></td><td>{item.position || '—'}</td><td>{item.current_club_name || '—'}</td><td>{item.nationality || '—'}</td><td className="description-cell">{item.description || '—'}</td><td><button className="favorite-button" aria-label={`Добавить ${item.name} в избранное`} onClick={(event) => toggleFavorite(event, item.id)}>☆</button></td></tr>)}</tbody></table>}</DataState> }

function FavoritesSection({ session, onRequireAuth }) {
  const [state, setState] = useState({ data: [], loading: true })
  useEffect(() => {
    if (!session) { setState({ data: [], loading: false }); return undefined }
    fetch(`${API_URL}/favorites`, { headers: { Authorization: `Bearer ${session.access_token}` } })
      .then((response) => response.ok ? response.json() : Promise.reject(new Error('Не удалось загрузить избранное')))
      .then((data) => setState({ data, loading: false }))
      .catch(() => setState({ data: [], loading: false }))
  }, [session])
  if (!session) return <section className="empty-state"><span className="empty-icon">☆</span><p className="eyebrow">ЛИЧНАЯ КОЛЛЕКЦИЯ</p><h2>Войдите, чтобы сохранять игроков</h2><button className="primary-button favorite-login" onClick={onRequireAuth}>Войти в систему</button></section>
  const removeFavorite = (favoriteId, playerId) => fetch(`${API_URL}/favorites/${playerId}`, { method: 'DELETE', headers: { Authorization: `Bearer ${session.access_token}` } }).then((response) => { if (!response.ok) throw new Error('Не удалось удалить игрока'); setState((current) => ({ ...current, data: current.data.filter((favorite) => favorite.id !== favoriteId) })) }).catch(() => {})
  return <section className="data-section"><CatalogHeader eyebrow="ЛИЧНАЯ КОЛЛЕКЦИЯ" title="Избранное" count={state.data.length} /><div className="favorite-grid">{state.loading ? <p className="table-message">Загрузка данных...</p> : state.data.length ? state.data.map((favorite) => <article className="favorite-card" key={favorite.id}><div className="mini-photo">{favorite.player.photo_url ? <img src={favorite.player.photo_url} alt="" /> : favorite.player.name.split(' ').map((word) => word[0]).join('')}</div><strong>{favorite.player.name}</strong><span>{favorite.player.position || 'Позиция не указана'}</span><button className="favorite-remove" aria-label={`Удалить ${favorite.player.name} из избранного`} onClick={() => removeFavorite(favorite.id, favorite.player_id)}>Удалить</button></article>) : <p className="table-message">В избранном пока ничего нет.</p>}</div></section>
}
function ClubTable({ data, loading, onSelect }) { return <DataState loading={loading} empty={!data.length}>{<table><thead><tr><th>Клуб</th><th>Страна</th><th>Лига</th><th></th></tr></thead><tbody>{data.map((item) => <tr className="clickable-row" key={item.id} onClick={() => onSelect(item.id)}><td><span className="table-club"><span className="mini-logo">{item.logo_url && <img src={item.logo_url} alt="" />}</span>{item.name}</span></td><td>{item.country || '—'}</td><td>{item.league || '—'}</td><td className="row-action">Открыть →</td></tr>)}</tbody></table>}</DataState> }
function ClubLink({ id, name, onSelect }) { return onSelect ? <button className="club-link" onClick={(event) => { event.stopPropagation(); onSelect(id) }}>{name}</button> : <span>{name}</span> }
function TransferTable({ data, loading, onClubSelect, onSelect }) { return <DataState loading={loading} empty={!data.length}>{<table><thead><tr><th>Футболист</th><th>Откуда</th><th>Куда</th><th>Дата</th><th>Сумма</th><th>Тип</th></tr></thead><tbody>{data.map((item) => <tr className="clickable-row" key={item.id} onClick={() => onSelect(item.id)}><td>{item.player_name || `Игрок #${item.player_id}`}</td><td><ClubLink id={item.from_club_id} name={item.from_club_name} onSelect={onClubSelect} /></td><td><ClubLink id={item.to_club_id} name={item.to_club_name} onSelect={onClubSelect} /></td><td>{item.transfer_date || '—'}</td><td className="fee">{item.fee ? `€${Number(item.fee).toLocaleString('ru-RU')}` : 'Бесплатно'}</td><td>{item.transfer_type || '—'}</td></tr>)}</tbody></table>}</DataState> }
function DataState({ loading, empty, children }) { return <div className="data-table-wrap">{loading ? <p className="table-message">Загрузка данных...</p> : empty ? <p className="table-message">Ничего не найдено.</p> : children}</div> }
function PlayerDetails({ player, onBack, onClubSelect }) { const [apiData, setApiData] = useState(null); useEffect(() => { fetch(`${API_URL}/players/${player.id}/api-data`).then((response) => response.ok ? response.json() : null).then(setApiData) }, [player.id]); return <section className="player-details"><button className="text-button back-button" onClick={onBack}>← Вернуться к списку</button><div className="player-hero"><div className="large-player-photo">{player.photo_url ? <img src={player.photo_url} alt={player.name} /> : player.name.split(' ').map((word) => word[0]).join('')}</div><div><p className="eyebrow">КАРТОЧКА ФУТБОЛИСТА</p><h2>{player.name}</h2><p className="player-meta">{player.position || 'Позиция не указана'} · {player.nationality || 'Гражданство не указано'} · {player.current_club_name || 'Без клуба'}</p><p className="player-birth">Дата рождения: {player.birth_date || 'нет данных API'} · Рыночная стоимость: {player.market_value ? `€${Number(player.market_value).toLocaleString('ru-RU')}` : 'нет данных API'}</p><p className="player-description">{player.description || 'Описание не предоставляется API-Football.'}</p></div></div><div className="panel detail-panel"><div className="panel-heading"><div><p className="eyebrow">ИСТОРИЯ</p><h3>Откуда → куда</h3></div></div>{player.transfers.length ? player.transfers.map((transfer) => <div className="history-row" key={transfer.id}><span>{transfer.transfer_date || 'Дата неизвестна'}</span><strong><ClubLink id={transfer.from_club_id} name={transfer.from_club_name} onSelect={onClubSelect} /> <b>→</b> <ClubLink id={transfer.to_club_id} name={transfer.to_club_name} onSelect={onClubSelect} /></strong><b>{transfer.fee ? `€${Number(transfer.fee).toLocaleString('ru-RU')}` : 'Сумма не указана API'}</b></div>) : <p className="table-message">История трансферов пока отсутствует.</p>}</div><ApiDataPanel title="Полный ответ API-Football" data={apiData} /></section> }
function ClubDetails({ club, onBack }) { const [apiData, setApiData] = useState(null); useEffect(() => { fetch(`${API_URL}/clubs/${club.id}/api-data`).then((response) => response.ok ? response.json() : null).then(setApiData) }, [club.id]); return <section className="player-details"><button className="text-button back-button" onClick={onBack}>← Вернуться к списку</button><div className="player-hero club-hero"><div className="club-logo">{club.logo_url ? <img src={club.logo_url} alt={club.name} /> : club.name[0]}</div><div><p className="eyebrow">КАРТОЧКА КЛУБА</p><h2>{club.name}</h2><p className="player-meta">{club.country || 'Страна не указана'} · {club.league || 'Лига не указана'} · основан в {club.founded || 'нет данных API'}</p><p className="player-birth">Стадион: {club.stadium || 'нет данных API'}</p><p className="player-description">{club.description || 'Описание не предоставляется API-Football.'}</p></div></div><div className="squad-panel panel"><p className="eyebrow">СОСТАВ</p><h3>Текущие футболисты · {club.current_players.length}</h3><div className="squad-list">{club.current_players.slice(0, 36).map((player) => <span className="squad-player" key={player.id}>{player.name} <small>{player.position || 'Позиция не указана'}</small></span>)}</div></div><div className="club-history-grid"><HistoryPanel title="Входящие трансферы" data={club.incoming_transfers} /><HistoryPanel title="Исходящие трансферы" data={club.outgoing_transfers} /></div><ApiDataPanel title="Полный ответ API-Football" data={apiData} /></section> }
function HistoryPanel({ title, data }) { return <div className="panel detail-panel"><p className="eyebrow">ТРАНСФЕРЫ КЛУБА</p><h3>{title}</h3>{data.length ? data.slice(0, 15).map((transfer) => <div className="history-row compact" key={transfer.id}><span>{transfer.transfer_date}</span><strong>{transfer.player_name}</strong><b>{transfer.fee ? `€${Number(transfer.fee).toLocaleString('ru-RU')}` : 'Бесплатно'}</b></div>) : <p className="table-message">Нет данных</p>}</div> }
function ApiDataPanel({ title, data }) { return <details className="api-data-panel"><summary>{title} <span>{data ? 'данные загружены' : 'загрузка...'}</span></summary>{data && <pre>{JSON.stringify(data, null, 2)}</pre>}</details> }
function TransferDetails({ transfer, onBack, onClubSelect }) { const [apiData, setApiData] = useState(null); useEffect(() => { fetch(`${API_URL}/transfers/${transfer.id}/api-data`).then((response) => response.ok ? response.json() : null).then(setApiData) }, [transfer.id]); return <section className="player-details"><button className="text-button back-button" onClick={onBack}>← Вернуться к списку</button><div className="panel detail-panel"><p className="eyebrow">КАРТОЧКА ТРАНСФЕРА</p><h2>{transfer.player_name || `Игрок #${transfer.player_id}`}</h2><div className="history-row"><span>{transfer.transfer_date || 'Дата неизвестна'}</span><strong><ClubLink id={transfer.from_club_id} name={transfer.from_club_name} onSelect={onClubSelect} /> <b>→</b> <ClubLink id={transfer.to_club_id} name={transfer.to_club_name} onSelect={onClubSelect} /></strong><b>{transfer.fee ? `€${Number(transfer.fee).toLocaleString('ru-RU')}` : 'Сумма не указана API'}</b></div><p className="player-description">Тип перехода: {transfer.transfer_type || 'не указан API-Football'}</p></div><ApiDataPanel title="Полный ответ API-Football" data={apiData} /></section> }
function AuthModal({ onClose, onSuccess }) { const [mode, setMode] = useState('login'); const [form, setForm] = useState({ username: '', email: '', password: '' }); const [error, setError] = useState(''); const submit = (event) => { event.preventDefault(); const endpoint = mode === 'login' ? '/auth/login' : '/auth/register'; fetch(`${API_URL}${endpoint}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(mode === 'login' ? { email: form.email, password: form.password } : form) }).then(async (response) => { const body = await response.json(); if (!response.ok) throw new Error(body.detail || 'Не удалось выполнить запрос'); return body }).then((body) => { localStorage.setItem('transfer-session', JSON.stringify(body)); onSuccess(body) }).catch((requestError) => setError(requestError.message)) }; return <div className="modal-backdrop" onClick={onClose}><form className="auth-modal" onSubmit={submit} onClick={(event) => event.stopPropagation()}><button type="button" className="modal-close" onClick={onClose}>×</button><p className="eyebrow">TRANSFER ROOM</p><h2>{mode === 'login' ? 'Вход в систему' : 'Регистрация'}</h2>{mode === 'register' && <input required minLength="3" placeholder="Имя пользователя" value={form.username} onChange={(event) => setForm({ ...form, username: event.target.value })} />}<input required type="email" placeholder="Email" value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} /><input required minLength="8" type="password" placeholder="Пароль" value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })} />{error && <p className="form-error">{error}</p>}<button className="primary-button" type="submit">{mode === 'login' ? 'Войти' : 'Создать аккаунт'}</button><button type="button" className="switch-auth" onClick={() => { setMode(mode === 'login' ? 'register' : 'login'); setError('') }}>{mode === 'login' ? 'Нет аккаунта? Зарегистрироваться' : 'Уже есть аккаунт? Войти'}</button></form></div> }

function AnalyticsSection() {
  const [summary, setSummary] = useState(null)
  useEffect(() => { fetch(`${API_URL}/analytics/summary`).then((response) => response.json()).then(setSummary).catch(() => setSummary(null)) }, [])
  return <section className="data-section"><div className="section-intro"><div><p className="eyebrow">ДАННЫЕ / СВОДКА</p><h2>Аналитика</h2></div></div>{summary ? <div className="analytics-grid"><StatCard label="Футболисты" value={summary.players_count} detail="В локальной базе" /><StatCard label="Клубы" value={summary.clubs_count} detail="В локальной базе" /><StatCard label="Трансферы" value={summary.transfers_count} detail="В локальной базе" /><StatCard label="Общая стоимость" value={`€${summary.total_fee}`} detail="Из известных сумм" /></div> : <p className="table-message">Не удалось загрузить аналитику.</p>}</section>
}

export default App
