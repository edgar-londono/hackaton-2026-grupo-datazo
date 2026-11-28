(() => {
  const picker = document.getElementById("property-picker");
  const view = document.getElementById("property-view");
  const formatter = new Intl.NumberFormat("es-CO", { maximumFractionDigits: 0 });
  const areaFormatter = new Intl.NumberFormat("es-CO", { maximumFractionDigits: 2 });
  const money = (value) => value == null ? "Sin datos suficientes" : `COP ${formatter.format(value)}`;
  const text = (value, fallback = "Sin dato") => value == null || value === "" ? fallback : value;
  const list = (value) => Array.isArray(value) ? value : [];
  const labelCase = (value) => text(value).replaceAll("_", " ").replace(/\b\p{L}/gu, (letter) => letter.toLocaleUpperCase("es-CO"));
  const municipality = (value) => ({ medellin: "Medellín", itagui: "Itagüí" }[value] || labelCase(value));

  function row(label, value) {
    const item = document.createElement("div");
    item.className = "detail-row";
    const term = document.createElement("dt");
    term.textContent = label;
    const description = document.createElement("dd");
    description.textContent = value;
    item.append(term, description);
    return item;
  }

  function stat(value, label) {
    const item = document.createElement("div");
    item.className = "stat";
    const number = document.createElement("b");
    number.textContent = value;
    const caption = document.createElement("span");
    caption.textContent = label;
    item.append(number, caption);
    return item;
  }

  function render(record, index, count) {
    const property = record.inmueble;
    const market = record.mercado;
    const price = market.precio_m2;
    const environment = record.entorno;
    const station = environment.estacion_mas_cercana;
    const article = document.createElement("div");
    const heading = document.createElement("h2");
    heading.textContent = record.id_inmueble;
    const subtitle = document.createElement("p");
    subtitle.className = "property-subtitle";
    const area = property.area_m2 == null ? "Área sin dato" : `${areaFormatter.format(property.area_m2)} m²`;
    subtitle.textContent = `${labelCase(property.barrio)}, ${municipality(property.municipio)} · ${area}`;

    const priceBlock = document.createElement("div");
    priceBlock.className = "price-block";
    const label = document.createElement("p");
    label.className = "price-label";
    label.textContent = "Mediana del precio anunciado por m²";
    const priceValue = document.createElement("p");
    priceValue.className = "price-value";
    priceValue.textContent = money(price.mediana);
    const range = document.createElement("p");
    range.className = "price-range";
    range.textContent = `${money(price.minimo)} a ${money(price.maximo)}`;
    priceBlock.append(label, priceValue, range);

    const stats = document.createElement("div");
    stats.className = "stat-grid";
    stats.append(
      stat(formatter.format(price.n), "Anuncios comparables"),
      stat(text(market.confianza.nivel, "No calculada"), "Confianza"),
      stat(`${formatter.format(environment.radio_busqueda_m)} m`, "Radio del entorno")
    );

    const details = document.createElement("dl");
    details.className = "detail-grid";
    details.append(
      row("Dirección", text(property.direccion)),
      row("Estado del inmueble", labelCase(property.estado_texto)),
      row("Zona de mercado", labelCase(property.zona)),
      row("Precisión de coordenadas", labelCase(property.coordenadas.precision)),
      row("Estación más cercana", station ? `${station.nombre} (${formatter.format(station.distancia_m)} m)` : "Sin datos"),
      row("Tratamiento POT", record.norma.estado === "pendiente_capa" ? "Pendiente: falta la capa de tratamientos" : labelCase(record.norma.estado))
    );

    const facilitiesTitle = document.createElement("h3");
    facilitiesTitle.className = "subsection-title";
    facilitiesTitle.textContent = "Equipamientos cercanos";
    const facilities = document.createElement("ul");
    facilities.className = "category-list";
    Object.entries(environment.equipamientos_en_radio || {}).forEach(([category, amount]) => {
      const item = document.createElement("li");
      const name = document.createElement("span");
      name.textContent = labelCase(category);
      const total = document.createElement("strong");
      total.textContent = formatter.format(amount);
      item.append(name, total);
      facilities.append(item);
    });

    const status = document.createElement("p");
    status.className = "status";
    status.textContent = `Confianza ${labelCase(text(market.confianza.nivel, "no calculada"))}: ${text(market.confianza.motivo, "No hay explicación disponible.")}`;

    const note = document.createElement("p");
    note.className = "data-note";
    const missing = list(record.datos_faltantes).map((item) => typeof item === "string" ? item : item.campo || item.dato).filter(Boolean);
    note.textContent = missing.length ? `Datos faltantes o no disponibles: ${missing.join(", ")}.` : "La ficha no registra datos faltantes para este inmueble.";

    const links = document.createElement("div");
    links.className = "property-links";
    const fullJson = document.createElement("a");
    fullJson.href = `data/fichas/${record.id_inmueble}.json`;
    fullJson.textContent = "Abrir datos JSON";
    const fullCard = document.createElement("a");
    fullCard.href = `data/cards/${record.id_inmueble}.md`;
    fullCard.textContent = "Abrir ficha completa";
    links.append(fullJson, fullCard);

    article.append(heading, subtitle, priceBlock, stats, details, facilitiesTitle, facilities, status, note, links);
    view.replaceChildren(article);
    picker.querySelectorAll("button").forEach((button, buttonIndex) => {
      button.setAttribute("aria-pressed", String(buttonIndex === index));
    });
    const liveTitle = document.createElement("span");
    liveTitle.className = "eyebrow";
    liveTitle.textContent = `Ficha ${String(index + 1).padStart(2, "0")} de ${String(count).padStart(2, "0")}`;
    view.prepend(liveTitle);
  }

  async function start() {
    const ids = Array.from({ length: 11 }, (_, index) => `INM-${String(index + 1).padStart(2, "0")}`);
    const records = await Promise.all(ids.map(async (id) => {
      const response = await fetch(`data/fichas/${id}.json`);
      if (!response.ok) throw new Error(`No se pudo cargar ${id}`);
      return response.json();
    }));

    records.forEach((record, index) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "property-choice";
      button.setAttribute("aria-pressed", "false");
      const id = document.createElement("span");
      id.textContent = record.id_inmueble;
      const arrow = document.createElement("small");
      arrow.textContent = "↗";
      button.append(id, arrow);
      button.addEventListener("click", () => render(record, index, records.length));
      picker.append(button);
    });
    render(records[0], 0, records.length);
  }

  start().catch((error) => {
    view.replaceChildren();
    const message = document.createElement("p");
    message.className = "status-error";
    message.textContent = "No se pudieron cargar las fichas. Abre la página desde el sitio publicado.";
    view.append(message);
    console.error(error);
  });
})();
