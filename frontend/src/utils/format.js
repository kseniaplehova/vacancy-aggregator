// Подписи и форматирование для показа вакансий.

const SOURCE_LABELS = {
  "greenhouse:issoft": "ISsoft",
  "greenhouse:coherentsolutions": "Coherent Solutions",
  "greenhouse:tripledotstudios": "Tripledot Studios",
  "lever:idt": "IDT",
  "lever:SatelliteInnovations": "Satellite Innovations",
};

// «lever:idt» → «IDT»: у сайтов компаний показываем название компании, а не сервиса найма.
export function sourceLabel(source) {
  return SOURCE_LABELS[source] || source.replace(/^(greenhouse|lever):/, "");
}

export function plural(count, one, few, many) {
  const mod10 = count % 10;
  const mod100 = count % 100;
  if (mod10 === 1 && mod100 !== 11) return one;
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) return few;
  return many;
}

export function vacanciesCount(count) {
  return `${count.toLocaleString("ru-RU")} ${plural(count, "вакансия", "вакансии", "вакансий")}`;
}

// Когда вакансия впервые попала в сервис: «сегодня», «вчера», «5 дней назад», дата.
export function seenAgo(iso) {
  const date = new Date(iso);
  const startOfDay = (value) => new Date(value.getFullYear(), value.getMonth(), value.getDate());
  const days = Math.round((startOfDay(new Date()) - startOfDay(date)) / 86_400_000);
  if (days <= 0) return "сегодня";
  if (days === 1) return "вчера";
  if (days < 30) return `${days} ${plural(days, "день", "дня", "дней")} назад`;
  return date.toLocaleDateString("ru-RU", { day: "numeric", month: "long", year: "numeric" });
}
